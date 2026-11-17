#!/usr/bin/env python3
"""Valide une ou plusieurs fiches VeriTrace.

Usage :
    python scripts/valider_fiche.py fiches/verification/mon-id.md [...]
    python scripts/valider_fiche.py fiches/          # tous les .md, récursivement

Contrôles :
  - front-matter conforme à schema/fiche.schema.json ;
  - id identique au nom du fichier, dossier cohérent avec le type ;
  - titres de niveau 2 du corps exacts et dans l'ordre (METHODE.md) ;
  - identifiants de sources uniques, toutes citées, aucune citation orpheline,
    derive_de pointant vers une source existante ;
  - chaque point des deux premiers blocs cite au moins une source ;
  - aucune source reseau_social comme preuve dans les deux premiers blocs (règle 2) ;
  - derniere_maj >= date_creation, dates non futures.

Code de sortie : 0 si tout est valide, 1 sinon.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

RACINE = Path(__file__).resolve().parent.parent
SCHEMA = RACINE / "schema" / "fiche.schema.json"

TITRES = {
    "verification": [
        "Ce qui est établi",
        "Ce qui est faux",
        "Ce qu'on ne sait pas, et pourquoi",
        "Pourquoi la rumeur tient",
    ],
    "debat": [
        "Positions en présence",
        "Chiffrages et hypothèses",
        "Points d'accord",
        "Points de désaccord, et pourquoi",
    ],
}
# Blocs dont chaque point doit être sourcé, et où reseau_social est interdit.
BLOCS_PREUVE = {"verification": TITRES["verification"][:2], "debat": []}

RE_FRONT = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n?(.*)\Z", re.S)
RE_H2 = re.compile(r"^##\s+(.+?)\s*$", re.M)
RE_REF = re.compile(r"\[(S[1-9]\d*)\]")
RE_POINT = re.compile(r"^[-*]\s+(.*)$")


class ChargeurSansDates(yaml.SafeLoader):
    """SafeLoader qui laisse les dates en chaînes (le schéma attend AAAA-MM-JJ)."""


ChargeurSansDates.yaml_implicit_resolvers = {
    k: [(tag, rx) for tag, rx in v if tag != "tag:yaml.org,2002:timestamp"]
    for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()
}


def annoter(niveau: str, fichier: Path | str, message: str) -> None:
    """Dans GitHub Actions, affiche l'erreur ou l'avertissement sur le fichier de la PR."""
    if os.environ.get("GITHUB_ACTIONS") != "true":
        return
    echap = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    chemin = Path(fichier).as_posix().replace(",", "%2C").replace(":", "%3A")
    print(f"::{niveau} file={chemin},line=1::{echap}")


def normaliser_apostrophes(s: str) -> str:
    return s.replace("’", "'")


def sections(corps: str) -> list[tuple[str, str]]:
    """Découpe le corps en (titre H2, contenu)."""
    pos = list(RE_H2.finditer(corps))
    return [
        (normaliser_apostrophes(m.group(1)), corps[m.end(): pos[i + 1].start() if i + 1 < len(pos) else len(corps)])
        for i, m in enumerate(pos)
    ]


def valider(chemin: Path, validateur: Draft202012Validator) -> list[str]:
    erreurs: list[str] = []
    texte = chemin.read_text(encoding="utf-8")
    m = RE_FRONT.match(texte)
    if not m:
        return ["front-matter YAML absent (le fichier doit commencer par '---')"]
    try:
        fm = yaml.load(m.group(1), Loader=ChargeurSansDates)
    except yaml.YAMLError as e:
        return [f"YAML invalide : {e}"]
    if not isinstance(fm, dict):
        return ["le front-matter doit être un dictionnaire"]
    corps = m.group(2)

    for e in sorted(validateur.iter_errors(fm), key=lambda e: list(e.absolute_path)):
        lieu = "/".join(str(p) for p in e.absolute_path) or "(racine)"
        erreurs.append(f"schéma — {lieu} : {e.message}")
    if erreurs:
        return erreurs  # le reste suppose un front-matter conforme

    type_ = fm["type"]

    # Fichier
    if fm["id"] != chemin.stem:
        erreurs.append(f"id '{fm['id']}' différent du nom de fichier '{chemin.stem}'")
    if chemin.parent.name in TITRES and chemin.parent.name != type_:
        erreurs.append(f"fiche de type '{type_}' rangée dans '{chemin.parent.name}/'")

    # Dates
    creation = dt.date.fromisoformat(fm["date_creation"])
    maj = dt.date.fromisoformat(fm["derniere_maj"])
    if maj < creation:
        erreurs.append("derniere_maj antérieure à date_creation")
    if maj > dt.date.today():
        erreurs.append("derniere_maj dans le futur")

    # Titres du corps
    secs = sections(corps)
    titres = [t for t, _ in secs]
    if titres != TITRES[type_]:
        erreurs.append(
            "titres de niveau 2 attendus, dans l'ordre : "
            + " | ".join(TITRES[type_])
            + f" — trouvés : {' | '.join(titres) or '(aucun)'}"
        )
    for titre, contenu in secs:
        if not contenu.strip():
            erreurs.append(f"bloc « {titre} » vide (s'il n'y a rien, l'écrire explicitement)")

    # Sources
    sources = {}
    for s in fm["sources"]:
        if s["id"] in sources:
            erreurs.append(f"identifiant de source en double : {s['id']}")
        sources[s["id"]] = s
    for s in fm["sources"]:
        if "derive_de" in s:
            if s["derive_de"] not in sources:
                erreurs.append(f"{s['id']}.derive_de pointe vers une source inexistante : {s['derive_de']}")
            elif s["derive_de"] == s["id"]:
                erreurs.append(f"{s['id']}.derive_de pointe vers elle-même")

    citees = set(RE_REF.findall(corps))
    for ref in sorted(citees - sources.keys()):
        erreurs.append(f"[{ref}] cité dans le corps mais absent de 'sources'")
    for ref in sorted(sources.keys() - citees):
        erreurs.append(f"source {ref} déclarée mais jamais citée dans le corps")

    # Blocs de preuve
    for titre, contenu in secs:
        if titre not in BLOCS_PREUVE[type_]:
            continue
        for ligne in contenu.splitlines():
            p = RE_POINT.match(ligne)  # points de premier niveau uniquement
            if p and not RE_REF.search(p.group(1)):
                erreurs.append(f"« {titre} » : point sans source — {p.group(1)[:80]}")
        for ref in set(RE_REF.findall(contenu)):
            if ref in sources and sources[ref]["type"] == "reseau_social":
                erreurs.append(
                    f"« {titre} » : [{ref}] est un réseau social — il sert à dater une rumeur, jamais à la prouver"
                )

    return erreurs


def fichiers(args: list[str]) -> list[Path]:
    out: list[Path] = []
    for a in args:
        p = Path(a)
        out.extend(sorted(p.rglob("*.md")) if p.is_dir() else [p])
    return out


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if not argv:
        print(__doc__)
        return 1
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    validateur = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)

    cibles = fichiers(argv)
    if not cibles:
        print("Aucune fiche trouvée.")
        return 0
    # Unicité des id sur toute la base (une vérification et un débat ne peuvent pas partager un id).
    ids_base: dict[str, list[Path]] = {}
    for f in sorted((RACINE / "fiches").rglob("*.md")):
        ids_base.setdefault(f.stem, []).append(f.relative_to(RACINE))

    nb_ko = 0
    for f in cibles:
        if not f.is_file():
            print(f"✗ {f} : fichier introuvable")
            nb_ko += 1
            continue
        erreurs = valider(f, validateur)
        doublons = [p for p in ids_base.get(f.stem, []) if (RACINE / p).resolve() != f.resolve()]
        if doublons:
            erreurs.append(f"id déjà utilisé par : {', '.join(map(str, doublons))}")
        if erreurs:
            nb_ko += 1
            print(f"✗ {f}")
            for e in erreurs:
                print(f"    - {e}")
                annoter("error", f, e)
        else:
            print(f"✓ {f}")
    print(f"\n{len(cibles) - nb_ko}/{len(cibles)} fiche(s) valide(s).")
    return 1 if nb_ko else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
