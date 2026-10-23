"""Statistical fingerprint of a text given as a list of lines (lists of words)."""
import math
import random
import re
from collections import Counter, defaultdict

# Glyph merging used by many researchers (Currier-like units)
MERGE = [('cth', 'T'), ('ckh', 'K'), ('cph', 'P'), ('cfh', 'F'),
         ('ch', 'C'), ('sh', 'S'), ('iii', 'J'), ('ii', 'I')]


def merge_glyphs(w):
    for a, b in MERGE:
        w = w.replace(a, b)
    return w


def H(counter):
    n = sum(counter.values())
    return -sum(c / n * math.log2(c / n) for c in counter.values() if c)


def cond_entropy(seqs, order):
    """H(X_t | X_{t-order..t-1}) over sequences of symbols."""
    ctx = defaultdict(Counter)
    for s in seqs:
        for i in range(order, len(s)):
            ctx[tuple(s[i - order:i])][s[i]] += 1
    tot = sum(sum(c.values()) for c in ctx.values())
    return sum(sum(c.values()) / tot * H(c) for c in ctx.values())


def edit1(a, b):
    if a == b:
        return False
    la, lb = len(a), len(b)
    if abs(la - lb) > 1:
        return False
    if la == lb:
        return sum(x != y for x, y in zip(a, b)) == 1
    if la > lb:
        a, b = b, a
    for i in range(len(b)):
        if b[:i] + b[i + 1:] == a:
            return True
    return False


def zipf_slope(counter, top=1000):
    f = sorted(counter.values(), reverse=True)[:top]
    xs = [math.log(i + 1) for i in range(len(f))]
    ys = [math.log(v) for v in f]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sum((x - mx) ** 2 for x in xs)


def word_mi(lines, seed=0):
    """Mutual information between adjacent words (within line), minus the
    same value for a within-line shuffle (bias correction)."""
    def mi(ls):
        pair, left, right = Counter(), Counter(), Counter()
        for l in ls:
            for a, b in zip(l, l[1:]):
                pair[(a, b)] += 1
                left[a] += 1
                right[b] += 1
        n = sum(pair.values())
        return sum(c / n * math.log2(c * n / (left[a] * right[b]))
                   for (a, b), c in pair.items())
    rnd = random.Random(seed)
    real = mi(lines)
    allw = [w for l in lines for w in l]
    rnd.shuffle(allw)
    sh, k = [], 0
    for l in lines:
        sh.append(allw[k:k + len(l)])
        k += len(l)
    return real - mi(sh)


def fingerprint(lines):
    words = [w for l in lines for w in l]
    n = len(words)
    wc = Counter(words)
    # char sequences: each word framed by a space symbol
    seq = []
    for l in lines:
        s = []
        for w in l:
            s.extend(list(w))
            s.append(' ')
        seq.append(s)
    chars = Counter(c for s in seq for c in s)
    lens = [len(w) for w in words]
    ml = sum(lens) / n
    sd = math.sqrt(sum((x - ml) ** 2 for x in lens) / n)
    # positional rigidity: entropy of char at position k from word start,
    # averaged, relative to unconditional char entropy (no spaces)
    inner = Counter(c for w in words for c in w)
    pos = defaultdict(Counter)
    for w in words:
        for i, c in enumerate(w[:6]):
            pos[i][c] += 1
    hp = sum(sum(pos[i].values()) * H(pos[i]) for i in pos) / sum(sum(pos[i].values()) for i in pos)
    adj = [(a, b) for l in lines for a, b in zip(l, l[1:])]
    return {
        'tokens': n,
        'alphabet': len(inner),
        'h1': H(chars),
        'h2': cond_entropy(seq, 1),
        'h3': cond_entropy(seq, 2),
        'mean_wlen': ml,
        'sd_wlen': sd,
        'ttr': len(wc) / n,
        'hapax_frac': sum(1 for c in wc.values() if c == 1) / len(wc),
        'top10_share': sum(c for _, c in wc.most_common(10)) / n,
        'zipf': zipf_slope(wc),
        'Hword': H(wc),
        'repeat_adj': sum(a == b for a, b in adj) / len(adj),
        'edit1_adj': sum(edit1(a, b) for a, b in adj) / len(adj),
        'pos_rigidity': 1 - hp / H(inner),
        'word_mi': word_mi(lines),
    }
