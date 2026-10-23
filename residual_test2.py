"""Prueba 3 bis: generador con regla de borde (EdgeGen) y base real-contra-real.
Referencias para puntuar la mitad de prueba de B:
  FullGen x1 y x20, EdgeGen x1 y x20 (réplicas con la forma de los bloques de prueba),
  texto REAL de la mitad de entrenamiento (≈ x1).
"""
from collections import Counter
from residual_test import shape, train, tokens, profile, recurrence
from fullgen import FullGen
from edgegen import EdgeGen
import random

P = dict(beta=0.8, rho=0.7, gamma=1.3, temp=0.75)


def ref_of(g, reps):
    c = Counter()
    for _ in range(reps):
        for b in g.like(shape):
            for l in b:
                c.update(l)
    return c


def report(name, ref, T):
    ue = [ref[w] == 0 for w, *_ in T]
    r, p = profile(T, ue)
    print(f'{name:38s} no explicadas {r:.3f}  pos', {k: v[0] for k, v in p['pos'].items()}, flush=True)
    return ue


if __name__ == '__main__':
    real = tokens(shape)
    refs = {}
    refs['texto real de entrenamiento (x1)'] = Counter(w for l in train for w in l)
    print('fichas entrenamiento', sum(refs['texto real de entrenamiento (x1)'].values()), 'prueba', len(real))
    gF, gE = FullGen(train, seed=0, **P), EdgeGen(train, seed=0, **P)
    refs['FullGen x1'] = ref_of(gF, 1)
    refs['EdgeGen x1'] = ref_of(gE, 1)
    refs['FullGen x20'] = ref_of(gF, 19) + refs['FullGen x1']
    refs['EdgeGen x20'] = ref_of(gE, 19) + refs['EdgeGen x1']
    print('--- texto REAL de prueba contra cada referencia')
    out = {k: report(k, v, real) for k, v in refs.items()}
    print('--- nulo: EdgeGen semilla 1 contra EdgeGen x20')
    Tn = tokens(EdgeGen(train, seed=1, **P).like(shape))
    uen = report('EdgeGen semilla 1', refs['EdgeGen x20'], Tn)
    print('--- nulo: texto real de entrenamiento troceado como prueba? (ver real x1 arriba)')
    rnd = random.Random(0)
    n = min(sum(uen), sum(out['EdgeGen x20']))
    print('recurrencia entre folios, n =', n)
    print('  REAL vs EdgeGen x20', recurrence(real, out['EdgeGen x20'], n, rnd))
    print('  REAL vs texto real ', recurrence(real, out['texto real de entrenamiento (x1)'], n, rnd))
    print('  NULO EdgeGen      ', recurrence(Tn, uen, n, rnd))
