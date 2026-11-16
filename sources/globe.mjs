// Globe de situation (projection orthographique), rayon 100, centré en (0,0)
import { geoOrthographic, geoPath, geoGraticule } from 'd3-geo';
import { feature } from 'topojson-client';
import fs from 'fs';
const topo = JSON.parse(fs.readFileSync('node_modules/world-atlas/countries-110m.json'));
const land = feature(topo, topo.objects.land);
const pays = feature(topo, topo.objects.countries);
const yemen = pays.features.find((f) => f.properties.name === 'Yemen');
const proj = geoOrthographic().rotate([-44, -16]).scale(100).translate([0, 0]).clipAngle(90).precision(0.4);
const path = geoPath(proj).digits(1);
const cadre = { type: 'Polygon', coordinates: [[[39.5, 10.5], [39.5, 20], [49.5, 20], [49.5, 10.5], [39.5, 10.5]]] };
const out = { land: path(land), grille: path(geoGraticule().step([15, 15])()), cadre: path(cadre) };
fs.writeFileSync('src/globe.json', JSON.stringify(out));
console.log(Object.fromEntries(Object.entries(out).map(([k, v]) => [k, v.length])), out.cadre);
