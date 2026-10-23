"""Word-substitution decipherment by simulated annealing.

Cipher: sequence of word tokens (lines). The top-N cipher word types are
mapped (many-to-one allowed) onto the top-M plaintext words of a target
language; every other type maps to UNK. The objective is the bigram
log-likelihood of the decoded token stream under a smoothed language
model trained on a separate corpus of the target language.
"""
import math
import random
from collections import Counter

import numpy as np


def bigram_lm(sents, M, alpha=0.1):
    wc = Counter(w for s in sents for w in s)
    vocab = [w for w, _ in wc.most_common(M)]
    idx = {w: i for i, w in enumerate(vocab)}
    U = M  # UNK index
    C = np.zeros((M + 1, M + 1))
    for s in sents:
        ids = [idx.get(w, U) for w in s]
        for a, b in zip(ids, ids[1:]):
            C[a, b] += 1
    P = (C + alpha) / (C + alpha).sum(1, keepdims=True)
    return vocab, np.log(P)


def cipher_counts(lines, N):
    wc = Counter(w for l in lines for w in l)
    ctypes = [w for w, _ in wc.most_common(N)]
    idx = {w: i for i, w in enumerate(ctypes)}
    C = np.zeros((N + 1, N + 1))
    for l in lines:
        ids = [idx.get(w, N) for w in l]
        for a, b in zip(ids, ids[1:]):
            C[a, b] += 1
    return ctypes, C


def score(C, LP, m):
    return float((C * LP[np.ix_(m, m)]).sum())


def anneal(C, LP, iters=150000, T0=20.0, T1=0.05, seed=0, init=None):
    rnd = random.Random(seed)
    N = C.shape[0] - 1
    M = LP.shape[0] - 1
    m = np.array(init if init is not None else [rnd.randrange(M) for _ in range(N)] + [M])
    m[N] = M  # cipher-UNK -> plain-UNK
    cur = score(C, LP, m)
    best, bestm = cur, m.copy()
    for t in range(iters):
        T = T0 * (T1 / T0) ** (t / iters)
        i = rnd.randrange(N)
        old = m[i]
        new = rnd.randrange(M)
        if new == old:
            continue
        # delta: row i and column i terms
        row_old = (C[i, :] * LP[old, m]).sum()
        col_old = (C[:, i] * LP[m, old]).sum()
        m[i] = new
        row_new = (C[i, :] * LP[new, m]).sum()
        col_new = (C[:, i] * LP[m, new]).sum()
        # self-pair counted in both row & column; fix double count
        d = (row_new + col_new - C[i, i] * LP[new, new]) - (row_old + col_old - C[i, i] * LP[old, old])
        if d >= 0 or rnd.random() < math.exp(d / T):
            cur += d
            if cur > best:
                best, bestm = cur, m.copy()
        else:
            m[i] = old
    return best, bestm


def anneal_perm(C, LP, iters=100000, T0=5.0, T1=0.01, seed=0):
    """1:1 mapping (cipher rank i -> plain rank perm[i]); start from
    frequency-rank alignment; moves are swaps; full rescoring."""
    rnd = random.Random(seed)
    N = C.shape[0] - 1
    m = np.arange(N + 1)
    cur = score(C, LP, m)
    best, bestm = cur, m.copy()
    for t in range(iters):
        T = T0 * (T1 / T0) ** (t / iters)
        i = rnd.randrange(N)
        # local swaps favoured (frequency ranks are informative)
        j = min(N - 1, max(0, i + int(rnd.gauss(0, 15)))) if rnd.random() < 0.7 else rnd.randrange(N)
        if i == j:
            continue
        m[i], m[j] = m[j], m[i]
        new = score(C, LP, m)
        d = new - cur
        if d >= 0 or rnd.random() < math.exp(d / T):
            cur = new
            if cur > best:
                best, bestm = cur, m.copy()
        else:
            m[i], m[j] = m[j], m[i]
    return best, bestm


def shuffled(lines, seed):
    rnd = random.Random(seed)
    return [rnd.sample(l, len(l)) for l in lines]
