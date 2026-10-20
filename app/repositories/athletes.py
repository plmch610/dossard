from __future__ import annotations

import csv
import io
import sqlite3
from datetime import date, datetime

from pydantic import ValidationError

from app.categories import age_category
from app.errors import ApiError, ConflictError, NotFoundError
from app.schemas import AthleteCreate, AthleteOut, ImportLineError, ImportReport

IMPORT_COLUMNS = (
    "nom",
    "prenom",
    "date_naissance",
    "sexe",
    "club",
    "licence",
    "certificat_valide_jusqu",
)


class InvalidImportError(ApiError):
    status_code = 422
    code = "invalid_import"


def _to_athlete(row: sqlite3.Row) -> AthleteOut:
    birth_date = date.fromisoformat(row["birth_date"])
    certificate = row["medical_certificate_valid_until"]
    return AthleteOut(
        id=row["id"],
        first_name=row["first_name"],
        last_name=row["last_name"],
        birth_date=birth_date,
        sex=row["sex"],
        club=row["club"],
        license_number=row["license_number"],
        medical_certificate_valid_until=date.fromisoformat(certificate) if certificate else None,
        category=age_category(birth_date),
    )


def list_athletes(conn: sqlite3.Connection, club: str | None = None) -> list[AthleteOut]:
    sql = "SELECT * FROM athletes"
    params: tuple[str, ...] = ()
    if club is not None:
        sql += " WHERE club = ?"
        params = (club,)
    sql += " ORDER BY last_name, first_name, id"
    return [_to_athlete(row) for row in conn.execute(sql, params)]


def get_athlete(conn: sqlite3.Connection, athlete_id: int) -> AthleteOut:
    row = conn.execute("SELECT * FROM athletes WHERE id = ?", (athlete_id,)).fetchone()
    if row is None:
        raise NotFoundError(f"Athlète {athlete_id} introuvable")
    return _to_athlete(row)


def create_athlete(conn: sqlite3.Connection, data: AthleteCreate) -> AthleteOut:
    existing = conn.execute(
        "SELECT id FROM athletes WHERE license_number = ?", (data.license_number,)
    ).fetchone()
    if existing is not None:
        raise ConflictError(f"Licence {data.license_number} déjà enregistrée")

    certificate = data.medical_certificate_valid_until
    cursor = conn.execute(
        "INSERT INTO athletes (first_name, last_name, birth_date, sex, club, license_number,"
        " medical_certificate_valid_until) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            data.first_name,
            data.last_name,
            data.birth_date.isoformat(),
            data.sex.value,
            data.club,
            data.license_number,
            certificate.isoformat() if certificate else None,
        ),
    )
    row = conn.execute("SELECT * FROM athletes WHERE id = ?", (cursor.lastrowid,)).fetchone()
    return _to_athlete(row)


def _parse_french_date(value: str) -> date | None:
    value = value.strip()
    if not value:
        return None
    return datetime.strptime(value, "%d/%m/%Y").date()


def _import_row(row: dict[str, str]) -> AthleteCreate:
    return AthleteCreate(
        last_name=row["nom"].strip(),
        first_name=row["prenom"].strip(),
        birth_date=_parse_french_date(row["date_naissance"]),
        sex=row["sexe"].strip(),
        club=row["club"].strip() or None,
        license_number=row["licence"].strip(),
        medical_certificate_valid_until=_parse_french_date(row["certificat_valide_jusqu"]),
    )


def _validation_message(error: ValidationError) -> str:
    return "; ".join(
        f"{'.'.join(str(part) for part in item['loc'])} : {item['msg']}" for item in error.errors()
    )


def import_athletes(conn: sqlite3.Connection, content: bytes) -> ImportReport:
    """Importe l'export CSV de la fédération ; une ligne invalide n'arrête pas les autres."""
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InvalidImportError("Le fichier doit être encodé en UTF-8") from exc

    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    missing = [name for name in IMPORT_COLUMNS if name not in (reader.fieldnames or [])]
    if missing:
        raise InvalidImportError(f"Colonnes manquantes : {', '.join(missing)}")

    created = 0
    skipped = 0
    errors: list[ImportLineError] = []
    for row in reader:
        line = reader.line_num
        if None in row or None in row.values():
            errors.append(ImportLineError(line=line, message="Nombre de colonnes incorrect"))
            continue
        try:
            data = _import_row(row)
            create_athlete(conn, data)
        except ConflictError:
            skipped += 1
        except ValidationError as exc:
            errors.append(ImportLineError(line=line, message=_validation_message(exc)))
        except ValueError as exc:
            errors.append(ImportLineError(line=line, message=f"Date invalide : {exc}"))
        else:
            created += 1
    return ImportReport(created=created, skipped=skipped, errors=errors)
