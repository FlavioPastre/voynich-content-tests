import json, math, random, warnings
warnings.filterwarnings('ignore')
import common as rf
from run_boundary import boundary_mi, beyond_boundary
from common import cut
from seqdep import heldout_mi
for tag, path in [('comma=space', 'zl.json'), ('comma=join', 'zl_join.json')]:
    rf.zl = json.load(open(path))
    for name, f in [('A', lambda l: l['lang']=='A'), ('B', lambda l: l['lang']=='B')]:
        L = cut(rf.voy_lines(f), 11000)
        print(tag, name, 'tokens', sum(map(len,L)), 'boundaryMI %.4f' % boundary_mi(L, random.Random(1)),
              'classMI %.4f' % heldout_mi(L, K=16)[0], 'beyond %.4f' % beyond_boundary(L))
