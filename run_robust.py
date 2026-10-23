"""Robustness of the adjacent-dependency test.

All texts are cut to the same number of tokens (NTOK, by whole lines) so
the estimator sees the same amount of data. Reports excess MI for
K in {8,16,32}, lags 1..3, full lines and interior-only.
"""
import json
import sys
import warnings

warnings.filterwarnings('ignore')
from ciphers import verbose_hard, verbose_letter, verbose_naibbe
from common import chunk, cut, refs, timm_lines, voy_lines
from seqdep import heldout_mi

NTOK = int(sys.argv[1])


def _cut_unused(lines, n=NTOK):
    out, k = [], 0
    for l in lines:
        if k >= n:
            break
        out.append(l)
        k += len(l)
    return out


texts = {
    'VOYNICH all': voy_lines(lambda l: True),
    'VOYNICH Currier A': voy_lines(lambda l: l['lang'] == 'A'),
    'VOYNICH Currier B': voy_lines(lambda l: l['lang'] == 'B'),
    'TIMM generator': timm_lines(),
}
for lang in ['latin_medieval', 'italian', 'german', 'czech', 'hebrew', 'turkish', 'vietnamese']:
    texts[f'{lang}: words'] = chunk(refs[lang], 9)
for lang in ['latin_medieval', 'italian']:
    s = refs[lang]
    texts[f'{lang}: verbose 1/word'] = verbose_letter(s)
    texts[f'{lang}: Naibbe-like'] = verbose_naibbe(s)
    texts[f'{lang}: Naibbe ~6k types'] = verbose_hard(s)
    texts[f'{lang}: Naibbe ~6k +30% nulls'] = verbose_hard(s, null_rate=0.3)
    texts[f'{lang}: Naibbe ~6k +50% nulls'] = verbose_hard(s, null_rate=0.5)

rows = {}
hdr = ['K8', 'K16', 'K32', 'K16 lag2', 'K16 lag3', 'K16 interior']
print(f'NTOK={NTOK}')
print(f"{'text':36s}{'types':>7s}" + ''.join(f'{h:>13s}' for h in hdr))
for name, lines in texts.items():
    L = cut(lines, NTOK)
    types = len(set(w for l in L for w in l))
    r = [heldout_mi(L, K=8)[0], heldout_mi(L, K=16)[0], heldout_mi(L, K=32)[0],
         heldout_mi(L, K=16, lag=2)[0], heldout_mi(L, K=16, lag=3)[0],
         heldout_mi(L, K=16, interior=True)[0]]
    sd = heldout_mi(L, K=16)[3]
    rows[name] = dict(types=types, values=dict(zip(hdr, r)), shuffle_sd=sd)
    print(f'{name:36s}{types:7d}' + ''.join(f'{x:13.4f}' for x in r))
json.dump(rows, open(f'robust_{NTOK}.json', 'w'), indent=1)
