"""Full no-message generator: builds words from slots, no real vocabulary used.

Word parse: PRE + CORE + SUF, where CORE is the span from the first to the last
gallows/bench/e unit (ckh cth cph cfh ch sh k t p f e), PRE is what precedes it,
SUF what follows. Words without core units: CORE='', PRE+SUF split at the
first vowel-like glyph boundary (PRE = leading q/o/y/d/s/l/r, rest SUF).

Generation per line:
  mode k ~ pi;  for each word:
    core ~ phi_k(core) * (1+beta if core == previous core)
    (pre, suf) ~ P(pre|core) P(suf|core) * edge(prev_last, first glyph)
                 * start(first glyph) on the first word, * edge^lam from the
                 previous line's last glyph on the first word
    an identical repeat of the previous word is kept only with prob rho.
"""
import re
from collections import Counter, defaultdict

import numpy as np

UNIT = re.compile(r'ckh|cth|cph|cfh|ch|sh|k|t|p|f|e')
LEAD = re.compile(r'^(qo|q|o|y|d|s|l|r)?')


def parse(w):
    ms = list(UNIT.finditer(w))
    if ms:
        a, b = ms[0].start(), ms[-1].end()
        return w[:a], w[a:b], w[b:]
    m = LEAD.match(w)
    p = m.group(0) if m else ''
    if p == w:
        return '', '', w
    return p, '', w[len(p):]


def edge_ratio(lines, smooth=1.0):
    pair = Counter((a[-1], b[0]) for l in lines for a, b in zip(l, l[1:]))
    L, R = Counter(), Counter()
    for (a, b), v in pair.items():
        L[a] += v
        R[b] += v
    n = sum(pair.values())
    return lambda a, b: (pair.get((a, b), 0) + smooth) / (L.get(a, 0) * R.get(b, 0) / n + smooth)


class FullGen:
    def __init__(self, train_lines, K=20, beta=2.0, rho=0.4, lam=0.25, seed=0, iters=30, gamma=1.0, temp=1.0):
        self.rng = np.random.default_rng(seed)
        self.beta, self.rho, self.lam, self.gamma, self.temp = beta, rho, lam, gamma, temp
        parsed = [[parse(w) for w in l] for l in train_lines]
        cc = Counter(p[1] for l in parsed for p in l)
        self.cores = [c for c, _ in cc.most_common()]
        cidx = {c: i for i, c in enumerate(self.cores)}
        C = len(self.cores)
        # P(pre|core), P(suf|core) with backoff to global
        pre_c, suf_c = defaultdict(Counter), defaultdict(Counter)
        pre_g, suf_g = Counter(), Counter()
        for l in parsed:
            for p, c, s in l:
                pre_c[c][p] += 1
                suf_c[c][s] += 1
                pre_g[p] += 1
                suf_g[s] += 1
        self.pre_opts, self.suf_opts = {}, {}
        for c in self.cores:
            def mix(local, glob, a=0.5):
                tot_l, tot_g = sum(local.values()), sum(glob.values())
                keys = set(local) | {k for k, _ in glob.most_common(8)}
                pr = {k: (local.get(k, 0) + a * tot_l * glob[k] / tot_g / 10) for k in keys}
                z = sum(pr.values())
                ks = list(pr)
                return ks, np.array([pr[k] / z for k in ks])
            self.pre_opts[c] = mix(pre_c[c], pre_g)
            self.suf_opts[c] = mix(suf_c[c], suf_g)
        # mode mixture over cores (EM)
        X = [Counter(cidx[p[1]] for p in l) for l in parsed]
        phi = self.rng.dirichlet(np.ones(C), size=K)
        pi = np.ones(K) / K
        for _ in range(iters):
            Rm = np.zeros((len(X), K))
            for n, x in enumerate(X):
                ll = np.log(pi).copy()
                for v, k in x.items():
                    ll += k * np.log(phi[:, v])
                ll -= ll.max()
                Rm[n] = np.exp(ll) / np.exp(ll).sum()
            pi = Rm.sum(0) / Rm.sum()
            cnt = np.full((K, C), 0.05)
            for n, x in enumerate(X):
                for v, k in x.items():
                    cnt[:, v] += Rm[n] * k
            phi = cnt / cnt.sum(1, keepdims=True)
        # temp<1 flattens modes toward the global core distribution
        glob = cnt.sum(0) / cnt.sum()
        phi = phi ** temp * glob ** (1 - temp)
        phi = phi / phi.sum(1, keepdims=True)
        self.pi, self.phi = pi, phi
        self.cidx = cidx
        self.edge = edge_ratio(train_lines)
        st = Counter(l[0][0] for l in train_lines)
        al = Counter(w[0] for l in train_lines for w in l)
        ns, na = sum(st.values()), sum(al.values())
        self.start = lambda b: (st.get(b, 0) + 1) / (al.get(b, 0) * ns / na + 1)
        self.prev_last = None

    def word(self, base, prev, first_in_line):
        p = base.copy()
        if prev is not None and self.beta:
            pc = parse(prev)[1]
            if pc in self.cidx:
                p[self.cidx[pc]] *= 1 + self.beta
        p /= p.sum()
        for _ in range(20):
            c = self.cores[self.rng.choice(len(p), p=p)]
            pk, pp = self.pre_opts[c]
            sk, sp = self.suf_opts[c]
            W = np.outer(pp, sp)
            cand = [[pk[i] + c + sk[j] for j in range(len(sk))] for i in range(len(pk))]
            for i in range(len(pk)):
                for j in range(len(sk)):
                    w = cand[i][j]
                    if not w:
                        W[i, j] = 0
                        continue
                    if prev is not None:
                        W[i, j] *= self.edge(prev[-1], w[0]) ** self.gamma
                    elif first_in_line:
                        W[i, j] *= self.start(w[0])
                        if self.lam and self.prev_last is not None:
                            W[i, j] *= self.edge(self.prev_last, w[0]) ** self.lam
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
            out.append(self.word(base, out[-1] if out else None, i == 0))
        self.prev_last = out[-1][-1]
        return out

    def like(self, blocks):
        res = []
        for b in blocks:
            self.prev_last = None
            res.append([self.line(len(l)) for l in b])
        return res
