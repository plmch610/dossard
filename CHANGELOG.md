# Changelog

## Non publié

- Ajoute la pagination de `GET /athletes` : `?limit=` (1 à 100, défaut 50) et `?offset=` (≥ 0, défaut 0), hors bornes en 422.
- Ajoute `POST /athletes/import` : import du CSV des licenciés (remplace `scripts/legacy/import_licencies.py`, supprimé).
- Ajoute `GET /athletes/{athlete_id}` : détail d'un athlète (404 si inconnu).
