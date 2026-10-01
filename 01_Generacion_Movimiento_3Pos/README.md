# 📐 01 · Generación de Movimiento de 3 Posiciones / 3-Position Motion Generation

**ES** Programa en Python que sintetiza mecanismos de 4 barras (dos díadas, izquierda y derecha) capaces de llevar un cuerpo rígido (el acoplador) por **3 posiciones prescritas**. Barre los ángulos libres β₂ y β₃, descarta las soluciones inviables y ordena los mecanismos del mejor al peor ángulo de transmisión mínimo.

**EN** Python program that synthesizes four-bar mechanisms (two dyads, left and right) able to carry a rigid body (the coupler) through **3 prescribed positions**. It sweeps the free angles β₂ and β₃, discards infeasible solutions and ranks the mechanisms from best to worst minimum transmission angle.

---

## 📁 Archivos / Files

| Archivo / File | ES | EN |
|---|---|---|
| `main.py` | Punto de entrada. | Entry point. |
| `BarridoCinemático_4B.py` | Versión en español del barrido. Genera `mecanismos_sintetizados.txt`. | Spanish version of the sweep. Writes `mecanismos_sintetizados.txt`. |
| `KineSweep.py` | Versión en inglés del barrido. Genera `synthesized_mechanisms.txt`. | English version of the sweep. Writes `synthesized_mechanisms.txt`. |
| `mecanismos_sintetizados.txt` | Ejemplo de resultados (ranking). | Example output (ranking). |

> ⚠️ TODO: confirmar el rol de `main.py` y los comandos de ejecución de abajo / confirm the role of `main.py` and the run commands below.

---

## 🚀 Uso / Usage

```bash
pip install -r ../requirements.txt
python main.py
```

---

## 🔄 Cómo funciona / How it works

1. **Entradas / Inputs:** posiciones prescritas y rangos de β₂ y β₃ (ver abajo / see below).
2. **Barrido anidado / Nested sweep:** recorre β₂ y β₃ de la díada izquierda y, para cada combinación, los de la derecha.
   *Sweeps β₂ and β₃ of the left dyad and, for each combination, those of the right dyad.*
3. **Filtro β₃ / β₃ filter:** descarta el mecanismo si β₃ de ambas díadas supera 100° en valor absoluto. Así queda al menos una díada donde conectar después la díada motriz con un ángulo de transmisión mínimo > 40° en el submecanismo de 4 barras, sin que condicione el ángulo mínimo global del mecanismo de 6 barras.
   *Discards the mechanism if β₃ of both dyads exceeds 100° in absolute value. This leaves at least one dyad where the driving dyad can later be attached with a minimum transmission angle > 40° in the 4-bar submechanism, without constraining the overall minimum angle of the 6-bar mechanism.*
4. **Díadas / Dyads:** plantea las ecuaciones de díada y resuelve el sistema con el método de Cramer (longitudes y orientaciones de los eslabones).
   *Sets up the dyad equations and solves the system with Cramer's rule (link lengths and orientations).*
5. **Filtro de rama y circuito / Branch and circuit filter:** descarta mecanismos con defecto de rama o circuito mediante un método de orientación vectorial basado en el producto cruz de vectores.
   *Discards mechanisms with branch or circuit defects using a vector-orientation method based on the cross product.*
6. **Evaluación / Evaluation:** calcula el ángulo de transmisión μ en las posiciones extremas 1 y 3, con la manivela izquierda o la derecha como impulsora.
   *Computes the transmission angle μ at extreme positions 1 and 3, with either the left or the right crank as driver.*
7. **Ranking:** guarda los mecanismos ordenados del mejor al peor ángulo de transmisión mínimo (el más cercano a 90°).
   *Saves the mechanisms sorted from best to worst minimum transmission angle (closest to 90°).*

---

## 📥 Datos de entrada / Input data

### 1) Datos prescritos / Prescribed data

| Símbolo / Symbol | ES | EN | Ejemplo / Example |
|---|---|---|---|
| δ₂ | Desplazamiento (complejo) del punto de referencia, posición 1 → 2 | Complex displacement of the reference point, position 1 → 2 | `0.16221483 + 0.83457915j` |
| δ₃ | Ídem, posición 1 → 3 | Same, position 1 → 3 | `4.48839208 + 3.85019818j` |
| α₂ | Rotación del acoplador, posición 1 → 2 | Coupler rotation, position 1 → 2 | `2°` |
| α₃ | Rotación del acoplador, posición 1 → 3 | Coupler rotation, position 1 → 3 | `20°` |

En el código / In the code: `prescribed_data_list`.

### 2) Rangos de β₂ y β₃ / β₂ and β₃ ranges

**ES** Los rangos salen de graficar en CAD los círculos M que cruzan el área donde se ubican los pivotes fijos. Se define un rango de β₂ y, **para cada β₂**, un rango de β₃ con su límite inferior, su límite superior y su paso. Todos los ángulos están en grados.

**EN** The ranges come from drawing, in CAD, the M circles that cross the area where the fixed pivots can be placed. A range of β₂ is defined and, **for each β₂**, a range of β₃ with its lower limit, upper limit and step. All angles are in degrees.

| β₂ (°) | β₃ límite inferior / lower (°) | β₃ límite superior / upper (°) | Paso / Step (°) |
|---:|---:|---:|---:|
| −10.6 | −86 | −85.7 | 0.1 |
| −10.8 | −89 | −86.2 | 0.4 |
| −11.0 | −92.8 | −86.6 | 0.2 |
| −11.2 | −97 | −87 | 1 |

En el código / In the code: `beta_2_range`, `beta_3_ranges_by_beta_2`.

#### Subintervalos / Subintervals

**ES** Algunos β₂ no tienen un único rango continuo de β₃, sino **hasta 2 subintervalos**. En ese caso solo se recorren los subintervalos. Ejemplo, para β₂ = −11.2° (paso 1°):

**EN** Some β₂ values do not have a single continuous β₃ range but **up to 2 subintervals**. In that case only the subintervals are swept. Example, for β₂ = −11.2° (step 1°):

```text
β₃ ∈ [-97, -92]  ∪  [-88, -87]
```

> ⚠️ TODO: indicar en qué archivo y línea se editan estas entradas / state in which file and line these inputs are edited.

---

## 📤 Salida / Output

**ES** El programa escribe un archivo de texto con los mecanismos que funcionan, ordenados del mejor al peor. Cada fila trae los datos de ambas díadas y los ángulos de transmisión para las dos opciones de manivela. Cada mecanismo aparece dos veces, con las díadas izquierda y derecha intercambiadas (par espejo).

**EN** The program writes a text file with the mechanisms that work, sorted from best to worst. Each row lists the data of both dyads and the transmission angles for the two crank options. Each mechanism appears twice, with the left and right dyads swapped (mirrored pair).

| Columna / Column | Significado / Meaning |
|---|---|
| `β₂`, `β₃` (°) | Ángulos libres de cada díada / Free angles of each dyad |
| `w` (mm), `θ_w` (°) | Módulo y ángulo del vector W de la díada / Magnitude and angle of the dyad vector W |
| `z` (mm), `θ_z` (°) | Módulo y ángulo del vector Z de la díada / Magnitude and angle of the dyad vector Z |
| `μ₁`, `μ₃` (°) — **Left crank** | Ángulo de transmisión en las posiciones extremas 1 y 3 con la manivela izquierda / Transmission angle at extreme positions 1 and 3 with the left crank |
| `μ₁`, `μ₃` (°) — **Right crank** | Ídem con la manivela derecha / Same with the right crank |

Ejemplo (primera fila / first row):

```text
 β₂(L)    β₃(L)    w      θ_w      z      θ_z   | β₂(R)    β₃(R)    w      θ_w      z      θ_z   | μ₁(L)   μ₃(L)  | μ₁(R)   μ₃(R)
-11.000  -87.400  4.442  172.516  0.845  79.356 | -11.000  -86.600  4.474  172.909  0.712  94.565 | 36.689  36.711 | 37.082  35.518
```

**ES** En este problema, el mejor mecanismo tiene un ángulo de transmisión mínimo de 36–37°, algo por debajo del ideal de 40°–140°. Es el mejor posible con las 3 posiciones y el área disponible.

**EN** In this problem, the best mechanism has a minimum transmission angle of 36–37°, slightly below the ideal 40°–140°. It is the best possible with the 3 positions and the available area.

---

## ➡️ Siguiente etapa / Next stage

**ES** El programa sintetiza el submecanismo de 4 barras. El siguiente paso de diseño es instalar la díada motriz (cilindro hidráulico) para obtener un mecanismo de 6 barras (cadena Watt II). El filtro β₃ prepara esa etapa.

**EN** The program synthesizes the 4-bar submechanism. The next design step is to install the driving dyad (hydraulic cylinder) to obtain a 6-bar mechanism (Watt II chain). The β₃ filter prepares that stage.