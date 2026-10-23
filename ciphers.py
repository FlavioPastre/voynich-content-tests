"""Cipher simulations applied to real plaintext.

All produce lists of lines of 'words'. The glyph strings are arbitrary;
the tests that use these simulations depend only on the token sequence.
"""
import random

GLYPHS = 'oehyacdiklrstnqpmf'


def rand_string(rnd, lo=3, hi=7):
    return ''.join(rnd.choice(GLYPHS) for _ in range(rnd.randint(lo, hi)))


def unique_strings(rnd, n):
    s, out = set(), []
    while len(out) < n:
        x = rand_string(rnd)
        if x not in s:
            s.add(x)
            out.append(x)
    return out


def letters_of(sents):
    return [c for s in sents for w in s for c in w]


def to_lines(tokens, size=9):
    return [tokens[i:i + size] for i in range(0, len(tokens), size)]


def verbose_letter(sents, homophones=4, seed=1, ntok=34000):
    """Each plaintext letter -> one cipher word chosen among k homophones."""
    rnd = random.Random(seed)
    letters = letters_of(sents)
    alpha = sorted(set(letters))
    pool = unique_strings(rnd, len(alpha) * homophones)
    table = {a: pool[i * homophones:(i + 1) * homophones] for i, a in enumerate(alpha)}
    toks = [rnd.choice(table[c]) for c in letters[:ntok]]
    return to_lines(toks)


def verbose_naibbe(sents, seed=2, p_bigram=0.5, uni_h=6, ntok=34000):
    """Naibbe-like: plaintext split into unigram/bigram chunks at random;
    unigrams have several homophones, each bigram one cipher word."""
    rnd = random.Random(seed)
    letters = letters_of(sents)
    alpha = sorted(set(letters))
    pool = iter(unique_strings(rnd, len(alpha) * uni_h + len(alpha) ** 2))
    uni = {a: [next(pool) for _ in range(uni_h)] for a in alpha}
    bi = {}
    toks, i = [], 0
    while i < len(letters) and len(toks) < ntok:
        if i + 1 < len(letters) and rnd.random() < p_bigram:
            k = letters[i] + letters[i + 1]
            if k not in bi:
                bi[k] = next(pool)
            toks.append(bi[k])
            i += 2
        else:
            toks.append(rnd.choice(uni[letters[i]]))
            i += 1
    return to_lines(toks)


def verbose_hard(sents, seed=5, p_bigram=0.5, uni_h=40, bi_h=8, null_rate=0.0, ntok=34000):
    """Harder Naibbe-like variant: many homophones (Voynich-sized vocabulary)
    and optional null words inserted at random."""
    rnd = random.Random(seed)
    letters = letters_of(sents)
    alpha = sorted(set(letters))
    uni = {a: unique_strings(rnd, uni_h) for a in alpha}
    bi = {}
    nulls = unique_strings(rnd, 60)
    toks, i = [], 0
    while i < len(letters) and len(toks) < ntok:
        if null_rate and rnd.random() < null_rate:
            toks.append(rnd.choice(nulls))
            continue
        if i + 1 < len(letters) and rnd.random() < p_bigram:
            k = letters[i] + letters[i + 1]
            if k not in bi:
                bi[k] = unique_strings(rnd, bi_h)
            toks.append(rnd.choice(bi[k]))
            i += 2
        else:
            toks.append(rnd.choice(uni[letters[i]]))
            i += 1
    return to_lines(toks)


def syllabic(sents, seed=3, ntok=34000):
    """Each plaintext word split into CV-ish syllables; each syllable type
    -> one fixed cipher word (a syllabary written with spaces)."""
    rnd = random.Random(seed)
    V = set('aeiouy')
    toks = []
    table = {}
    for s in sents:
        for w in s:
            syl, cur = [], ''
            for c in w:
                cur += c
                if c in V:
                    syl.append(cur)
                    cur = ''
            if cur:
                if syl:
                    syl[-1] += cur
                else:
                    syl.append(cur)
            for x in syl:
                if x not in table:
                    table[x] = rand_string(rnd, 3, 7)
                toks.append(table[x])
        if len(toks) >= ntok:
            break
    return to_lines(toks[:ntok])


def codebook(sents, seed=4, ntok=34000):
    """Nomenclator: each plaintext word -> one fixed code word. Equivalent
    to the plaintext word sequence for sequence statistics."""
    rnd = random.Random(seed)
    table = {}
    lines = []
    n = 0
    for s in sents:
        for i in range(0, len(s), 9):
            seg = s[i:i + 9]
            out = []
            for w in seg:
                if w not in table:
                    table[w] = rand_string(rnd, 3, 8)
                out.append(table[w])
            lines.append(out)
            n += len(out)
        if n >= ntok:
            break
    return lines
