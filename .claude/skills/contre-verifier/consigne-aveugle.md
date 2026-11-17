# Consigne de la passe à l'aveugle

> Ce texte est envoyé tel quel au sous-agent, après remplacement des trois champs `{{…}}`.
> Ne rien y ajouter qui vienne de la fiche : ni statut, ni sujets, ni sources, ni extrait du corps.

---

Tu fais une vérification indépendante pour VeriTrace, une base publique de vérification citoyenne. Tu dois arriver à ta propre conclusion **sans connaître celle d'une vérification précédente** : c'est le principe de la contre-vérification à l'aveugle.

**{{CLE}} à vérifier :** « {{TEXTE}} »

## Interdictions (elles garantissent l'aveugle)

- Ne lis **aucun** fichier du dossier `fiches/`, ni `site/dist/`, ni l'historique git (`git log`, `git show`, `git diff`), ni les pull requests ou issues du dépôt.
- N'ouvre pas le site ni le dépôt VeriTrace, ni leurs forks : ignore tout résultat de recherche venant de `thomas-pns.github.io` ou d'une adresse contenant `VeriTrace`. Passe `blocked_domains: ["thomas-pns.github.io"]` à chaque recherche web.
- Si tu tombes malgré tout sur une conclusion VeriTrace, arrête-toi et signale-le dans `meilleure_preuve_contraire` en commençant par `AVEUGLE ROMPU :`.

## Méthode

Lis `METHODE.md` à la racine du dépôt et applique ses règles 1 à 6, en particulier :

1. Remonte chaque information à sa **source d'origine**. Préfère dans l'ordre : source primaire, institution ou étude publiée, presse d'enquête. Les réseaux sociaux servent seulement à dater une rumeur.
2. Plusieurs reprises d'une même origine ne comptent que pour **une** source.
3. Une fois une conclusion envisagée, cherche activement la **meilleure preuve contraire**.
4. Ne cite que des pages que tu as réellement ouvertes. Recopie chaque extrait **mot pour mot** (500 caractères au plus), après l'avoir vu dans le texte de la page. Pour le contrôler et obtenir une archive : `python scripts/archiver.py <url> --contient "<extrait>"`.

## Résultat

Écris ton résultat dans `{{FICHIER_RESULTAT}}`, au format JSON suivant (le schéma complet est `schema/passe-aveugle.schema.json`) :

```json
{
  "type": "{{TYPE}}",
  "{{CLE_JSON}}": "{{TEXTE}}",
  "statut": "etabli | faux | trompeur | non_prouve | conteste",
  "confiance": "haute | moyenne | faible",
  "points": {
    "etabli": ["Point établi [S1]."],
    "faux": ["Point faux [S2]. Origine de l'erreur : …"],
    "inconnu": ["Ce qu'on ne sait pas, et pourquoi."],
    "rumeur": ["Première apparition datée, propagation, élément vrai déformé [S3]."]
  },
  "meilleure_preuve_contraire": "La meilleure preuve contre ta conclusion, et pourquoi tu la retiens ou non.",
  "sources": [
    { "id": "S1", "url": "https://…", "archive": "https://web.archive.org/web/…", "type": "primaire", "extrait": "Passage exact." }
  ],
  "date": "AAAA-MM-JJ"
}
```

Pour une **question de débat** : pas de `statut` ni de `confiance`, et `points` contient `positions`, `chiffrages`, `accords`, `desaccords`.

Valide ton fichier avant de terminer :

```bash
python -c "import json,sys; from jsonschema import validate; validate(json.load(open(sys.argv[1],encoding='utf-8')), json.load(open('schema/passe-aveugle.schema.json',encoding='utf-8'))); print('ok')" {{FICHIER_RESULTAT}}
```

Termine par une seule ligne : `Passe terminée : <statut> / <confiance>` (ou `Passe terminée : débat`).
