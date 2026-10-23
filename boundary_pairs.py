"""Which (last glyph -> first glyph) transitions drive the boundary effect."""
import json, math
from collections import Counter
from common import voy_lines
import sys
for name, f in [('B', lambda l: l['lang']=='B'), ('A', lambda l: l['lang']=='A')]:
    L = voy_lines(f)
    pair = Counter((a[-1], b[0]) for l in L for a, b in zip(l, l[1:]))
    n = sum(pair.values()); Lc, Rc = Counter(), Counter()
    for (a,b),v in pair.items(): Lc[a]+=v; Rc[b]+=v
    contrib = sorted(((v/n*math.log2(v*n/(Lc[a]*Rc[b])), a, b, v, v*n/(Lc[a]*Rc[b])) for (a,b),v in pair.items()), reverse=True)
    print(f'--- Currier {name}: pairs n={n}; top last-glyph', Lc.most_common(6), 'top first-glyph', Rc.most_common(8))
    print(' contribution  last->first   count   obs/expected')
    for c,a,b,v,r in contrib[:12]: print(f'   {c:8.4f}     -{a} -> {b}-   {v:6d}   {r:5.2f}')
    # strongest avoidances among common pairs
    av = sorted(((v*n/(Lc[a]*Rc[b]), a, b, v, Lc[a]*Rc[b]/n) for (a,b),v in pair.items() if Lc[a]*Rc[b]/n > 80))
    print(' strongest avoidance (obs/exp, expected>80):', [(f'-{a}->{b}-', round(r,2), v, round(e)) for r,a,b,v,e in av[:6]])
    # check missing pairs with large expectation
    miss=[(a,b,round(Lc[a]*Rc[b]/n)) for a in Lc for b in Rc if (a,b) not in pair and Lc[a]*Rc[b]/n>30]
    print(' absent though expected>30:', miss)
