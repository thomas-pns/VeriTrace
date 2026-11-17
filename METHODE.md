# Méthode VeriTrace

Ce document décrit les règles que suivent le skill `verifier`, le skill `contre-verifier` et les relecteurs humains. Elles s'appliquent à toutes les fiches, sans exception.

Principe directeur : **« n'importe quoi, pas n'importe qui »**. On vérifie des affirmations, jamais des personnes.

---

## Les 7 règles

### 1. Les preuves comptent, les opinions non

- Une affirmation sans source n'entre pas dans une fiche.
- Chaque point des blocs « Ce qui est établi » et « Ce qui est faux » renvoie à au moins une source, par son identifiant (`[S1]`, `[S2]`…).
- L'autorité, la notoriété ou le nombre de personnes qui affirment quelque chose ne sont pas des preuves.
- Le texte de la fiche reste factuel : pas d'adjectifs de jugement, pas d'ironie, pas de procès d'intention.

### 2. Hiérarchie des sources

Du plus fort au plus faible :

| Rang | Type (`type` dans le schéma) | Exemples |
|---|---|---|
| 1 | `primaire` | Texte de loi, décision de justice, jeu de données brut, document original, enregistrement intégral |
| 2 | `institutionnelle`, `etude` | Rapport d'une institution publique, statistique officielle, étude publiée dans une revue à comité de lecture |
| 3 | `presse` | Presse d'enquête, agence de presse, article citant ses sources |
| 4 | `reseau_social` | Publication sur un réseau social, forum, vidéo virale |

- Quand une source de rang inférieur cite une source de rang supérieur, **on remonte à cette dernière** et on cite celle-ci.
- Les **réseaux sociaux servent uniquement à dater et tracer une rumeur** (bloc 4), **jamais à la prouver**. Une source `reseau_social` ne peut pas appuyer un point des blocs 1 ou 2.
- Une source de rang 3 seule suffit rarement pour `confiance: haute`.

### 3. Indépendance des sources

- Remonter chaque information à son **origine**. Une dépêche reprise par 500 médias = **1 source**.
- Deux sources ne sont indépendantes que si aucune ne dépend de l'autre ni d'une origine commune.
- La fiche indique, quand c'est pertinent, que plusieurs sources dérivent d'une même origine (champ `derive_de` de la source).

### 4. Chercher activement à se contredire

- Avant de conclure, chercher **la meilleure preuve contraire** à la conclusion envisagée — pas la plus faible.
- Si elle existe, elle figure dans la fiche, avec la raison pour laquelle elle est (ou n'est pas) retenue.
- Si des sources de même rang se contredisent sans qu'on puisse les départager : statut `conteste`.

### 5. Trois niveaux de certitude

Chaque point d'une fiche relève de l'un de ces niveaux :

| Niveau | Condition | Où il apparaît |
|---|---|---|
| **Établi** | Appuyé par au moins une source primaire, ou plusieurs sources indépendantes de rang 2 concordantes | Blocs 1 et 2, sans mention |
| **Probable** | Faisceau d'indices concordants, sans preuve directe | Préfixé explicitement par **« Probable : »** |
| **Non prouvé** | Pas de preuve suffisante dans un sens ou dans l'autre | Bloc 3 (« Ce qu'on ne sait pas ») |

- Un croisement de documents produit un **indice**, jamais une **accusation**.
- **Aucune hypothèse n'est publiée comme un fait.**
- Le champ `confiance` (`haute` / `moyenne` / `faible`) exprime la solidité du statut global de la fiche, pas la gravité du sujet.

### 6. Tout est vérifiable

Chaque source comporte obligatoirement :

- l'**URL d'origine** (`url`) ;
- un **lien d'archive Wayback Machine** (`archive`, de la forme `https://web.archive.org/web/<horodatage>/<url>`) ;
- les **passages exacts cités** (`extraits`), un par point de la fiche qui s'appuie sur la source, chacun court (500 caractères maximum) et **recopié mot pour mot** ;
- le **type** de source (`type`), selon la hiérarchie de la règle 2.

Pour un document long (PDF, rapport, décision), chaque extrait précise la **page, le paragraphe ou l'article** (`localisation`). N'importe quel lecteur doit pouvoir retrouver le passage en moins d'une minute.

L'archive doit **réellement contenir** les passages cités : une capture vide, tronquée ou réduite à une page anti-robot ne compte pas.

### 7. Contre-vérification à l'aveugle

- Une seconde passe (skill `contre-verifier`) refait la recherche **à partir de la seule affirmation**, sans voir la conclusion ni les sources de la première passe.
- Si les deux conclusions concordent : `contre_verification: ok`.
- Si elles divergent : `contre_verification: divergence` **et** `statut: a_revoir`. Le schéma refuse toute autre combinaison.
- Tant que la seconde passe n'a pas eu lieu : `contre_verification: en_attente`.

---

## Format d'une fiche de vérification

Fichier Markdown dans `fiches/verification/<id>.md`, avec un front-matter YAML validé par [`schema/fiche.schema.json`](schema/fiche.schema.json).

```yaml
---
type: verification
id: exemple-d-affirmation          # identique au nom du fichier, en kebab-case
affirmation: "L'affirmation vérifiée, formulée telle qu'elle circule."
statut: faux                       # etabli | faux | trompeur | non_prouve | conteste | a_revoir
confiance: haute                   # haute | moyenne | faible
sujets: [sujet-a, sujet-b]
sensible: false                    # true → deux relecteurs humains requis
date_creation: 2026-01-01
derniere_maj: 2026-01-01
contre_verification: en_attente    # ok | divergence | en_attente
sources:
  - id: S1
    url: https://exemple.org/document.pdf
    archive: https://web.archive.org/web/20260101000000/https://exemple.org/document.pdf
    extraits:
      - texte: "Passage exact, court."
        localisation: "p. 12, § 3"
    type: primaire
    titre: "Titre du document"
---
```

Le corps contient **exactement ces quatre titres**, dans cet ordre :

```markdown
## Ce qui est établi
## Ce qui est faux
## Ce qu'on ne sait pas, et pourquoi
## Pourquoi la rumeur tient
```

1. **Ce qui est établi** — chaque point relié à une source (`[S1]`).
2. **Ce qui est faux** — chaque point relié à une source, avec l'**origine de l'erreur** (mauvaise lecture, chiffre sorti de son contexte, confusion de dates, montage…).
3. **Ce qu'on ne sait pas, et pourquoi** — la raison est qualifiée : classifié, caviardé, procédure en cours, absence de données, données non publiques… et **ce qu'il faudrait pour savoir**. Si rien n'est inconnu, l'écrire explicitement (« Rien d'identifié à ce jour. »).
4. **Pourquoi la rumeur tient** — **première apparition datée** (avec source et archive), voies de propagation, et l'**élément vrai qui a été déformé** s'il existe.

## Format d'une fiche de débat

Pour les questions qui n'ont pas de réponse vrai/faux. Fichier dans `fiches/debat/<id>.md`.

Front-matter : comme une fiche de vérification, sauf que `affirmation` est remplacé par `question`, et que `statut` et `confiance` sont **absents** — une fiche de débat ne rend **pas de verdict**.

Le corps contient ces titres, dans cet ordre :

```markdown
## Positions en présence
## Chiffrages et hypothèses
## Points d'accord
## Points de désaccord, et pourquoi
```

Les chiffrages institutionnels sont présentés **avec leurs hypothèses** : deux chiffres différents viennent souvent de deux hypothèses différentes, et c'est cela qu'il faut montrer.

---

## Règles éthiques

Ces règles priment sur tout le reste. Une fiche qui les enfreint est refusée.

- **Pas de pistage de personnes** : pas de recherche de pseudos ou d'identités, pas d'accès à des caméras, pas de dossiers sur des individus.
- **Aucune donnée de victime**, jamais, même si un document officiel l'a laissée passer.
- **Être cité dans un document ≠ être coupable.** La fiche dit précisément ce que le document établit, rien de plus.
- **Pas de recopie de corpus massifs** contenant des données personnelles : on pointe vers la source officielle avec la référence exacte.
- **Pas de documents obtenus illégalement**, pas d'intrusion.

## Cycle de vie d'une fiche

1. **Recherche préalable** : la fiche existe-t-elle déjà ? Si oui, mise à jour plutôt que doublon.
2. **Rédaction** par le skill `verifier`.
3. **Proposition** via pull request (sous le pseudo GitHub du contributeur).
4. **CI** : validation du schéma, liens vivants, archives présentes.
5. **Contre-vérification à l'aveugle** (skill `contre-verifier`).
6. **Relecture humaine** : un relecteur, deux si `sensible: true`.
7. **Fusion** dans la base.
8. **Contestation** : uniquement avec des preuves. Une nouvelle preuve fait repasser la fiche en `a_revoir` et déclenche une revérification.
