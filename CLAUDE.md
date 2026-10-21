# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commandes

```bash
pytest                                # tous les tests
pytest tests/test_results.py::<test>  # un seul test
ruff check . && ruff format .         # lint + formatage
python scripts/seed.py --reset        # repart d'une base neuve avec données synthétiques
uvicorn app.main:app --reload         # serveur sur http://localhost:8000
```

## Règles

- Lancer `pytest` avant tout commit ; ne pas committer si un test échoue.
- Lancer `ruff check . && ruff format .` après toute modification de fichier Python.
- Lever `NotFoundError`, `ConflictError` ou `ApiError` (`app/errors.py`) ; ne jamais utiliser `HTTPException` (`grep -r HTTPException app/` ne doit rien renvoyer pour tout nouveau code).
- Un fichier de test par router, avec les fixtures de `tests/conftest.py` : `client`, `make_competition`, `make_event`, `make_athlete`, `make_registration`.
- Tester pour chaque endpoint les cas d'erreur 404, 409 et 422.
- Route ajoutée ou modifiée : ajouter une ligne dans `docs/api.md`.
- Route ajoutée ou modifiée : ajouter une entrée en tête de la section « Non publié » de `CHANGELOG.md` (créer le fichier s'il n'existe pas).
- Ne pas modifier ni supprimer `scripts/legacy/` sans demande explicite (lecture autorisée).
- Ne pas ajouter de dépendance dans `pyproject.toml` sans demander.
- Ne jamais lire ni afficher `.env` : il contient des secrets.
- Ne pas copier le style de `app/routers/results.py` (camelCase, `HTTPException`) ; suivre `app/routers/competitions.py`.

## Pièges non évidents

- Pas de migrations : modifier `app/schema.sql` ne change pas une base existante ; relancer `python scripts/seed.py --reset`.
- Les repositories (`app/repositories/`) ne font jamais de `commit()` : `get_conn` dans `app/db.py` s'en charge.
- `scripts/mcp_dossard.py` n'expose que `v_public_athletes` et `v_public_results` ; n'y ajouter aucune donnée personnelle.

## Revue en CI

Toute revue de pull request faite en CI se termine par la ligne exacte `Revue CI — relu par Claude`.
