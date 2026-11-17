# VeriTrace

> *Every claim, traced to its source.*

VeriTrace est une base de connaissances **publique, open source et auto-alimentée** de vérification citoyenne. Pour n'importe quelle affirmation, elle cherche à dire :

- ce qui est **établi**, preuves à l'appui ;
- ce qui est **faux**, et d'où ça vient ;
- ce qu'on **ne sait pas**, et pourquoi ;
- **pourquoi une rumeur tient**.

Principe directeur : **« n'importe quoi, pas n'importe qui »**. L'unité de base est une *affirmation*, jamais une personne.

## Comment ça marche

1. **Une IA fait le travail de fond.** Un skill Claude Code (`verifier`) recherche, remonte chaque information à sa source d'origine, lit les documents primaires que personne ne lit (rapports officiels, décisions de justice, PDF de plusieurs centaines de pages) et recoupe.
2. **Elle produit une fiche.** Format fixe, chaque point relié à une source citée mot pour mot et archivée sur la Wayback Machine.
3. **Une seconde passe vérifie à l'aveugle.** Le skill `contre-verifier` refait la recherche sans voir la conclusion. En cas de divergence, la fiche passe au statut `a_revoir`.
4. **Des humains valident.** La fiche est *proposée* au dépôt commun par pull request. Elle n'entre dans la base qu'après la CI (schéma, liens vivants, archives) et une relecture humaine — deux relecteurs pour les sujets sensibles.
5. **La base grandit à chaque utilisation.** Chaque vérification lancée par un contributeur enrichit la base pour tout le monde.

La méthode complète est décrite dans [METHODE.md](METHODE.md).

## Deux types de fiches

| Type | Dossier | Pour quoi |
|---|---|---|
| **Vérification** | `fiches/verification/` | Une affirmation qu'on peut trancher (vrai, faux, trompeur, non prouvé…). Quatre blocs obligatoires. |
| **Débat** | `fiches/debat/` | Une question sans réponse vrai/faux. Positions en présence, chiffrages et hypothèses, accords et désaccords. **Pas de verdict.** |

Le format est défini et validé automatiquement par [`schema/fiche.schema.json`](schema/fiche.schema.json).

### Statuts d'une fiche de vérification

| Statut | Signification |
|---|---|
| `etabli` | Les preuves disponibles confirment l'affirmation. |
| `faux` | Les preuves disponibles contredisent l'affirmation. |
| `trompeur` | Des éléments exacts, mais présentés de façon à induire une conclusion fausse. |
| `non_prouve` | Aucune preuve suffisante dans un sens ou dans l'autre. |
| `conteste` | Des sources de même rang se contredisent. |
| `a_revoir` | La contre-vérification diverge, ou une nouvelle preuve a été apportée. |

## Contribuer

### Avec le skill (recommandé)

**Pas de clé API, pas de serveur** : chaque contributeur fait tourner le skill avec son propre Claude.

1. Installer [Claude Code](https://claude.com/claude-code) et le [GitHub CLI](https://cli.github.com/) (`gh auth login`).
2. Cloner ce dépôt et l'ouvrir dans Claude Code.
3. Lancer le skill `verifier` avec l'affirmation à vérifier.

> **Ce skill contribue à une base publique. Chaque recherche produit une fiche proposée au dépôt commun.**

- Avant de créer une fiche, le skill cherche si elle existe déjà : il propose une mise à jour plutôt qu'un doublon.
- À la fin, il propose la fiche via fork + pull request. **La PR apparaît sous votre pseudo GitHub.** La fiche ne contient que le sujet vérifié, rien de personnel.
- Vous pouvez choisir de **ne pas partager** une recherche donnée : la fiche reste alors sur votre machine.

### À la main

Toute fiche respectant le schéma et la méthode est bienvenue. Ouvrez une pull request ; le modèle de PR rappelle les points à vérifier.

### Contester une fiche

Une fiche se conteste **uniquement avec des preuves**. Ouvrez une issue ou une PR en apportant la source (URL d'origine, archive, passage exact). Une nouvelle preuve déclenche une revérification.

## Règles éthiques non négociables

- **Pas de pistage de personnes** : pas de recherche de pseudos ou d'identités, pas d'accès à des caméras, pas de dossiers sur des individus.
- **Aucune donnée de victime**, jamais, même si un document officiel l'a laissée passer.
- **Être cité dans un document ≠ être coupable.** Une fiche dit précisément ce que le document établit, rien de plus.
- **Pas de recopie de corpus massifs** contenant des données personnelles : on pointe vers la source officielle avec la référence exacte.
- **Pas de documents obtenus illégalement**, pas d'intrusion.

Toute contribution qui enfreint ces règles est refusée, quelle que soit sa qualité par ailleurs.

## Organisation du dépôt

```
fiches/verification/   fiches vrai/faux
fiches/debat/          fiches sur des questions sans réponse vrai/faux
schema/                format des fiches (JSON Schema)
.claude/skills/        skills verifier et contre-verifier
scripts/               archivage Wayback, vérification des liens, extraction PDF
site/                  site statique (Astro + Pagefind), publié sur GitHub Pages
```

Hébergement : uniquement GitHub (dépôt + GitHub Pages).

## Vérifications automatiques

| Workflow | Quand | Ce qu'il vérifie |
|---|---|---|
| **Fiches** | chaque PR | format de toutes les fiches ; archives, extraits et liens des fiches modifiées |
| **Relecture** | chaque PR et chaque avis | 1 approbation sur le dernier commit, 2 si une fiche est sensible |
| **Vérification périodique** | chaque lundi | sources de toute la base ; ouvre une issue `sources-a-verifier` en cas de problème |

En local :

```bash
pip install -r scripts/requirements.txt
python scripts/valider_fiche.py fiches/
python scripts/verifier_sources.py fiches/verification/mon-id.md
```

### Mise en place (mainteneurs)

Dans *Settings → Branches*, protéger `main` :
- exiger une pull request avant fusion ;
- vérifications obligatoires : **Format des fiches**, **Sources (archives, extraits, liens)**, **Relecture humaine** ;
- exiger la relecture des propriétaires de code, avec un fichier `.github/CODEOWNERS` attribuant `.github/`, `scripts/` et `schema/` aux mainteneurs. Ces dossiers contrôlent la CI : une PR qui les modifie ne doit pas pouvoir valider ses propres règles.

## Licence

À définir. Les outils réutilisés gardent leur propre licence (par exemple ICIJ Datashare, AGPL-3.0).
