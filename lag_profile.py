"""Dependency vs distance (lags 1-5) with a position-preserving cross-line null.

Sequence (message letters in order) -> fast decay with lag.
Line-level homogeneity (same 'mode' for a whole line) -> flat plateau.
"""
import random
import sys
import warnings

warnings.filterwarnings('ignore')
import edge_tests as E
from core_tests import core, core_cipher
from projection_tests import PROJ
from common import refs, chunk, cut

rnd = random.Random(5)
REPS = 30


def lag_test(blocks, g, k):
    real = [(g(l[i]), g(l[i + k])) for b in blocks for l in b for i in range(len(l) - k)]
    nulls = []
    for _ in range(REPS):
        p = []
        for b in blocks:
            for li, l in enumerate(b):
                for i in range(len(l) - k):
                    c = [m for mj, m in enumerate(b) if mj != li and len(m) > i + k]
                    if c:
                        p.append((g(l[i]), g(rnd.choice(c)[i + k])))
        nulls.append(E.mi(p))
    m = sum(nulls) / REPS
    sd = (sum((x - m) ** 2 for x in nulls) / (REPS - 1)) ** .5
    return E.mi(real) - m, sd, len(real)


if __name__ == "__main__":
    texts = {
        'VOYNICH B': E.voy_blocks(lambda l: l['lang'] == 'B'),
        'VOYNICH A': E.voy_blocks(lambda l: l['lang'] == 'A'),
        'TIMM (sin mensaje)': E.text_blocks(E.timm_lines()),
        'control: latín en el núcleo': E.text_blocks(core_cipher(refs['latin_medieval'], ntok=20000)),
        'latín: palabras reales': E.text_blocks(cut(chunk(refs['latin_medieval'], 9), 20000)),
    }
    gs = {'núcleo': core, 'primer+último glifo': PROJ['primer+último glifo'], 'prefijo+sufijo': PROJ['prefijo+sufijo']}
    for name, blocks in texts.items():
        for gn, g in gs.items():
            out = []
            for k in range(1, 6):
                v, sd, n = lag_test(blocks, g, k)
                out.append(f'{v:6.3f}±{sd:.3f}')
            print(f'{name:28s} {gn:20s} ' + '  '.join(f'd{k+1}: {o}' for k, o in enumerate(out)), flush=True)
