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


train = [l for b in train_b for l in b]
test_lines = [l for b in test_b for l in b]
test_vocab = set(w for l in test_lines for w in l)
test_tokens = [w for l in test_lines for w in l]
train_vocab = set(w for l in train for w in l)

# reference: how well does the TRAIN vocabulary itself cover the test half?
cover_train = sum(1 for w in test_tokens if w in train_vocab) / len(test_tokens)
print(f'Referencia: fichas de la mitad de prueba que ya aparecen en la mitad de entrenamiento: {cover_train:.3f}')

# quick tuning on the train half only
lag_profile.REPS = 10
tr_fit = [l for b in train_b[0::2] for l in b]
tr_eval = train_b[1::2]
_, T = summary('t', tr_eval)
W = {'núcleo d1': 0.12, 'núcleo d4': 0.05, 'vecina a 1 letra': 0.034, 'repetición': 0.009, 'borde renglón': 0.025, 'borde d1': 0.23}
best = None
for beta in [1.0, 2.0]:
    for rho in [0.3, 0.6]:
        g = FullGen(tr_fit, beta=beta, rho=rho)
        _, r = summary('x', g.like(tr_eval))
        loss = sum(abs(r[k] - T[k]) / w for k, w in W.items())
        print(f'beta={beta} rho={rho} ' + '  '.join(f'{k} {r[k]:.3f}' for k in W) + f'  pérdida {loss:.2f}', flush=True)
        if best is None or loss < best[0]:
            best = (loss, beta, rho)
print('elegido', best)

lag_profile.REPS = 30
rows = [('VOYNICH B (mitad de prueba)', test_b)]
for seed in (0, 1):
    g = FullGen(train, beta=best[1], rho=best[2], seed=seed)
    rows.append((f'Generador completo, semilla {seed}', g.like(test_b)))
rows.append(('TIMM (sin mensaje)', E.text_blocks(E.timm_lines())))

out = []
for name, bl in rows:
    ws = word_stats(bl, test_vocab, test_tokens)
    _, ss = summary(name, bl)
    out.append((name, ws, ss))
for part in (1, 2):
    keys = list(out[0][part].keys())
    print()
    print(f"{'':34s}" + ''.join(f'{k[:12]:>13s}' for k in keys))
    for name, ws, ss in out:
        d = ws if part == 1 else ss
        print(f'{name:34s}' + ''.join(f'{d.get(k, float("nan")):13.4f}' for k in keys))
json.dump(dict(best=best, cover_train=cover_train, rows=[(n, a, b) for n, a, b in out]),
          open('fullgen_results.json', 'w'), indent=1, ensure_ascii=False)

# sample of generated text
g = FullGen(train, beta=best[1], rho=best[2], seed=7)
print('\nMuestra de texto generado:')
for l in g.like(test_b[:1])[0][:6]:
    print('  ' + ' '.join(l))
print('Muestra real (mitad de prueba):')
for l in test_b[0][:6]:
    print('  ' + ' '.join(l))
