import json
import sys

from ciphers import codebook, syllabic, verbose_letter, verbose_naibbe
from common import chunk, timm_lines, voy_lines, refs
from seqdep import heldout_mi, letter_mi

K = int(sys.argv[1]) if len(sys.argv) > 1 else 16
texts = {
    'VOYNICH all': voy_lines(lambda l: True),
    'VOYNICH Currier A': voy_lines(lambda l: l['lang'] == 'A'),
    'VOYNICH Currier B': voy_lines(lambda l: l['lang'] == 'B'),
    'VOYNICH herbal': voy_lines(lambda l: l['illus'] == 'H'),
    'VOYNICH stars(S)': voy_lines(lambda l: l['illus'] == 'S'),
    'VOYNICH balneo(B)': voy_lines(lambda l: l['illus'] == 'B'),
    'TIMM generator': timm_lines(),
}
for lang in ['latin_medieval', 'italian', 'german', 'czech', 'hebrew', 'turkish', 'vietnamese', 'old_french']:
    s = refs[lang]
    texts[f'{lang}: plain words'] = chunk(s, 9)
    if lang in ('latin_medieval', 'italian', 'german', 'hebrew'):
        texts[f'{lang}: verbose 1 letter/word'] = verbose_letter(s)
        texts[f'{lang}: verbose Naibbe-like'] = verbose_naibbe(s)
        texts[f'{lang}: syllabary'] = syllabic(s)
        texts[f'{lang}: codebook'] = codebook(s)

res = {}
print(f'K={K}')
print(f"{'text':42s}{'tokens':>8s}{'MI-excess':>11s}{'real':>8s}{'shuf':>8s}{'sd':>7s}")
for k, v in texts.items():
    n = sum(len(l) for l in v)
    ex, real, m, sd = heldout_mi(v, K=K)
    res[k] = dict(tokens=n, excess=ex, real=real, shuf=m, sd=sd)
    print(f'{k:42s}{n:8d}{ex:11.4f}{real:8.4f}{m:8.4f}{sd:7.4f}')
for lang in ['latin_medieval', 'italian', 'german', 'hebrew']:
    print('letter MI floor', lang, round(letter_mi(refs[lang]), 3))
json.dump(res, open(f'seqdep_K{K}.json', 'w'), indent=1)
