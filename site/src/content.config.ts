import { defineCollection } from "astro:content";
import { glob } from "astro/loaders";
import { z } from "astro/zod";

// Les fiches vivent à la racine du dépôt (fiches/), hors du dossier du site.
// Le format complet est validé par la CI (schema/fiche.schema.json) ; ce schéma-ci
// ne décrit que ce dont le site a besoin, pour qu'un ajout au schéma ne casse pas le build.
const date = z.coerce.date();

const source = z.object({
  id: z.string(),
  url: z.string(),
  archive: z.string(),
  type: z.enum(["primaire", "institutionnelle", "etude", "presse", "reseau_social"]),
  extraits: z.array(z.object({ texte: z.string(), localisation: z.string().optional() })),
  titre: z.string().optional(),
  editeur: z.string().optional(),
  date_publication: date.optional(),
  derive_de: z.string().optional(),
});

const fiches = defineCollection({
  loader: glob({
    pattern: "**/*.md",
    base: "../fiches",
    generateId: ({ entry }) => entry.split("/").pop()!.replace(/\.md$/, ""),
  }),
  schema: z.object({
    type: z.enum(["verification", "debat"]),
    id: z.string(),
    affirmation: z.string().optional(),
    question: z.string().optional(),
    statut: z.enum(["etabli", "faux", "trompeur", "non_prouve", "conteste", "a_revoir"]).optional(),
    confiance: z.enum(["haute", "moyenne", "faible"]).optional(),
    sujets: z.array(z.string()),
    sensible: z.boolean(),
    date_creation: date,
    derniere_maj: date,
    contre_verification: z.enum(["ok", "divergence", "en_attente"]),
    sources: z.array(source),
  }),
});

export const collections = { fiches };
