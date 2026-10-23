"""Edge-dependency tests: lag 1 vs lag 2, and across line breaks.

Feature pair: last glyph of word t -> first glyph of word t+k.
Excess MI = plug-in MI minus mean MI under a null that keeps the marginal
distributions and positions but breaks the pairing:
  - within line (lag k): shuffle words inside each line;
  - across line break: pair the end of each line with the start of a
    random other line of the same page / text block.
"""
import json
import math
import random
import sys
from collections import Counter, defaultdict

from ciphers import letters_of, to_lines
from common import chunk, refs, timm_lines, cut

rnd = random.Random(0)


def mi(pairs):
    c = Counter(pairs)
    n = sum(c.values())
    L, R = Counter(), Counter()
    for (a, b), v in c.items():
        L[a] += v
        R[b] += v
    return sum(v / n * math.log2(v * n / (L[a] * R[b])) for (a, b), v in c.items())


def lag_pairs(lines, k):
    return [(l[i][-1], l[i + k][0]) for l in lines for i in range(len(l) - k)]


def within(lines, k, reps=30):
    real = mi(lag_pairs(lines, k))
    null = [mi(lag_pairs([rnd.sample(l, len(l)) for l in lines], k)) for _ in range(reps)]
    m = sum(null) / reps
    sd = math.sqrt(sum((x - m) ** 2 for x in null) / (reps - 1))
    return real - m, sd


def across(blocks, reps=200):
    """blocks: list of lists of lines (a page / paragraph). Pairs consecutive lines."""
    pairs, groups = [], []
    for b in blocks:
        ends = [l[-1][-1] for l in b[:-1]]
        starts = [l[0][0] for l in b[1:]]
        pairs += list(zip(ends, starts))
        groups.append((ends, starts))
    real = mi(pairs)
    null = []
    for _ in range(reps):
        p = []
        for ends, starts in groups:
            s = starts[:]
            rnd.shuffle(s)
            p += list(zip(ends, s))
        null.append(mi(p))
    m = sum(null) / reps
    sd = math.sqrt(sum((x - m) ** 2 for x in null) / (reps - 1))
    return real - m, sd, len(pairs)


def voy_blocks(filt):
    zl = json.load(open('zl.json'))
    pages = defaultdict(list)
    for l in zl:
        if not l['type'].startswith('P') or not filt(l):
            continue
        ws = [w['w'] for w in l['words'] if not w['unc']]
        if not ws:
            continue
        # split blocks at paragraph starts so a new paragraph is not paired
        if l['sep'] in '@*' or not pages[l['folio']]:
            pages[l['folio']].append([])
        pages[l['folio']][-1].append(ws)
    return [b for p in pages.values() for b in p if len(b) >= 2]


def text_blocks(lines, size=8):
    return [lines[i:i + size] for i in range(0, len(lines), size) if len(lines[i:i + size]) >= 2]


def structured_verbose(sents, seed=7, ntok=24000, uni_h=30, bi_h=6, p_bigram=0.5):
    """Naibbe-like cipher whose homophones are built as prefix+core+suffix,
    with prefix and suffix drawn from small letter-specific sets, so word
    edges carry information about the enciphered letter."""
    r = random.Random(seed)
    letters = letters_of(sents)
    alpha = sorted(set(letters))
    PRE = ['qo', 'o', 'ch', 'sh', 'd', 'y', 'ok', 'ot', 'l', 's', 'k', 't', 'a', 'p']
    SUF = ['dy', 'y', 'aiin', 'ain', 'ol', 'ar', 'al', 'or', 'ey', 'eey', 'am', 'iin', 'r', 'l']
    CORE = ['e', 'ee', 'ke', 'te', 'ch', 'he', 'o', 'a', 'ed', 'eo', '']
    pre_of = {a: r.sample(PRE, 3) for a in alpha}
    suf_of = {a: r.sample(SUF, 3) for a in alpha}

    def homs(key, n):
        a, b = key[0], key[-1]
        out = set()
        while len(out) < n:
            out.add(r.choice(pre_of[a]) + r.choice(CORE) + r.choice(suf_of[b]))
        return sorted(out)
    uni = {a: homs(a, uni_h) for a in alpha}
    bi = {}
    toks, i = [], 0
    while i < len(letters) and len(toks) < ntok:
        if i + 1 < len(letters) and r.random() < p_bigram:
            k = letters[i] + letters[i + 1]
            if k not in bi:
                bi[k] = homs(k, bi_h)
            toks.append(r.choice(bi[k]))
            i += 2
        else:
            toks.append(r.choice(uni[letters[i]]))
            i += 1
    return to_lines(toks, 9)


def letter_lag(sents, k):
    s = letters_of(sents)
    return mi(list(zip(s, s[k:])))


if __name__ == '__main__':
    rows = []
    def report(name, lines, blocks):
        l1, s1 = within(lines, 1)
        l2, s2 = within(lines, 2)
        ax, sx, n = across(blocks)
        rows.append(dict(name=name, lag1=l1, lag2=l2, across=ax, sd1=s1, sd2=s2, sdx=sx, n_across=n))
        ratio2 = l2 / l1 if l1 > 0 else float('nan')
        ratiox = ax / l1 if l1 > 0 else float('nan')
        print(f'{name:34s} lag1 {l1:7.4f}±{s1:.4f}  lag2 {l2:7.4f}±{s2:.4f}  salto de renglón {ax:7.4f}±{sx:.4f} (n={n})  lag2/lag1 {ratio2:5.2f}  renglón/lag1 {ratiox:5.2f}')


    for name, f in [('VOYNICH Currier B', lambda l: l['lang'] == 'B'), ('VOYNICH Currier A', lambda l: l['lang'] == 'A')]:
        blocks = voy_blocks(f)
        lines = [l for b in blocks for l in b]
        report(name, lines, blocks)
    tl = timm_lines()
    report('TIMM generador', tl, text_blocks(tl))
    for lang in ['latin_medieval', 'italian']:
        w = chunk(refs[lang], 9)
        report(f'{lang}: palabras', cut(w, 24000), text_blocks(cut(w, 24000)))
        c = structured_verbose(refs[lang])
        report(f'{lang}: cifrado verboso estructurado', c, text_blocks(c))
        print(f'   referencia letras {lang}: I(lag1)={letter_lag(refs[lang],1):.3f}  I(lag2)={letter_lag(refs[lang],2):.3f}  cociente {letter_lag(refs[lang],2)/letter_lag(refs[lang],1):.2f}')
    json.dump(rows, open('edge_tests.json', 'w'), indent=1)
