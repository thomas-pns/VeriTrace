import type { CollectionEntry } from "astro:content";

export type Fiche = CollectionEntry<"fiches">;

export const STATUTS = {
  etabli: { libelle: "Établi", aide: "Les preuves disponibles confirment l'affirmation." },
  faux: { libelle: "Faux", aide: "Les preuves disponibles contredisent l'affirmation." },
  trompeur: { libelle: "Trompeur", aide: "Des éléments exacts, présentés de façon à induire une conclusion fausse." },
  non_prouve: { libelle: "Non prouvé", aide: "Aucune preuve suffisante dans un sens ou dans l'autre." },
  conteste: { libelle: "Contesté", aide: "Des sources de même rang se contredisent." },
  a_revoir: { libelle: "À revoir", aide: "La contre-vérification diverge, ou une nouvelle preuve a été apportée." },
} as const;

export const CONFIANCE = { haute: "Confiance haute", moyenne: "Confiance moyenne", faible: "Confiance faible" } as const;

export const CONTRE_VERIF = {
  ok: "Contre-vérifiée à l'aveugle",
  divergence: "Contre-vérification divergente",
  en_attente: "Contre-vérification en attente",
} as const;

export const TYPES_SOURCE = {
  primaire: "Source primaire",
  institutionnelle: "Source institutionnelle",
  etude: "Étude publiée",
  presse: "Presse",
  reseau_social: "Réseau social",
} as const;

export const intitule = (f: Fiche) => f.data.affirmation ?? f.data.question ?? f.data.id;

export const sujetLisible = (s: string) => {
  const t = s.replace(/-/g, " ");
  return t.charAt(0).toUpperCase() + t.slice(1);
};

export const dateFr = (d: Date) =>
  d.toLocaleDateString("fr-FR", { day: "numeric", month: "long", year: "numeric", timeZone: "UTC" });

/** Lien interne qui respecte le chemin de base (site de projet GitHub Pages). */
export const lien = (chemin = "") => `${import.meta.env.BASE_URL.replace(/\/$/, "")}/${chemin.replace(/^\//, "")}`;

export const DEPOT = "https://github.com/thomas-pns/VeriTrace";

export const parDate = (a: Fiche, b: Fiche) => b.data.derniere_maj.getTime() - a.data.derniere_maj.getTime();
