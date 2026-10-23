"""Is the adjacent-word dependency explained by boundary glyphs?

1. boundary MI: I(last glyph of w_t ; first glyph of w_t+1), excess over
   within-line shuffle.
2. class MI beyond boundary: real class-MI minus a null where every word
   in held-out half B is replaced by a random word from B with the same
   (first glyph, last glyph, length bucket) signature at the same slot.
   The null keeps the boundary pattern and word-length profile; any
   remaining excess comes from word identity beyond its edges.
"""
import math
import random
import sys
import warnings
from collections import Counter, defaultdict

warnings.filterwarnings('ignore')
from common import chunk, refs, timm_lines, voy_lines
from common import cut
from seqdep import learn_classes, mi_pairs

NTOK = int(sys.argv[1])


def boundary_mi(lines, rnd, shuffles=20):
    def mi(ls):
        pair = Counter((a[-1], b[0]) for l in ls for a, b in zip(l, l[1:]))
        n = sum(pair.values())
        L, R = Counter(), Counter()
        for (a, b), v in pair.items():
            L[a] += v
            R[b] += v
        return sum(v / n * math.log2(v * n / (L[a] * R[b])) for (a, b), v in pair.items())
    real = mi(lines)
    sh = []
    for _ in range(shuffles):
        sh.append(mi([rnd.sample(l, len(l)) for l in lines]))
    return real - sum(sh) / len(sh)


def sig(w):
    return (w[0], w[-1], min(len(w), 7))


def beyond_boundary(lines, K=16, reps=20, seed=0):
    rnd = random.Random(seed)
    A, B = lines[0::2], lines[1::2]
    cls = learn_classes(A, K, seed=seed)
    real = mi_pairs(B, cls, K)
    pool = defaultdict(list)
    for l in B:
        for w in l:
            pool[sig(w)].append(w)
    nulls = []
    for _ in range(reps):
        Bn = [[rnd.choice(pool[sig(w)]) for w in l] for l in B]
        nulls.append(mi_pairs(Bn, cls, K))
    return real - sum(nulls) / len(nulls)


texts = {
    'VOYNICH all': voy_lines(lambda l: True),
    'VOYNICH Currier A': voy_lines(lambda l: l['lang'] == 'A'),
    'VOYNICH Currier B': voy_lines(lambda l: l['lang'] == 'B'),
    'TIMM generator': timm_lines(),
}
for lang in ['latin_medieval', 'italian', 'german', 'czech', 'hebrew', 'turkish', 'vietnamese']:
    texts[f'{lang}: words'] = chunk(refs[lang], 9)

print(f'NTOK={NTOK}')
print(f"{'text':28s}{'boundaryMI':>12s}{'classMI beyond boundary':>26s}")
rnd = random.Random(1)
for k, v in texts.items():
    L = cut(v, NTOK)
    print(f'{k:28s}{boundary_mi(L, rnd):12.4f}{beyond_boundary(L):26.4f}')
