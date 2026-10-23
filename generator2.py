"""Generator with two extra rules:
Rule 3 (copy): next word upweighted by (1 + beta) if it shares the core of the
       previous word (self-citation of the core).
Rule 4 (carry-over): the first word of a line feels the edge rule of the previous
       line's last word with exponent lam.
"""
import numpy as np
from core_tests import core
from generator import Generator


class Generator2(Generator):
    def __init__(self, train_lines, beta=0.0, lam=0.0, **kw):
        super().__init__(train_lines, **kw)
        self.beta, self.lam = beta, lam
        self.cores = np.array([core(w) for w in self.vocab])
        self.core_index = {}
        for i, c in enumerate(self.cores):
            self.core_index.setdefault(c, []).append(i)
        self.prev_last = None

    def line(self, n):
        if self.use_modes:
            k = self.rng.choice(len(self.pi), p=self.pi)
            base = self.phi[k]
        else:
            base = self.uni
        out = []
        for i in range(n):
            p = base.copy()
            if i == 0:
                if self.use_start:
                    p = p * self.S
                if self.lam and self.prev_last is not None:
                    p = p * self.E[self.prev_last] ** self.lam
            else:
                if self.use_edges:
                    p = p * self.E[out[-1][-1]]
                if self.beta:
                    boost = np.ones(len(p))
                    boost[self.core_index[core(out[-1])]] += self.beta
                    p = p * boost
            p = p / p.sum()
            out.append(self.vocab[self.rng.choice(len(p), p=p)])
        self.prev_last = out[-1][-1]
        return out

    def like(self, blocks):
        res = []
        for b in blocks:
            self.prev_last = None
            res.append([self.line(len(l)) for l in b])
        return res
