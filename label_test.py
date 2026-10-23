"""Prueba 1: ¿aparecen las etiquetas farmacéuticas en el texto de su página de hierbas emparejada?
Control: la misma etiqueta contra todas las demás páginas de hierbas (rango), y permutación de parejas.
"""
import re, random, math
from collections import Counter, defaultdict

PAIRS = [  # (folio hierbas, etiqueta, fuente)
    ('f19r', 'opchdard', 'Stolfi'), ('f18v', 'koldarod', 'Stolfi'), ('f23r', 'odalydary', 'Stolfi'),
    ('f48v', 'chokam', 'Stolfi?'), ('f48r', 'daseky', 'Stolfi?'), ('f53r', 'okeor', 'Petersen'),
    ('f55r', 'doldam', 'Petersen'), ('f90v1', 'otal', 'Petersen+Stolfi'),
]

meta, pages, cur = {}, defaultdict(list), None
for raw in open('ZL3b-n.txt', encoding='utf-8', errors='replace'):
    m = re.match(r'^<(f\w+)>\s+<!(.*)>', raw)
    if m:
        cur = m.group(1); meta[cur] = dict(re.findall(r'\$(\w)=(\w+)', m.group(2))); continue
    m = re.match(r'^<(f\w+)\.\d+,(.)(\w)(\w)>\s+(.*)', raw)
    if not m or m.group(3) != 'P':
        continue
    t = re.sub(r'<[^>]*>', '', m.group(5))
    t = re.sub(r'\[([^:\]]*):[^\]]*\]', r'\1', t)
    t = re.sub(r'\{[^}]*\}', '', t)
    pages[m.group(1)] += [w for w in re.split(r'[.,\s]+', t) if w and '?' not in w and re.fullmatch(r'[a-z]+', w)]

herbal = [f for f in pages if meta.get(f, {}).get('I') == 'H' and len(pages[f]) >= 30]
allw = Counter(w for f in herbal for w in pages[f])
N = sum(allw.values())


def lev(a, b):
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        p, d[0] = d[0], i
        for j, cb in enumerate(b, 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (ca != cb))
    return d[-1]


def grams(w, n=3):
    w = f'^{w}$'
    return {w[i:i + n] for i in range(len(w) - n + 1)}


gdf = Counter(g for f in herbal for g in {g for w in set(pages[f]) for g in grams(w)})


def scores(label, f):
    ws = pages[f]; n = len(ws)
    exact = ws.count(label) / n * 1000  # por mil palabras
    near = sum(1 for w in set(ws) if lev(label, w) <= 1)  # tipos a distancia <=1
    near = near / math.sqrt(len(set(ws)))
    pg = {g for w in set(ws) for g in grams(w)}
    tri = sum(math.log(len(herbal) / gdf[g]) for g in grams(label) if g in pg and gdf[g])
    return exact, near, tri


def rank(label, f, k):
    mine = scores(label, f)[k]
    others = [scores(label, g)[k] for g in herbal if g != f]
    # rango percentil: fracción de otras páginas con puntuación >= la propia (p empírico)
    return (1 + sum(o >= mine for o in others)) / (1 + len(others)), mine


if __name__ == '__main__':
    print('páginas de hierbas', len(herbal))
    names = ['exacta(‰)', 'casi(≤1)', 'trigramas']
    tot = [[], [], []]
    for f, lab, src in PAIRS:
        assert f in herbal, f
        row = []
        for k in range(3):
            p, v = rank(lab, f, k); tot[k].append(p); row.append(f'{v:6.2f} p={p:.2f}')
        print(f'{f:6} {lab:10} frec.global={allw[lab]:3}  ' + ' | '.join(row), f'  L={meta[f].get("L")}')
    # combinación de Fisher de los p empíricos
    for k in range(3):
        chi = -2 * sum(math.log(p) for p in tot[k])
        # p de chi2 con 2n gl (serie exacta para gl par)
        n = len(tot[k]); x = chi / 2
        pf = math.exp(-x) * sum(x ** i / math.factorial(i) for i in range(n))
        print(f'{names[k]:10} media p={sum(tot[k])/n:.2f}  Fisher p={pf:.3f}')
    # permutación: asignar las 8 etiquetas a 8 páginas al azar entre las de hierbas
    rnd = random.Random(0)
    obs = [sum(scores(l, f)[k] for f, l, _ in PAIRS) for k in range(3)]
    cnt = [0, 0, 0]; R = 2000
    for _ in range(R):
        fs = rnd.sample(herbal, len(PAIRS))
        for k in range(3):
            if sum(scores(l, g)[k] for g, (_, l, _) in zip(fs, PAIRS)) >= obs[k]:
                cnt[k] += 1
    for k in range(3):
        print(f'permutación {names[k]}: suma obs={obs[k]:.2f}  p={(cnt[k]+1)/(R+1):.3f}')
