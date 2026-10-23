"""Prueba 3: ¿dónde caen las palabras reales que el generador sin mensaje no produce?
Currier B, mismos bloques (párrafos) y mismos parámetros que run_fullgen2 (temp .75, beta .8, gamma 1.3, rho .7).
'No explicada' = palabra que no aparece en un corpus de referencia de 20 réplicas generadas para los bloques de prueba.
Nulo: texto generado con otra semilla, con las mismas formas de bloque, puntuado contra la misma referencia.
"""
import json, random, math
from collections import Counter, defaultdict
import numpy as np
from fullgen import FullGen

zl = json.load(open('zl.json'))
pages = defaultdict(list)
for l in zl:
    if not l['type'].startswith('P') or l['lang'] != 'B':
        continue
    ws = [w['w'] for w in l['words'] if not w['unc']]
    if not ws:
        continue
    if l['sep'] in '@*' or not pages[l['folio']]:
        pages[l['folio']].append([])
    pages[l['folio']][-1].append(dict(ws=ws, folio=l['folio'], illus=l['illus'], hand=l['hand']))
blocks = [b for p in pages.values() for b in p if len(b) >= 2]
train_b, test_b = blocks[0::2], blocks[1::2]
train = [l['ws'] for b in train_b for l in b]
shape = [[l['ws'] for l in b] for b in test_b]


def tokens(gen_blocks):
    """lista de (palabra, categoría de posición, folio, sección)"""
    out, seen = [], set()
    for b, gb in zip(test_b, gen_blocks):
        for li, (l, gl) in enumerate(zip(b, gb)):
            for wi, w in enumerate(gl):
                f = l['folio']
                if wi == 0 and li == 0:
                    pos = 'inicio de página' if f not in seen else 'inicio de párrafo'
                elif wi == 0:
                    pos = 'inicio de renglón'
                elif wi == len(gl) - 1:
                    pos = 'fin de renglón'
                else:
                    pos = 'interior'
                seen.add(f)
                out.append((w, pos, f, l['illus']))
    return out


def profile(T, unexpl):
    rate = sum(unexpl) / len(T)
    res = {}
    for key in ('pos', 'sec'):
        idx = 1 if key == 'pos' else 3
        c, u = Counter(), Counter()
        for t, x in zip(T, unexpl):
            c[t[idx]] += 1; u[t[idx]] += x
        res[key] = {k: (round(u[k] / c[k] / rate, 2), c[k]) for k in c}
    return rate, res


def recurrence(T, unexpl, n, rnd, R=200):
    """de n fichas no explicadas tomadas al azar: fracción cuyo tipo aparece (no explicado) en otro folio,
    y dispersión entre folios (varianza/media de conteos por folio)."""
    idx = [i for i, x in enumerate(unexpl) if x]
    fr, disp = [], []
    for _ in range(R):
        s = rnd.sample(idx, n)
        folios = defaultdict(set)
        for i in s:
            folios[T[i][0]].add(T[i][2])
        fr.append(sum(1 for i in s if len(folios[T[i][0]]) >= 2) / n)
    return float(np.mean(fr)), float(np.percentile(fr, 2.5)), float(np.percentile(fr, 97.5))


if __name__ == '__main__':
    g = FullGen(train, beta=0.8, rho=0.7, gamma=1.3, temp=0.75, seed=0)
    ref = Counter()
    for _ in range(20):
        for b in g.like(shape):
            for l in b:
                ref.update(l)
    real = tokens(shape)
    ue_real = [ref[w] == 0 for w, *_ in real]
    nulls = []
    for seed in (1, 2, 3):
        gn = FullGen(train, beta=0.8, rho=0.7, gamma=1.3, temp=0.75, seed=seed)
        T = tokens(gn.like(shape))
        nulls.append((T, [ref[w] == 0 for w, *_ in T]))
    print('fichas de prueba', len(real), ' referencia: tipos', len(ref))
    r, p = profile(real, ue_real)
    print(f'REAL: no explicadas {r:.3f}')
    for k in ('pos', 'sec'):
        print('  ', k, p[k])
    for j, (T, ue) in enumerate(nulls):
        r2, p2 = profile(T, ue)
        print(f'NULO {j+1}: no explicadas {r2:.3f}')
        for k in ('pos', 'sec'):
            print('  ', k, p2[k])
    n = min(sum(ue) for _, ue in nulls + [(real, ue_real)])
    rnd = random.Random(0)
    print('recurrencia entre folios con n =', n)
    print('  REAL', recurrence(real, ue_real, n, rnd))
    for j, (T, ue) in enumerate(nulls):
        print(f'  NULO {j+1}', recurrence(T, ue, n, rnd))
    # tipos no explicados más repetidos en el texto real
    c = Counter(w for (w, *_), x in zip(real, ue_real) if x)
    fol = defaultdict(set)
    for (w, _, f, _), x in zip(real, ue_real):
        if x: fol[w].add(f)
    print('no explicadas más frecuentes (real):', [(w, k, len(fol[w])) for w, k in c.most_common(25)])
    json.dump(dict(real=[list(t) + [x] for t, x in zip(real, ue_real)]), open('residual_real.json', 'w'))
