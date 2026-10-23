"""Do word 'cores' carry sequential information?

Core = the gallows/bench/e material of a word, in order, with prefixes
(q, o, y, d, s, l, a ...) and suffixes (-dy, -y, -aiin, -ol, -ar ...) removed.
Operationally: keep only the glyph units ckh, cth, cph, cfh, ch, sh, k, t, p, f, e
in the order they appear. Words with no such material get core '-'.

Tests (same nulls as edge_tests): core_t vs core_t+1 (lag 1), lag 2, and the
last core of a line vs the first core of the next line.
Positive control: a cipher of Latin/Italian whose letter is encoded in the core
(edges random), analysed with the identical extraction.
"""
import random
import re
import sys
import warnings
from collections import Counter

warnings.filterwarnings('ignore')
sys.argv = ['x']
import edge_tests as E
from ciphers import letters_of, to_lines
from common import refs

UNIT = re.compile(r'ckh|cth|cph|cfh|ch|sh|k|t|p|f|e')


def core(w):
    u = UNIT.findall(w)
    return ''.join(u) if u else '-'


def to_cores(lines):
    return [[core(w) for w in l] for l in lines]


def mi_lag(lines, k):
    return E.mi([(l[i], l[i + k]) for l in lines for i in range(len(l) - k)])


def within(lines, k, reps=30):
    real = mi_lag(lines, k)
    null = [mi_lag([E.rnd.sample(l, len(l)) for l in lines], k) for _ in range(reps)]
    m = sum(null) / reps
    sd = (sum((x - m) ** 2 for x in null) / (reps - 1)) ** .5
    return real - m, sd


def across(blocks, reps=200):
    pairs, groups = [], []
    for b in blocks:
        ends = [l[-1] for l in b[:-1]]
        starts = [l[0] for l in b[1:]]
        pairs += list(zip(ends, starts))
        groups.append((ends, starts))
    real = E.mi(pairs)
    null = []
    for _ in range(reps):
        p = []
        for ends, starts in groups:
            s = starts[:]
            E.rnd.shuffle(s)
            p += list(zip(ends, s))
        null.append(E.mi(p))
    m = sum(null) / reps
    sd = (sum((x - m) ** 2 for x in null) / (reps - 1)) ** .5
    return real - m, sd


def report(name, lines, blocks):
    cl = to_cores(lines)
    cb = [to_cores(b) for b in blocks]
    l1, s1 = within(cl, 1)
    l2, s2 = within(cl, 2)
    ax, sx = across(cb)
    ntypes = len(set(c for l in cl for c in l))
    print(f'{name:36s} tipos de núcleo {ntypes:4d}  lag1 {l1:7.4f}±{s1:.4f}  lag2 {l2:7.4f}±{s2:.4f}  renglón {ax:7.4f}±{sx:.4f}')


def core_cipher(sents, seed=5, ntok=24000, p_bigram=0.0):
    """Each letter -> fixed core; prefix and suffix random (decoration)."""
    r = random.Random(seed)
    L = letters_of(sents)
    alpha = sorted(set(L))
    cores = sorted({''.join(x) for x in [('k', 'e'), ('t', 'e'), ('ch', 'e'), ('sh', 'e'), ('k', 'e', 'e'), ('t', 'e', 'e'),
                                          ('ch', 'e', 'e'), ('k',), ('t',), ('ch',), ('sh',), ('p',), ('f',), ('ckh',), ('cth',),
                                          ('e',), ('ee',), ('ch', 'k'), ('sh', 'k'), ('ch', 't'), ('p', 'ch'), ('f', 'ch'),
                                          ('k', 'ch'), ('t', 'ch'), ('e', 'k'), ('cth', 'e'), ('ckh', 'e'), ('sh', 'ee')]})
    cmap = {a: cores[i % len(cores)] for i, a in enumerate(alpha)}
    PRE = ['qo', 'o', 'y', 'd', 'l', 's', 'a', '']
    SUF = ['dy', 'y', 'aiin', 'ain', 'ol', 'ar', 'al', 'or', 'ey', 'am', 'eedy', 'ody']
    toks = [r.choice(PRE) + cmap[c] + r.choice(SUF) for c in L[:ntok]]
    return to_lines(toks, 9)


if __name__ == '__main__':
    for name, f in [('VOYNICH Currier B', lambda l: l['lang'] == 'B'), ('VOYNICH Currier A', lambda l: l['lang'] == 'A')]:
        blocks = E.voy_blocks(f)
        report(name, [l for b in blocks for l in b], blocks)
    tl = E.timm_lines()
    report('TIMM generador', tl, E.text_blocks(tl))
    for lang in ['latin_medieval', 'italian']:
        c = core_cipher(refs[lang])
        report(f'{lang}: mensaje en el núcleo', c, E.text_blocks(c))
