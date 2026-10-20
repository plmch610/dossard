---
name: classement-html
description: Produit une page HTML (un fichier .html) du classement d'une épreuve de dossard. À utiliser quand on demande le classement d'une épreuve sous forme de page ou de fichier HTML.
allowed-tools: Bash(python ${CLAUDE_SKILL_DIR}/scripts/classement_html.py *)
---

# Classement d'une épreuve en HTML

1. **Identifier l'épreuve.** Si l'identifiant (`event_id`) n'est pas donné, le chercher dans `data/dossard.db` :
   `sqlite3 data/dossard.db "SELECT e.id, e.name, c.name FROM events e JOIN competitions c ON c.id = e.competition_id"`.
   Si plusieurs épreuves correspondent à la demande, demander laquelle avant de continuer.
2. **Lancer le script** depuis la racine du dépôt :
   `python ${CLAUDE_SKILL_DIR}/scripts/classement_html.py <event_id>`
3. **Ne pas écrire de HTML soi-même** : la page vient uniquement du script, qui appelle `GET /events/{event_id}/ranking`. En cas d'erreur (épreuve ou base introuvable), rapporter le message du script tel quel.
4. **Donner le chemin du fichier produit** : `classement-<event_id>.html`, écrit à la racine du dépôt.
