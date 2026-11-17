#!/usr/bin/env python3
"""Vérifie qu'une pull request a assez de relectures humaines.

Règle (CLAUDE.md) : 1 relecteur, 2 si une fiche modifiée est sensible
(`sensible: true` dans son front-matter, ou étiquette « sensible » posée sur la PR).

Une approbation compte si :
  - elle porte sur le dernier commit de la PR (une nouvelle preuve poussée = nouvelle relecture) ;
  - c'est le dernier avis de ce relecteur (une demande de modifications ultérieure l'annule) ;
  - le relecteur n'est pas l'auteur de la PR et a un rôle sur le dépôt (OWNER, MEMBER, COLLABORATOR).

Tout est lu via l'API GitHub : aucun code de la PR n'est exécuté.

Usage (dans GitHub Actions) :
    GITHUB_TOKEN=… GITHUB_REPOSITORY=org/depot python scripts/relecture_requise.py --pr 12
Code de sortie : 0 si le nombre d'approbations est atteint, 1 sinon.
"""

from __future__ import annotations

import argparse
import os
import sys

import requests
import yaml

from valider_fiche import RE_FRONT, ChargeurSansDates

API = "https://api.github.com"
ROLES_RELECTEURS = {"OWNER", "MEMBER", "COLLABORATOR"}
ETIQUETTE_SENSIBLE = "sensible"


# --------------------------------------------------------------------------- logique pure (testable)

def est_sensible(contenu_fiche: str) -> bool:
    m = RE_FRONT.match(contenu_fiche)
    if not m:
        return False
    try:
        fm = yaml.load(m.group(1), Loader=ChargeurSansDates)
    except yaml.YAMLError:
        return True  # illisible : on ne prend pas de risque
    return isinstance(fm, dict) and fm.get("sensible") is True


def approbations_requises(contenus_fiches: list[str], etiquettes: list[str]) -> int:
    if ETIQUETTE_SENSIBLE in etiquettes or any(est_sensible(c) for c in contenus_fiches):
        return 2
    return 1


def approbateurs(avis: list[dict], auteur: str, sha_tete: str) -> set[str]:
    """Relecteurs dont le dernier avis est une approbation valable sur le dernier commit."""
    dernier: dict[str, dict] = {}
    for a in sorted(avis, key=lambda a: a.get("submitted_at") or ""):
        user = (a.get("user") or {}).get("login")
        # COMMENTED et PENDING ne changent pas l'avis d'un relecteur.
        if user and a.get("state") in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED"):
            dernier[user] = a
    return {
        u for u, a in dernier.items()
        if a["state"] == "APPROVED"
        and a.get("commit_id") == sha_tete
        and u != auteur
        and a.get("author_association") in ROLES_RELECTEURS
    }


# --------------------------------------------------------------------------- API GitHub

class GitHub:
    def __init__(self, depot: str, jeton: str):
        self.depot = depot
        self.s = requests.Session()
        self.s.headers.update({
            "Authorization": f"Bearer {jeton}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        })

    def get(self, chemin: str, **params) -> object:
        r = self.s.get(f"{API}/repos/{self.depot}/{chemin}", params=params, timeout=30)
        r.raise_for_status()
        return r.json()

    def pages(self, chemin: str) -> list[dict]:
        out, page = [], 1
        while True:
            lot = self.get(chemin, per_page=100, page=page)
            out.extend(lot)
            if len(lot) < 100:
                return out
            page += 1

    def fichier_brut(self, chemin: str, ref: str) -> str:
        r = self.s.get(f"{API}/repos/{self.depot}/contents/{chemin}", params={"ref": ref},
                       headers={"Accept": "application/vnd.github.raw+json"}, timeout=30)
        r.raise_for_status()
        return r.text


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--pr", type=int, required=True)
    a = p.parse_args()

    gh = GitHub(os.environ["GITHUB_REPOSITORY"], os.environ["GITHUB_TOKEN"])
    pr = gh.get(f"pulls/{a.pr}")
    sha, auteur = pr["head"]["sha"], pr["user"]["login"]
    etiquettes = [e["name"] for e in pr.get("labels", [])]

    fiches = [f for f in gh.pages(f"pulls/{a.pr}/files")
              if f["filename"].startswith("fiches/") and f["filename"].endswith(".md")
              and f["status"] != "removed"]
    contenus = []
    for f in fiches:
        # Les fichiers d'un fork sont lisibles via le dépôt de la tête de PR.
        depot_tete = pr["head"]["repo"]["full_name"] if pr["head"].get("repo") else gh.depot
        contenus.append(GitHub(depot_tete, os.environ["GITHUB_TOKEN"]).fichier_brut(f["filename"], sha))

    requis = approbations_requises(contenus, etiquettes)
    ok = approbateurs(gh.pages(f"pulls/{a.pr}/reviews"), auteur, sha)

    motif = "fiche sensible" if requis == 2 else "cas général"
    print(f"Relectures requises : {requis} ({motif}).")
    print(f"Approbations valables sur {sha[:7]} : {len(ok)}" + (f" ({', '.join(sorted(ok))})" if ok else ""))
    resume = os.environ.get("GITHUB_STEP_SUMMARY")
    if resume:
        with open(resume, "a", encoding="utf-8") as fh:
            fh.write(f"### Relecture humaine\n\n- Requises : **{requis}** ({motif})\n"
                     f"- Approbations valables sur le dernier commit : **{len(ok)}**\n")
    if len(ok) < requis:
        print(f"::error::Il manque {requis - len(ok)} relecture(s) humaine(s) approuvant le dernier commit.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
