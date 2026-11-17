"""Outils réseau communs aux scripts VeriTrace : HTTP poli, extraction de texte, Wayback Machine.

Pas de clé API, pas de donnée personnelle : l'User-Agent est générique.
"""

from __future__ import annotations

import html
import io
import re
import time
import unicodedata
import urllib.parse
from dataclasses import dataclass

import requests

USER_AGENT = "Mozilla/5.0 (compatible; VeriTrace/0.1; verification de sources)"
TIMEOUT = 60
# Pause minimale entre deux requêtes vers archive.org (limite de débit, erreur 429).
INTERVALLE_ARCHIVE = 5.0
ATTENTES_REESSAI = (20, 60, 120)

_session = requests.Session()
_session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "fr,en;q=0.8"})
_derniere_requete_archive = 0.0

RE_ARCHIVE = re.compile(r"^https?://web\.archive\.org/web/(\d{8,14})([a-z_]*)/(.+)$")


# --------------------------------------------------------------------------- HTTP

def _est_archive(url: str) -> bool:
    return urllib.parse.urlsplit(url).hostname in {"web.archive.org", "archive.org"}


def _attendre_tour_archive() -> None:
    global _derniere_requete_archive
    attente = INTERVALLE_ARCHIVE - (time.monotonic() - _derniere_requete_archive)
    if attente > 0:
        time.sleep(attente)
    _derniere_requete_archive = time.monotonic()


def requete(url: str, methode: str = "GET", **kw) -> requests.Response:
    """Requête avec pause sur archive.org et réessais sur 429 / 5xx / erreur réseau."""
    kw.setdefault("timeout", TIMEOUT)
    kw.setdefault("allow_redirects", True)
    derniere_erreur: Exception | None = None
    for i, attente in enumerate((0, *ATTENTES_REESSAI)):
        if attente:
            time.sleep(attente)
        if _est_archive(url):
            _attendre_tour_archive()
        try:
            r = _session.request(methode, url, **kw)
        except requests.RequestException as e:
            derniere_erreur = e
            continue
        if r.status_code == 429 or r.status_code >= 500:
            retry_after = r.headers.get("Retry-After", "")
            if retry_after.isdigit() and i < len(ATTENTES_REESSAI):
                time.sleep(min(int(retry_after), 300))
            derniere_erreur = None
            dernier = r
            continue
        return r
    if derniere_erreur:
        raise derniere_erreur
    return dernier  # dernière réponse 429/5xx


# --------------------------------------------------------------------------- texte

def normaliser(texte: str) -> str:
    """Normalisation typographique pour comparer des extraits : NFKC, apostrophes et
    guillemets droits, espaces insécables, tirets, césures, blancs fusionnés."""
    t = unicodedata.normalize("NFKC", texte)
    t = t.translate({
        0x2018: "'", 0x2019: "'", 0x02BC: "'", 0x201B: "'", 0x2032: "'",
        0x201C: '"', 0x201D: '"', 0x201E: '"', 0x00AB: '"', 0x00BB: '"',
        0x2010: "-", 0x2011: "-", 0x2012: "-", 0x2013: "-", 0x2014: "-",
        0x00AD: None,  # césure conditionnelle
    })
    return re.sub(r"\s+", " ", t).strip()


def html_vers_texte(source: str) -> str:
    source = re.sub(r"(?is)<(script|style|noscript|template)\b.*?</\1>", " ", source)
    source = re.sub(r"(?s)<!--.*?-->", " ", source)
    return html.unescape(re.sub(r"<[^>]+>", " ", source))


def pdf_vers_texte(contenu: bytes) -> str | None:
    """Texte d'un PDF si pdfplumber est installé, sinon None."""
    try:
        import pdfplumber  # dépendance facultative
    except ImportError:
        return None
    with pdfplumber.open(io.BytesIO(contenu)) as pdf:
        pages = [p.extract_text() or "" for p in pdf.pages]
    # Recolle les mots coupés en fin de ligne (« démo-\ncratie »).
    return re.sub(r"(\w)-\n(\w)", r"\1\2", "\n".join(pages))


RE_META_CHARSET = re.compile(rb"""<meta[^>]+charset\s*=\s*["']?\s*([a-z0-9_.:-]+)""", re.I)


def choisir_encodage(r: requests.Response) -> str:
    """Encodage comme un navigateur : en-tête HTTP explicite, sinon <meta charset>,
    sinon détection. requests suppose ISO-8859-1 quand l'en-tête est muet, ce qui
    corrompt les pages UTF-8 (apostrophes typographiques, accents)."""
    declare = re.search(r"charset\s*=\s*[\"']?([\w.:-]+)", r.headers.get("Content-Type", ""), re.I)
    enc = declare.group(1) if declare else None
    if not enc:
        m = RE_META_CHARSET.search(r.content[:4096])
        enc = m.group(1).decode("ascii") if m else None
    enc = enc or r.apparent_encoding or "utf-8"
    if enc.lower() in ("iso-8859-1", "latin-1", "latin1", "us-ascii", "ascii"):
        enc = "cp1252"  # règle WHATWG
    try:
        "".encode(enc)
    except LookupError:
        enc = "utf-8"
    return enc


@dataclass
class Page:
    url_demandee: str
    url_finale: str
    statut: int
    type_contenu: str
    texte: str | None  # normalisé ; None si non extractible (PDF sans pdfplumber, binaire…)


def lire(url: str) -> Page:
    r = requete(url)
    type_contenu = r.headers.get("Content-Type", "").split(";")[0].strip().lower()
    texte: str | None = None
    if r.ok:
        if "pdf" in type_contenu or r.content[:5] == b"%PDF-":
            brut = pdf_vers_texte(r.content)
            texte = normaliser(brut) if brut is not None else None
        elif type_contenu.startswith("text/") or "html" in type_contenu or "xml" in type_contenu or not type_contenu:
            r.encoding = choisir_encodage(r)
            texte = normaliser(html_vers_texte(r.text))
    return Page(url, r.url, r.status_code, type_contenu, texte)


def ressemble_anti_robot(texte: str | None) -> bool:
    """Heuristique : page de défi anti-robot ou quasi vide."""
    if texte is None:
        return False
    if len(texte) < 1500:
        return True
    marqueurs = ("verify you are human", "are you a robot", "captcha", "enable javascript and cookies",
                 "checking your browser", "access denied", "just a moment")
    debut = texte[:3000].lower()
    return any(m in debut for m in marqueurs)


# --------------------------------------------------------------------------- Wayback

def encoder(url: str) -> str:
    return urllib.parse.quote(url, safe="")


def decomposer_archive(archive: str) -> tuple[str, str] | None:
    """'https://web.archive.org/web/20240101000000/https://x' -> ('20240101000000', 'https://x')."""
    m = RE_ARCHIVE.match(archive)
    return (m.group(1), m.group(3)) if m else None


def url_archive(horodatage: str, url: str, brut: bool = False) -> str:
    """URL d'une capture ; brut=True renvoie le contenu d'origine sans la barre Wayback (id_)."""
    return f"https://web.archive.org/web/{horodatage}{'id_' if brut else ''}/{url}"


def capture_la_plus_proche(url: str) -> str | None:
    r = requete(f"https://archive.org/wayback/available?url={encoder(url)}")
    if not r.ok:
        return None
    try:
        proche = r.json().get("archived_snapshots", {}).get("closest")
    except ValueError:
        return None
    if proche and proche.get("available") and str(proche.get("status")) == "200":
        return url_archive(proche["timestamp"], url)
    return None


def captures(url: str, limite: int = 25) -> list[str]:
    """Horodatages des captures HTTP 200, de la plus récente à la plus ancienne."""
    r = requete(
        "https://web.archive.org/cdx/search/cdx",
        params={"url": url, "output": "json", "filter": "statuscode:200",
                "fl": "timestamp", "limit": str(-limite)},
    )
    if not r.ok:
        return []
    try:
        lignes = r.json()
    except ValueError:
        return []
    return sorted({l[0] for l in lignes[1:]}, reverse=True)


def demander_capture(url: str) -> str | None:
    """Demande une nouvelle capture (Save Page Now, sans compte). Renvoie l'URL d'archive ou None."""
    r = requete(f"https://web.archive.org/save/{url}", allow_redirects=False)
    for entete in ("Content-Location", "Location"):
        valeur = r.headers.get(entete, "")
        m = re.search(r"/web/(\d{14})", valeur)
        if m:
            return url_archive(m.group(1), url)
    m = RE_ARCHIVE.match(r.url) if r.ok else None
    return url_archive(m.group(1), url) if m else None


def memes_urls(a: str, b: str) -> bool:
    """Égalité à http/https, www., barre finale et casse de l'hôte près."""
    def cle(u: str) -> tuple[str, str, str]:
        p = urllib.parse.urlsplit(u)
        hote = (p.hostname or "").lower().removeprefix("www.")
        return hote, p.path.rstrip("/") or "/", p.query
    return cle(a) == cle(b)
