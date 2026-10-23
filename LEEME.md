# Voynich: qué tipo de sistema produjo el texto (fase Claude, 22/10/2026)

Complementa el informe de GPT (pares de dibujos, posición, modelos de forma).
Aquí la pregunta es otra: **qué familias de hipótesis son compatibles con la
estadística del texto**, usando controles positivos (cifrados conocidos de
textos reales) y nulos (generador sin mensaje de Timm).

## Datos
- Voynich: ZL3b-n.txt (Zandbergen-Landini, v3b 13/05/2025), solo párrafos
  (locus P), palabras con glifos ilegibles excluidas. Coma (espacio dudoso) =
  espacio, salvo en `boundary_join.py`.
- Referencias: 21 idiomas de Universal Dependencies (GitHub), solo letras,
  minúsculas, sin diacríticos (el vietnamita pierde los tonos).
- Nulo: `timm_generated.txt` del repositorio TorstenTimm/SelfCitationTextgenerator
  (configuración por defecto incluida en el repo).

## Scripts (ejecutar con PYTHONHASHSEED=0 en este orden)
| Script | Qué hace | Resultado |
|---|---|---|
| parse_zl.py | IVTFF -> zl.json | |
| build_refs.py / build_refs_big.py | corpus de referencia | refs.json, refs_big.json |
| run_fingerprints.py | h1/h2/h3, longitudes, repeticiones, rigidez | final_fingerprints.txt |
| run_robust.py 11000 | dependencia entre palabras con muestras iguales, cifrados simulados | final_robust_11000.txt |
| run_boundary.py 11000 | efecto de borde y dependencia más allá del borde | final_boundary_11000.txt |
| boundary_join.py 11000 | lo mismo con espacios dudosos unidos | final_boundary_join.txt |
| run_solver2.py 120 30000 5 | ataque de sustitución 1:1 con control positivo | final_solver.txt |
| run_solver3.py | ataque sin repeticiones inmediatas | final_solver_norepeat.txt |

## Límites
- Un cifrado verboso con muchos homófonos (~2.000+ formas) no es detectable con
  el estimador de dependencia usado (demostrado en run_robust.py); esa familia
  queda abierta.
- El generador de Timm se probó en una sola configuración.
- Las referencias son prosa moderna o clásica, no recetarios ni herbarios del s. XV.
- Las lecturas que muestra el solucionador para el Voynich son la mejor
  asignación de un procedimiento que dio ganancia negativa: **no son traducción**.

## Fase 3 (23/10/2026): borde, núcleo y generador sin mensaje
| Script | Qué hace | Resultado |
|---|---|---|
| edge_tests.py, edge_sim2.py | efecto de borde a distancia 1, 2 y a través del renglón, con cifrado de control | consola |
| clean_tests.py | mismas pruebas con línea base que conserva la posición (otra línea de la página) | final_clean_tests.txt |
| lag_profile.py | dependencia a distancias 1-5 por rasgo | final_lag_profile.txt |
| generator.py, generator2.py, generator3.py | generador sin mensaje: modo por renglón, regla de borde, copia de núcleo con modificación, arrastre entre renglones | |
| run_generator*.py | ajuste en la mitad de entrenamiento, evaluación en la mitad de prueba | final_generator3.txt, final_generator4.txt |
Conclusión: el efecto de borde es local (desaparece a distancia 2, casi no cruza el renglón);
la dependencia de núcleos es plana más allá de la vecina (modo por renglón), no decae como un texto;
un generador de 4 reglas sin mensaje reproduce aproximadamente la secuencia de Currier B en páginas no vistas.
Esto muestra que no hace falta un mensaje para explicar la secuencia; no prueba que no lo haya.

## Fase 4 (23/10/2026): generador completo (construye las palabras)
| Script | Qué hace | Resultado |
|---|---|---|
| fullgen.py | partición prefijo+núcleo+sufijo; modo por renglón sobre núcleos; copia de núcleo; regla de borde; arrastre | |
| run_fullgen.py, run_fullgen2.py | ajuste en la mitad de entrenamiento, evaluación en páginas no vistas (3 semillas) | final_fullgen1.txt, final_fullgen2.txt |
Resultado: sin vocabulario real, el generador reproduce entropías, longitud, Zipf y rigidez de la palabra,
produce un 77% de palabras que existen en las páginas no vistas y cubre el 79% de ellas (el propio
vocabulario de entrenamiento cubre el 81%), y reproduce la secuencia (borde, núcleo, vecinas) en el mismo orden de magnitud.
Fallos restantes: menos repeticiones exactas (0,5% vs 0,9%), menos palabras raras (hapax 0,58 vs 0,68), h2 algo mayor.

## Fase 5 — Prueba 1: etiquetas farmacéuticas vs. páginas de hierbas (label_test.py)
8 parejas de dibujos repetidos (Stolfi, Notes/091; Petersen, notas en voynich.nu herb_oldid; numeración de Petersen = `<!NNN>` en ZL):
f19r–opchdard, f18v–koldarod, f23r–odalydary, f48v–chokam*, f48r–daseky*, f53r–okeor, f55r–doldam, f90v1–otal (*posición en f89v probable).
Resultado: 0/8 etiquetas aparecen en su página, ni exactas ni a distancia de edición 1; tampoco quitando el prefijo o-/ok-/ot-/op-.
Trigramas raros: Fisher p=0.33, permutación p=0.086 (3 métricas, no significativo).
Si la etiqueta apareciera en su página al menos la mitad de las veces, P(0/8)=1/256. Se rechaza "etiqueta = nombre repetido en el texto".
Las etiquetas de planta (191 tipos) aparecen en el texto de hierbas menos que palabras farmacéuticas de igual longitud (38% vs 53%, IC95 47–60%).

## Fase 5 — Prueba 2: plantilla del Circa instans (template_test.py, final_template_*.txt)
Control positivo: CELT G600006 (latín fuente, irlandés de Ó Cuinn, inglés). Métrica: fracción de entradas cuya palabra en la posición i
se repite en la misma posición de otra entrada; T = inicio(2..10) − mitad(2..10).
Herbarios reales: T = +0.20 a +0.28 (resiste un cifrado de 4 homófonos por letra: +0.11/+0.16). Voynich: T = −0.05 (IC95 −0.03..0.00), T_near −0.09, T_set −0.08; A y B igual.
Las páginas del Voynich no empiezan con una fórmula fija; su comienzo es más variado que su mitad.

## Fase 5 — Prueba 3: dónde caen las palabras que el generador no explica (residual_test.py, final_residual_test.txt)
Currier B, mitad de prueba (11.534 fichas). No explicada = no aparece en 20 réplicas del generador (referencia, 10.390 tipos).
Real: 12,3 % no explicadas; nulo (otras semillas): 1,5 %.
Concentración relativa (real): inicio de página ×4,0; inicio de renglón ×1,6; fin de renglón ×1,7; interior ×0,8. Nulo ≈ plano.
Secciones: ×0,7–1,2 (sin concentración; el nulo varía ×0,3–1,3).
Rasgos: en inicio de renglón empiezan por p/t el 45 % (explicadas 18 %); en fin de renglón acaban en -m el 26 % (17 %). Longitud 6,9 vs 4,9 glifos.
Vocabulario: 1326 tipos, 1249 hapax; solo 74 aparecen en ≥2 folios; recurrencia entre folios igual al nulo (1,5 % vs 1,2–5,5 %).
Lectura: el residuo son palabras largas y únicas más las formas especiales de borde de renglón (convención de escritura); no hay vocabulario reutilizado ni concentración por tema.

## Fase 5 — Prueba 3 bis: regla de borde y base real-contra-real (edgegen.py, residual_test2.py, final_residual_test2.txt)
Con referencias del mismo tamaño, la mitad de prueba de B deja sin explicar: texto real de la otra mitad 18,7 %; generador 20,6 %; generador con regla de borde 20,7 %.
El perfil por posición es el mismo con texto real como referencia (inicio de página ×2,8, inicio de renglón ×1,7, fin ×1,5): el exceso en bordes es del texto, no del generador.
La regla de borde no cambia el residuo (12,3 % con 20 réplicas, igual que sin ella). Recurrencia entre folios: real 2,0 %, con texto real 3,0 %, nulo 3,2 %.
