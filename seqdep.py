"""Held-out lower bound on mutual information between adjacent tokens.

Procedure (identical for every text):
 1. split lines into two halves (even / odd line index);
 2. on half A, learn K word classes from left/right context vectors
    (PPMI + SVD + k-means); unseen words in B go to an 'other' class;
 3. on half B, compute plug-in MI of (class_t, class_t+1) within lines,
    minus the mean MI after shuffling tokens within each line (removes
    estimator bias and any effect not due to order).
Because classes are a function of the word, true I(w_t; w_t+1) is at least
this value (up to estimation noise).
"""
import math
import random
from collections import Counter

import numpy as np
from sklearn.cluster import KMeans


def learn_classes(lines, K, min_count=3, dim=40, seed=0):
    wc = Counter(w for l in lines for w in l)
    vocab = [w for w, c in wc.items() if c >= min_count]
    idx = {w: i for i, w in enumerate(vocab)}
    ctx_vocab = [w for w, _ in wc.most_common(300)]
    cidx = {w: i for i, w in enumerate(ctx_vocab)}
    M = np.zeros((len(vocab), 2 * len(ctx_vocab)))
    for l in lines:
        for a, b in zip(l, l[1:]):
            if a in idx and b in cidx:
                M[idx[a], len(ctx_vocab) + cidx[b]] += 1   # right context
            if b in idx and a in cidx:
                M[idx[b], cidx[a]] += 1                    # left context
    tot = M.sum()
    rs = M.sum(1, keepdims=True) + 1e-9
    cs = M.sum(0, keepdims=True) + 1e-9
    P = np.log(np.maximum(M * tot / (rs * cs), 1e-12))
    P = np.maximum(P, 0)
    U, S, _ = np.linalg.svd(P, full_matrices=False)
    X = U[:, :dim] * S[:dim]
    X /= np.linalg.norm(X, axis=1, keepdims=True) + 1e-9
    km = KMeans(n_clusters=K, n_init=4, random_state=seed).fit(X)
    return {w: int(km.labels_[i]) for w, i in idx.items()}


def mi_pairs(lines, cls, K, lag=1):
    pair = Counter()
    for l in lines:
        c = [cls.get(w, K) for w in l]
        for a, b in zip(c, c[lag:]):
            pair[(a, b)] += 1
    n = sum(pair.values())
    L, R = Counter(), Counter()
    for (a, b), v in pair.items():
        L[a] += v
        R[b] += v
    return sum(v / n * math.log2(v * n / (L[a] * R[b])) for (a, b), v in pair.items())


def heldout_mi(lines, K=16, shuffles=20, seed=0, lag=1, interior=False):
    """interior=True drops the first and last word of every line before
    measuring, so line-start / line-end effects cannot create the signal."""
    A = lines[0::2]
    B = lines[1::2]
    cls = learn_classes(A, K, seed=seed)
    if interior:
        B = [l[1:-1] for l in B if len(l) > 3]
    real = mi_pairs(B, cls, K, lag)
    rnd = random.Random(seed)
    sh = []
    for _ in range(shuffles):
        Bs = []
        for l in B:
            l2 = l[:]
            rnd.shuffle(l2)
            Bs.append(l2)
        sh.append(mi_pairs(Bs, cls, K, lag))
    m = sum(sh) / len(sh)
    sd = math.sqrt(sum((x - m) ** 2 for x in sh) / (len(sh) - 1))
    return real - m, real, m, sd


def letter_mi(sents):
    """I(letter_t; letter_t+1) within words+spaces stream of the plaintext,
    the floor that a letter-per-word verbose cipher must exceed."""
    seq = []
    for s in sents:
        for w in s:
            seq.extend(w)
    pair = Counter(zip(seq, seq[1:]))
    n = sum(pair.values())
    L, R = Counter(), Counter()
    for (a, b), v in pair.items():
        L[a] += v
        R[b] += v
    return sum(v / n * math.log2(v * n / (L[a] * R[b])) for (a, b), v in pair.items())
