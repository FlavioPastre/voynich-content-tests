"""Projection battery.

If each Voynich word encodes a plaintext unit u and u can be recovered from
some feature g(word), then (data-processing inequality)
    I(g(w_t); g(w_t+k)) >= I(u_t; u_t+k)  for every lag k.
Real plaintext has I(u_t; u_t+2) clearly > 0, so a projection g with
lag-2 MI ~ 0 rules out every scheme in which the unit is a function of g.

Also: adjacent-line similarity control. If lines resemble their neighbour
(copying from the line above), ANY word of line i is related to ANY word
of line i+1. If text flows sequentially, the end(i)->start(i+1) pair should
be special compared with start(i)->start(i+1).
"""
import random
import re
import sys
import warnings
from collections import Counter

warnings.filterwarnings('ignore')
sys.argv = ['x']
import edge_tests as E
from core_tests import core, core_cipher
from ciphers import letters_of
from common import refs

PRE = re.compile(r'^(qo|q|o|y|d|s|l|r|a|ch|sh|cth|ckh|cph|cfh|k|t|p|f|e|i)')
SUF = re.compile(r'(aiin|aiir|ain|iin|dy|ey|y|ol|al|or|ar|am|an|om|im|in|ir|r|l|s|m|n|g|o|d|e|h|i|a)$')


def pre(w):
    m = PRE.match(w)
    return m.group(1) if m else '_'


def suf(w):
    m = SUF.search(w)
    return m.group(1) if m else '_'


PROJ = {
    'primer+último glifo': lambda w: w[0] + '|' + w[-1],
    'prefijo+sufijo': lambda w: pre(w) + '|' + suf(w),
    'núcleo': core,
    'longitud': lambda w: str(min(len(w), 9)),
    'prefijo+núcleo': lambda w: pre(w) + '|' + core(w),
}


def mi_lag(lines, k, g):
    return E.mi([(g(l[i]), g(l[i + k])) for l in lines for i in range(len(l) - k)])


def within(lines, k, g, reps=20):
    real = mi_lag(lines, k, g)
    null = [mi_lag([E.rnd.sample(l, len(l)) for l in lines], k, g) for _ in range(reps)]
    m = sum(null) / reps
    sd = (sum((x - m) ** 2 for x in null) / (reps - 1)) ** .5
    return real - m, sd


def line_pairs(blocks, g, which):
    """which: 'end->start', 'start->start', 'end->end', 'mid->mid'."""
    pick = {'end': lambda l: l[-1], 'start': lambda l: l[0], 'mid': lambda l: l[len(l) // 2]}
    a, b = which.split('->')
    groups = []
    for bl in blocks:
        xs = [g(pick[a](l)) for l in bl[:-1]]
        ys = [g(pick[b](l)) for l in bl[1:]]
        groups.append((xs, ys))
    real = E.mi([p for xs, ys in groups for p in zip(xs, ys)])
    null = []
    for _ in range(100):
        p = []
        for xs, ys in groups:
            s = ys[:]
            E.rnd.shuffle(s)
            p += list(zip(xs, s))
        null.append(E.mi(p))
    m = sum(null) / len(null)
    sd = (sum((x - m) ** 2 for x in null) / (len(null) - 1)) ** .5
    return real - m, sd


def letter_mi(sents, k):
    s = letters_of(sents)
    return E.mi(list(zip(s, s[k:])))


if __name__ == '__main__':
    print('Referencia: dependencia entre letras del texto llano (bits)')
    for lang in ['latin_medieval', 'italian', 'german', 'hebrew']:
        print(f'  {lang:15s} ' + '  '.join(f'lag{k} {letter_mi(refs[lang], k):.3f}' for k in (1, 2, 3, 4)))

    texts = {}
    for name, f in [('VOYNICH B', lambda l: l['lang'] == 'B'), ('VOYNICH A', lambda l: l['lang'] == 'A')]:
        bl = E.voy_blocks(f)
        texts[name] = ([l for b in bl for l in b], bl)
    c = core_cipher(refs['latin_medieval'])
    texts['control: latín en el núcleo'] = (c, E.text_blocks(c))
    tl = E.timm_lines()
    texts['TIMM'] = (tl, E.text_blocks(tl))

    print('\nProyecciones: exceso de dependencia (bits) a distancia 1 y 2 dentro del renglón')
    for name, (lines, _) in texts.items():
        for pn, g in PROJ.items():
            l1, s1 = within(lines, 1, g)
            l2, s2 = within(lines, 2, g)
            print(f'  {name:28s} {pn:22s} lag1 {l1:7.4f}±{s1:.4f}   lag2 {l2:7.4f}±{s2:.4f}')

    print('\nRenglones vecinos: ¿flujo (fin->inicio) o parecido general?')
    for name, (_, blocks) in texts.items():
        for pn in ['núcleo', 'primer+último glifo']:
            g = PROJ[pn]
            out = []
            for w in ['end->start', 'start->start', 'end->end', 'mid->mid']:
                v, s = line_pairs(blocks, g, w)
                out.append(f'{w} {v:6.3f}±{s:.3f}')
            print(f'  {name:28s} {pn:20s} ' + '  '.join(out))
