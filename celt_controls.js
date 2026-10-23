// Positive controls for template_test.py (Content test 2).
// Run in the browser console on any page of https://celt.ucc.ie (same origin as the fetches).
// CELT G600006 = Tadhg Ó Cuinn, An Irish Materia Medica (1415):
//   text100–322 = Irish (ch. 70–292), text323–614 = Latin source (ch. 1–292), text615–906 = English (ch. 1–292).
// Same metric as template_test.py: share_i, T = mean(start[2..10]) - mean(middle[2..10]), N = 120 entries, 40 draws.

async function g(n) {
  const r = await fetch('/published/G600006/text' + n + '.html');
  if (!r.ok) return null;
  const d = new DOMParser().parseFromString(await r.text(), 'text/html');
  return d.body.innerText.replace(/\s+/g, ' ').replace(/^.*?Ó Cuinn\) /, '');
}
const C = {};
for (let n = 20; n <= 910; n += 30) {
  const ns = [...Array(30).keys()].map(i => n + i);
  (await Promise.all(ns.map(g))).forEach((t, j) => { if (t) C[ns[j]] = t; });
}
function tok(t) {
  t = t.replace(/^subsection \d+ \d+\.\s*/, '').replace(/\{[^}]*\}/g, ' ').replace(/p\.\d+/g, ' ').toLowerCase();
  return t.match(/[a-záéíóúæœ]+/g) || [];
}
function pack(a, b) {
  const S = [], I = [];
  for (let n = a; n <= b; n++) {
    if (!C[n]) continue;
    const w = tok(C[n]);
    if (w.length < 40) continue;
    const m = Math.floor(w.length / 2);
    S.push(w.slice(0, 15)); I.push(w.slice(m, m + 15));
  }
  return [S, I];
}
function rng(s) { return () => { s = (s * 1103515245 + 12345) % 2147483648; return s / 2147483648; }; }
function lev(a, b) {
  if (Math.abs(a.length - b.length) > 1) return 9;
  let d = [...Array(b.length + 1).keys()];
  for (let i = 1; i <= a.length; i++) {
    let p = d[0]; d[0] = i;
    for (let j = 1; j <= b.length; j++) { const t = d[j]; d[j] = Math.min(d[j] + 1, d[j - 1] + 1, p + (a[i - 1] !== b[j - 1])); p = t; }
  }
  return d[b.length];
}
function share(W, i, near) {
  const t = W.map(w => w[i] || null);
  if (!near) { const c = {}; t.forEach(x => { if (x) c[x] = (c[x] || 0) + 1; }); return t.filter(x => x && c[x] > 1).length / W.length; }
  let k = 0; t.forEach((x, a) => { if (x && t.some((u, b) => u && b !== a && lev(x, u) <= 1)) k++; }); return k / W.length;
}
function setshare(W) {
  const cnt = {}; W.forEach(w => new Set(w.slice(0, 15)).forEach(x => cnt[x] = (cnt[x] || 0) + 1));
  let k = 0, n = 0;
  W.forEach(w => { const own = new Set(w.slice(0, 15)); w.slice(1, 10).forEach(x => { n++; if (cnt[x] - (own.has(x) ? 1 : 0) > 0) k++; }); });
  return k / n;
}
function shuf(w, r) { w = w.slice(); for (let i = w.length - 1; i > 0; i--) { const j = Math.floor(r() * (i + 1)); [w[i], w[j]] = [w[j], w[i]]; } return w; }
function analyse(S, I, N, R) {
  const r = rng(7); let T = 0, Tn = 0, Ts = 0, p1 = 0;
  for (let k = 0; k < R; k++) {
    const idx = shuf([...Array(S.length).keys()], r).slice(0, N);
    const s = idx.map(i => S[i]), it = idx.map(i => I[i]);
    let a = 0, b = 0, an = 0, bn = 0;
    for (let i = 1; i < 10; i++) { a += share(s, i); b += share(it, i); an += share(s, i, 1); bn += share(it, i, 1); }
    T += (a - b) / 9 / R; Tn += (an - bn) / 9 / R; Ts += (setshare(s) - setshare(it)) / R; p1 += share(s, 0) / R;
  }
  return { T: +T.toFixed(3), T_near: +Tn.toFixed(3), T_set: +Ts.toFixed(3), pos1: +p1.toFixed(2) };
}
// homophonic cipher: each letter -> one of k random 1–2 glyph strings, chosen at random per occurrence
function mkcipher(k, seed) {
  const r = rng(seed), G = 'abcdefghijklmnopqrst', m = {};
  for (const c of 'abcdefghijklmnopqrstuvwxyzáéíóúæœ') {
    m[c] = [];
    for (let h = 0; h < k; h++) { const L = 1 + Math.floor(r() * 2); let s = ''; for (let q = 0; q < L; q++) s += G[Math.floor(r() * 20)]; m[c].push(s); }
  }
  const rr = rng(seed + 1);
  return w => [...w].map(c => { const o = m[c] || [c]; return o[Math.floor(rr() * o.length)]; }).join('');
}
const out = {};
const [S, I] = pack(323, 614); out.latin = analyse(S, I, 120, 40);
for (const k of [1, 2, 4]) { const e = mkcipher(k, 11 + k); out['latin_homophones_' + k] = analyse(S.map(w => w.map(e)), I.map(w => w.map(e)), 120, 40); }
let [a, b] = pack(615, 906); out.english = analyse(a, b, 120, 40);
[a, b] = pack(100, 322); out.irish = analyse(a, b, 120, 40);
console.log(JSON.stringify(out, null, 1));
