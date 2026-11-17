---
name: contre-verifier
description: Contre-vérification à l'aveugle d'une fiche VeriTrace existante (règle 7 de la méthode) — un sous-agent refait la recherche à partir de la seule affirmation, sans voir la conclusion, puis les deux passes sont comparées ; en cas de divergence la fiche passe en « a_revoir ». À utiliser quand l'utilisateur demande de contre-vérifier, revérifier à l'aveugle ou valider une fiche dont la contre-vérification est « en_attente ».
---

# Skill `contre-verifier`

Règle 7 de [METHODE.md](../../../METHODE.md) : *une seconde passe refait la recherche sans voir la conclusion ; si divergence → `a_revoir`.*

Le point délicat est **l'aveugle**. Toi, tu vas voir la fiche (pour comparer à la fin). La recherche, elle, est confiée à un **sous-agent** qui ne reçoit que l'affirmation. Tant que la passe à l'aveugle n'est pas terminée, **ne lis pas la fiche** : tu risquerais d'en laisser fuiter quelque chose dans la consigne.

## 0. Annonce (obligatoire, à chaque exécution)

> **Ce skill contribue à une base publique. Chaque recherche produit une fiche proposée au dépôt commun.**
> La contre-vérification sera proposée par pull request sous votre pseudo GitHub, sous licence CC BY-SA 4.0. Vous pourrez choisir de ne pas la partager à la fin.

Idéalement, la contre-vérification est faite par **quelqu'un d'autre que l'auteur de la fiche**. Si l'utilisateur en est l'auteur, ce n'est pas bloquant, mais il faudra le dire dans la PR.

## 1. Choisir la fiche

- Fiche désignée par l'utilisateur ; sinon, proposer celles qui attendent :
  `grep -l "^contre_verification: en_attente" -r fiches/`
- Vérifier qu'aucune PR ouverte ne contre-vérifie déjà cette fiche : `gh pr list --search "<id>" --state open`.

## 2. Extraire l'affirmation, et rien d'autre

```bash
python scripts/extraire_affirmation.py fiches/<type>/<id>.md
```

Ce script ne renvoie que `id`, `type` et `affirmation` (ou `question`). N'ouvre pas la fiche avec un autre outil à ce stade.

## 3. Lancer la passe à l'aveugle (sous-agent)

1. Lis [consigne-aveugle.md](consigne-aveugle.md) et remplace :
   - `{{TEXTE}}` : l'affirmation ou la question extraite, telle quelle ;
   - `{{CLE}}` / `{{CLE_JSON}}` : « Affirmation » / `affirmation` (ou « Question » / `question`) ;
   - `{{TYPE}}` : `verification` ou `debat` ;
   - `{{FICHIER_RESULTAT}}` : un chemin **hors du dépôt** (répertoire temporaire), par exemple `<scratchpad>/passe-aveugle-<id>.json`.
2. Envoie **uniquement la partie sous la ligne `---`** au sous-agent (outil `Agent`, type `general-purpose`), sans rien ajouter qui vienne de la fiche : ni statut, ni sujets, ni sources, ni ton propre avis.
3. Attends la fin de la passe. Si le résultat commence par `AVEUGLE ROMPU`, la passe est **invalide** : relance un nouveau sous-agent, ou arrête-toi et dis-le à l'utilisateur.

## 4. Comparer

Maintenant seulement, tu peux lire la fiche.

```bash
python scripts/comparer_passes.py fiches/<type>/<id>.md <fichier-resultat>
```

Le script vérifie le format de la passe, compare les statuts et liste les sources nouvelles. Puis **juge** :

| Situation | Décision |
|---|---|
| Statuts différents | `divergence` (le script refuse `ok`) |
| Statuts identiques, mais une source nouvelle de rang 1 ou 2 contredit un point des blocs « établi » ou « faux » | `divergence` |
| Statuts identiques, écart de confiance haute ↔ faible | examiner ; `divergence` si l'écart vient d'une preuve que la fiche ignore |
| Fiche de débat : une position, un chiffrage institutionnel ou un désaccord majeur manque, ou un chiffre est contredit | `divergence` |
| Sinon | `ok` |

Une source nouvelle qui **renforce** la fiche n'est pas une divergence : propose de l'ajouter (avec son extrait et son archive) dans la même PR.

Présente la comparaison à l'utilisateur (verdicts des deux passes, sources nouvelles, ta décision et pourquoi) **avant** d'appliquer.

## 5. Appliquer

```bash
python scripts/comparer_passes.py fiches/<type>/<id>.md <fichier-resultat> --appliquer ok
# ou
python scripts/comparer_passes.py fiches/<type>/<id>.md <fichier-resultat> --appliquer divergence
```

- `ok` → `contre_verification: ok`.
- `divergence` → `contre_verification: divergence` et `statut: a_revoir` (fiche de vérification).
- `derniere_maj` est mise à la date du jour.

En cas de divergence, **ne réécris pas** la fiche pour l'aligner sur la seconde passe : c'est le rôle d'une revérification ultérieure, relue par des humains. Ajoute seulement les sources nouvelles utiles si l'utilisateur le souhaite.

Puis valide :

```bash
python scripts/valider_fiche.py fiches/<type>/<id>.md
python scripts/verifier_sources.py fiches/<type>/<id>.md
```

## 6. Proposer

Demande : *« Proposer cette contre-vérification au dépôt commun ? La pull request apparaîtra sous votre pseudo GitHub. (oui / non) »*

Si oui, comme pour le skill `verifier` (fork, branche `contre-verification/<id>`, commit, PR). Le corps de PR contient :

- la décision (`ok` / `divergence`) et sa raison ;
- les verdicts des deux passes (statut, confiance) ;
- les sources nouvelles trouvées, et ce qu'on en a fait ;
- la mention : « Passe à l'aveugle réalisée par un sous-agent n'ayant reçu que l'affirmation. » ;
- si l'utilisateur est l'auteur de la fiche, le dire.

Joins le résultat JSON de la passe à l'aveugle en commentaire de la PR (`gh pr comment <n> --body-file …`), pour que les relecteurs puissent comparer eux-mêmes. Ne l'ajoute pas au dépôt.
