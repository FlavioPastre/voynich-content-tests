import json, warnings
warnings.filterwarnings('ignore')
import lag_profile
from run_generator import summary, test_b, train_b
from run_fullgen_lib import word_stats
from fullgen import FullGen
import edge_tests as E
train=[l for b in train_b for l in b]; test_lines=[l for b in test_b for l in b]
tv=set(w for l in test_lines for w in l); tt=[w for l in test_lines for w in l]
lag_profile.REPS=10
tr_fit=[l for b in train_b[0::2] for l in b]; tr_eval=train_b[1::2]
_,T=summary('t',tr_eval)
W={'núcleo d1':0.12,'núcleo d4':0.05,'vecina a 1 letra':0.034,'repetición':0.009,'borde renglón':0.025,'borde d1':0.23}
best=None
for temp in [0.5,0.75]:
    for beta in [0.4,0.8]:
        for gamma in [1.3,1.7]:
            g=FullGen(tr_fit,beta=beta,rho=0.7,gamma=gamma,temp=temp); _,r=summary('x',g.like(tr_eval))
            loss=sum(abs(r[k]-T[k])/w for k,w in W.items())
            print(f'temp={temp} beta={beta} gamma={gamma} '+'  '.join(f'{k} {r[k]:.3f}' for k in W)+f'  pérdida {loss:.2f}',flush=True)
            if best is None or loss<best[0]: best=(loss,temp,beta,gamma)
print('elegido',best)
lag_profile.REPS=30
rows=[('VOYNICH B (mitad de prueba)',test_b)]
for seed in (0,1,2):
    rows.append((f'Generador completo, semilla {seed}',FullGen(train,beta=best[2],rho=0.7,gamma=best[3],temp=best[1],seed=seed).like(test_b)))
out=[(n,word_stats(bl,tv,tt),summary(n,bl)[1]) for n,bl in rows]
for part in (1,2):
    keys=list(out[0][part].keys()); print(); print(f"{'':34s}"+''.join(f'{k[:12]:>13s}' for k in keys))
    for n,ws,ss in out:
        d=ws if part==1 else ss; print(f'{n:34s}'+''.join(f'{d.get(k,float("nan")):13.4f}' for k in keys))
json.dump(dict(best=best,rows=out),open('fullgen2_results.json','w'),indent=1,ensure_ascii=False)
