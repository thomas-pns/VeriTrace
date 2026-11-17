#!/usr/bin/env python3
"""Extrait d'une fiche UNIQUEMENT ce que la contre-vérification à l'aveugle a le droit de voir.

Usage :
    python scripts/extraire_affirmation.py fiches/verification/mon-id.md

Sortie JSON : {"id", "type", "affirmation"} ou {"id", "type", "question"}.
Rien d'autre : ni statut, ni confiance, ni sujets (un sujet comme « mythes-historiques »
trahirait le verdict), ni sources, ni corps.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

from valider_fiche import RE_FRONT, ChargeurSansDates


def extraire(chemin: Path) -> dict:
    m = RE_FRONT.match(chemin.read_text(encoding="utf-8"))
    if not m:
        raise ValueError("front-matter absent")
    fm = yaml.load(m.group(1), Loader=ChargeurSansDates)
    type_ = fm.get("type")
    cle = "question" if type_ == "debat" else "affirmation"
    if not fm.get(cle):
        raise ValueError(f"champ '{cle}' absent")
    return {"id": fm["id"], "type": type_, cle: fm[cle]}


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if len(argv) != 1:
        print(__doc__)
        return 1
    try:
        print(json.dumps(extraire(Path(argv[0])), ensure_ascii=False, indent=2))
    except (OSError, ValueError, yaml.YAMLError, KeyError) as e:
        print(f"Erreur : {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
