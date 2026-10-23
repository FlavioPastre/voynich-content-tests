import numpy as np
from core_tests import core
from generator2 import Generator2
class Generator3(Generator2):
    """Copy-with-modification: same-core boost, but the identical word is damped by rho."""
    def __init__(self, train_lines, rho=1.0, **kw):
        super().__init__(train_lines, **kw); self.rho = rho
    def line(self, n):
        base = self.phi[self.rng.choice(len(self.pi), p=self.pi)] if self.use_modes else self.uni
        out = []
        for i in range(n):
            p = base.copy()
            if i == 0:
                if self.use_start: p = p * self.S
                if self.lam and self.prev_last is not None: p = p * self.E[self.prev_last] ** self.lam
            else:
                if self.use_edges: p = p * self.E[out[-1][-1]]
                if self.beta:
                    boost = np.ones(len(p)); boost[self.core_index[core(out[-1])]] += self.beta
                    p = p * boost
                p[self.vidx[out[-1]]] *= self.rho
            p = p / p.sum(); out.append(self.vocab[self.rng.choice(len(p), p=p)])
        self.prev_last = out[-1][-1]; return out
