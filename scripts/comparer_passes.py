#!/usr/bin/env python3
"""Compare une fiche avec le résultat de sa contre-vérification à l'aveugle (règle 7).

Usage :
    python scripts/comparer_passes.py <fiche.md> <passe-aveugle.json>
    python scripts/comparer_passes.py <fiche.md> <passe-aveugle.json> --appliquer ok
    python scripts/comparer_passes.py <fiche.md> <passe-aveugle.json> --appliquer divergence

Sans --appliquer : affiche la comparaison et la décision proposée, sans rien modifier.
  - fiche de vérification : statuts identiques → « ok » proposé ; statuts différents → « divergence ».
  - fiche de débat : pas de verdict à comparer → décision humaine (le rapport liste les points).
  - dans tous les cas : sources trouvées par la seconde passe et absentes de la fiche
    (à examiner : une preuve nouvelle qui contredit un point établi impose une divergence).

--appliquer met à jour le front-matter : contre_verification, derniere_maj et, en cas de
divergence sur une fiche de vérification, statut: a_revoir. « ok » est refusé si les
statuts diffèrent : la règle 7 ne laisse pas de place à l'appréciation sur ce point.

Codes de sortie : 0 concordance (ou appliqué), 2 divergence ou décision humaine requise, 1 erreur.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

import yaml
from jsonschema import Draft202012Validator

from valider_fiche import RACINE, RE_FRONT, ChargeurSansDates
from veritrace_web import memes_urls

SCHEMA_PASSE = RACINE / "schema" / "passe-aveugle.schema.json"
RANG = {"primaire": 1, "institutionnelle": 2, "etude": 2, "presse": 3, "reseau_social": 4}


def domaine(url: str) -> str:
    return (urlsplit(url).hostname or "").lower().removeprefix("www.")


def normaliser_phrase(s: str) -> str:
    return re.sub(r"\s+", " ", s.replace("’", "'")).strip().rstrip(".").casefold()


def charger(fiche: Path, passe: Path) -> tuple[str, dict, dict]:
    texte = fiche.read_text(encoding="utf-8")
    m = RE_FRONT.match(texte)
    if not m:
        raise ValueError(f"{fiche} : front-matter absent")
    fm = yaml.load(m.group(1), Loader=ChargeurSansDates)
    p = json.loads(passe.read_text(encoding="utf-8"))
    erreurs = list(Draft202012Validator(json.loads(SCHEMA_PASSE.read_text(encoding="utf-8"))).iter_errors(p))
    if erreurs:
        def court(e) -> str:
            # Les erreurs « not » / « anyOf » recopient tout l'objet : on ne garde que la règle violée.
            msg = e.message if e.validator not in ("not", "anyOf", "oneOf") else f"règle « {e.validator} » non respectée ({e.schema})"
            return f"{'/'.join(map(str, e.absolute_path)) or '(racine)'} : {msg[:200]}"
        raise ValueError("passe aveugle invalide : " + "; ".join(court(e) for e in erreurs))
    if p["type"] != fm["type"]:
        raise ValueError(f"types différents : fiche {fm['type']}, passe {p['type']}")
    cle = "question" if fm["type"] == "debat" else "affirmation"
    if normaliser_phrase(p.get(cle, "")) != normaliser_phrase(fm.get(cle, "")):
        raise ValueError(f"la passe ne porte pas sur la même {cle} que la fiche")
    return texte, fm, p


def comparer(fm: dict, p: dict) -> tuple[str, list[str]]:
    """Renvoie (décision proposée : ok | divergence | humain, lignes du rapport)."""
    lignes: list[str] = []
    if fm["type"] == "verification":
        s1, s2 = fm["statut"], p["statut"]
        c1, c2 = fm["confiance"], p["confiance"]
        if s1 == "a_revoir":
            lignes.append("La fiche est déjà « a_revoir » : la comparaison des statuts n'est pas concluante.")
            decision = "humain"
        elif s1 == s2:
            lignes.append(f"Statut : concordant ({s1}).")
            decision = "ok"
        else:
            lignes.append(f"Statut : DIVERGENT — fiche « {s1} », seconde passe « {s2} ».")
            decision = "divergence"
        if c1 != c2:
            ecart = abs(["faible", "moyenne", "haute"].index(c1) - ["faible", "moyenne", "haute"].index(c2))
            lignes.append(f"Confiance : fiche « {c1} », seconde passe « {c2} »"
                          + (" — écart important, à examiner." if ecart == 2 else "."))
    else:
        lignes.append("Fiche de débat : pas de verdict à comparer. Vérifier que positions, chiffrages "
                      "et désaccords de la seconde passe figurent dans la fiche.")
        decision = "humain"

    # Sources
    urls_fiche = [s["url"] for s in fm["sources"]]
    domaines_fiche = {domaine(u) for u in urls_fiche}
    communes = [s for s in p["sources"] if any(memes_urls(s["url"], u) for u in urls_fiche)]
    nouvelles = sorted((s for s in p["sources"] if s not in communes), key=lambda s: RANG[s["type"]])
    lignes.append(f"Sources : {len(communes)} en commun sur {len(p['sources'])} trouvées par la seconde passe "
                  f"({len(fm['sources'])} dans la fiche).")
    if nouvelles:
        lignes.append("Sources de la seconde passe absentes de la fiche (les plus fortes d'abord) :")
        for s in nouvelles:
            meme_site = " — même site qu'une source de la fiche" if domaine(s["url"]) in domaines_fiche else ""
            lignes.append(f"  - [{s['type']}] {s['url']}{meme_site}\n      « {s['extrait'][:160]} »")
        if any(RANG[s["type"]] <= 2 for s in nouvelles):
            lignes.append("  → Au moins une source primaire, institutionnelle ou une étude est nouvelle : "
                          "vérifier qu'elle ne contredit aucun point de la fiche. Si elle en contredit un, "
                          "c'est une divergence, même avec des statuts identiques.")
    lignes.append(f"Meilleure preuve contraire selon la seconde passe : {p['meilleure_preuve_contraire']}")
    return decision, lignes


def appliquer(chemin: Path, texte: str, fm: dict, decision: str) -> None:
    m = RE_FRONT.match(texte)
    front, corps = m.group(1), texte[m.end(1):]
    aujourd_hui = dt.date.today().isoformat()

    def remplacer(cle: str, valeur: str, f: str) -> str:
        nouveau, n = re.subn(rf"(?m)^{cle}:.*$", f"{cle}: {valeur}", f, count=1)
        if n != 1:
            raise ValueError(f"champ '{cle}' introuvable dans le front-matter")
        return nouveau

    front = remplacer("contre_verification", decision, front)
    front = remplacer("derniere_maj", aujourd_hui, front)
    if decision == "divergence" and fm["type"] == "verification":
        front = remplacer("statut", "a_revoir", front)
    chemin.write_text(texte[: m.start(1)] + front + corps, encoding="utf-8")


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fiche", type=Path)
    ap.add_argument("passe", type=Path)
    ap.add_argument("--appliquer", choices=["ok", "divergence"])
    a = ap.parse_args()

    try:
        texte, fm, p = charger(a.fiche, a.passe)
    except (OSError, ValueError, json.JSONDecodeError, yaml.YAMLError) as e:
        print(f"Erreur : {e}")
        return 1

    decision, lignes = comparer(fm, p)
    print(f"Contre-vérification de {fm['id']}\n")
    print("\n".join(lignes))
    print(f"\nDécision proposée : {'décision humaine requise' if decision == 'humain' else decision}")

    if not a.appliquer:
        return 0 if decision == "ok" else 2
    if a.appliquer == "ok" and decision == "divergence":
        print("Refusé : les statuts diffèrent, la règle 7 impose « divergence ».")
        return 1
    try:
        appliquer(a.fiche, texte, fm, a.appliquer)
    except ValueError as e:
        print(f"Erreur : {e}")
        return 1
    suite = " et statut: a_revoir" if a.appliquer == "divergence" and fm["type"] == "verification" else ""
    print(f"Appliqué : contre_verification: {a.appliquer}{suite}, derniere_maj mise à jour.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
