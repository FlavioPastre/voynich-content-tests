import json, warnings
warnings.filterwarnings('ignore')
import lag_profile
from run_generator import summary, test_b, train_b
from generator3 import Generator3
lag_profile.REPS = 12
tr_fit=[l for b in train_b[0::2] for l in b]; tr_eval=train_b[1::2]
_,T=summary('t',tr_eval)
W={'núcleo d1':0.12,'núcleo d4':0.05,'vecina a 1 letra':0.034,'repetición':0.009,'borde renglón':0.025,'borde d1':0.23}
best=None
for K in [10,40]:
    for beta in [1.5,2.5]:
        for rho in [0.3,0.6]:
            g=Generator3(tr_fit,beta=beta,lam=0.25,rho=rho,K=K); _,r=summary('x',g.like(tr_eval))
            loss=sum(abs(r[k]-T[k])/w for k,w in W.items())
            print(f'K={K} beta={beta} rho={rho}  '+'  '.join(f'{k} {r[k]:.3f}' for k in W)+f'  pérdida {loss:.2f}',flush=True)
            if best is None or loss<best[0]: best=(loss,K,beta,rho)
print('elegido',best)
lag_profile.REPS=30
train=[l for b in train_b for l in b]
rows=[summary('VOYNICH B (mitad de prueba)',test_b)]
_,K,beta,rho=best
for seed in (0,1,2):
    g=Generator3(train,beta=beta,lam=0.25,rho=rho,K=K,seed=seed); rows.append(summary(f'Generador final semilla {seed}',g.like(test_b)))
keys=list(rows[0][1].keys())
print(f"{'':32s}"+''.join(f'{k[:13]:>14s}' for k in keys))
for n,r in rows: print(f'{n:32s}'+''.join(f'{r[k]:14.4f}' for k in keys))
json.dump(dict(best=best,rows=rows),open('generator4_results.json','w'),indent=1,ensure_ascii=False)
