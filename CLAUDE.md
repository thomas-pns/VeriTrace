# CLAUDE.md — VeriTrace

> *Every claim, traced to its source.* — Projet open source de vérification citoyenne.

## Mission

Créer une base de connaissances **publique, open source et auto-alimentée** qui permet à n'importe qui de savoir, sur n'importe quel sujet :
- ce qui est **établi**, preuves à l'appui ;
- ce qui est **faux**, et d'où ça vient ;
- ce qu'on **ne sait pas**, et pourquoi ;
- **pourquoi une rumeur tient**.

L'IA (Claude, via un skill Claude Code) fait le travail de fond : recherche, remontée à la source, lecture des documents primaires que personne ne lit (PDF de 1 000 pages, décisions de justice, rapports officiels), recoupement. Les humains valident. La base grandit à chaque utilisation.

Principe directeur : **« n'importe quoi, pas n'importe qui »**. L'unité de base est une *affirmation*, jamais une personne.

## Architecture

```
repo/
├── CLAUDE.md
├── README.md                  # mission, méthode, comment contribuer (sans exemples de sujets)
├── METHODE.md                 # les 7 règles détaillées
├── fiches/
│   ├── verification/          # fiches vrai/faux (4 blocs)
│   └── debat/                 # fiches sur des questions sans réponse vrai/faux
├── schema/
│   └── fiche.schema.json      # format validé automatiquement
├── .claude/skills/
│   ├── verifier/SKILL.md      # skill principal : vérifier une affirmation et produire une fiche
│   └── contre-verifier/SKILL.md  # vérification à l'aveugle d'une fiche existante
├── scripts/                   # Python : archivage Wayback, vérif des liens, extraction PDF/métadonnées
├── site/                      # site statique (Astro + recherche Pagefind), publié sur GitHub Pages
└── .github/
    ├── workflows/             # CI : validation schéma, liens vivants, sources archivées, build du site
    └── PULL_REQUEST_TEMPLATE.md
```

- **Hébergement : uniquement GitHub (repo + GitHub Pages).** Aucun serveur perso, aucun NAS.
- **Pas de clé API** : chaque contributeur fait tourner le skill avec son propre Claude.
- Langages : Python (scripts), Markdown + front-matter YAML/JSON (fiches), Astro (site).

## Format d'une fiche de vérification

Front-matter : `id`, `affirmation`, `statut` (`etabli` | `faux` | `trompeur` | `non_prouve` | `conteste` | `a_revoir`), `confiance` (haute/moyenne/faible), `sujets` (tags pour regrouper), `date_creation`, `derniere_maj`, `contre_verification` (ok / divergence / en_attente).

Corps en 4 blocs obligatoires :
1. **Ce qui est établi** — chaque point relié à une source.
2. **Ce qui est faux** — et l'origine de l'erreur.
3. **Ce qu'on ne sait pas, et pourquoi** — classifié, caviardé, procédure en cours, absence de données… et ce qu'il faudrait pour savoir. Peut être vide : le dire explicitement.
4. **Pourquoi la rumeur tient** — première apparition datée, propagation, élément vrai déformé.

Chaque source : URL d'origine + lien archive Wayback + passage exact cité (court) + type (primaire / institutionnelle / presse / réseau social).

## Format d'une fiche de débat

Pour les questions qui ne sont pas vrai/faux (ex. impact économique d'une mesure) : positions en présence, chiffrages des institutions et leurs hypothèses, points d'accord, points de désaccord et pourquoi. Pas de verdict.

## Méthode (les 7 règles du skill)

1. **Les preuves comptent, les opinions non.** Une affirmation sans source n'entre pas.
2. **Hiérarchie des sources** : primaires > institutionnelles / études publiées > presse d'enquête > réseaux sociaux (qui servent seulement à dater et tracer une rumeur, jamais à la prouver).
3. **Indépendance** : remonter chaque info à son origine ; 500 reprises d'une même source = 1 source.
4. **Chercher activement à se contredire** : trouver la meilleure preuve contraire avant de conclure.
5. **Trois niveaux** : établi / probable / non prouvé. Un croisement de documents produit un *indice*, jamais une *accusation*. Aucune hypothèse publiée comme un fait.
6. **Tout est vérifiable** : passage exact + archive Wayback pour chaque source.
7. **Contre-vérification à l'aveugle** : une seconde passe refait la recherche sans voir la conclusion ; si divergence → `a_revoir`.

Une fiche se conteste uniquement avec des preuves ; une nouvelle preuve déclenche une revérification.

## Contribution automatique (auto-alimentation)

- À l'installation et à chaque exécution, le skill annonce clairement : *« Ce skill contribue à une base publique. Chaque recherche produit une fiche proposée au dépôt commun. »*
- Par défaut, à la fin d'une vérification, le skill propose la fiche via fork + pull request (`gh`). Option pour ne pas partager une recherche donnée.
- Prévenir que la PR apparaît sous le pseudo GitHub du contributeur. La fiche ne contient que le sujet vérifié, rien de personnel.
- « Publier » = *proposer*. Une fiche n'entre dans la base qu'après la CI et une relecture humaine (2 relecteurs pour les sujets sensibles).
- Avant de créer une fiche, le skill cherche si elle existe déjà (mise à jour plutôt que doublon).

## Règles éthiques non négociables

- **Pas d'outils de pistage de personnes** : pas de recherche de pseudos ou d'identités, pas d'accès à des caméras, pas de dossiers sur des individus.
- **Aucune donnée de victime**, jamais, même si un document officiel l'a laissée passer.
- **Être cité dans un document ≠ être coupable.** Une fiche dit précisément ce que le document établit, rien de plus.
- **Pas de recopie de corpus massifs** contenant des données personnelles : on pointe vers la source officielle avec la référence exacte.
- **Pas de documents obtenus illégalement**, pas d'intrusion.
- Respect des licences des outils réutilisés (ex. ICIJ Datashare en AGPL-3.0).

## Outils à réutiliser plutôt que recréer

API Wayback Machine (archivage et première apparition), yt-dlp, exiftool, extraction PDF (pdfplumber / Tika), OCR (Tesseract), Pagefind (recherche du site). Plus tard, ICIJ Datashare pour indexer de gros corpus documentaires.

## Ordre de construction (MVP)

1. README + METHODE.md + schéma de fiche.
2. Skill `verifier` (recherche → fiche 4 blocs → proposition de PR).
3. Scripts Python : archivage Wayback + vérification des liens.
4. CI GitHub Actions : validation du schéma, liens, archives.
5. Site Astro + Pagefind sur GitHub Pages : recherche, regroupement par sujets, pages de fiches.
6. Skill `contre-verifier`.
7. Premier dossier : une vingtaine d'affirmations virales sur un même sujet, pour tester le circuit de bout en bout.
