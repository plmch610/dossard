#!/usr/bin/env python3
"""Hook PreToolUse : bloque quelques commandes shell destructrices.

Lit le JSON de Claude Code sur l'entrée standard. Sort avec le code 2 (et un
message sur la sortie d'erreur) si la commande Bash/PowerShell est dangereuse,
avec le code 0 dans tous les autres cas.
"""

import json
import re
import sys

OUTILS = {"Bash", "PowerShell"}

# Une commande composée (;, &&, ||, |, &, retour à la ligne) est analysée par segment.
SEPARATEURS = re.compile(r"[;&|\n]")
DROP = re.compile(r"\bDROP\s+(?:TABLE|VIEW)\b", re.IGNORECASE)
RM = re.compile(r"(?<![\w-])rm(?=\s)")
GIT_PUSH = re.compile(r"(?<![\w-])git\s(?:.*\s)?push(?=\s|$)")
OPTION = re.compile(r"(?<=\s)(--?[A-Za-z][\w-]*)")


def options(texte: str) -> list[str]:
    return OPTION.findall(texte)


def courtes(opts: list[str]) -> str:
    """Lettres des options courtes groupées (-rf -> 'rf'), sans les options longues."""
    return "".join(o[1:] for o in opts if not o.startswith("--"))


def est_rm_rf(segment: str) -> bool:
    for m in RM.finditer(segment):
        opts = options(segment[m.end() :])
        lettres = courtes(opts)
        recursif = "--recursive" in opts or "r" in lettres or "R" in lettres
        force = "--force" in opts or "f" in lettres
        if recursif and force:
            return True
    return False


def est_push_force(segment: str) -> bool:
    m = GIT_PUSH.search(segment)
    if not m:
        return False
    opts = options(segment[m.end() :])
    return "--force" in opts or "f" in courtes(opts)


def raison(commande: str) -> str | None:
    if DROP.search(commande):
        return "DROP TABLE / DROP VIEW"
    for segment in SEPARATEURS.split(commande):
        if est_rm_rf(segment):
            return "rm -rf"
        if est_push_force(segment):
            return "git push --force"
    return None


def main() -> int:
    try:
        donnees = json.load(sys.stdin)
        if donnees.get("tool_name") not in OUTILS:
            return 0
        commande = donnees["tool_input"]["command"]
    except (ValueError, KeyError, TypeError, AttributeError):
        return 0
    if not isinstance(commande, str):
        return 0

    motif = raison(commande)
    if motif:
        print(f"Bloqué par le hook garde.py : {motif}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.stderr.reconfigure(encoding="utf-8")
    sys.exit(main())
