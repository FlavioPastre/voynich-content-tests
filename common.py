import json
import re
from metrics import merge_glyphs

zl = json.load(open('zl.json'))
refs = json.load(open('refs.json'))


def voy_lines(filt, merged=False):
    out = []
    for l in zl:
        if not l['type'].startswith('P') or not filt(l):
            continue
        ws = [w['w'] for w in l['words'] if not w['unc']]
        if merged:
            ws = [merge_glyphs(w) for w in ws]
        if ws:
            out.append(ws)
    return out


def timm_lines():
    out = []
    for line in open('timm_generated.txt'):
        if line.startswith('#') or not line.strip():
            continue
        ws = [w for w in re.split(r'[\s.]+', line.strip()) if w and re.fullmatch(r'[a-z]+', w)]
        if ws:
            out.append(ws)
    return out


def chunk(sents, size=10):
    # split sentences into pseudo-lines of ~10 words (Voynich lines avg ~8-9)
    out = []
    for s in sents:
        for i in range(0, len(s), size):
            out.append(s[i:i + size])
    return out




def cut(lines, n):
    out, k = [], 0
    for l in lines:
        if k >= n:
            break
        out.append(l)
        k += len(l)
    return out
