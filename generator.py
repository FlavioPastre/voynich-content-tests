"""Minimal no-message generator for Currier B, fitted on half the pages and
evaluated against the other half.

Rule 1 (line mode): each line draws one of K latent modes; a mode is a
         distribution over the word vocabulary (mixture of unigrams, EM).
Rule 2 (edge rule): the next word is reweighted by how compatible its first
         glyph is with the previous word's last glyph (obs/exp ratio table).
Rule 0 (line start): the first word of a line is reweighted by how often its
         first glyph starts lines.
No word-to-word memory beyond the previous word's last glyph.
"""
import math
import random
from collections import Counter, defaultdict

import numpy as np


def fit_modes(lines, vocab_idx, K=10, iters=40, seed=0, alpha=0.05):
    rng = np.random.default_rng(seed)
    V = len(vocab_idx)
    X = [Counter(vocab_idx[w] for w in l if w in vocab_idx) for l in lines]
    phi = rng.dirichlet(np.ones(V), size=K)
    pi = np.ones(K) / K
    for _ in range(iters):
        R = np.zeros((len(X), K))
        for n, c in enumerate(X):
            ll = np.log(pi).copy()
            for v, k in c.items():
                ll += k * np.log(phi[:, v])
            ll -= ll.max()
            R[n] = np.exp(ll) / np.exp(ll).sum()
        pi = R.sum(0) / R.sum()
        counts = np.full((K, V), alpha)
        for n, c in enumerate(X):
            for v, k in c.items():
                counts[:, v] += R[n] * k
        phi = counts / counts.sum(1, keepdims=True)
    return pi, phi


def edge_table(lines, smooth=1.0):
    pair = Counter((a[-1], b[0]) for l in lines for a, b in zip(l, l[1:]))
    L, R = Counter(), Counter()
    for (a, b), v in pair.items():
        L[a] += v
        R[b] += v
    n = sum(pair.values())
    lastset, firstset = list(L), list(R)

    def ratio(a, b):
        return (pair.get((a, b), 0) + smooth) / (L.get(a, 0) * R.get(b, 0) / n + smooth)
    return ratio


def start_table(lines, smooth=1.0):
    st = Counter(l[0][0] for l in lines)
    al = Counter(w[0] for l in lines for w in l)
    ns, na = sum(st.values()), sum(al.values())
    return lambda b: (st.get(b, 0) + smooth) / (al.get(b, 0) * ns / na + smooth)


class Generator:
    def __init__(self, train_lines, K=10, use_modes=True, use_edges=True, use_start=True, seed=0):
        wc = Counter(w for l in train_lines for w in l)
        self.vocab = [w for w, _ in wc.most_common()]
        self.vidx = {w: i for i, w in enumerate(self.vocab)}
        self.use_modes, self.use_edges, self.use_start = use_modes, use_edges, use_start
        uni = np.array([wc[w] for w in self.vocab], float)
        self.uni = uni / uni.sum()
        if use_modes:
            self.pi, self.phi = fit_modes(train_lines, self.vidx, K=K, seed=seed)
        er = edge_table(train_lines)
        sr = start_table(train_lines)
        lasts = sorted({w[-1] for w in self.vocab})
        self.first = np.array([w[0] for w in self.vocab])
        # precompute edge weight vectors per previous last glyph
        self.E = {a: np.array([er(a, w[0]) for w in self.vocab]) for a in lasts}
        self.S = np.array([sr(w[0]) for w in self.vocab])
        self.rng = np.random.default_rng(seed + 1)

    def line(self, n):
        if self.use_modes:
            k = self.rng.choice(len(self.pi), p=self.pi)
            base = self.phi[k]
        else:
            base = self.uni
        out = []
        for i in range(n):
            p = base.copy()
            if i == 0 and self.use_start:
                p = p * self.S
            if i > 0 and self.use_edges:
                p = p * self.E[out[-1][-1]]
            p = p / p.sum()
            out.append(self.vocab[self.rng.choice(len(p), p=p)])
        return out

    def like(self, blocks):
        return [[self.line(len(l)) for l in b] for b in blocks]
