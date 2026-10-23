# Voynich manuscript: controlled tests of what kind of system produced the text

Statistical tests on the Voynich manuscript transliteration (ZL3b, Zandbergen 2025), each with a positive control (a known cipher or real medieval text, where the effect is present) and a null (generated text with no message). Spanish notes on every phase: `LEEME.md`.

## Main results

| Question | Result |
|---|---|
| Simple substitution of a known language? | No: character conditional entropy h2 = 2.07 bits vs 2.9–3.7 in 21 reference languages |
| Zodiac labels as a crib (days, saints, degrees)? | No: 263 of 299 labels distinct, no month with 31 figures, no positional pattern |
| Word-boundary effect (last glyph → next first glyph)? | 0.23 bits in Currier B, but 0.0005 at distance 2 and 0.018 across line breaks; a cipher carrying plaintext at word edges predicts 0.18–0.26 |
| Dependence that decays like running text? | No: a flat within-line plateau beyond the next word, for edges, cores and prefix+suffix |
| Can a no-message generator fit unseen pages? | Yes: 77% of its tokens are real words of held-out Currier B; it produces 79% of them (the real training vocabulary covers 81%) |
| Content test 1: does a pharma label appear on the herbal page of the same plant? | 0 of 8 pairs (Stolfi; Petersen), exact or one letter off; P(0/8) = 1/256 if labels appeared half the time |
| Content test 2: do herbal pages open with a fixed formula, like Circa instans? | No: T = −0.05 (95% CI −0.03 to 0.00) vs +0.20 to +0.28 in Ó Cuinn 1415 (Latin, Irish, English); +0.11 survives a 4-homophone cipher |
| Content test 3: where do the words the generator cannot produce fall? | Real held-out text leaves 18.7% unexplained against the other real half, the generator 20.6%, with the same line-edge profile; no topical clustering, no reused vocabulary |

None of this proves the text is meaningless. It rules out several families of hypotheses, with controls showing each test could have detected them.

## How to reproduce

```
./get_data.sh          # downloads ZL3b, Timm's generator output and 21 UD treebanks; builds zl.json, refs.json, refs_big.json
export PYTHONHASHSEED=0
python3 run_fingerprints.py
python3 run_boundary.py 11000
python3 lag_profile.py
python3 run_fullgen2.py
python3 label_test.py
python3 template_test.py
python3 residual_test.py
python3 residual_test2.py
```

The Ó Cuinn controls for content test 2 run in a browser: open any page on celt.ucc.ie, paste `celt_controls.js` into the console. Expected outputs are in `results/` (`final_*.txt`). The order and arguments of the earlier scripts are listed in `LEEME.md`.

## Data (not redistributed; `get_data.sh` fetches it)

- Voynich: ZL3b-n.txt, Zandbergen–Landini v3b (2025), via [noah-chelednik/voynich-data](https://github.com/noah-chelednik/voynich-data)
- Null text: [TorstenTimm/SelfCitationTextgenerator](https://github.com/TorstenTimm/SelfCitationTextgenerator) (MIT)
- Reference languages: [Universal Dependencies](https://github.com/UniversalDependencies) treebanks, letters only
- Herbal control: [CELT G600006](https://celt.ucc.ie/published/G600006/index.html), Tadhg Ó Cuinn, *An Irish Materia Medica* (1415)
- Herbal–pharma pairs: [Stolfi, Repeated plant drawings](https://ic.unicamp.br/~stolfi/voynich/Notes/091/report/report_091.html); Petersen's notes on [voynich.nu](https://www.voynich.nu/extra/herb_oldid.html)

## AI assistance

Analysis and code by Claude (Anthropic), at Flavio Pastre's request, October 2026. An earlier phase used ChatGPT (OpenAI). Every number comes from the code here and can be rerun.
