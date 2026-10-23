import json
import math
import random
import warnings
from collections import Counter

warnings.filterwarnings('ignore')
import edge_tests as E
from core_tests import core
from projection_tests import PROJ
from lag_profile import lag_test
from metrics import edit1, cond_entropy
from generator import Generator

blocks = E.voy_blocks(lambda l: l['lang'] == 'B')
# split pages alternately (blocks keep page order from voy_blocks)
train_b = blocks[0::2]
test_b = blocks[1::2]
train = [l for b in train_b for l in b]
print('train lines', len(train), 'test lines', sum(len(b) for b in test_b))


def across_edge(bl, reps=40):
    rnd = random.Random(3)
    real = [(b[j][-1][-1], b[j + 1][0][0]) for b in bl for j in range(len(b) - 1)]
    nulls = []
    for _ in range(reps):
        p = []
        for b in bl:
            if len(b) < 3:
                continue
            for j in range(len(b) - 1):
                c = [x for x in range(len(b)) if x not in (j, j + 1)]
                p.append((b[j][-1][-1], b[rnd.choice(c)][0][0]))
        nulls.append(E.mi(p))
    m = sum(nulls) / reps
    return E.mi(real) - m


def summary(name, bl):
    lines = [l for b in bl for l in b]
    words = [w for l in lines for w in l]
    adj = [(a, b) for l in lines for a, b in zip(l, l[1:])]
    seq = [[c for w in l for c in list(w) + [' ']] for l in lines]
    edge = lambda w: w  # placeholder
    r = {}
    r['h2'] = cond_entropy(seq, 1)
    r['TTR'] = len(set(words)) / len(words)
    r['repetición'] = sum(a == b for a, b in adj) / len(adj)
    r['vecina a 1 letra'] = sum(edit1(a, b) for a, b in adj) / len(adj)
    # edge last->first at d1, d2 with cross-line null
    g_last_first = None
    for k in (1, 2):
        real = [(l[i][-1], l[i + k][0]) for l in lines for i in range(len(l) - k)]
        rnd = random.Random(k)
        nulls = []
        for _ in range(30):
            p = []
            for b in bl:
                for li, l in enumerate(b):
                    for i in range(len(l) - k):
                        c = [m for mj, m in enumerate(b) if mj != li and len(m) > i + k]
                        if c:
                            p.append((l[i][-1], rnd.choice(c)[i + k][0]))
            nulls.append(E.mi(p))
        r[f'borde d{k}'] = E.mi(real) - sum(nulls) / len(nulls)
    r['borde renglón'] = across_edge(bl)
    for k in (1, 2, 4):
        r[f'núcleo d{k}'] = lag_test(bl, core, k)[0]
    return name, r


if __name__ == '__main__':
    rows = [summary('VOYNICH B (mitad de prueba)', test_b)]
    variants = [('Generador: modo + borde', dict()),
                ('Solo borde (sin modo)', dict(use_modes=False)),
                ('Solo modo (sin borde)', dict(use_edges=False)),
                ('Ninguna regla', dict(use_modes=False, use_edges=False))]
    for name, kw in variants:
        g = Generator(train, K=10, **kw)
        rows.append(summary(name, g.like(test_b)))
    rows.append(summary('TIMM (sin mensaje)', E.text_blocks(E.timm_lines())))

    keys = list(rows[0][1].keys())
    print(f"{'':30s}" + ''.join(f'{k[:13]:>14s}' for k in keys))
    for name, r in rows:
        print(f'{name:30s}' + ''.join(f'{r[k]:14.4f}' for k in keys))
    json.dump(rows, open('generator_results.json', 'w'), indent=1, ensure_ascii=False)
