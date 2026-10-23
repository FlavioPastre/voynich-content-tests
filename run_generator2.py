"""Tune beta/lam on the TRAIN half only (generator fitted on one half of the
train pages, scored against the other half of the train pages), then evaluate
once on the held-out test half."""
import json
import warnings

warnings.filterwarnings('ignore')
import edge_tests as E
import lag_profile
from run_generator import summary, test_b, train_b
from generator2 import Generator2

lag_profile.REPS = 12
tr_fit = [l for b in train_b[0::2] for l in b]
tr_eval = train_b[1::2]
_, target = summary('train-eval', tr_eval)
print('objetivo (mitad de entrenamiento):', {k: round(v, 4) for k, v in target.items()})

best = None
for beta in [0, 3, 8, 15]:
    for lam in [0, 0.5, 1.0]:
        g = Generator2(tr_fit, beta=beta, lam=lam, K=10)
        _, r = summary('x', g.like(tr_eval))
        loss = abs(r['núcleo d1'] - target['núcleo d1']) / 0.12 + abs(r['vecina a 1 letra'] - target['vecina a 1 letra']) / 0.034 \
            + abs(r['borde renglón'] - target['borde renglón']) / 0.025 + abs(r['borde d1'] - target['borde d1']) / 0.23
        print(f'beta={beta:2d} lam={lam:.1f}  núcleo d1 {r["núcleo d1"]:.3f}  vecina {r["vecina a 1 letra"]:.4f}  renglón {r["borde renglón"]:.4f}  borde d1 {r["borde d1"]:.3f}  pérdida {loss:.2f}', flush=True)
        if best is None or loss < best[0]:
            best = (loss, beta, lam)
print('elegido', best)

lag_profile.REPS = 30
train = [l for b in train_b for l in b]
rows = [summary('VOYNICH B (mitad de prueba)', test_b)]
g = Generator2(train, beta=best[1], lam=best[2], K=10)
rows.append(summary(f'Generador 4 reglas (beta={best[1]}, lam={best[2]})', g.like(test_b)))
keys = list(rows[0][1].keys())
print(f"{'':42s}" + ''.join(f'{k[:13]:>14s}' for k in keys))
for name, r in rows:
    print(f'{name:42s}' + ''.join(f'{r[k]:14.4f}' for k in keys))
json.dump(rows, open('generator2_results.json', 'w'), indent=1, ensure_ascii=False)
