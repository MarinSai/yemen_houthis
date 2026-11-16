<script>
  import { onMount } from 'svelte';
  import D from './data.json';
  import G from './globe.json';

  /* ------------------------------------------------------------------
     Textes : tout ce qui se lit est ici.
     ------------------------------------------------------------------ */
  const TITRE = 'Les Houthis se rapprochent d’Aden';
  const CHAPO = 'Zones sous contrôle houthi au Yémen, du 6 octobre au 15 novembre 2026';
  const SOURCE = 'Source : Institute for the Study of War, Critical Threats Project · Carte : Le Grand Continent';
  const JOURS = ['6 octobre', '11 octobre', '18 octobre', '26 octobre', '1er novembre', '8 novembre', '15 novembre'];
  const COURTS = ['6 oct.', '11 oct.', '18 oct.', '26 oct.', '1er nov.', '8 nov.', '15 nov.'];
  const ECARTS = [0, 5, 12, 20, 26, 33, 40]; // jours écoulés depuis le 6 octobre

  /* ------------------------------------------------------------------
     Projection (identique à celle du script de préparation des données)
     ------------------------------------------------------------------ */
  const merc = (lat) => Math.log(Math.tan(Math.PI / 4 + (lat * Math.PI) / 360)) * 180 / Math.PI;
  const P = (lon, lat) => [(lon - D.lon0) * D.K, (D.mercLat0 - merc(lat)) * D.K];
  const boite = (lonO, lonE, latS, latN) => {
    const [x0, y1] = P(lonO, latS), [x1, y0] = P(lonE, latN);
    return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
  };
  // cadre fixe : tout l'ouest du Yémen, d'Aden à la frontière saoudienne
  const CADRE_ETROIT = boite(41.85, 46.45, 11.7, 18.25);
  const CADRE_LARGE = boite(42.2, 46.5, 11.6, 18.2);
  const KM = 100 / 111.2; // unités carte par kilomètre vers 15° N

  /* ------------------------------------------------------------------
     Déroulé : un relevé après l'autre, sans mouvement de caméra
     ------------------------------------------------------------------ */
  const PAR_JOUR = 0.37; // secondes d'animation par jour de calendrier
  const SEQ = [
    { type: 'pose', dur: 1.2, date: 0 },
    ...[0, 1, 2, 3, 4, 5].map((k) => ({ type: 'sem', k, dur: (ECARTS[k + 1] - ECARTS[k]) * PAR_JOUR })),
    { type: 'bilan', dur: 1.6, date: 6 }
  ];
  let acc = 0;
  for (const s of SEQ) { s.t0 = acc; acc += s.dur; }
  const FIN = acc;
  const semDebut = (k) => SEQ.find((s) => s.type === 'sem' && s.k === k).t0;
  // instant où la carte montre exactement le relevé i
  const instant = (i) => (i === 6 ? FIN : semDebut(i));

  const borne = (v, a = 0, b = 1) => Math.max(a, Math.min(b, v));
  const doux = (x) => (x < 0.5 ? 4 * x * x * x : 1 - Math.pow(-2 * x + 2, 3) / 2);
  const sortie = (x) => 1 - Math.pow(1 - x, 3);

  let t = 0;
  let lecture = false;
  let lance = false;
  let cw = 0;
  let scene;

  $: etroit = cw > 0 && cw < 600;
  $: ratio = etroit ? 7 / 10 : 7 / 5;
  function cadrer(b, r) {
    let { x, y, w, h } = b;
    if (w / h < r) { const nw = h * r; x -= (nw - w) / 2; w = nw; }
    else { const nh = w / r; y -= (nh - h) / 2; h = nh; }
    return { x, y, w, h };
  }
  $: vb = cadrer(etroit ? CADRE_ETROIT : CADRE_LARGE, ratio);
  $: upp = cw > 0 ? vb.w / cw : 1; // unités carte par pixel
  $: vbTxt = `${vb.x.toFixed(2)} ${vb.y.toFixed(2)} ${vb.w.toFixed(2)} ${vb.h.toFixed(2)}`;

  function etat(t) {
    const tt = borne(t, 0, FIN);
    let s = SEQ[SEQ.length - 1];
    for (const q of SEQ) { if (tt < q.t0 + q.dur) { s = q; break; } }
    const tau = tt - s.t0;
    const o = { tau, opa: [0, 0, 0, 0, 0, 0, 0], k: -1, rev: 0, frais: 0, fl: 0, flA: 0, bil: 0, entree: 1, onde: -1 };
    if (s.type === 'sem') {
      // tout avance à vitesse constante : le fondu, la tache rouge et le curseur couvrent l'intervalle entier
      const u = tau / s.dur;
      o.opa[s.k] = 1 - u; o.opa[s.k + 1] = u;
      o.k = s.k; o.rev = borne(u / 0.8);
      o.frais = Math.min(borne(u / 0.12), 1 - borne((u - 0.78) / 0.22));
      o.fl = doux(borne((u - 0.12) / 0.5));
      o.flA = 1 - borne((u - 0.8) / 0.2);
      o.onde = tau;
      o.pos = s.k + u; o.date = u < 0.5 ? s.k : s.k + 1;
    } else {
      o.opa[s.date] = 1; o.pos = s.date; o.date = s.date;
      if (s.type === 'pose') o.entree = sortie(borne(tau / 0.9));
      if (s.type === 'bilan') o.bil = doux(borne(tau / 1.3));
    }
    return o;
  }
  $: E = etat(t);
  $: fini = t >= FIN;
  $: jour = E.date;

  const interp = (serie, pos) => {
    const i = Math.floor(pos), f = pos - i;
    return serie[i] + (serie[Math.min(6, i + 1)] - serie[i]) * f;
  };
  const nombre = (n) => String(Math.abs(Math.round(n))).replace(/\B(?=(\d{3})+(?!\d))/g, ' ');
  const dizaine = (n) => Math.round(n / 10) * 10;
  $: net = Math.round(interp(D.area, E.pos) - D.area[0]);
  $: gainSud = dizaine(interp(D.gainSud, E.pos));
  $: perteNord = dizaine(interp(D.perteNord, E.pos));
  $: frise = interp(ECARTS, E.pos) / 40 * 100;

  /* ------------------------------------------------------------------
     Géométries
     ------------------------------------------------------------------ */
  const Y_SECTEUR = P(44, 14.3)[1];
  // sépare un tracé en deux secteurs (sud-ouest / nord-est) pour limiter la zone de flou
  function secteurs(d) {
    const so = [], ne = [];
    for (const m of d.split('M')) {
      if (!m) continue;
      const y = +m.slice(m.indexOf(',') + 1, m.search(/[LZ]/));
      (y > Y_SECTEUR ? so : ne).push('M' + m);
    }
    return [so.join(''), ne.join('')].filter(Boolean);
  }
  const GCUM = D.gcum.map(secteurs);
  const PAYS = Object.values(D.land).join('');
  const TERRES = PAYS + D.yemen;

  // flèche effilée le long d'une courbe de Bézier quadratique, tracée jusqu'à la fraction g
  function fleche(S, C, F, g, W) {
    if (g <= 0.02) return '';
    const N = 18, pts = [];
    for (let i = 0; i <= N; i++) {
      const u = (g * i) / N, v = 1 - u;
      pts.push([v * v * S[0] + 2 * v * u * C[0] + u * u * F[0], v * v * S[1] + 2 * v * u * C[1] + u * u * F[1]]);
    }
    const cum = [0];
    for (let i = 1; i <= N; i++) cum.push(cum[i - 1] + Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]));
    const L = cum[N]; if (L < 0.01) return '';
    const tete = Math.min(2.7 * W, L * 0.55), corps = L - tete;
    const g1 = [], d1 = [];
    let base = null, tan = null;
    for (let i = 0; i <= N; i++) {
      const a = pts[Math.max(0, i - 1)], b = pts[Math.min(N, i + 1)];
      const n = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1;
      const tx = (b[0] - a[0]) / n, ty = (b[1] - a[1]) / n;
      if (cum[i] <= corps) {
        const l = (0.1 + 0.4 * (cum[i] / Math.max(corps, 0.001))) * W;
        g1.push([pts[i][0] - ty * l, pts[i][1] + tx * l]); d1.push([pts[i][0] + ty * l, pts[i][1] - tx * l]);
      } else if (!base) {
        const f = (corps - cum[i - 1]) / (cum[i] - cum[i - 1]);
        base = [pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * f, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * f];
        tan = [tx, ty];
      }
    }
    if (!base) { base = pts[N - 1]; tan = [1, 0]; }
    const [tx, ty] = tan, p = pts[N];
    const f2 = (q) => q[0].toFixed(2) + ',' + q[1].toFixed(2);
    const poly = [
      ...g1,
      [base[0] - ty * 0.5 * W, base[1] + tx * 0.5 * W],
      [base[0] - ty * 1.15 * W, base[1] + tx * 1.15 * W],
      p,
      [base[0] + ty * 1.15 * W, base[1] - tx * 1.15 * W],
      [base[0] + ty * 0.5 * W, base[1] - tx * 0.5 * W],
      ...d1.reverse()
    ];
    return 'M' + poly.map(f2).join('L') + 'Z';
  }

  /* Flèches. L'ISW ne publie pas d'axes : le sens va de l'ancienne ligne houthie vers la nouvelle.
     Tracé manuel { pointe: [lon, lat], sens: [dx, dy] } quand la zone gagnée était déjà bordée de plusieurs côtés. */
  const AXES = {
    // 15 novembre, sud-est de Taëz : la zone touchait déjà les lignes houthies à l'ouest (36 km) et à l'est (38 km)
    '5-0': [{ pointe: [44.1, 13.33], sens: [1, 0.12] }, { pointe: [44.2, 13.37], sens: [-1, 0.3] }]
  };
  const BILAN_AXES = [
    { pointe: [43.9, 13.44], sens: [1, -0.32], long: 50 },
    { pointe: [44.22, 13.36], sens: [-1, 0.34], long: 38 }
  ];
  // longueur à l'écran, en pixels, selon la surface gagnée
  const longueur = (km2) => borne(14 + Math.sqrt(km2) * 1.75, 24, 62);
  function tracer(pointe, sens, longPx, upp, courbe = 0.17) {
    const n = Math.hypot(sens[0], sens[1]) || 1, dx = sens[0] / n, dy = sens[1] / n;
    const L = longPx * upp;
    const F = pointe, S = [F[0] - dx * L, F[1] - dy * L];
    const mx = (S[0] + F[0]) / 2, my = (S[1] + F[1]) / 2;
    return { S, F, C: [mx - dy * L * courbe, my + dx * L * courbe], W: borne(longPx * 0.125, 3.2, 7.5) * upp };
  }
  function axesSemaine(w, k, upp) {
    const axes = [];
    w.gain.forEach((c, i) => {
      if (c.km2 < 35) return;
      const m = AXES[k + '-' + i];
      if (m) {
        for (const a of m) axes.push(tracer(P(...a.pointe), a.sens, longueur(c.km2 / m.length), upp));
        return;
      }
      let dx = c.f[0] - c.o[0], dy = c.f[1] - c.o[1], n = Math.hypot(dx, dy);
      if (n < 1.2) { dx = c.c[0] - c.o[0]; dy = c.c[1] - c.o[1]; n = Math.hypot(dx, dy); }
      if (n < 0.4) return;
      const L = longueur(c.km2);
      axes.push(tracer([c.c[0] + (dx / n) * L * upp * 0.3, c.c[1] + (dy / n) * L * upp * 0.3], [dx, dy], L, upp));
    });
    return axes.map((a, j) => ({ ...a, id: 'ax' + k + '_' + j }));
  }
  const SEMAINES = D.weeks.map((w, k) => ({
    ...w,
    gain: w.gain.map((c, i) => ({ ...c, id: 'rv' + k + '_' + i })),
    // ondes : là où le relevé change (gains en rouge, reculs en gris)
    ondes: [...w.gain.filter((c) => c.km2 >= 35).map((c) => ({ c: c.c, gain: true })), ...w.loss.filter((c) => c.km2 >= 35).map((c) => ({ c: c.c, gain: false }))]
  }));
  $: AXES_SEM = SEMAINES.map((w, k) => axesSemaine(w, k, upp));
  $: AXES_BILAN = BILAN_AXES.map((a) => tracer(P(...a.pointe), a.sens, a.long, upp, 0.2));

  // distance entre Aden et la position houthie la plus proche (inchangée sur les sept relevés)
  const ADEN = D.aden.p, PROCHE = D.aden.H[6].p, ADEN_KM = Math.round(D.aden.H[6].km);
  const mesureAngle = Math.atan2(ADEN[1] - PROCHE[1], ADEN[0] - PROCHE[0]) * 180 / Math.PI;

  /* ------------------------------------------------------------------
     Étiquettes
     ------------------------------------------------------------------ */
  const PAYS_NOMS = [
    { t: 'Arabie saoudite', p: [44.6, 17.85] },
    { t: 'Yémen', p: [46.8, 15.5], etroit: [45.98, 15.0] },
    { t: 'Érythrée', p: [40.99, 14.36], large: true },
    { t: 'Éthiopie', p: [40.96, 13.0], large: true },
    { t: 'Djibouti', p: [42.55, 12.05], large: true }
].map((e) => ({ ...e, xy: P(...e.p), xyE: P(...(e.etroit || e.p)) }));
  const MERS = [
    { t: ['Mer', 'Rouge'], p: [41.05, 16.28], etroit: [42.24, 16.0] },
    { t: ['Golfe', 'd’Aden'], p: [47.85, 12.35], etroit: [45.75, 12.42] }
  ].map((e) => ({ ...e, xy: P(...e.p), xyE: e.etroit ? P(...e.etroit) : P(...e.p) }));
  const VILLES = [
    { t: 'Sanaa', p: [44.21, 15.35], a: 'd', cap: true },
    { t: 'Taëz', p: [44.02, 13.58], a: 'h' },
    { t: 'Marib', p: [45.32, 15.46], a: 'd' },
    { t: 'Hodeïda', p: [42.95, 14.8], a: 'd' },
    { t: 'Saada', p: [43.76, 16.94], a: 'd' },
    { t: 'Mocha', p: [43.25, 13.32], a: 'g' }
  ].map((e) => ({ ...e, xy: P(...e.p) }));
  const etoile = (r) => {
    let d = '';
    for (let i = 0; i < 10; i++) { const a = -Math.PI / 2 + (i * Math.PI) / 5, q = i % 2 ? r * 0.42 : r; d += (i ? 'L' : 'M') + (Math.cos(a) * q).toFixed(3) + ',' + (Math.sin(a) * q).toFixed(3); }
    return d + 'Z';
  };

  // encadrés : titre en Sanomat, chiffre qui évolue, filet vers la zone
  const NOTE_TAEZ = { xy: P(42.08, 14.42), cible: P(43.8, 13.53) };
  const NOTE_NORD = { xy: P(45.16, 16.62), cible: P(45.47, 16.04) };
  const NOTE_DISPUTE = { cible: P(44.02, 12.86), coude: P(44.02, 12.47) };

  // boîtes des blocs de texte des encadrés, mesurées après chargement des polices
  let bTaez = null, bNord = null;
  function mesure(node, opt) {
    let { cb, cle } = opt, prec = '';
    const lire = () => {
      try {
        const b = node.getBBox(); if (!b.width) return;
        const k = [b.x, b.y, b.width, b.height].map((v) => v.toFixed(2)).join();
        if (k !== prec) { prec = k; cb({ x: b.x, y: b.y, width: b.width, height: b.height }); }
      } catch (e) {}
    };
    requestAnimationFrame(lire); if (document.fonts) document.fonts.ready.then(lire);
    return { update(n) { cb = n.cb; if (n.cle !== cle) { cle = n.cle; requestAnimationFrame(lire); } } };
  }
  $: ptsTaez = bTaez ? `${bTaez.x + bTaez.width / 2},${bTaez.y + bTaez.height + 4 * upp} ${bTaez.x + bTaez.width / 2},${NOTE_TAEZ.cible[1]} ${NOTE_TAEZ.cible[0]},${NOTE_TAEZ.cible[1]}` : '';
  $: ptsNord = bNord ? `${bNord.x + bNord.width / 2},${bNord.y + bNord.height + 4 * upp} ${bNord.x + bNord.width / 2},${NOTE_NORD.cible[1]} ${NOTE_NORD.cible[0]},${NOTE_NORD.cible[1]}` : '';
  $: ptsDispute = `${NOTE_DISPUTE.coude[0]},${NOTE_DISPUTE.coude[1] - 14 * upp} ${NOTE_DISPUTE.cible[0]},${NOTE_DISPUTE.cible[1]}`;

  /* ------------------------------------------------------------------
     Lecture
     ------------------------------------------------------------------ */
  let dernier = 0, raf = 0;
  function image(maint) {
    const dt = dernier ? Math.min(0.05, (maint - dernier) / 1000) : 0;
    dernier = maint;
    if (lecture) {
      t = Math.min(FIN, t + dt);
      if (t >= FIN) lecture = false; // la carte reste figée au 15 novembre
    }
    raf = lecture ? requestAnimationFrame(image) : 0;
  }
  function jouer() { if (!lecture) { lecture = true; dernier = 0; if (!raf) raf = requestAnimationFrame(image); } }
  function bouton() {
    if (lecture) lecture = false;
    else { if (t >= FIN) t = 0; lance = true; jouer(); }
  }
  function aller(i) { lecture = false; lance = true; t = instant(i); }

  onMount(() => {
    const q = new URLSearchParams(location.search);
    const reduit = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (q.has('t')) { t = +q.get('t') || 0; lance = true; return; }
    if (reduit) { t = FIN; lance = true; return; }
    // l'animation démarre une seule fois, quand la carte entre dans l'écran
    if ('IntersectionObserver' in window) {
      const io = new IntersectionObserver((es) => {
        if (es[0].isIntersecting && !lance) { lance = true; jouer(); io.disconnect(); }
      }, { threshold: 0.35 });
      io.observe(scene);
      return () => io.disconnect();
    }
    lance = true; jouer();
  });
</script>

<main class="bloc">
  <header class="tete">
    <h1>{TITRE}</h1>
    <p class="chapo">{CHAPO}</p>
  </header>

  <ul class="cle" aria-label="Clé de lecture">
    <li><svg width="18" height="14" viewBox="0 0 18 14" aria-hidden="true"><rect x="1.5" y="1.5" width="15" height="11" rx="2" fill="rgba(221,32,60,.15)" stroke="#dd203c" stroke-width="1.3"/></svg>Contrôle houthi</li>
    <li><svg width="18" height="14" viewBox="0 0 18 14" aria-hidden="true"><defs><filter id="cleflou" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="1.3"/></filter></defs><rect x="2.5" y="2.5" width="13" height="9" rx="2" fill="#dd203c" opacity=".85" filter="url(#cleflou)"/></svg>Gains depuis le 6 octobre</li>
    <li><svg width="18" height="14" viewBox="0 0 18 14" aria-hidden="true"><defs><pattern id="cleh1" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="4" stroke="#dd203c" stroke-width="1.4"/></pattern></defs><rect x="1" y="1" width="16" height="12" rx="2" fill="url(#cleh1)"/></svg>Zone disputée</li>
    <li><svg width="18" height="14" viewBox="0 0 18 14" aria-hidden="true"><defs><pattern id="cleh2" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><line x1="0" y1="0" x2="0" y2="4" stroke="#4a4a4f" stroke-width="1.4"/></pattern></defs><rect x="1" y="1" width="16" height="12" rx="2" fill="url(#cleh2)"/></svg>Terrain perdu</li>
  </ul>

  <div class="repere">
    <p class="quand"><span class="jour">{JOURS[jour]} 2026</span>
      {#if jour > 0}<span class="net" class:moins={net < 0}>{net < 0 ? '−' : '+'}{nombre(net)}&nbsp;km² depuis le 6 octobre</span>{/if}</p>
    <button class="rejouer" type="button" on:click={bouton}>
      {#if lecture}
        <svg width="11" height="11" viewBox="0 0 14 14" aria-hidden="true"><rect x="2" y="1" width="3.6" height="12" fill="currentColor" /><rect x="8.4" y="1" width="3.6" height="12" fill="currentColor" /></svg>Pause
      {:else if fini}
        <svg width="13" height="13" viewBox="0 0 16 16" aria-hidden="true"><path d="M13.2 8a5.2 5.2 0 1 1-1.6-3.75" fill="none" stroke="currentColor" stroke-width="1.6" /><path d="M12.9 1.2v3.6H9.3" fill="none" stroke="currentColor" stroke-width="1.6" /></svg>Rejouer
      {:else}
        <svg width="11" height="11" viewBox="0 0 14 14" aria-hidden="true"><path d="M3 1 L13 7 L3 13 Z" fill="currentColor" /></svg>Lire
      {/if}
    </button>
  </div>

  <div class="scene" bind:this={scene} bind:clientWidth={cw} style="aspect-ratio:{etroit ? '7 / 10' : '7 / 5'}">
    {#if cw > 0}
    <!-- 1. fond : ne change jamais, dessiné une seule fois -->
    <svg class="couche" viewBox={vbTxt} preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      <defs>
        <filter id="rivage" x="-5%" y="-5%" width="110%" height="110%"><feGaussianBlur stdDeviation={(11 * upp).toFixed(3)} /></filter>
      </defs>
      <path d={TERRES} class="rivage" filter="url(#rivage)" />
      <path d={TERRES} class="terre" />
      <path d={D.urban} class="bati" />
      <path d={D.roads} class="route" />
      <path d={D.borders} class="frontiere-halo" />
      <path d={D.yborder} class="frontiere-halo" />
      <path d={D.borders} class="frontiere" />
      <path d={D.yborder} class="frontiere" />
    </svg>

    <div class="voile"></div>

    <!-- 2. contrôle houthi : un groupe par relevé, en fondu enchaîné -->
    <svg class="couche" viewBox={vbTxt} preserveAspectRatio="xMidYMid slice" role="img"
         aria-label="Carte animée de l’ouest du Yémen montrant, relevé après relevé du 6 octobre au 15 novembre 2026, l’extension des zones contrôlées par les Houthis au sud-ouest, autour de Taëz, et leurs reculs autour de Marib et d’Al-Jawf.">
      <defs>
        <filter id="flou" x="-40%" y="-40%" width="180%" height="180%"><feGaussianBlur stdDeviation={(2.2 * upp).toFixed(3)} /></filter>
        <filter id="flou-vif" x="-60%" y="-60%" width="220%" height="220%"><feGaussianBlur stdDeviation={(3.2 * upp).toFixed(3)} /></filter>
        <filter id="halo-vif" x="-90%" y="-90%" width="280%" height="280%"><feGaussianBlur stdDeviation={(9 * upp).toFixed(3)} /></filter>
        <radialGradient id="disque"><stop offset="0" stop-color="#fff" /><stop offset=".55" stop-color="#fff" /><stop offset="1" stop-color="#fff" stop-opacity="0" /></radialGradient>
        <pattern id="h-dispute" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="scale({upp.toFixed(4)}) rotate(45)"><line x1="0" y1="0" x2="0" y2="5" stroke="#dd203c" stroke-width="1.4" /></pattern>
        <pattern id="h-perdu" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="scale({upp.toFixed(4)}) rotate(-45)"><line x1="0" y1="0" x2="0" y2="5" stroke="#4a4a4f" stroke-width="1.3" /></pattern>
        {#if E.k >= 0}
          {#each SEMAINES[E.k].gain as c (c.id)}
            <mask id={c.id} maskUnits="userSpaceOnUse" x={c.o[0] - 3 * c.r} y={c.o[1] - 3 * c.r} width={6 * c.r} height={6 * c.r}>
              <circle cx={c.o[0]} cy={c.o[1]} r={(0.5 + (c.r / 0.55) * E.rev).toFixed(2)} fill="url(#disque)" />
            </mask>
          {/each}
          {#each AXES_SEM[E.k] as a (a.id)}
            <linearGradient id={'g' + a.id} gradientUnits="userSpaceOnUse" x1={a.S[0]} y1={a.S[1]} x2={a.F[0]} y2={a.F[1]}>
              <stop offset="0" stop-color="#a3122a" stop-opacity="0" /><stop offset=".5" stop-color="#a3122a" /><stop offset="1" stop-color="#8f0f24" />
            </linearGradient>
          {/each}
        {/if}
        {#each AXES_BILAN as a, i}
          <linearGradient id={'gb' + i} gradientUnits="userSpaceOnUse" x1={a.S[0]} y1={a.S[1]} x2={a.F[0]} y2={a.F[1]}>
            <stop offset="0" stop-color="#a3122a" stop-opacity="0" /><stop offset=".5" stop-color="#a3122a" /><stop offset="1" stop-color="#8f0f24" />
          </linearGradient>
        {/each}
      </defs>

      <g opacity={E.entree.toFixed(3)}>
        {#each D.H as d, i}
          {#if E.opa[i] > 0.002}
            <g opacity={E.opa[i].toFixed(3)}>
              <path {d} class="ctrl" />
              {#each GCUM[i] as g}<path d={g} class="gain" filter="url(#flou)" />{/each}
              {#if D.lcum[i]}<path d={D.lcum[i]} class="perdu" />{/if}
              <path d={D.C[i]} class="dispute" />
              <path {d} class="halo h3" /><path {d} class="halo h2" /><path {d} class="halo h1" />
            </g>
          {/if}
        {/each}
      </g>

      <!-- le relevé en cours : le rouge se répand depuis l'ancienne ligne -->
      {#if E.k >= 0}
        {#if E.frais > 0.002}
          <g opacity={E.frais.toFixed(3)}>
            {#if SEMAINES[E.k].lossAll}<path d={SEMAINES[E.k].lossAll} class="perdu vif" opacity={borne(E.rev * 1.4).toFixed(3)} />{/if}
            <g filter="url(#halo-vif)" opacity=".55">
              {#each SEMAINES[E.k].gain as c (c.id)}<path d={c.d} class="gain vif" mask="url(#{c.id})" />{/each}
            </g>
            <g filter="url(#flou-vif)">
              {#each SEMAINES[E.k].gain as c (c.id)}<path d={c.d} class="gain vif" mask="url(#{c.id})" />{/each}
            </g>
          </g>
        {/if}
        <!-- ondes : attirent l'œil là où la ligne bouge -->
        {#each SEMAINES[E.k].ondes as o}
          {#each [0, 0.45] as retard}
            {@const p = borne((E.onde - retard) / 1.25)}
            {#if p > 0 && p < 1}
              <circle cx={o.c[0]} cy={o.c[1]} r={((7 + 30 * sortie(p)) * upp).toFixed(2)} class="onde" class:recul={!o.gain} opacity={(0.75 * (1 - p)).toFixed(3)} />
            {/if}
          {/each}
        {/each}
        {#if E.flA > 0.002}
          <g opacity={E.flA.toFixed(3)}>
            {#each AXES_SEM[E.k] as a (a.id)}<path d={fleche(a.S, a.C, a.F, E.fl, a.W)} class="fleche" fill="url(#g{a.id})" />{/each}
          </g>
        {/if}
      {/if}
      {#if E.bil > 0.002}
        {#each AXES_BILAN as a, i}<path d={fleche(a.S, a.C, a.F, E.bil, a.W)} class="fleche" fill="url(#gb{i})" />{/each}
      {/if}
    </svg>

    <!-- 3. étiquettes et encadrés : taille constante à l'écran -->
    <svg class="couche textes" viewBox={vbTxt} preserveAspectRatio="xMidYMid slice" aria-hidden="true">
      {#each PAYS_NOMS as e}
        {#if !e.large || !etroit}
          <text class="pays" x={(etroit ? e.xyE : e.xy)[0]} y={(etroit ? e.xyE : e.xy)[1]} font-size={(10.5 * upp).toFixed(3)} letter-spacing={(2.4 * upp).toFixed(3)} text-anchor="middle">{e.t.toUpperCase()}</text>
        {/if}
      {/each}
      {#each MERS as e}
        <text class="mer" font-size={(12.5 * upp).toFixed(3)} text-anchor="middle">
          {#each e.t as ligne, j}<tspan x={(etroit ? e.xyE : e.xy)[0]} y={(etroit ? e.xyE : e.xy)[1] + j * 15 * upp}>{ligne}</tspan>{/each}
        </text>
      {/each}

      <!-- Aden : distance à la position houthie la plus proche -->
      <g class="mesure">
        <line x1={PROCHE[0]} y1={PROCHE[1]} x2={ADEN[0]} y2={ADEN[1]} stroke-dasharray="{(3.5 * upp).toFixed(2)} {(3 * upp).toFixed(2)}" />
        <circle cx={PROCHE[0]} cy={PROCHE[1]} r={2.2 * upp} />
        <text font-size={(12 * upp).toFixed(3)} stroke-width={(3.2 * upp).toFixed(3)} text-anchor="middle"
              transform="translate({((PROCHE[0] + ADEN[0]) / 2).toFixed(2)} {((PROCHE[1] + ADEN[1]) / 2).toFixed(2)}) rotate({mesureAngle.toFixed(1)})" y={-5 * upp}>{ADEN_KM}&nbsp;km</text>
      </g>
      <g transform="translate({ADEN[0]} {ADEN[1]})">
        <circle r={7 * upp} class="aden-anneau" stroke-width={1.3 * upp} />
        <circle r={3 * upp} class="aden-point" />
        <text class="aden" font-size={(17 * upp).toFixed(3)} stroke-width={(3.6 * upp).toFixed(3)} x={11 * upp} y={5.5 * upp}>Aden</text>
      </g>

      {#each VILLES as e}
        <g transform="translate({e.xy[0].toFixed(2)} {e.xy[1].toFixed(2)})">
          {#if e.cap}<path d={etoile(5.2 * upp)} class="point" />{:else}<circle r={2.5 * upp} class="point" />{/if}
          <text class="ville" font-size={(13 * upp).toFixed(3)} stroke-width={(3.2 * upp).toFixed(3)}
                text-anchor={e.a === 'd' ? 'start' : e.a === 'g' ? 'end' : 'middle'}
                x={(e.a === 'd' ? 7 : e.a === 'g' ? -7 : 0) * upp} y={(e.a === 'h' ? -7.5 : 4.4) * upp}>{e.t}</text>
        </g>
      {/each}

      <!-- encadrés chiffrés -->
      {#if E.pos > 0.5}
        {@const o = borne((E.pos - 0.5) / 0.3)}
        <g opacity={o.toFixed(3)}>
          
          <polyline class="filet fond" points={ptsTaez} /><polyline class="filet" points={ptsTaez} /><circle class="bout" cx={NOTE_TAEZ.cible[0]} cy={NOTE_TAEZ.cible[1]} r={2.3 * upp} />
          <g use:mesure={{ cb: (b) => (bTaez = b), cle: upp + '' + etroit }}>
          <text class="note-titre" x={NOTE_TAEZ.xy[0]} y={NOTE_TAEZ.xy[1]} font-size={(14 * upp).toFixed(3)} stroke-width={(3.4 * upp).toFixed(3)}>Autour de Taëz</text>
          <text class="note-chiffre" x={NOTE_TAEZ.xy[0]} y={NOTE_TAEZ.xy[1] + 18 * upp} font-size={(15 * upp).toFixed(3)} stroke-width={(3.4 * upp).toFixed(3)}>+{nombre(gainSud)}&nbsp;km²</text>
          {#if !etroit}<text class="note-texte" x={NOTE_TAEZ.xy[0]} y={NOTE_TAEZ.xy[1] + 33 * upp} font-size={(12 * upp).toFixed(3)} stroke-width={(3.2 * upp).toFixed(3)}>gagnés par les Houthis</text>{/if}
          </g>
        </g>
        <g opacity={o.toFixed(3)}>
          
          <g opacity={E.pos >= 1.3 ? 1 : 0}><polyline class="filet fond" points={ptsNord} /><polyline class="filet" points={ptsNord} /><circle class="bout" cx={NOTE_NORD.cible[0]} cy={NOTE_NORD.cible[1]} r={2.3 * upp} /></g>
          <g use:mesure={{ cb: (b) => (bNord = b), cle: upp + '' + etroit }}>
          <text class="note-titre" text-anchor="end" x={NOTE_NORD.xy[0]} y={NOTE_NORD.xy[1]} font-size={(14 * upp).toFixed(3)} stroke-width={(3.4 * upp).toFixed(3)}>Marib et Al-Jawf</text>
          <text class="note-chiffre gris" text-anchor="end" x={NOTE_NORD.xy[0]} y={NOTE_NORD.xy[1] + 18 * upp} font-size={(15 * upp).toFixed(3)} stroke-width={(3.4 * upp).toFixed(3)}>−{nombre(perteNord)}&nbsp;km²</text>
          {#if !etroit}<text class="note-texte" text-anchor="end" x={NOTE_NORD.xy[0]} y={NOTE_NORD.xy[1] + 33 * upp} font-size={(12 * upp).toFixed(3)} stroke-width={(3.2 * upp).toFixed(3)}>perdus par les Houthis</text>{/if}
          </g>
        </g>
      {/if}
      {#if E.pos > 5.4}
        {@const o = borne((E.pos - 5.4) / 0.3)}
        <g opacity={o.toFixed(3)}>
          
          <polyline class="filet fond" points={ptsDispute} /><polyline class="filet" points={ptsDispute} /><circle class="bout" cx={NOTE_DISPUTE.cible[0]} cy={NOTE_DISPUTE.cible[1]} r={2.3 * upp} />
          <text class="note-titre" text-anchor="middle" x={NOTE_DISPUTE.coude[0]} y={NOTE_DISPUTE.coude[1]} font-size={(14 * upp).toFixed(3)} stroke-width={(3.4 * upp).toFixed(3)}>+1&nbsp;800&nbsp;km² disputés</text>
          <text class="note-texte" text-anchor="middle" x={NOTE_DISPUTE.coude[0]} y={NOTE_DISPUTE.coude[1] + 15 * upp} font-size={(12 * upp).toFixed(3)} stroke-width={(3.2 * upp).toFixed(3)}>entre le 8 et le 15 novembre</text>
        </g>
      {/if}
    </svg>

    <!-- globe de situation -->
<div class="globe" aria-hidden="true"><svg viewBox="-102 -102 204 204">
      <circle r="100" class="g-mer" />
      <path d={G.land} class="g-terre" />
      <path d={G.grille} class="g-grille" />
      <path d={G.cadre} class="g-cadre" />
    </svg></div>

    <!-- échelle -->
    <div class="echelle" aria-hidden="true"><span>100 km</span><i style="width:{(100 * KM / upp).toFixed(1)}px"></i></div>
    {/if}
  </div>

  <div class="frise" class:etroit>
    <div class="fil"><i style="width:{frise.toFixed(2)}%"></i><b style="left:{frise.toFixed(2)}%"></b></div>
    <ol>
      {#each COURTS as c, i}
        {@const montre = !etroit || i === jour || (i === 0 && jour >= 2) || (i === 6 && jour <= 4)}
        <li style="left:{(ECARTS[i] / 40) * 100}%" class:premier={i === 0} class:dernier={i === 6}>
          <button type="button" class:passe={E.pos >= i - 0.001} class:actif={jour === i} on:click={() => aller(i)}
                  aria-label="Afficher la situation au {JOURS[i]}" aria-current={jour === i ? 'true' : null}>
            <span class="grain"></span><span class="nom" class:cache={!montre}>{c}</span>
          </button>
        </li>
      {/each}
    </ol>
  </div>

  <p class="source">{SOURCE}</p>
</main>

<style>
  .bloc{max-width:1040px;margin:0 auto;padding:6px var(--marge) 10px;display:flex;flex-direction:column;gap:14px}
  .tete{display:flex;flex-direction:column;gap:6px}
  h1{font-family:var(--titre);font-weight:700;font-size:clamp(21px,3.3vw,28px);line-height:1.16;text-wrap:balance}
  .chapo{font-size:15px;line-height:1.4;color:var(--gris);max-width:70ch}

  .cle{list-style:none;display:flex;flex-wrap:wrap;gap:6px 18px;font-size:12.5px;line-height:1.3;color:#3b3b40}
  .cle li{display:flex;align-items:center;gap:6px;white-space:nowrap}
  .cle svg{flex:none;display:block}

  .repere{display:flex;align-items:flex-end;justify-content:space-between;gap:12px;margin-bottom:-4px;min-height:28px}
  .quand{display:flex;flex-wrap:wrap;align-items:baseline;gap:2px 14px}
  .jour{font-family:var(--titre);font-weight:700;font-size:22px;line-height:1.2}
  .net{font-size:14.5px;font-weight:600;color:var(--rouge);font-variant-numeric:tabular-nums}
  .net.moins{color:#4a4a4f}
  .rejouer{flex:none;display:inline-flex;align-items:center;gap:6px;min-height:32px;padding:0 2px;border:0;background:none;font:inherit;font-size:13px;
           color:var(--gris);cursor:pointer;-webkit-tap-highlight-color:transparent}
  .rejouer:hover{color:var(--encre)}
  .rejouer svg{display:block}

  /* carte : mer pâle, terres blanches, rivage estompé */
  .scene{position:relative;line-height:0;overflow:hidden;background:#e7f1f0}
  .voile{position:absolute;inset:0;pointer-events:none;box-shadow:inset 0 0 18px 10px #fff}
  .couche{position:absolute;inset:0;display:block;width:100%;height:100%}
  .rivage{fill:#b9d6d3}
  .terre{fill:#fff}
  .bati{fill:#e9e3dc}
  .route{fill:none;stroke:#ebe6e0;stroke-width:.8;vector-effect:non-scaling-stroke;stroke-linejoin:round}
  .frontiere-halo{fill:none;stroke:#8c8c90;stroke-opacity:.12;stroke-width:4;vector-effect:non-scaling-stroke;stroke-linejoin:round;stroke-linecap:round}
  .frontiere{fill:none;stroke:#7b7b80;stroke-width:.8;vector-effect:non-scaling-stroke;stroke-linejoin:round;stroke-linecap:round}

  .ctrl{fill:#dd203c;fill-opacity:.15}
  .halo{fill:none;stroke:#dd203c;vector-effect:non-scaling-stroke;stroke-linejoin:round}
  .halo.h3{stroke-width:9;stroke-opacity:.06}
  .halo.h2{stroke-width:5;stroke-opacity:.12}
  .halo.h1{stroke-width:1.2;stroke-opacity:.8}
  .gain{fill:#dd203c;fill-opacity:.66}
  .gain.vif{fill-opacity:.96}
  .dispute{fill:url(#h-dispute);fill-opacity:.6}
  .perdu{fill:url(#h-perdu);fill-opacity:.75;stroke:#4a4a4f;stroke-opacity:.5;stroke-width:.8;vector-effect:non-scaling-stroke}
  .perdu.vif{fill-opacity:.95;stroke-opacity:.95;stroke-width:1.2}
  .onde{fill:none;stroke:#dd203c;stroke-width:1.6;vector-effect:non-scaling-stroke}
  .onde.recul{stroke:#4a4a4f}
  .fleche{stroke:#fff;stroke-opacity:.92;stroke-width:1.1;vector-effect:non-scaling-stroke;paint-order:stroke;stroke-linejoin:round}

  .textes text{font-family:var(--texte);fill:var(--encre)}
  text.pays{font-weight:500;fill:#2a2a2d}
  text.mer{font-style:italic;fill:#86aeab}
  text.ville{font-weight:400;paint-order:stroke;stroke:#fff;stroke-opacity:.85;stroke-linejoin:round}
  .point{fill:#141414}
  .mesure line{stroke:#141414;stroke-width:1;vector-effect:non-scaling-stroke}
  .mesure circle{fill:#141414}
  .mesure text{font-weight:600;paint-order:stroke;stroke:#fff;stroke-opacity:.9;stroke-linejoin:round;font-variant-numeric:lining-nums}
  .aden-anneau{fill:#fff;fill-opacity:.7;stroke:#141414}
  .aden-point{fill:#141414}
  .textes text.aden{font-family:var(--titre);font-weight:700;paint-order:stroke;stroke:#fff;stroke-opacity:.9;stroke-linejoin:round}
  .filet{fill:none;stroke:#141414;stroke-width:.8;vector-effect:non-scaling-stroke;stroke-linejoin:round}
  .filet.fond{stroke:#fff;stroke-opacity:.85;stroke-width:3}
  .bout{fill:#141414;stroke:#fff;stroke-width:1.2;vector-effect:non-scaling-stroke}
  .textes text.note-titre{font-family:var(--titre);font-weight:700;paint-order:stroke;stroke:#fff;stroke-opacity:.9;stroke-linejoin:round}
  text.note-chiffre{font-weight:600;fill:var(--rouge);paint-order:stroke;stroke:#fff;stroke-opacity:.9;stroke-linejoin:round}
  text.note-chiffre.gris{fill:#4a4a4f}
  text.note-texte{font-weight:400;paint-order:stroke;stroke:#fff;stroke-opacity:.9;stroke-linejoin:round}

  .globe{position:absolute;top:12px;right:12px;width:96px;height:96px;border-radius:50%;background:#fff;box-shadow:0 1px 6px rgba(0,0,0,.22)}
  .globe svg{display:block;width:100%;height:100%}
  .g-mer{fill:#fff}
  .g-terre{fill:#d9d9d9}
  .g-grille{fill:none;stroke:#fff;stroke-width:1.1;stroke-opacity:.9}
  .g-cadre{fill:none;stroke:#dd203c;stroke-width:4.5;stroke-linejoin:miter}
  .echelle{position:absolute;left:12px;bottom:12px;display:flex;flex-direction:column;gap:3px;font-size:11.5px;line-height:1;color:#5a5a5e}
  .echelle i{display:block;height:1px;background:#5a5a5e}

  /* frise : un fil, des grains, un curseur qui glisse */
  .frise{position:relative;height:50px;margin:2px 7px 0}
  .fil{position:absolute;left:0;right:0;top:10px;height:1px;background:#cfcfcf}
  .fil i{position:absolute;left:0;top:-.5px;height:2px;background:var(--rouge);border-radius:1px}
  .fil b{position:absolute;top:.5px;width:13px;height:13px;margin:-6.5px 0 0 -6.5px;border-radius:50%;background:var(--rouge);box-shadow:0 0 0 5px rgba(221,32,60,.16)}
  .frise ol{list-style:none;position:absolute;left:0;right:0;top:0;height:100%}
  .frise li{position:absolute;top:0;transform:translateX(-50%)}
  .frise button{display:flex;flex-direction:column;align-items:center;gap:9px;padding:7px 6px 4px;min-height:46px;border:0;background:none;font:inherit;
                color:var(--gris);cursor:pointer;-webkit-tap-highlight-color:transparent}
  .grain{display:block;width:7px;height:7px;border-radius:50%;background:#fff;border:1.5px solid #b5b5b5}
  .frise button.passe .grain{background:var(--rouge);border-color:var(--rouge)}
  .nom{font-size:12.5px;line-height:1.2;white-space:nowrap}
  .nom.cache{visibility:hidden}
  .frise button:hover .nom{color:var(--encre)}
  .frise button.actif .nom{color:var(--encre);font-weight:600}
  .frise li.premier{transform:translateX(-10px)}
  .frise li.premier button{align-items:flex-start}
  .frise li.dernier{transform:translateX(calc(-100% + 10px))}
  .frise li.dernier button{align-items:flex-end}

  button:focus-visible{outline:2px solid #1f4aa8;outline-offset:3px}

  .source{font-size:12px;line-height:1.45;color:var(--gris);border-top:1px solid var(--filet);padding-top:10px}

  @media (max-width:600px){
    .bloc{gap:12px}
    .chapo{font-size:14px}
    .cle{gap:5px 14px;font-size:12px}
    .quand{flex-direction:column;gap:1px;min-height:45px}
    .jour{font-size:20px}
    .net{font-size:13.5px}
    .globe{width:78px;height:78px;top:10px;right:10px}
  }
</style>
