"""Plaintext-driven cipher with strong edges: each letter has ONE prefix and
ONE suffix (cores vary = homophones). Words encode 1 or 2 letters; prefix
comes from the first letter of the unit, suffix from the last one."""
import random, warnings, sys
warnings.filterwarnings('ignore')
sys.argv=['x']
import edge_tests as E
from ciphers import letters_of, to_lines
from common import refs
def strong(sents, seed=3, ntok=24000, p_bigram=0.5):
    r=random.Random(seed); L=letters_of(sents); alpha=sorted(set(L))
    PRE=['qo','o','ch','sh','d','y','ok','ot','l','s','k','t','a','p','f','r','cth','ckh','e','i','n','m','g','x','b','j','u','v']
    SUF=['dy','y','aiin','ain','ol','ar','al','or','ey','eey','am','iin','r','l','s','m','g','an','on','ir','im','en','in','os','as','es','us','is']
    pre={a:PRE[i] for i,a in enumerate(alpha)}; suf={a:SUF[i] for i,a in enumerate(alpha)}
    CORE=['e','ee','ke','te','he','o','a','ed','eo','ch','kee','tee']
    toks=[];i=0
    while i<len(L) and len(toks)<ntok:
        if i+1<len(L) and r.random()<p_bigram: u=L[i:i+2]; i+=2
        else: u=[L[i]]; i+=1
        toks.append(pre[u[0]]+r.choice(CORE)+suf[u[-1]])
    return to_lines(toks,9)
if __name__ == '__main__':
    for lang in ['latin_medieval','italian']:
        c=strong(refs[lang]); E.report(f'{lang}: cifrado con bordes fuertes', c, E.text_blocks(c))
