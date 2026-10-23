#!/usr/bin/env bash
# Downloads the third-party data (not redistributed here) and builds the derived files.
set -e
mkdir -p ext && cd ext
git clone --depth 1 https://github.com/noah-chelednik/voynich-data.git
git clone --depth 1 https://github.com/TorstenTimm/SelfCitationTextgenerator.git
mkdir -p ud && cd ud
for t in UD_Latin-PROIEL UD_Latin-ITTB UD_Italian-ISDT UD_German-GSD UD_Czech-CAC UD_Hebrew-HTB UD_Arabic-PADT \
         UD_Turkish-BOUN UD_Spanish-AnCora UD_Old_French-PROFITEROLE UD_Vietnamese-VTB UD_Ancient_Greek-Perseus \
         UD_English-EWT UD_Old_East_Slavic-TOROT UD_Classical_Armenian-CAVaL UD_Hungarian-Szeged UD_Finnish-TDT \
         UD_Persian-Seraji UD_Polish-PDB UD_Catalan-AnCora UD_Portuguese-Bosque; do
  git clone --depth 1 https://github.com/UniversalDependencies/$t.git
done
cd ../..
cp ext/voynich-data/data_sources/cache/ZL3b-n.txt .
cp ext/SelfCitationTextgenerator/executable/generate/generated_text.txt timm_generated.txt
python3 parse_zl.py ZL3b-n.txt zl.json
python3 parse_zl_join.py ZL3b-n.txt zl_join.json
python3 build_refs.py ext/ud 32000
python3 build_refs_big.py ext/ud 200000 refs_big.json
echo "Data ready. Run the scripts with PYTHONHASHSEED=0 (see README.md)."
