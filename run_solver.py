"""Decipherment attempt with positive and null controls.

For each (cipher text, target language):
  gain = best LL(real order) - best LL(within-line shuffled order),
  per bigram. A solvable cipher shows a large gain AND (for the positive
  control) the recovered mapping matches the true key.
"""
import json
import random
import sys
import warnings

warnings.filterwarnings('ignore')
from ciphers import codebook
from common import chunk, timm_lines, voy_lines
from common import cut
from solver import anneal, bigram_lm, cipher_counts, shuffled

NTOK = 30000
N, M = int(sys.argv[1]), int(sys.argv[2])
ITERS = int(sys.argv[3])
big = json.load(open('refs_big.json'))

# positive control: Vulgate-Latin (held-out tail) encoded with a 1:1 codebook
vul = big['latin_vulgata']
k = 0
for cutpos in range(len(vul) - 1, 0, -1):
    k += len(vul[cutpos])
    if k >= NTOK:
        break
pc_plain = vul[cutpos:]
pc_lm_same = vul[:cutpos]
pc_cipher_lines = codebook(pc_plain, seed=11, ntok=NTOK)
pc_plain_lines = [seg for s in pc_plain for seg in [s[i:i + 9] for i in range(0, len(s), 9)]]
key = {}
for cl, pl in zip(pc_cipher_lines, pc_plain_lines):
    for c, p in zip(cl, pl):
        key[c] = p

lms = {
    'latin(same corpus)': bigram_lm(pc_lm_same, M),
    'latin_medieval': bigram_lm(big['latin_medieval'], M),
    'italian': bigram_lm(big['italian'], M),
    'german': bigram_lm(big['german'], M),
    'hebrew': bigram_lm(big['hebrew'], M),
    'old_french': bigram_lm(big['old_french'], M),
    'czech': bigram_lm(big['czech'], M),
}
ciphers = {
    'POSITIVE: Latin codebook': pc_cipher_lines,
    'VOYNICH Currier B': cut(voy_lines(lambda l: l['lang'] == 'B'), NTOK),
    'VOYNICH Currier A': cut(voy_lines(lambda l: l['lang'] == 'A'), NTOK),
    'NULL: Timm generator': timm_lines(),
}
plan = [
    ('POSITIVE: Latin codebook', ['latin(same corpus)', 'latin_medieval', 'italian']),
    ('VOYNICH Currier B', ['latin_medieval', 'italian', 'german', 'hebrew', 'old_french', 'czech']),
    ('VOYNICH Currier A', ['latin_medieval', 'italian', 'german', 'hebrew', 'old_french', 'czech']),
    ('NULL: Timm generator', ['latin_medieval', 'italian', 'german', 'hebrew']),
]
results = []
print(f'N={N} M={M} iters={ITERS}')
for cname, targets in plan:
    lines = ciphers[cname]
    ctypes, C = cipher_counts(lines, N)
    _, Cs = cipher_counts(shuffled(lines, 5), N)
    # use same type list for the shuffle (types identical; counts reordered)
    npairs = C.sum()
    for tname in targets:
        vocab, LP = lms[tname]
        best, m = anneal(C, LP, iters=ITERS, seed=1)
        best_s, _ = anneal(Cs, LP, iters=ITERS, seed=1)
        gain = (best - best_s) / npairs
        acc = ''
        if cname.startswith('POSITIVE'):
            # token-weighted accuracy over mapped types
            from collections import Counter
            wc = Counter(w for l in lines for w in l)
            ok = sum(wc[c] for i, c in enumerate(ctypes) if m[i] < len(vocab) and vocab[m[i]] == key[c])
            tot = sum(wc[c] for c in ctypes)
            acc = ok / tot
        decoded = [vocab[m[i]] if m[i] < len(vocab) else '<unk>' for i in range(min(N, 12))]
        row = dict(cipher=cname, lm=tname, ll=best / npairs, ll_shuf=best_s / npairs, gain=gain,
                   acc=acc, top_cipher=ctypes[:12], top_decoded=decoded)
        results.append(row)
        a = f'{acc:.3f}' if acc != '' else '  -  '
        print(f'{cname:26s} {tname:20s} LL/pair {best/npairs:8.4f} shuf {best_s/npairs:8.4f} gain {gain:7.4f} acc {a}')
        print('    ', ' '.join(f'{c}={d}' for c, d in zip(ctypes[:12], decoded)))
json.dump(results, open(f'solver_N{N}_M{M}.json', 'w'), indent=1, ensure_ascii=False)
