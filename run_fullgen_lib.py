import json
import math
import warnings
from collections import Counter

warnings.filterwarnings('ignore')
import lag_profile
from metrics import fingerprint, zipf_slope
from run_generator import summary, test_b, train_b
from fullgen import FullGen, parse
import edge_tests as E


def word_stats(bl, real_test_vocab=None, real_test_tokens=None):
    lines = [l for b in bl for l in b]
    f = fingerprint(lines)
    words = [w for l in lines for w in l]
    wc = Counter(words)
    r = dict(h1=f['h1'], h2=f['h2'], h3=f['h3'], long_media=f['mean_wlen'], long_sd=f['sd_wlen'],
             TTR=f['ttr'], hapax=f['hapax_frac'], top10=f['top10_share'], zipf=f['zipf'],
             rigidez=f['pos_rigidity'])
    if real_test_vocab is not None:
        r['% fichas que son palabras reales'] = sum(c for w, c in wc.items() if w in real_test_vocab) / len(words)
        gen_types = set(wc)
        r['% fichas reales que produce'] = sum(1 for w in real_test_tokens if w in gen_types) / len(real_test_tokens)
    return r


