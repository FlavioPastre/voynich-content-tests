"""Clean dependency tests with a position-preserving cross-line null.

Lag k within line: real pairs (l[i], l[i+k]). Null: (l[i], m[i+k]) where m is a
random OTHER line of the same block that is long enough. Keeps position-
specific marginals, has no true dependence.

Across line break: real pairs (end of line j, start of line j+1). Null: end of
line j with start of a random line j' of the same block, j' not in {j, j+1}.
Adjacent-line similarity control: start(j)->start(j+1) vs start(j)->start(j'),
same exclusion, no self pairs possible.
"""
import math
import random
import sys
import warnings
from collections import Counter

warnings.filterwarnings('ignore')
sys.argv = ['x']
import edge_tests as E
from core_tests import core, core_cipher
from projection_tests import PROJ
from edge_sim2 import strong
from common import refs, chunk, cut

rnd = random.Random(11)
REPS = 40


def mi(pairs):
    return E.mi(pairs)


def stat(real, nulls):
    m = sum(nulls) / len(nulls)
    sd = (sum((x - m) ** 2 for x in nulls) / (len(nulls) - 1)) ** .5
    return real - m, sd


def lag_test(blocks, g, k):
    real = [(g(l[i]), g(l[i + k])) for b in blocks for l in b for i in range(len(l) - k)]
    nulls = []
    for _ in range(REPS):
        p = []
        for b in blocks:
            for li, l in enumerate(b):
                for i in range(len(l) - k):
                    cands = [m for mj, m in enumerate(b) if mj != li and len(m) > i + k]
                    if cands:
                        p.append((g(l[i]), g(rnd.choice(cands)[i + k])))
        nulls.append(mi(p))
    return stat(mi(real), nulls)


def line_test(blocks, g, a, b):
    pick = {'fin': lambda l: l[-1], 'inicio': lambda l: l[0]}
    real, idx = [], []
    for bl in blocks:
        for j in range(len(bl) - 1):
            real.append((g(pick[a](bl[j])), g(pick[b](bl[j + 1]))))
    nulls = []
    for _ in range(REPS):
        p = []
        for bl in blocks:
            if len(bl) < 3:
                continue
            for j in range(len(bl) - 1):
                c = [x for x in range(len(bl)) if x not in (j, j + 1)]
                p.append((g(pick[a](bl[j])), g(pick[b](bl[rnd.choice(c)]))))
        nulls.append(mi(p))
    return stat(mi(real), nulls)


texts = {}
for name, f in [('VOYNICH B', lambda l: l['lang'] == 'B'), ('VOYNICH A', lambda l: l['lang'] == 'A')]:
    texts[name] = E.voy_blocks(f)
texts['TIMM (sin mensaje)'] = E.text_blocks(E.timm_lines())
texts['latín: palabras reales'] = E.text_blocks(cut(chunk(refs['latin_medieval'], 9), 20000))
texts['control: latín en el núcleo'] = E.text_blocks(core_cipher(refs['latin_medieval'], ntok=20000))
texts['control: latín en los bordes'] = E.text_blocks(strong(refs['latin_medieval'], ntok=20000))

gs = {'bordes (último→primero)': None, 'primer+último glifo': PROJ['primer+último glifo'],
      'núcleo': core, 'prefijo+sufijo': PROJ['prefijo+sufijo']}

print(f"{'texto':30s}{'rasgo':26s}{'dist. 1':>16s}{'dist. 2':>16s}{'fin→inicio renglón':>22s}{'inicio→inicio':>18s}")
for name, blocks in texts.items():
    for gn, g in gs.items():
        if g is None:
            # edge pair: last glyph of w_t vs first glyph of w_t+k
            last = lambda w: w[-1]
            first = lambda w: w[0]
            def lt(k):
                real = [(l[i][-1], l[i + k][0]) for b in blocks for l in b for i in range(len(l) - k)]
                nulls = []
                for _ in range(REPS):
                    p = []
                    for b in blocks:
                        for li, l in enumerate(b):
                            for i in range(len(l) - k):
                                c = [m for mj, m in enumerate(b) if mj != li and len(m) > i + k]
                                if c:
                                    p.append((l[i][-1], rnd.choice(c)[i + k][0]))
                    nulls.append(mi(p))
                return stat(mi(real), nulls)
            r1, r2 = lt(1), lt(2)
            rx = line_test(blocks, lambda w: w, 'fin', 'inicio')  # placeholder replaced below
            # proper edge across: last glyph of line end vs first glyph of next start
            real = [(bl[j][-1][-1], bl[j + 1][0][0]) for bl in blocks for j in range(len(bl) - 1)]
            nulls = []
            for _ in range(REPS):
                p = []
                for bl in blocks:
                    if len(bl) < 3:
                        continue
                    for j in range(len(bl) - 1):
                        c = [x for x in range(len(bl)) if x not in (j, j + 1)]
                        p.append((bl[j][-1][-1], bl[rnd.choice(c)][0][0]))
                nulls.append(mi(p))
            rx = stat(mi(real), nulls)
            rs = (float('nan'), float('nan'))
        else:
            r1, r2 = lag_test(blocks, g, 1), lag_test(blocks, g, 2)
            rx = line_test(blocks, g, 'fin', 'inicio')
            rs = line_test(blocks, g, 'inicio', 'inicio')
        f = lambda r: f'{r[0]:7.3f}±{r[1]:.3f}'
        print(f'{name:30s}{gn:26s}{f(r1):>16s}{f(r2):>16s}{f(rx):>22s}{f(rs):>18s}', flush=True)
