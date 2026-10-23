"""Prueba 2: plantilla del Circa instans. Misma métrica que el cálculo JS sobre CELT G600006.
share_i = fracción de ventanas cuya palabra en la posición i aparece en la posición i de otra ventana.
start = primeras 15 palabras de la página; inter = 15 palabras desde la mitad; shuf = start barajado dentro de cada ventana.
T = media(start[2..10]) - media(inter[2..10]); P = media(start[2..10]) - media(shuf[2..10]).
"""
import re, random, sys
from collections import Counter, defaultdict

meta, pages = {}, defaultdict(list)
for raw in open('ZL3b-n.txt', encoding='utf-8', errors='replace'):
    m = re.match(r'^<(f\w+)>\s+<!(.*)>', raw)
    if m:
        meta[m.group(1)] = dict(re.findall(r'\$(\w)=(\w+)', m.group(2))); continue
    m = re.match(r'^<(f\w+)\.\d+,(.)(\w)(\w)>\s+(.*)', raw)
    if not m or m.group(3) != 'P':
        continue
    t = re.sub(r'<[^>]*>', '', m.group(5))
    t = re.sub(r'\[([^:\]]*):[^\]]*\]', r'\1', t)
    t = re.sub(r'\{[^}]*\}', '', t)
    pages[m.group(1)] += [w for w in re.split(r'[.,\s]+', t) if w and re.fullmatch(r'[a-z?]+', w)]


def lev(a, b):
    d = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        p, d[0] = d[0], i
        for j, cb in enumerate(b, 1):
            p, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, p + (ca != cb))
    return d[-1]


def share(W, i, near=False):
    toks = [w[i] if i < len(w) and '?' not in w[i] else None for w in W]
    if not near:
        c = Counter(t for t in toks if t)
        return sum(1 for t in toks if t and c[t] > 1) / len(W)
    k = 0
    for a, t in enumerate(toks):
        if t and any(u and b != a and lev(t, u) <= 1 for b, u in enumerate(toks)):
            k += 1
    return k / len(W)


def windows(f):
    w = pages[f]; m = len(w) // 2
    return w[:15], w[m:m + 15]


def analyse(S, I, N, R=200, seed=7, near=False):
    r = random.Random(seed)
    acc = {k: [0.0] * 15 for k in ('start', 'inter', 'shuf')}
    for _ in range(R):
        idx = r.sample(range(len(S)), N)
        s = [S[i] for i in idx]; it = [I[i] for i in idx]
        sh = [r.sample(w, len(w)) for w in s]
        for i in range(15):
            acc['start'][i] += share(s, i, near) / R
            acc['inter'][i] += share(it, i, near) / R
            acc['shuf'][i] += share(sh, i, near) / R
    m = lambda a: sum(a[1:10]) / 9
    return dict(start=[round(x, 2) for x in acc['start']], inter=[round(x, 2) for x in acc['inter']],
                pos1=round(acc['start'][0], 2), T=round(m(acc['start']) - m(acc['inter']), 3),
                P=round(m(acc['start']) - m(acc['shuf']), 3))


def herbal(lang=None):
    return [f for f in pages if meta.get(f, {}).get('I') == 'H' and len(pages[f]) >= 40
            and (lang is None or meta[f].get('L') == lang)]


if __name__ == '__main__':
    for lang, N in ((None, 120), ('A', 80), ('B', 25)):
        fs = herbal(lang)
        S, I = zip(*[windows(f) for f in fs])
        res = analyse(list(S), list(I), min(N, len(fs)))
        print('Voynich hierbas', lang or 'todo', 'páginas', len(fs), 'N', min(N, len(fs)), res)


def setshare(W):
    cnt = Counter()
    for w in W:
        cnt.update(set(w[:15]))
    k = n = 0
    for w in W:
        own = set(w[:15])
        for x in w[1:10]:
            n += 1
            k += (cnt[x] - (x in own)) > 0
    return k / n


def analyse3(S, I, N, R=40, seed=7):
    r = random.Random(seed); T = Tn = Ts = p1 = 0
    for _ in range(R):
        idx = r.sample(range(len(S)), N)
        s = [S[i] for i in idx]; it = [I[i] for i in idx]
        a = sum(share(s, i) for i in range(1, 10)); b = sum(share(it, i) for i in range(1, 10))
        an = sum(share(s, i, True) for i in range(1, 10)); bn = sum(share(it, i, True) for i in range(1, 10))
        T += (a - b) / 9 / R; Tn += (an - bn) / 9 / R; Ts += (setshare(s) - setshare(it)) / R; p1 += share(s, 0) / R
    return dict(T=round(T, 3), T_near=round(Tn, 3), T_set=round(Ts, 3), pos1=round(p1, 2))


def run3():
    for lang, N in ((None, 120), ('A', 80), ('B', 25)):
        fs = herbal(lang)
        S, I = zip(*[windows(f) for f in fs])
        print('Voynich', lang or 'todo', len(fs), 'N', N, analyse3(list(S), list(I), min(N, len(fs))))
