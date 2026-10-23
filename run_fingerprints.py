from metrics import fingerprint
from common import *

texts = {
    'VOYNICH all (EVA)': voy_lines(lambda l: True),
    'VOYNICH all (merged ch/sh/cth..)': voy_lines(lambda l: True, True),
    'VOYNICH Currier A': voy_lines(lambda l: l['lang'] == 'A'),
    'VOYNICH Currier B': voy_lines(lambda l: l['lang'] == 'B'),
    'TIMM generator (no meaning)': timm_lines(),
}
for k, v in refs.items():
    texts[k] = chunk(v, 9)

res = {k: fingerprint(v) for k, v in texts.items()}
json.dump(res, open('fingerprints.json', 'w'), indent=1)
cols = ['tokens', 'alphabet', 'h1', 'h2', 'h3', 'mean_wlen', 'sd_wlen', 'ttr', 'hapax_frac',
        'top10_share', 'zipf', 'repeat_adj', 'edit1_adj', 'pos_rigidity', 'word_mi']
print(f"{'text':34s}" + ''.join(f'{c[:9]:>10s}' for c in cols))
for k, r in res.items():
    print(f'{k[:34]:34s}' + ''.join(f'{r[c]:10.3f}' if isinstance(r[c], float) else f'{r[c]:10d}' for c in cols))
