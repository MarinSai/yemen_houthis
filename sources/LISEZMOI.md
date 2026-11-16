# Carte animée : progression des Houthis au Yémen (6 octobre – 15 novembre 2026)

Fichier unique `yemen-houthis.html`, prévu pour une intégration en iframe (hauteur automatique via iframe-resizer v5).

- Textes (titre, chapô, légendes par date, source) : en tête de `src/App.svelte`.
- Déroulé de l'animation (durées) : tableau `SEQ`. Cadre fixe : `CADRE_ETROIT` et `CADRE_LARGE`.
- Flèches : calculées de l'ancienne ligne vers la nouvelle ; tracé manuel possible dans `AXES` et `BILAN_AXES` (lon/lat).
- Encadrés chiffrés : `NOTE_TAEZ`, `NOTE_NORD`, `NOTE_DISPUTE` (position du texte et point visé, en lon/lat).
- Données : `donnees/build_data.py <dossier shapefiles ISW> <dossier Natural Earth> src/data.json` ; globe : `node globe.mjs`.
- Recompiler : `npm install` puis `npx vite build` (sortie : `dist/index.html`).
- `?t=12.5` dans l'adresse fige la carte à la seconde 12,5 de l'animation (contrôle visuel).
