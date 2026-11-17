// @ts-check
import { defineConfig } from "astro/config";

// Site de projet GitHub Pages : https://<propriétaire>.github.io/<dépôt>/
// SITE et BASE sont fournis par le workflow de déploiement ; valeurs par défaut pour ce dépôt.
export default defineConfig({
  // `||` et non `??` : en PR, le workflow transmet des chaînes vides.
  site: process.env.SITE || "https://thomas-pns.github.io",
  base: process.env.BASE || "/VeriTrace",
  trailingSlash: "always",
  build: { format: "directory" },
  // Aucun script de suivi, aucune ressource externe : le site est entièrement statique.
  devToolbar: { enabled: false },
});
