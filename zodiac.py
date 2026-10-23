"""Extract zodiac nymph labels (f70v2-f73v) with sign, ring index, clock position."""
import json
import re

PAGES = ['f70v2', 'f70v1', 'f71r', 'f71v', 'f72r1', 'f72r2', 'f72r3', 'f72v3', 'f72v2', 'f72v1', 'f73r', 'f73v']
SIGN = {'f70v2': 'Piscis', 'f70v1': 'Aries oscuro', 'f71r': 'Aries claro', 'f71v': 'Tauro claro',
        'f72r1': 'Tauro oscuro', 'f72r2': 'Géminis', 'f72r3': 'Cáncer', 'f72v3': 'Leo',
        'f72v2': 'Virgo', 'f72v1': 'Libra', 'f73r': 'Escorpio', 'f73v': 'Sagitario'}
# month = sign merged (Aries and Taurus are split over two pages)
MONTH = {k: v.split()[0] for k, v in SIGN.items()}


def clean(t):
    t = re.sub(r'<!\d\d:\d\d>', '', t)
    t = re.sub(r'<![^>]*>', '', t)
    t = re.sub(r'<[^>]*>', '', t)
    t = re.sub(r'\[([^:\]]*):[^\]]*\]', r'\1', t)
    t = t.replace('{', '').replace('}', '').replace("'", '')
    t = re.sub(r'@\d+;', '?', t)
    return t


labels = []
cur = None
ring = -1
for raw in open('ZL3b-n.txt', encoding='utf-8', errors='replace'):
    m = re.match(r'^<(f\w+)>\s+<!', raw)
    if m:
        cur = m.group(1)
        ring = -1
        continue
    if cur not in PAGES:
        continue
    m = re.match(r'^<(f\w+)\.(\d+),(.)(\w+)>\s*(.*)$', raw.rstrip('\n'))
    if not m:
        continue
    sep, typ, txt = m.group(3), m.group(4), m.group(5)
    if not typ.startswith('Lz'):
        continue
    if sep == '@':
        ring += 1          # a new ring of labels starts
    clock = re.search(r'<!(\d\d):(\d\d)>', txt)
    ang = None
    if clock:
        h, mi = int(clock.group(1)), int(clock.group(2))
        ang = ((h % 12) * 60 + mi) / 720 * 360
    t = clean(txt)
    words = [w for w in re.split(r'[.,]', t) if w]
    labels.append(dict(folio=cur, sign=SIGN[cur], month=MONTH[cur], ring=ring, angle=ang,
                       line=int(m.group(2)), text='.'.join(words), words=words,
                       unc=any('?' in w for w in words)))

json.dump(labels, open('zodiac_labels.json', 'w'), ensure_ascii=False, indent=0)
from collections import Counter
c = Counter((l['month']) for l in labels)
print(len(labels), 'labels'); print(c)
print('rings per page', Counter((l['folio'], l['ring']) for l in labels))
