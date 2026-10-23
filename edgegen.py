"""FullGen + regla de borde: la primera y la última palabra de cada renglón toman núcleo, prefijo y sufijo
de distribuciones propias de esa posición (con respaldo a las generales). Sin vocabulario real.
"""
from collections import Counter, defaultdict
import numpy as np
from fullgen import FullGen, parse


class EdgeGen(FullGen):
    def __init__(self, train_lines, edge_w=1.0, **kw):
        super().__init__(train_lines, **kw)
        self.edge_w = edge_w
        allc = Counter(parse(w)[1] for l in train_lines for w in l)
        tot = sum(allc.values())
        self.pos_core, self.pos_pre, self.pos_suf = {}, {}, {}
        for pos, pick in (('first', lambda l: l[:1]), ('last', lambda l: l[-1:] if len(l) > 1 else [])):
            ws = [w for l in train_lines for w in pick(l)]
            pc = Counter(parse(w)[1] for w in ws); n = sum(pc.values())
            # cociente P(núcleo|pos)/P(núcleo), suavizado
            self.pos_core[pos] = np.array([((pc[c] + 1) / (n + len(self.cores))) / ((allc[c] + 1) / (tot + len(self.cores)))
                                           for c in self.cores]) ** edge_w
            pre, suf = defaultdict(Counter), defaultdict(Counter)
            for w in ws:
                p, c, s = parse(w); pre[c][p] += 1; suf[c][s] += 1
            self.pos_pre[pos], self.pos_suf[pos] = pre, suf

    def _opts(self, c, pos):
        pk, pp = self.pre_opts[c]; sk, sp = self.suf_opts[c]
        if pos is None:
            return pk, pp, sk, sp
        def blend(keys, probs, cnt, k=3.0):
            keys = list(keys) + [x for x in cnt if x not in keys]
            base = dict(zip(keys[:len(probs)], probs)); n = sum(cnt.values())
            pr = np.array([(cnt.get(x, 0) + k * base.get(x, 0)) / (n + k) for x in keys])
            return keys, pr / pr.sum()
        pk, pp = blend(pk, pp, self.pos_pre[pos].get(c, Counter()))
        sk, sp = blend(sk, sp, self.pos_suf[pos].get(c, Counter()))
        return pk, pp, sk, sp

    def word(self, base, prev, first_in_line, last_in_line=False):
        pos = 'first' if first_in_line else ('last' if last_in_line else None)
        p = base.copy()
        if pos:
            p = p * self.pos_core[pos]
        if prev is not None and self.beta:
            pc = parse(prev)[1]
            if pc in self.cidx:
                p[self.cidx[pc]] *= 1 + self.beta
        p /= p.sum()
        w = ''
        for _ in range(20):
            c = self.cores[self.rng.choice(len(p), p=p)]
            pk, pp, sk, sp = self._opts(c, pos)
            W = np.outer(pp, sp)
            cand = [[pk[i] + c + sk[j] for j in range(len(sk))] for i in range(len(pk))]
            for i in range(len(pk)):
                for j in range(len(sk)):
                    x = cand[i][j]
                    if not x:
                        W[i, j] = 0; continue
                    if prev is not None:
                        W[i, j] *= self.edge(prev[-1], x[0]) ** self.gamma
                    elif first_in_line:
                        W[i, j] *= self.start(x[0])
                        if self.lam and self.prev_last is not None:
                            W[i, j] *= self.edge(self.prev_last, x[0]) ** self.lam
            if W.sum() == 0:
                continue
            W = W / W.sum()
            k = self.rng.choice(W.size, p=W.ravel())
            w = cand[k // len(sk)][k % len(sk)]
            if prev is not None and w == prev and self.rng.random() > self.rho:
                continue
            return w
        return w

    def line(self, n):
        base = self.phi[self.rng.choice(len(self.pi), p=self.pi)]
        out = []
        for i in range(n):
            out.append(self.word(base, out[-1] if out else None, i == 0, i == n - 1 and n > 1))
        self.prev_last = out[-1][-1]
        return out
