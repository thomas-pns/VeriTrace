#!/usr/bin/env python3
"""Vérifie les sources d'une ou plusieurs fiches VeriTrace : liens, archives, extraits.

Usage :
    python scripts/verifier_sources.py fiches/verification/mon-id.md [...]
    python scripts/verifier_sources.py fiches/            # tous les .md, récursivement
Options :
    --strict          les avertissements comptent comme des erreurs
    --sans-origine    ne consulte pas les URL d'origine (archives seulement)

Pour chaque source :
  ERREUR          archive inaccessible, ou extrait absent de l'archive (règle 6) ;
  AVERTISSEMENT   lien d'origine mort ou bloqué, redirection vers une autre adresse,
                  extrait absent de la page actuelle (la source a pu changer),
                  archive qui ne correspond pas à l'URL d'origine,
                  contenu non lisible (PDF sans pdfplumber, binaire).

Les extraits sont comparés après normalisation typographique (apostrophes, guillemets,
espaces, tirets), jamais après reformulation.

Code de sortie : 0 si aucune erreur (ni avertissement avec --strict), 1 sinon.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

import veritrace_web as w
from valider_fiche import RE_FRONT, ChargeurSansDates, annoter, fichiers

_cache: dict[str, w.Page | Exception] = {}


def lire(url: str) -> w.Page:
    if url not in _cache:
        try:
            _cache[url] = w.lire(url)
        except Exception as e:  # réseau
            _cache[url] = e
    r = _cache[url]
    if isinstance(r, Exception):
        raise r
    return r


def verifier_source(s: dict, sans_origine: bool) -> tuple[list[str], list[str]]:
    erreurs: list[str] = []
    avert: list[str] = []
    extraits = [x["texte"] for x in s.get("extraits", [])]

    # --- archive
    dec = w.decomposer_archive(s["archive"])
    if dec:
        horodatage, url_archivee = dec
        if not w.memes_urls(url_archivee, s["url"]):
            avert.append(f"l'archive porte sur {url_archivee}, pas sur l'URL d'origine")
        cible = w.url_archive(horodatage, url_archivee, brut=True)
    elif w.RE_ITEM_INTERNET_ARCHIVE.match(s["archive"]):
        cible = s["archive"]  # document hébergé par l'Internet Archive : il est lui-même l'archive
    else:
        return [f"lien d'archive mal formé : {s['archive']}"], []
    try:
        page = lire(cible)
    except Exception as e:
        return [f"archive injoignable : {e}"], avert
    if page.statut != 200:
        erreurs.append(f"archive inaccessible (HTTP {page.statut})")
    elif page.texte is None:
        avert.append(f"archive non lisible ({page.type_contenu or 'type inconnu'}) — "
                     "installer pdfplumber pour les PDF ; extraits non vérifiés")
    else:
        absents = [x for x in extraits if w.normaliser(x) not in page.texte]
        for x in absents:
            erreurs.append(f"extrait absent de l'archive : « {x[:80]} »")
        if absents and w.ressemble_anti_robot(page.texte):
            erreurs.append("la capture ressemble à une page anti-robot ou vide — "
                           f"chercher une autre capture : python scripts/archiver.py {s['url']} --contient \"…\"")

    # --- origine
    if sans_origine:
        return erreurs, avert
    try:
        orig = lire(s["url"])
    except Exception as e:
        avert.append(f"URL d'origine injoignable : {e}")
        return erreurs, avert
    if orig.statut in (404, 410):
        avert.append(f"lien d'origine mort (HTTP {orig.statut}) — l'archive fait foi")
    elif orig.statut >= 400:
        avert.append(f"URL d'origine en erreur ou bloquée (HTTP {orig.statut}) — vérification inconclusive")
    else:
        redirige = not w.memes_urls(orig.url_finale, s["url"])
        absents = [x for x in extraits if orig.texte is not None and w.normaliser(x) not in orig.texte]
        if redirige:
            detail = f" ; {len(absents)}/{len(extraits)} extrait(s) absent(s) de la nouvelle page" if absents else ""
            avert.append(f"l'URL d'origine redirige vers {orig.url_finale}{detail} — l'archive fait foi")
        else:
            for x in absents:
                avert.append(f"extrait absent de la page actuelle (source modifiée ou bloquée ?) : « {x[:60]} »")
    return erreurs, avert


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("chemins", nargs="+")
    p.add_argument("--strict", action="store_true")
    p.add_argument("--sans-origine", action="store_true")
    a = p.parse_args()

    total_err = total_av = 0
    for f in fichiers(a.chemins):
        m = RE_FRONT.match(Path(f).read_text(encoding="utf-8"))
        fm = yaml.load(m.group(1), Loader=ChargeurSansDates) if m else None
        if not isinstance(fm, dict) or not isinstance(fm.get("sources"), list):
            print(f"✗ {f} : front-matter illisible — lancer d'abord scripts/valider_fiche.py")
            total_err += 1
            continue
        print(f"— {f}")
        for s in fm["sources"]:
            try:
                erreurs, avert = verifier_source(s, a.sans_origine)
            except (KeyError, TypeError) as e:
                erreurs, avert = [f"source mal formée ({e}) — lancer scripts/valider_fiche.py"], []
            total_err += len(erreurs)
            total_av += len(avert)
            etat = "✗" if erreurs else ("!" if avert else "✓")
            print(f"  {etat} {s.get('id', '?')} {s.get('url', '')}")
            for e in erreurs:
                print(f"      ERREUR : {e}")
                annoter("error", f, f"{s.get('id', '?')} : {e}")
            for e in avert:
                print(f"      AVERTISSEMENT : {e}")
                annoter("error" if a.strict else "warning", f, f"{s.get('id', '?')} : {e}")
    print(f"\n{total_err} erreur(s), {total_av} avertissement(s).")
    return 1 if total_err or (a.strict and total_av) else 0


if __name__ == "__main__":
    sys.exit(main())
