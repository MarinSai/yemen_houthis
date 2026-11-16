// Textes de la carte en trois langues. La langue est choisie à la compilation (VITE_LANGUE = fr, es ou it).
const MILLIERS = { fr: ' ', es: '.', it: '.' };
export const LANGUES = {
  fr: {
    titre: 'Les Houthis se rapprochent d’Aden',
    chapo: 'Zones sous contrôle houthi au Yémen, du 6 octobre au 15 novembre 2026',
    source: 'Source : Institute for the Study of War, Critical Threats Project · Carte : Le Grand Continent',
    jours: ['6 octobre', '11 octobre', '18 octobre', '26 octobre', '1er novembre', '8 novembre', '15 novembre'],
    date: (j) => `${j} 2026`,
    courts: ['6 oct.', '11 oct.', '18 oct.', '26 oct.', '1er nov.', '8 nov.', '15 nov.'],
    cle: ['Contrôle houthi', 'Gains depuis le 6 octobre', 'Zone disputée', 'Terrain perdu'],
    lire: 'Lire', pause: 'Pause', rejouer: 'Rejouer',
    net: 'km² depuis le 6 octobre',
    carte: 'Carte animée de l’ouest du Yémen montrant, relevé après relevé du 6 octobre au 15 novembre 2026, l’extension des zones contrôlées par les Houthis au sud-ouest, autour de Taëz, et leurs reculs autour de Marib et d’Al-Jawf.',
    pays: ['Arabie saoudite', 'Yémen', 'Érythrée', 'Éthiopie', 'Djibouti'],
    mers: [['Mer', 'Rouge'], ['Golfe', 'd’Aden']],
    villes: ['Sanaa', 'Taëz', 'Marib', 'Hodeïda', 'Saada', 'Mocha'],
    aden: 'Aden',
    taez: ['Autour de Taëz', 'gagnés par les Houthis'],
    nord: ['Marib et Al-Jawf', 'perdus par les Houthis'],
    dispute: ['km² disputés', 'entre le 8 et le 15 novembre'],
    aller: (j) => `Afficher la situation au ${j}`
  },
  es: {
    titre: 'Los hutíes se acercan a Adén',
    chapo: 'Zonas bajo control hutí en Yemen, del 6 de octubre al 15 de noviembre de 2026',
    source: 'Fuente: Institute for the Study of War, Critical Threats Project · Mapa: El Grand Continent',
    jours: ['6 de octubre', '11 de octubre', '18 de octubre', '26 de octubre', '1 de noviembre', '8 de noviembre', '15 de noviembre'],
    date: (j) => `${j} de 2026`,
    courts: ['6 oct.', '11 oct.', '18 oct.', '26 oct.', '1 nov.', '8 nov.', '15 nov.'],
    cle: ['Control hutí', 'Avances desde el 6 de octubre', 'Zona en disputa', 'Terreno perdido'],
    lire: 'Reproducir', pause: 'Pausa', rejouer: 'Repetir',
    net: 'km² desde el 6 de octubre',
    carte: 'Mapa animado del oeste de Yemen que muestra, actualización tras actualización del 6 de octubre al 15 de noviembre de 2026, la expansión de las zonas controladas por los hutíes en el suroeste, en torno a Taiz, y sus retrocesos en torno a Marib y Al Yauf.',
    pays: ['Arabia Saudí', 'Yemen', 'Eritrea', 'Etiopía', 'Yibuti'],
    mers: [['Mar', 'Rojo'], ['Golfo', 'de Adén']],
    villes: ['Saná', 'Taiz', 'Marib', 'Hodeida', 'Saada', 'Moca'],
    aden: 'Adén',
    taez: ['En torno a Taiz', 'ganados por los hutíes'],
    nord: ['Marib y Al Yauf', 'perdidos por los hutíes'],
    dispute: ['km² en disputa', 'entre el 8 y el 15 de noviembre'],
    aller: (j) => `Mostrar la situación el ${j}`
  },
  it: {
    titre: 'Gli houthi si avvicinano ad Aden',
    chapo: 'Zone sotto il controllo houthi in Yemen, dal 6 ottobre al 15 novembre 2026',
    source: 'Fonte: Institute for the Study of War, Critical Threats Project · Mappa: Il Grand Continent',
    jours: ['6 ottobre', '11 ottobre', '18 ottobre', '26 ottobre', '1º novembre', '8 novembre', '15 novembre'],
    date: (j) => `${j} 2026`,
    courts: ['6 ott.', '11 ott.', '18 ott.', '26 ott.', '1º nov.', '8 nov.', '15 nov.'],
    cle: ['Controllo houthi', 'Avanzate dal 6 ottobre', 'Zona contesa', 'Territorio perso'],
    lire: 'Riproduci', pause: 'Pausa', rejouer: 'Rivedi',
    net: 'km² dal 6 ottobre',
    carte: 'Mappa animata dello Yemen occidentale che mostra, aggiornamento dopo aggiornamento dal 6 ottobre al 15 novembre 2026, l’espansione delle zone controllate dagli houthi nel sud-ovest, intorno a Taiz, e i loro arretramenti intorno a Marib e al-Jawf.',
    pays: ['Arabia Saudita', 'Yemen', 'Eritrea', 'Etiopia', 'Gibuti'],
    mers: [['Mar', 'Rosso'], ['Golfo', 'di Aden']],
    villes: ['Sana’a', 'Taiz', 'Marib', 'Hodeida', 'Saada', 'Mokha'],
    aden: 'Aden',
    taez: ['Intorno a Taiz', 'conquistati dagli houthi'],
    nord: ['Marib e al-Jawf', 'persi dagli houthi'],
    dispute: ['km² contesi', 'tra l’8 e il 15 novembre'],
    aller: (j) => `Mostra la situazione al ${j}`
  }
};
export const LANGUE = (import.meta.env.VITE_LANGUE || 'fr');
export const T = LANGUES[LANGUE];
export const nombre = (n) => String(Math.abs(Math.round(n))).replace(/\B(?=(\d{3})+(?!\d))/g, MILLIERS[LANGUE]);
