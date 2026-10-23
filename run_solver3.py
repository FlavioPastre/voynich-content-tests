"""Same attack after collapsing immediate repeats (w w -> w) in Voynich."""
import json, statistics as st, warnings
warnings.filterwarnings('ignore')
from common import cut, voy_lines, timm_lines
from solver import anneal_perm, bigram_lm, cipher_counts, shuffled
big = json.load(open('refs_big.json'))
N, ITERS, S = 120, 30000, 5
def collapse(lines):
    return [[w for i, w in enumerate(l) if i == 0 or w != l[i-1]] for l in lines]
lms = {t: bigram_lm(big[t], N) for t in ['latin_medieval', 'italian', 'german']}
for cname, lines in [('VOYNICH B no-repeats', collapse(cut(voy_lines(lambda l: l['lang']=='B'), 30000))),
                     ('VOYNICH A no-repeats', collapse(cut(voy_lines(lambda l: l['lang']=='A'), 30000))),
                     ('TIMM no-repeats', collapse(timm_lines()))]:
    ctypes, C = cipher_counts(lines, N); n = C.sum()
    Cs = [cipher_counts(shuffled(lines, 100+s), N)[1] for s in range(S)]
    for t, (vocab, LP) in lms.items():
        b, m = anneal_perm(C, LP, ITERS, seed=1)
        bs = [anneal_perm(c, LP, ITERS, seed=1)[0]/n for c in Cs]
        print(f'{cname:24s} {t:16s} gain {b/n-st.mean(bs):7.4f} z {(b/n-st.mean(bs))/st.stdev(bs):7.2f}')
