"""Prépare data.json pour la carte : contours ISW par date, gains/reculs, fond Natural Earth.
Unités carte : Mercator, 1° de longitude = K unités, origine (36°E, 21°N), y vers le bas."""
import sys, glob, os, json, math
import geopandas as gpd
from shapely.ops import unary_union, transform
from shapely import make_valid
from shapely.geometry import Point, box, Polygon, MultiPolygon, LineString, MultiLineString, GeometryCollection
from pyproj import Transformer
root, base, out = sys.argv[1], sys.argv[2], sys.argv[3]
DATES = ['20261006','20261011','20261018','20261026','20261101','20261108','20261115']
LAEA = '+proj=laea +lat_0=15 +lon_0=44.5 +datum=WGS84 +units=m'
to_ll = Transformer.from_crs(LAEA, 4326, always_xy=True).transform
to_la = Transformer.from_crs(4326, LAEA, always_xy=True).transform
LON0, LAT0 = 36.0, 21.0
K = 100*math.cos(math.radians(15))
merc = lambda lat: math.degrees(math.log(math.tan(math.pi/4+math.radians(lat)/2)))
def proj_ll(lon, lat): return ((lon-LON0)*K, (merc(LAT0)-merc(lat))*K)
def proj_m(x, y):
    lon, lat = to_ll(x, y); return proj_ll(lon, lat)
def polys(g):
    if g is None or g.is_empty: return []
    if isinstance(g, Polygon): return [g]
    if isinstance(g, (MultiPolygon, GeometryCollection)): return [p for q in g.geoms for p in polys(q)]
    return []
def lines(g):
    if g is None or g.is_empty: return []
    if isinstance(g, LineString): return [g]
    if isinstance(g, (MultiLineString, GeometryCollection)): return [p for q in g.geoms for p in lines(q)]
    return []
def ring(coords):
    pts = [proj_m(x, y) for x, y in coords]
    s = 'M' + 'L'.join(f'{x:.2f},{y:.2f}' for x, y in pts[:-1]) + 'Z'
    return s
def path(g, tol=60, minarea=0.05e6):
    g = g.simplify(tol, preserve_topology=True)
    return ''.join(ring(p.exterior.coords) + ''.join(ring(i.coords) for i in p.interiors if Polygon(i).area > minarea) for p in polys(g) if p.area > minarea)
def lpath(g, tol=60):
    out = []
    for l in lines(g.simplify(tol)):
        pts = [proj_m(x, y) for x, y in l.coords]
        out.append('M' + 'L'.join(f'{x:.2f},{y:.2f}' for x, y in pts))
    return ''.join(out)
def clean(g, w=90):  # retire les éclats plus fins que 2w mètres
    return make_valid(g.buffer(-w).buffer(w)) if not g.is_empty else g
def P(pt): x, y = proj_m(pt.x, pt.y); return [round(x, 2), round(y, 2)]

def load(prefix, d):
    shp = glob.glob(os.path.join(root, '*', f'{prefix}_{d}', '*.shp'))[0]
    g = gpd.read_file(shp); g = g[g.geometry.notna() & ~g.geometry.is_empty].to_crs(LAEA)
    return make_valid(unary_union([make_valid(x) for x in g.geometry]))
H = [load('Houthi_Controlled_Terrain', d) for d in DATES]
C = [load('Contested_Houthi_Yemeni_Government_Aligned_Forces_Terrain', d) for d in DATES]
G = [load('Yemeni_Government_Aligned_Forces', d) for d in DATES]
yemen = make_valid(unary_union([H[0], C[0], G[0]]).buffer(40).buffer(-40))

adm = gpd.read_file(os.path.join(base, 'yem_adm1.geojson')).to_crs(LAEA)
def gov(p):
    a = adm[adm.contains(p)]
    if not len(a): a = adm.iloc[[adm.distance(p).argmin()]]
    return a.shapeName.iloc[0].replace(' Governorate', '')

data = {'K': K, 'lon0': LON0, 'mercLat0': merc(LAT0), 'dates': DATES}
data['area'] = [round(h.area/1e6) for h in H]
data['H'] = [path(h) for h in H]
data['C'] = [path(c) for c in C]
data['gcum'] = [path(clean(h.difference(H[0]))) for h in H]
data['lcum'] = [path(clean(H[0].difference(h))) for h in H]
weeks = []
for k in range(len(DATES)-1):
    gain = clean(H[k+1].difference(H[k])); loss = clean(H[k].difference(H[k+1]))
    comps = []
    for p in sorted(polys(gain), key=lambda p: -p.area):
        if p.area < 4e6: continue
        rear = p.boundary.intersection(H[k].boundary.buffer(200))
        front = p.boundary.intersection(H[k+1].boundary.buffer(200))
        rc = rear.centroid if not rear.is_empty else p.centroid
        fc = front.centroid if not front.is_empty else p.centroid
        far = max(Point(c).distance(rc) for c in p.exterior.coords)
        src = 'contested' if p.intersection(C[k]).area > 0.5*p.area else 'gov'
        rp = p.representative_point()
        comps.append({'d': path(p), 'km2': round(p.area/1e6), 'from': src, 'gov': gov(rp), 'o': P(rc), 'f': P(fc), 'c': P(p.centroid),
                      'r': round(far/1000/111.32*100*1.02, 1), 'll': [round(v, 3) for v in to_ll(rp.x, rp.y)]})
    lcomps = []
    for p in sorted(polys(loss), key=lambda p: -p.area):
        if p.area < 4e6: continue
        rp = p.representative_point()
        dst = 'contested' if p.intersection(C[k+1]).area > 0.5*p.area else 'gov'
        lcomps.append({'d': path(p), 'km2': round(p.area/1e6), 'to': dst, 'gov': gov(rp), 'c': P(p.centroid), 'll': [round(v, 3) for v in to_ll(rp.x, rp.y)]})
    weeks.append({'gain': comps, 'loss': lcomps, 'gainAll': path(gain), 'lossAll': path(loss),
                  'gain_km2': round(H[k+1].difference(H[k]).area/1e6), 'loss_km2': round(H[k].difference(H[k+1]).area/1e6)})
data['weeks'] = weeks

# Fond : Natural Earth 10m, découpé ; le Yémen vient des contours ISW
ne = gpd.read_file(os.path.join(base, 'ne_10m_admin_0_countries.geojson'))
bb = box(33.5, 7.5, 56.5, 23.5)
ne = ne[ne.intersects(bb)].copy(); ne['geometry'] = ne.geometry.intersection(bb); ne = ne.to_crs(LAEA)
ybuf = yemen.buffer(1); countries = {}
for _, r in ne.iterrows():
    if r.ADM0_A3 == 'YEM': ne_yem = r.geometry; continue
    g = make_valid(r.geometry.difference(ybuf))
    countries[r.ADM0_A3] = g
    print('pays', r.ADM0_A3, r.NAME_FR if 'NAME_FR' in r else r.NAME, round(g.area/1e6))
print('NE Yémen vs ISW : NE seul', round(ne_yem.difference(yemen).area/1e6), 'km2 ; ISW seul', round(yemen.difference(ne_yem).area/1e6), 'km2')
data['land'] = {k: path(g, tol=250, minarea=1e6) for k, g in countries.items()}
data['yemen'] = path(yemen, tol=80, minarea=0.2e6)
# frontières terrestres
allb = []
keys = list(countries)
for i, a in enumerate(keys):
    for b in keys[i+1:]:
        s = countries[a].boundary.intersection(countries[b].buffer(300))
        if not s.is_empty and s.length > 5000: allb.append(s)
ybord = []
for a in ('SAU', 'OMN'):
    s = yemen.boundary.intersection(make_valid(ne[ne.ADM0_A3 == a].geometry.iloc[0]).buffer(12000))
    # ne garder que la partie loin de la mer : retire ce qui longe la côte
    ybord.append(s)
sea = box(*[v for v in (-3e6, -3e6, 3e6, 3e6)]).difference(unary_union([make_valid(g) for g in ne.geometry]).buffer(4000)).difference(yemen.buffer(-4000) if False else Polygon())
data['borders'] = lpath(unary_union(allb), tol=250)
yb = unary_union(ybord)
# exclure les tronçons côtiers : garder ce qui est à plus de 6 km de la mer ouverte
landmass = unary_union([make_valid(g) for g in ne.geometry] + [yemen]).buffer(500)
open_sea = box(-3e6, -3e6, 3e6, 3e6).difference(landmass)
yb = yb.difference(open_sea.buffer(9000))
data['yborder'] = lpath(yb, tol=80)
data['land']['YEMGAP'] = path(make_valid(ne_yem.difference(yemen).difference(open_sea.buffer(15000))), tol=150, minarea=0.5e6)
data['sauBorder'] = lpath(yemen.boundary.intersection(make_valid(ne[ne.ADM0_A3 == 'SAU'].geometry.iloc[0]).buffer(12000)).difference(open_sea.buffer(9000)), tol=80)

# --- compléments v2 : routes, zones urbaines, surfaces par secteur, distance à Aden ---
from shapely.ops import nearest_points
from pyproj import Geod
geod = Geod(ellps='WGS84')
fr = box(39.0, 10.0, 50.5, 20.0)
roads = gpd.read_file(os.path.join(base, 'ne_10m_roads.geojson'), bbox=(39.0, 10.0, 50.5, 20.0))
roads = roads[roads.geometry.notna()].copy(); roads['geometry'] = roads.geometry.intersection(fr); roads = roads[~roads.geometry.is_empty].to_crs(LAEA)
print('routes', len(roads), roads['type'].value_counts().to_dict() if 'type' in roads else '')
data['roads'] = lpath(unary_union(list(roads.geometry)), tol=200)
urb = gpd.read_file(os.path.join(base, 'ne_10m_urban_areas.geojson'), bbox=(39.0, 10.0, 50.5, 20.0))
urb = urb[urb.geometry.notna()].to_crs(LAEA)
data['urban'] = path(unary_union([make_valid(g) for g in urb.geometry]), tol=150, minarea=0.3e6)
ysplit = to_la(44.0, 14.3)[1]
south = box(-3e6, -3e6, 3e6, ysplit); north = box(-3e6, ysplit, 3e6, 3e6)
data['gainSud'] = [round(h.difference(H[0]).intersection(south).area/1e6) for h in H]
data['perteNord'] = [round(H[0].difference(h).intersection(north).area/1e6) for h in H]
data['disputeSud'] = [round(c.intersection(south).area/1e6) for c in C]
aden_ll = (45.03, 12.79); aden = Point(*to_la(*aden_ll))
def near(geom):
    a, b = nearest_points(geom, aden); lon, lat = to_ll(a.x, a.y)
    return {'km': round(geod.inv(lon, lat, *aden_ll)[2]/1000, 1), 'p': [round(v, 2) for v in proj_ll(lon, lat)], 'll': [round(lon, 3), round(lat, 3)]}
data['aden'] = {'p': [round(v, 2) for v in proj_ll(*aden_ll)], 'H': [near(h) for h in H], 'C': [near(c) for c in C]}
for k, w in enumerate(weeks):
    for c, poly in zip(w['gain'], [p for p in sorted(polys(clean(H[k+1].difference(H[k]))), key=lambda p: -p.area) if p.area >= 4e6]):
        c['adenKm'] = round(poly.distance(aden)/1000)
    print(DATES[k+1], [(c['km2'], c['gov'], 'à', c.get('adenKm'), 'km d’Aden') for c in w['gain'] if c['km2'] >= 35])
print('gainSud', data['gainSud'], 'perteNord', data['perteNord'], 'disputeSud', data['disputeSud'])
print('aden H', [(n['km'], n['ll']) for n in data['aden']['H']][::6], 'C', [(n['km']) for n in data['aden']['C']])
# la route Taëz–Aden traverse-t-elle le gain du 15 novembre ?
g6 = clean(H[6].difference(H[5]))
inter = roads[roads.intersects(g6)]
print('routes NE traversant le gain du 15 nov. :', len(inter), [round(x/1000) for x in inter.geometry.intersection(g6).length])
c6 = C[6].difference(C[5])
print('routes NE traversant la nouvelle zone disputée du 15 nov. :', len(roads[roads.intersects(c6)]))

json.dump(data, open(out, 'w'), ensure_ascii=False, separators=(',', ':'))
print('data.json', os.path.getsize(out), 'octets')
for k in ('H', 'C', 'gcum', 'lcum'): print(k, [len(s) for s in data[k]])
print('yemen', len(data['yemen']), 'land', {k: len(v) for k, v in data['land'].items()}, 'borders', len(data['borders']), len(data['yborder']))
for k, w in enumerate(weeks):
    print(DATES[k], '->', DATES[k+1], 'gain', w['gain_km2'], 'loss', w['loss_km2'])
    for c in w['gain']: print('   +', c['km2'], c['from'], c['gov'], c['ll'], 'o', c['o'], 'f', c['f'], 'r', c['r'])
    for c in w['loss']: print('   -', c['km2'], c['to'], c['gov'], c['ll'])
