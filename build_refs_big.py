"""Extract plain running text (surface word forms) from UD treebanks.

Each reference corpus is reduced to lowercase letters only, diacritics and
vowel points stripped, and cut to the same token count as the Voynich
paragraph text so statistics are comparable.
"""
import glob
import json
import os
import sys
import unicodedata

UD = sys.argv[1]
N = int(sys.argv[2])
OUT = sys.argv[3]
langs = {
    'latin_vulgata': 'UD_Latin-PROIEL', 'latin_medieval': 'UD_Latin-ITTB',
    'italian': 'UD_Italian-ISDT', 'german': 'UD_German-GSD',
    'czech': 'UD_Czech-CAC', 'hebrew': 'UD_Hebrew-HTB',
    'arabic': 'UD_Arabic-PADT', 'turkish': 'UD_Turkish-BOUN',
    'spanish': 'UD_Spanish-AnCora', 'old_french': 'UD_Old_French-PROFITEROLE',
    'vietnamese': 'UD_Vietnamese-VTB', 'ancient_greek': 'UD_Ancient_Greek-Perseus',
    'english': 'UD_English-EWT', 'old_east_slavic': 'UD_Old_East_Slavic-TOROT',
    'classical_armenian': 'UD_Classical_Armenian-CAVaL',
    'hungarian': 'UD_Hungarian-Szeged', 'finnish': 'UD_Finnish-TDT',
    'persian': 'UD_Persian-Seraji', 'polish': 'UD_Polish-PDB',
    'catalan': 'UD_Catalan-AnCora', 'portuguese': 'UD_Portuguese-Bosque',
}


def norm(w):
    w = unicodedata.normalize('NFD', w.lower())
    w = ''.join(c for c in w if unicodedata.category(c).startswith('L'))
    return unicodedata.normalize('NFC', w)


out = {}
for name, d in langs.items():
    files = sorted(glob.glob(os.path.join(UD, d, '*.conllu')))
    files.sort(key=lambda f: ('train' not in f, f))
    sents = []
    for f in files:
        skip_until = 0
        cur = []
        for line in open(f, encoding='utf-8'):
            if line.startswith('#'):
                continue
            if not line.strip():
                if cur:
                    sents.append(cur)
                cur = []
                continue
            cols = line.split('\t')
            tid = cols[0]
            if '.' in tid:
                continue
            if '-' in tid:
                a, b = tid.split('-')
                skip_until = int(b)
                w = norm(cols[1])
                if w:
                    cur.append(w)
                continue
            if int(tid) <= skip_until:
                continue
            w = norm(cols[1])
            if w:
                cur.append(w)
        if cur:
            sents.append(cur)
    words = []
    for s in sents:
        if name.startswith('latin'):
            s = [w.replace('j', 'i').replace('v', 'u') for w in s]
        words.append(s)
        if sum(len(x) for x in words) >= N:
            break
    out[name] = words
    print(name, sum(len(x) for x in words), 'tokens', len(words), 'sentences',
          ''.join(sorted(set(c for s in words for w in s for c in w)))[:60])

json.dump(out, open(OUT, 'w'), ensure_ascii=False)
