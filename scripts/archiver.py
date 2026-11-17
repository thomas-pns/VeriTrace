#!/usr/bin/env python3
"""Trouve ou crée une archive Wayback Machine pour une ou plusieurs URL.

Usage :
    python scripts/archiver.py <url> [<url> ...]
    python scripts/archiver.py <url> --contient "passage exact" [--contient "autre passage"]
    python scripts/archiver.py <url> --nouvelle

Par défaut : renvoie la capture existante la plus proche, ou en demande une nouvelle.
--contient : parcourt les captures (de la plus récente à la plus ancienne) et renvoie la
             première qui contient TOUS les passages — écarte les captures vides ou anti-robot.
             Si aucune ne convient, demande une nouvelle capture et la vérifie.
--nouvelle : demande toujours une nouvelle capture.
--json     : sortie JSON (une ligne par URL).

Code de sortie : 0 si chaque URL a une archive valable, 1 sinon.
"""

from __future__ import annotations

import argparse
import json
import sys

import veritrace_web as w


def contient_tout(archive: str, passages: list[str]) -> bool:
    ho, url = w.decomposer_archive(archive)
    page = w.lire(w.url_archive(ho, url, brut=True))
    return page.texte is not None and all(w.normaliser(p) in page.texte for p in passages)


def archiver(url: str, passages: list[str], nouvelle: bool, max_captures: int) -> tuple[str | None, str]:
    """Renvoie (archive, explication)."""
    if not nouvelle:
        if passages:
            for ho in w.captures(url, limite=max_captures):
                archive = w.url_archive(ho, url)
                if contient_tout(archive, passages):
                    return archive, "capture existante contenant les passages"
        else:
            archive = w.capture_la_plus_proche(url)
            if archive:
                return archive, "capture existante"

    archive = w.demander_capture(url)
    if not archive:
        return None, "échec de la demande de capture (Save Page Now) — réessayer plus tard ou essayer l'URL canonique"
    if passages and not contient_tout(archive, passages):
        return None, f"nouvelle capture {archive} ne contient pas les passages (page anti-robot, contenu dynamique ?)"
    return archive, "nouvelle capture"


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("urls", nargs="+")
    p.add_argument("--contient", action="append", default=[], metavar="PASSAGE")
    p.add_argument("--nouvelle", action="store_true")
    p.add_argument("--max-captures", type=int, default=15)
    p.add_argument("--json", action="store_true")
    a = p.parse_args()

    ko = 0
    for url in a.urls:
        try:
            archive, pourquoi = archiver(url, a.contient, a.nouvelle, a.max_captures)
        except Exception as e:  # réseau, réponse inattendue
            archive, pourquoi = None, f"erreur : {e}"
        ko += archive is None
        if a.json:
            print(json.dumps({"url": url, "archive": archive, "detail": pourquoi}, ensure_ascii=False))
        else:
            print(f"{'✓' if archive else '✗'} {url}\n    {archive or '—'}  ({pourquoi})")
    return 1 if ko else 0


if __name__ == "__main__":
    sys.exit(main())
