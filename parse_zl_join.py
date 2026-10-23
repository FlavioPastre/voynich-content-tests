"""Parse the ZL IVTFF transliteration into a clean JSON corpus.

Output: list of lines with folio, line id, locus type, page metadata and
a list of words. Words containing unreadable glyphs ('?', '@nnn;', '*')
are flagged as uncertain.
"""
import json
import re
import sys

src = sys.argv[1]
out = sys.argv[2]

page_meta = {}
cur_page = None
lines = []

hdr_re = re.compile(r'^<(f\w+)>\s+<!(.*)>')
loc_re = re.compile(r'^<(f\w+)\.(\d+),([@+*=&~/!])(\w+)>\s*(.*)$')


def clean(txt):
    t = re.sub(r'<![^>]*>', '', txt)          # inline comments
    t = t.replace('<->', '.')                  # plant interruption -> space
    t = re.sub(r'<[%$]>', '', t)               # paragraph start/end markers
    t = re.sub(r'<[^>]*>', '', t)
    # alternative readings [a:b] -> first
    t = re.sub(r'\[([^:\]]*):[^\]]*\]', r'\1', t)
    t = re.sub(r'[{}]', '', t)                 # ligature braces
    t = t.replace("'", '')
    return t


for raw in open(src, encoding='utf-8', errors='replace'):
    raw = raw.rstrip('\n')
    if not raw or raw.startswith('#'):
        continue
    m = hdr_re.match(raw)
    if m:
        cur_page = m.group(1)
        meta = dict(re.findall(r'\$(\w)=(\w+)', m.group(2)))
        page_meta[cur_page] = meta
        continue
    m = loc_re.match(raw)
    if not m:
        continue
    folio, num, sep, ltype, txt = m.groups()
    meta = page_meta.get(folio, {})
    t = clean(txt)
    toks = [w for w in re.split(r"[.]", t.replace(",", "")) if w]
    words = []
    for w in toks:
        unc = bool(re.search(r'[?*@&0-9]', w))
        w2 = re.sub(r'@\d+;', '?', w)
        words.append({'w': w2, 'unc': unc})
    lines.append({
        'folio': folio, 'line': int(num), 'sep': sep, 'type': ltype,
        'lang': meta.get('L', '?'), 'hand': meta.get('H', '?'),
        'illus': meta.get('I', '?'), 'quire': meta.get('Q', '?'),
        'words': words,
    })

json.dump(lines, open(out, 'w'))
ntok = sum(len(l['words']) for l in lines)
nunc = sum(w['unc'] for l in lines for w in l['words'])
print('lines', len(lines), 'tokens', ntok, 'uncertain', nunc)
from collections import Counter
print('types', Counter(l['type'][0] for l in lines))
print('lang', Counter(l['lang'] for l in lines if l['type'].startswith('P')))
print('illus', Counter(l['illus'] for l in lines if l['type'].startswith('P')))
