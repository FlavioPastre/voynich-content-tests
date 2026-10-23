"""1:1 word-substitution attack with positive control and shuffle nulls.

gain_z = (LL_real - mean LL_shuffled) / sd LL_shuffled over S shuffles,
where every LL is the best found by the same annealer and budget.
"""
import json
import statistics as st
import sys
import warnings
from collections import Counter

warnings.filterwarnings('ignore')
from ciphers import codebook
from common import cut, timm_lines, voy_lines
from solver import anneal_perm, bigram_lm, cipher_counts, shuffled

NTOK = 30000
N = int(sys.argv[1])
ITERS = int(sys.argv[2])
S = int(sys.argv[3])
big = json.load(open('refs_big.json'))

vul = big['latin_vulgata']
k = 0
for cutpos in range(len(vul) - 1, 0, -1):
    k += len(vul[cutpos])
    if k >= NTOK:
        break
pc_plain, pc_lm_same = vul[cutpos:], vul[:cutpos]
pc_cipher = codebook(pc_plain, seed=11, ntok=NTOK)
pc_plain_lines = [s[i:i + 9] for s in pc_plain for i in range(0, len(s), 9)]
key = {c: p for cl, pl in zip(pc_cipher, pc_plain_lines) for c, p in zip(cl, pl)}

lms = {name: bigram_lm(c, N) for name, c in [
    ('latin(same corpus)', pc_lm_same), ('latin_medieval', big['latin_medieval']),
    ('italian', big['italian']), ('german', big['german']), ('hebrew', big['hebrew']),
    ('old_french', big['old_french']), ('czech', big['czech'])]}
ciphers = {
    'POSITIVE: Latin codebook': pc_cipher,
    'VOYNICH Currier B': cut(voy_lines(lambda l: l['lang'] == 'B'), NTOK),
    'VOYNICH Currier A': cut(voy_lines(lambda l: l['lang'] == 'A'), NTOK),
    'NULL: Timm generator': timm_lines(),
}
langs = ['latin_medieval', 'italian', 'german', 'hebrew', 'old_french', 'czech']
plan = [('POSITIVE: Latin codebook', ['latin(same corpus)', 'latin_medieval', 'italian'])] + \
       [(c, langs) for c in ['VOYNICH Currier B', 'VOYNICH Currier A', 'NULL: Timm generator']]

out = []
print(f'N={N} iters={ITERS} shuffles={S}')
for cname, targets in plan:
    lines = ciphers[cname]
    ctypes, C = cipher_counts(lines, N)
    wc = Counter(w for l in lines for w in l)
    np_ = C.sum()
    Cs = [cipher_counts(shuffled(lines, 100 + s), N)[1] for s in range(S)]
    for t in targets:
        vocab, LP = lms[t]
        b, m = anneal_perm(C, LP, ITERS, seed=1)
        bs = [anneal_perm(c, LP, ITERS, seed=1)[0] / np_ for c in Cs]
        z = (b / np_ - st.mean(bs)) / (st.stdev(bs) + 1e-12)
        acc = ''
        if cname.startswith('POS'):
            ok = sum(wc[c] for i, c in enumerate(ctypes) if vocab[m[i]] == key[c])
            acc = ok / sum(wc[c] for c in ctypes)
            base = sum(wc[c] for i, c in enumerate(ctypes) if vocab[i] == key[c]) / sum(wc[c] for c in ctypes)
            acc = f'{acc:.3f} (rank-only start {base:.3f})'
        dec = [vocab[m[i]] for i in range(15)]
        out.append(dict(cipher=cname, lm=t, ll=b / np_, ll_shuf=bs, z=z, acc=acc,
                        sample=list(zip(ctypes[:15], dec))))
        print(f'{cname:26s} {t:20s} gain {b/np_-st.mean(bs):7.4f}  z {z:7.2f}  {acc}')
        print('     ', ' '.join(f'{c}={d}' for c, d in zip(ctypes[:15], dec)))
json.dump(out, open(f'solver2_N{N}.json', 'w'), indent=1, ensure_ascii=False)
