from datetime import date
from pathlib import Path

SAMPLE_CSV = Path(__file__).parent.parent / "scripts" / "legacy" / "licencies_exemple.csv"
CSV_HEADERS = {"Content-Type": "text/csv"}


def test_create_athlete_returns_201_with_category(client):
    birth_date = date(date.today().year - 30, 3, 2)

    response = client.post(
        "/athletes",
        json={
            "first_name": "Inès",
            "last_name": "Morel",
            "birth_date": birth_date.isoformat(),
            "sex": "F",
            "license_number": "DOS-000042",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["category"] == "SENIOR"
    assert body["club"] is None


def test_create_athlete_rejects_duplicate_license(client, make_athlete):
    athlete = make_athlete()

    response = client.post(
        "/athletes",
        json={
            "first_name": "Hugo",
            "last_name": "Lemaire",
            "birth_date": "1995-05-20",
            "sex": "M",
            "license_number": athlete["license_number"],
        },
    )

    assert response.status_code == 409
    assert response.json()["error"]["code"] == "conflict"


def test_list_athletes_filters_by_club(client, make_athlete):
    make_athlete("Durand", club="AC Rivebelle")
    make_athlete("Petit", club="Stade Nordval")

    response = client.get("/athletes", params={"club": "AC Rivebelle"})

    assert response.status_code == 200
    assert [a["last_name"] for a in response.json()] == ["Durand"]


def test_get_athlete_returns_200_with_category(client, make_athlete):
    athlete = make_athlete("Durand", club="AC Rivebelle")

    response = client.get(f"/athletes/{athlete['id']}")

    assert response.status_code == 200
    assert response.json() == athlete


def test_get_athlete_unknown_returns_404(client):
    response = client.get("/athletes/999")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_get_athlete_invalid_id_returns_422(client):
    response = client.get("/athletes/abc")

    assert response.status_code == 422


def _import_sample(client):
    return client.post("/athletes/import", content=SAMPLE_CSV.read_bytes(), headers=CSV_HEADERS)


def test_import_athletes_sample_file_returns_report(client):
    response = _import_sample(client)

    assert response.status_code == 200
    body = response.json()
    assert (body["created"], body["skipped"]) == (17, 1)
    assert [e["line"] for e in body["errors"]] == [15, 16]
    assert len(client.get("/athletes").json()) == 17


def test_import_athletes_twice_skips_existing_licenses(client):
    first = _import_sample(client).json()

    response = _import_sample(client)

    assert response.status_code == 200
    body = response.json()
    assert (body["created"], body["skipped"]) == (0, 18)
    assert body["errors"] == first["errors"]


def test_import_athletes_skips_license_already_in_database(client, make_athlete):
    athlete = make_athlete()
    csv_text = (
        "nom;prenom;date_naissance;sexe;club;licence;certificat_valide_jusqu\n"
        f"Valette;Margaux;14/03/1998;F;;{athlete['license_number']};\n"
    )

    response = client.post("/athletes/import", content=csv_text, headers=CSV_HEADERS)

    assert response.status_code == 200
    assert response.json() == {"created": 0, "skipped": 1, "errors": []}


def test_import_athletes_missing_columns_returns_422(client):
    response = client.post("/athletes/import", content="nom;prenom\nA;B\n", headers=CSV_HEADERS)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_import"


def test_import_athletes_empty_body_returns_422(client):
    response = client.post("/athletes/import", content=b"", headers=CSV_HEADERS)

    assert response.status_code == 422


def test_import_athletes_invalid_encoding_returns_422(client):
    response = client.post("/athletes/import", content=b"\xff\xfe\x00", headers=CSV_HEADERS)

    assert response.status_code == 422


def test_import_athletes_is_not_shadowed_by_athlete_id_route(client):
    response = client.get("/athletes/import")

    assert response.status_code == 422
