---
name: verifier
description: Vérifie une affirmation selon la méthode VeriTrace (remontée à la source, documents primaires, recherche de la meilleure preuve contraire) et produit une fiche de vérification en 4 blocs — ou une fiche de débat si la question n'est pas tranchable — puis la propose au dépôt commun par pull request. À utiliser quand l'utilisateur demande de vérifier, fact-checker ou sourcer une affirmation, une rumeur, un chiffre ou une citation.
---

# Skill `verifier`

Tu vérifies **une affirmation**, jamais une personne. Tu appliques strictement [METHODE.md](../../../METHODE.md) — relis-la au début de chaque exécution, elle fait foi en cas de doute.

## 0. Annonce (obligatoire, à chaque exécution)

Commence par afficher, mot pour mot :

> **Ce skill contribue à une base publique. Chaque recherche produit une fiche proposée au dépôt commun.**
> La proposition se fait par pull request sous votre pseudo GitHub. La fiche ne contient que le sujet vérifié, rien de personnel. Vous pourrez choisir de ne pas partager cette recherche à la fin.

## 1. Contrôle éthique (avant toute recherche)

Refuse poliment et arrête-toi si la demande revient à :

- identifier, localiser ou profiler une personne (pseudo, identité réelle, adresse, caméras, « dossier » sur quelqu'un) ;
- exposer des données de victimes ;
- exploiter des documents obtenus illégalement ou une intrusion ;
- recopier un corpus de données personnelles.

Si l'affirmation vise une personne (« X a fait Y »), c'est l'**affirmation** qu'on vérifie, avec ses sources publiques. La fiche dit ce que les documents établissent, rien de plus : *être cité dans un document ≠ être coupable*.

## 2. Reformuler et cadrer

1. Écris l'affirmation **telle qu'elle circule**, puis découpe-la en sous-affirmations vérifiables (qui, quoi, quand, combien, selon qui).
2. Décide du type de fiche :
   - **vérification** si l'affirmation peut, en principe, être confirmée ou infirmée par des faits ;
   - **débat** si c'est une question d'évaluation, de prévision ou de valeurs (ex. effet attendu d'une mesure) : pas de verdict.
3. En cas d'ambiguïté réelle sur le sens de l'affirmation, demande à l'utilisateur avant de chercher.

## 3. Chercher si la fiche existe déjà

Avant toute recherche web :

```bash
grep -ril "<mots-clés>" fiches/
```

Cherche aussi par `sujets` voisins et dans les PR ouvertes (`gh pr list --search "<mots-clés>" --state open`).
- Fiche existante → tu fais une **mise à jour** de ce fichier (même `id`, `date_creation` inchangée, `derniere_maj` = aujourd'hui), pas un doublon.
- PR ouverte sur le même sujet → signale-la à l'utilisateur et propose de contribuer à celle-ci plutôt que d'en ouvrir une autre.

## 4. Recherche (règles 1 à 5)

Mène la recherche dans cet ordre et garde des notes de travail (elles ne vont pas dans la fiche) :

1. **Origine de la rumeur.** Trouve la première apparition datée que tu peux documenter (réseaux sociaux, forums, médias). Utilise l'API CDX de la Wayback Machine pour dater les plus anciennes captures d'une URL :
   `https://web.archive.org/cdx/search/cdx?url=<url>&limit=5&output=json`
   Les sources `reseau_social` servent **uniquement** au bloc 4.
2. **Remonter à la source primaire.** Pour chaque fait invoqué, suis la chaîne de citations jusqu'au document d'origine (texte officiel, décision, rapport, jeu de données, enregistrement intégral). Lis-le **toi-même**, au bon endroit : un PDF long se lit à la page pertinente, pas via son résumé de presse. Note la page / le paragraphe.
3. **Indépendance (règle 3).** Regroupe les sources qui dérivent d'une même origine (champ `derive_de`). 500 reprises = 1 source.
4. **Chercher à se contredire (règle 4).** Une fois une conclusion envisagée, cherche délibérément la **meilleure** preuve contraire (requêtes formulées dans le sens opposé, sources institutionnelles divergentes, erratums, décisions en appel). Si elle tient, elle figure dans la fiche.
5. **Niveaux (règle 5).** Classe chaque point : établi / « Probable : » / non prouvé (bloc 3). Un croisement de documents produit un *indice*, jamais une *accusation*.

Ne cite jamais une source que tu n'as pas effectivement ouverte. Si une page est inaccessible, dis-le plutôt que de la reconstituer.

## 5. Archiver chaque source (règle 6)

Chaque source doit avoir un lien Wayback horodaté **qui contient réellement les passages cités**.

Pour chaque source, une fois ses passages choisis :

```bash
python scripts/archiver.py <url> --contient "passage 1" --contient "passage 2"
```

Le script parcourt les captures existantes et renvoie la plus récente qui contient **tous** les passages (il écarte ainsi les captures vides ou anti-robot) ; à défaut, il demande une nouvelle capture et la vérifie. S'il échoue sur une URL courte, essaie l'URL canonique longue de la page. Il gère l'encodage des URL et la limite de débit de la Wayback Machine (erreur 429) : sois patient, n'en lance pas plusieurs en parallèle.

**Extraits mot pour mot.** Les outils de lecture web qui résument une page peuvent reformuler les citations. Ne recopie un passage dans `extraits[].texte` qu'après l'avoir vu dans le texte brut de la page ; `archiver.py --contient` et `verifier_sources.py` (étape 7) le contrôlent.

**URL qui redirige.** Si l'URL d'origine redirige aujourd'hui vers un autre contenu, garde l'URL d'origine dans `url` et une capture **d'avant** la redirection dans `archive`.

Une source peut porter plusieurs `extraits` (un par point qu'elle appuie). Si aucune archive valable ne peut être obtenue, signale-le à l'utilisateur : la fiche ne passera pas la CI sans archive.

## 6. Rédiger la fiche

Pars du modèle :
- vérification : [modele-verification.md](modele-verification.md) → `fiches/verification/<id>.md`
- débat : [modele-debat.md](modele-debat.md) → `fiches/debat/<id>.md`

Règles de rédaction :
- `id` en kebab-case, court, décrivant l'affirmation (pas un nom de personne si on peut l'éviter), identique au nom du fichier.
- `statut` et `confiance` selon METHODE.md. `contre_verification: en_attente` (la contre-vérification à l'aveugle est faite par un autre skill).
- `sensible: true` si le sujet touche à des victimes, des mineurs, la santé, une procédure judiciaire en cours, un conflit armé ou des personnes nommées.
- Chaque point des blocs 1 et 2 renvoie à au moins une source `[S1]`. Aucune source `reseau_social` dans ces deux blocs.
- Bloc 2 : donne l'**origine de l'erreur** pour chaque point faux.
- Bloc 3 : qualifie la raison de l'inconnu (classifié, caviardé, procédure en cours, absence de données…) et ce qu'il faudrait pour savoir. S'il est vide, écris « Rien d'identifié à ce jour. »
- Bloc 4 : première apparition **datée et sourcée**, propagation, élément vrai déformé.
- Ton neutre et factuel. Aucune donnée personnelle hors de ce que l'affirmation exige ; jamais de donnée de victime.

## 7. Valider

```bash
python scripts/valider_fiche.py fiches/<type>/<id>.md
python scripts/verifier_sources.py fiches/<type>/<id>.md
```

(Dépendances : `pip install -r scripts/requirements.txt` ; ajouter `pdfplumber` si une source est un PDF.)

- `valider_fiche.py` : format (schéma, titres, citations `[Sn]`, réseaux sociaux hors des blocs de preuve).
- `verifier_sources.py` : chaque archive est accessible et contient chaque extrait (**erreur** sinon) ; liens d'origine morts, redirections ou extraits disparus de la page actuelle (**avertissements**, à signaler à l'utilisateur).

Corrige jusqu'à zéro erreur. Ne passe jamais à l'étape suivante avec une erreur.

## 8. Restituer à l'utilisateur

Présente un résumé court : affirmation, statut, confiance, les 2-3 sources décisives, ce qui reste inconnu, et le chemin du fichier.

## 9. Proposer la fiche (contribution)

Demande explicitement :

> Proposer cette fiche au dépôt commun ? La pull request apparaîtra sous votre pseudo GitHub. (oui / non — ne pas partager cette recherche)

- **Non** → arrête-toi. La fiche reste en local ; rappelle son chemin.
- **Oui** → vérifie `gh auth status`, puis :

```bash
gh repo fork --remote --remote-name fork   # sans effet si le fork existe déjà
git switch -c fiche/<id>
git add fiches/<type>/<id>.md
git commit -m "Fiche : <affirmation abrégée>"
git push -u fork fiche/<id>
gh pr create --title "Fiche : <affirmation abrégée>" --body-file <corps-de-pr>
```

Corps de PR (fichier temporaire) :
- type de fiche, statut, confiance, `sensible` ;
- nouvelle fiche ou mise à jour (et ce qui change) ;
- la liste de contrôle : sources primaires consultées, archives présentes, meilleure preuve contraire cherchée, aucune donnée personnelle ni de victime ;
- la mention : « Fiche produite avec le skill `verifier`. Contre-vérification à l'aveugle : en attente. »

N'inclus dans la PR **que** le fichier de la fiche. Ne pousse jamais sur la branche principale du dépôt commun. Donne à l'utilisateur le lien de la PR et rappelle qu'elle n'entrera dans la base qu'après la CI et la relecture humaine (deux relecteurs si `sensible: true`).
