> **Archivos fuente:**
> - `src/models/03_event_study.py` — implementación principal
> - `src/tesis_alcaldesas/models/event_study.py` — versión paquete
> - `src/tesis_alcaldesas/models/event_study_sensitivity.py` — análisis de sensibilidad
> - `src/models/utils.py` — definición de outcomes y carga de datos
>
> **Prerequisitos para entender este documento:**
> - `docs/08_DATASET_CONSTRUCCION.md` (cómo se construyó la muestra analítica)
> - `docs/09_MODELADO_PROPUESTA.md` §1–§4 (estrategia de identificación y ecuaciones)
> - `docs/10_EXPLICACION_MODELADO.md` §4 (supuesto de tendencias paralelas) y §9 (resumen breve)
> - **`docs/11_TABLA1_ESTADISTICAS_DESCRIPTIVAS.md`** (Tabla 1 — paso previo al event study)
>
> **Lecturas que profundizan después de este documento:**
> - `docs/15_EVENT_STUDY_SENSIBILIDAD.md` (sensibilidad del event study al bin extremo)
> - `docs/13_MODELADO_ECONOMETRICO.md` (implementación completa del pipeline econométrico)

# 12 — El Event Study: Tutorial Completo

---

## Tabla de contenidos

| Sección | Tema | Pregunta que responde |
|---------|------|----------------------|
| 1 | ¿En qué momento del pipeline entra el event study? | ¿Es lo primero que se hace? |
| 2 | ¿Qué es un event study? | Intuición desde cero |
| 3 | ¿Qué hipótesis prueba? | Pre-trends y tendencias paralelas |
| 4 | La anatomía del "tiempo relativo al evento" | ¿Qué es $k$, $g_i$, event_time? |
| 5 | La ecuación del event study, pieza por pieza | Desglose completo para principiantes |
| 6 | El periodo de referencia: ¿por qué $k = -1$? | Normalización e interpretación |
| 7 | Endpoint binning: ¿por qué agrupar los extremos? | Tratamiento de $k \leq -K$ y $k \geq L$ |
| 8 | Cómo leer un gráfico de event study | Guía visual paso a paso |
| 9 | El test formal de pre-trends | Test conjunto $\chi^2$ |
| 10 | Nuestra implementación concreta en Python | Línea por línea del código |
| 11 | ¿Qué pasa con los always-treated y never-treated? | Exclusiones y grupo de control |
| 12 | Los 5 outcomes primarios | ¿Qué estamos midiendo? |
| 13 | ¿Qué hacer según el resultado del event study? | Árbol de decisión |
| 14 | Limitaciones y debates actuales | Roth (2022), poder estadístico |
| 15 | Conexión con el resto del pipeline | ¿Qué viene después? |

---

## 1. ¿En qué momento del pipeline entra el event study?

### 1.1 El orden correcto

Cuando ya tienes tu **muestra analítica** (el panel limpio y listo para estimar), el
pipeline empírico sigue este orden:

```
 Muestra analítica                            ← 08_DATASET_CONSTRUCCION
       │
       ▼
 ┌──────────────────────┐
 │ PASO 1: Tabla 1      │ ← 11_TABLA1_ESTADISTICAS_DESCRIPTIVAS
 │ (Descriptivos)       │   ¿Cómo se ven los datos?
 └──────────┬───────────┘   ¿Están balanceados T vs C?
            │
            ▼
 ┌──────────────────────┐
 │ PASO 2: EVENT STUDY  │ ← 🔎 ESTÁS AQUÍ
 │ (Diagnóstico)        │   ¿Es creíble el DiD?
 └──────────┬───────────┘
            │
       ¿Pre-trends planos?
       ╱                ╲
     Sí                  No
      │                   │
      ▼                   ▼
 ┌──────────┐    ┌─────────────────┐
 │ PASO 3:  │    │ PARAR y revisar │
 │ TWFE    │    │ la estrategia   │
 └──────────┘    └─────────────────┘
```

### 1.2 ¿Por qué NO es lo primero?

Porque antes del event study necesitas confirmar que tus datos son razonables.
Eso es exactamente lo que hace la **Tabla 1** — el paso previo que se documenta
en detalle en `docs/11_TABLA1_ESTADISTICAS_DESCRIPTIVAS.md`.

En resumen, la Tabla 1 confirmó que:
- Los 5 outcomes tienen medias razonables y sin anomalías
- Los switchers (pre) son ~10-25% más altos que los never-treated (explicable por
  mayor urbanización)
- Los always-treated (101 muni) se excluirán del event study
- Créditos hipotecarios tienen media baja → precaución al interpretar

Con ese diagnóstico hecho, podemos proceder al event study con confianza en los datos.

### 1.3 ¿Por qué SÍ es lo primero *analítico*?

Porque el event study es la **prueba de credibilidad** de toda tu estrategia de
identificación. Si los coeficientes pre-tratamiento NO son cercanos a cero, el
supuesto de tendencias paralelas no se sostiene, y todo el análisis DiD pierde fuerza.

> **Analogía:** La Tabla 1 es el examen médico de rutina
> (ver `docs/11_TABLA1_ESTADISTICAS_DESCRIPTIVAS.md`).
> El event study es la prueba de sangre específica que
> determina si puedes proceder con la operación (el DiD).

---

## 2. ¿Qué es un event study?

### 2.1 Intuición desde cero

Imagina que quieres saber si poner una alcaldesa en un municipio *cambia* la inclusión
financiera de las mujeres. Tienes dos enfoques:

**Enfoque A — DiD estándar (un solo número):**
> "En promedio, los municipios con alcaldesa tienen 0.27 unidades más de saldo
> per cápita que los que no."

Esto te da **un número** ($\beta$), pero no te dice:
- ¿Ya había diferencias *antes* de que llegara la alcaldesa?
- ¿El efecto fue inmediato o tardó en aparecer?
- ¿El efecto crece con el tiempo o se desvanece?

**Enfoque B — Event study (una película):**
> "3 trimestres antes de la alcaldesa: sin diferencia. 2 trimestres antes: sin
> diferencia. 1 trimestre antes: sin diferencia. Trimestre de llegada: +0.05.
> Un trimestre después: +0.12. Dos trimestres después: +0.20..."

Esto te da **una serie de números** ($\mu_{-3}, \mu_{-2}, \mu_0, \mu_1, \mu_2, \ldots$),
uno para cada periodo relativo al "evento" (la llegada de la alcaldesa).

### 2.2 Definición formal

Un **event study** (estudio de eventos) es una extensión del modelo de diferencias en
diferencias que estima **coeficientes separados para cada periodo relativo al
tratamiento**, en lugar de un solo coeficiente promedio.

En vez de estimar:

$$
Y_{it} = \alpha_i + \gamma_t + \beta \cdot D_{it} + \varepsilon_{it}
$$

estimamos:

$$
Y_{it} = \alpha_i + \gamma_t + \sum_{k \neq -1} \mu_k \cdot \mathbf{1}\{t - g_i = k\} + \varepsilon_{it}
$$

donde cada $\mu_k$ captura el efecto en el periodo $k$ relativo al tratamiento.

### 2.3 ¿Cuál es la diferencia clave con el DiD?

| | DiD estándar | Event study |
|---|---|---|
| **Qué estima** | Un coeficiente $\beta$ | Múltiples coeficientes $\mu_k$ |
| **Información temporal** | Efecto promedio | Efecto periodo por periodo |
| **Valida supuestos** | No directamente | Sí (tendencias paralelas) |
| **Output visual** | Un número | Un gráfico (los famosos "puntos con bigotes") |
| **Relación** | Es un caso particular | Es la versión generalizada |

> **Punto clave:** Si todos los $\mu_k$ post-tratamiento se promediaran con los pesos
> correctos, recuperarías algo cercano al $\beta$ del DiD estándar. El event study
> simplemente "desempaca" ese promedio periodo por periodo.

---

## 3. ¿Qué hipótesis prueba?

### 3.1 La hipótesis nula del event study

El event study prueba **dos hipótesis implícitas**:

**Hipótesis 1 — Pre-trends (la más importante):**

$$
H_0: \mu_k = 0 \quad \forall \; k < 0
$$

> "No hay diferencia sistemática entre tratados y controles *antes* del tratamiento."

Si esto se rechaza, significa que los grupos ya divergían antes de que la alcaldesa
llegara al poder. Si los grupos ya eran diferentes, no puedes atribuir ningún cambio
posterior a la alcaldesa — podría ser una continuación de la tendencia preexistente.

**Hipótesis 2 — Efecto post-tratamiento:**

$$
H_1: \exists \; k \geq 0 \text{ tal que } \mu_k \neq 0
$$

> "El tratamiento sí tiene un efecto en algún periodo posterior."

### 3.2 ¿Qué es el supuesto de tendencias paralelas?

El supuesto central de todo DiD es:

> En ausencia de tratamiento, el grupo tratado habría seguido la misma trayectoria
> que el grupo de control.

Esto es un **contrafactual** — no lo podemos observar directamente porque, por
definición, los tratados sí recibieron tratamiento. Pero podemos hacer una prueba
indirecta: si las trayectorias eran paralelas *antes* del tratamiento, es razonable
suponer que lo habrían seguido siendo.

```
Variable Y
    │
    │          Tratados (observado)
    │         ╱
    │     ●──●──●──●
    │    ╱           ╲──── Efecto real
    │   ╱             ╲
    │  ●                ●──●──●  Tratados (contrafactual)
    │ ╱                 ╱
    │╱          ●──●──●──●──●──●  Control (observado)
    │──────────────────────────────── tiempo
                   ↑
              tratamiento
```

**El event study verifica esto empíricamente:** si $\mu_{-4}, \mu_{-3}, \mu_{-2}$ son
todos cercanos a cero y no significativos, las trayectorias eran paralelas antes.

### 3.3 ¿Qué NO prueba el event study?

Es importante entender los límites:

1. **No prueba que las tendencias paralelas se cumplan en el futuro.** Solo muestra
   que se cumplían en el pasado. Es una condición necesaria pero no suficiente.

2. **No prueba causalidad por sí solo.** La causalidad viene del diseño completo
   (DiD + el supuesto de que no hay anticipación). El event study solo valida una parte
   del diseño.

3. **No es inmune a problemas de poder estadístico.** Un pre-trend "no significativo"
   podría simplemente ser un efecto que no tenemos poder para detectar (ver Sección 14).

---

## 4. La anatomía del "tiempo relativo al evento"

### 4.1 ¿Qué es $g_i$ (cohorte de tratamiento)?

$g_i$ es el **primer periodo** en que el municipio $i$ recibe tratamiento. En nuestra
tesis:

$$
g_i = \text{primer trimestre en que } \texttt{alcaldesa\_final}_i = 1
$$

Ejemplos:

| Municipio | $g_i$ | Significado |
|-----------|-------|-------------|
| Aguascalientes (001) | 2018Q3 | Alcaldesa desde el inicio del panel |
| Calvillo (003) | 2021Q4 | Primera alcaldesa en el ciclo 2021 |
| Cosío (004) | $\infty$ (never-treated) | Nunca tuvo alcaldesa |

> En el código, $g_i$ se almacena como `first_treat_t` — un índice numérico (0, 1, 2, ...)
> que mapea al trimestre calendario.

### 4.2 ¿Qué es $k$ (event time)?

$k$ es el **tiempo relativo al evento** para cada municipio-periodo:

$$
k_{it} = t - g_i
$$

| Valor de $k$ | Significado | Ejemplo |
|---------------|-------------|---------|
| $k = -4$ | 4 periodos antes del tratamiento | Calvillo en 2020Q4 ($g = 2021$Q4) |
| $k = -1$ | 1 periodo antes (referencia) | Calvillo en 2021Q3 |
| $k = 0$ | Periodo del tratamiento | Calvillo en 2021Q4 |
| $k = +3$ | 3 periodos después | Calvillo en 2022Q3 |
| $k = \text{NaN}$ | Never-treated (sin evento) | Cosío en cualquier periodo |

### 4.3 ¿Por qué el event time es relativo y no absoluto?

Porque los municipios reciben tratamiento en **momentos diferentes** (tratamiento
escalonado). El event time "re-centra" a todos los municipios para que $k = 0$
sea el momento del tratamiento *para cada uno*.

```
Tiempo absoluto:    2018Q3  2018Q4  2019Q1  2019Q2  2019Q3  2019Q4
                    ------  ------  ------  ------  ------  ------
Municipio A (g=Q4):   -1      0      +1      +2      +3      +4
Municipio B (g=Q2):   -3     -2      -1       0      +1      +2
                                              ↑       ↑
                                        B llega    A ya llevaba
                                        al poder   2 trimestres
```

Al alinear por event time, podemos comparar "qué pasa 2 periodos después del
tratamiento" para ambos municipios, aunque en calendario uno fue en 2019Q2 y
otro en 2019Q1.

### 4.4 ¿Cómo se construye en nuestros datos?

En el código (`src/models/03_event_study.py`), el event time ya viene precalculado
en el panel como la columna `event_time`:

```python
# event_time = t_index - first_treat_t
# Para never-treated: event_time = NaN
```

Esto se calcula en el pipeline de construcción del dataset
(`src/tesis_alcaldesas/data/build_panel.py`).

---

## 5. La ecuación del event study, pieza por pieza

### 5.1 La ecuación completa

$$
Y_{it} = \alpha_i + \gamma_t + \sum_{\substack{k = -K \\ k \neq -1}}^{L} \mu_k \cdot \mathbf{1}\{t - g_i = k\} + \delta \cdot \log\_\text{pob}_{it} + \varepsilon_{it}
$$

### 5.2 Desglose término por término

#### $Y_{it}$ — Variable dependiente

Es el outcome de inclusión financiera para el municipio $i$ en el trimestre $t$.

En nuestra tesis, usamos la transformación **asinh per cápita**:

$$
Y_{it} = \text{asinh}\left(\frac{\text{Variable original}_{it}}{\text{Población}_{it}}\right)
$$

¿Por qué asinh? Porque muchos municipios tienen valores de cero (no tienen créditos
hipotecarios, por ejemplo), y el logaritmo natural no está definido para cero. La
función asinh se comporta como logaritmo para valores grandes pero acepta ceros.

> **En el código:** Las columnas se llaman `{outcome}_pc_asinh`, por ejemplo
> `saldocont_total_m_pc_asinh`.

#### $\alpha_i$ — Efectos fijos de municipio

Capturan todo lo que es **permanente** en cada municipio: geografía, cultura,
infraestructura bancaria histórica, etc. Con efectos fijos de municipio, estamos
comparando cada municipio **consigo mismo** a lo largo del tiempo.

> **En el código:** `entity_effects=True` en `PanelOLS`.

#### $\gamma_t$ — Efectos fijos de tiempo

Capturan todo lo que afecta a **todos** los municipios en un trimestre dado: inflación,
política monetaria del Banco de México, COVID-19, reformas financieras nacionales, etc.

> **En el código:** `time_effects=True` en `PanelOLS`.

#### $\mathbf{1}\{t - g_i = k\}$ — Indicadores de event time

Estas son **variables dummy** (indicadoras). Para cada valor de $k$ (excepto $k = -1$),
se crea una columna que vale:

$$
\mathbf{1}\{t - g_i = k\} = \begin{cases} 1 & \text{si el municipio } i \text{ está exactamente } k \text{ periodos del tratamiento en } t \\ 0 & \text{en caso contrario} \end{cases}
$$

**Ejemplo para un municipio con $g_i = 5$ (trimestre 5):**

| $t$ | $k = t - g_i$ | $\mathbf{1}\{k=-3\}$ | $\mathbf{1}\{k=-2\}$ | $\mathbf{1}\{k=0\}$ | $\mathbf{1}\{k=+1\}$ |
|-----|----------------|-----------------------|-----------------------|----------------------|-----------------------|
| 2 | -3 | 1 | 0 | 0 | 0 |
| 3 | -2 | 0 | 1 | 0 | 0 |
| 4 | -1 | *omitida (referencia)* | | | |
| 5 | 0 | 0 | 0 | 1 | 0 |
| 6 | +1 | 0 | 0 | 0 | 1 |

Para **never-treated** (sin alcaldesa nunca), $g_i = \infty$, así que $k$ no está
definido → todas las dummies valen 0. Esto los convierte automáticamente en el
**grupo de control**.

#### $\mu_k$ — Los coeficientes de interés

Cada $\mu_k$ mide la diferencia en la variable dependiente entre tratados y controles
en el periodo $k$ relativo al tratamiento, **comparado con el periodo de referencia**
$k = -1$.

**Interpretación según la zona:**

| Zona | Coeficientes | Interpretación |
|------|-------------|----------------|
| Pre-tratamiento | $\mu_{-K}, \ldots, \mu_{-2}$ | ¿Había diferencias antes del tratamiento? Deberían ser ≈ 0 |
| Referencia | $\mu_{-1} = 0$ | Normalizado por construcción |
| Post-tratamiento | $\mu_0, \mu_1, \ldots, \mu_L$ | ¿Cuánto cambió después del tratamiento? |

#### $\delta \cdot \log\text{pob}_{it}$ — Control de población

Controla por el tamaño del municipio. Aunque las variables ya están per cápita,
municipios más grandes pueden tener dinámicas de inclusión financiera diferentes
(más sucursales bancarias, más competencia, etc.).

> **En el código:** `exog = dummy_cols + ["log_pob"]`

#### $\varepsilon_{it}$ — Término de error

El error se clusteriza a nivel de municipio para permitir correlación serial
(las observaciones de un mismo municipio a lo largo del tiempo están correlacionadas):

> **En el código:** `res = mod.fit(cov_type="clustered", cluster_entity=True)`

---

## 6. El periodo de referencia: ¿por qué $k = -1$?

### 6.1 ¿Qué significa normalizar?

Cuando incluimos dummies para todos los $k$ excepto uno, estamos diciendo:
"todos los coeficientes se interpretan *en comparación con* el periodo omitido."

Si $\mu_{-1} = 0$ (por construcción), entonces:
- $\mu_{-3} = 0.02$ significa "en $k = -3$, la diferencia era 0.02 unidades *mayor*
  que en $k = -1$"
- $\mu_{+2} = 0.15$ significa "en $k = +2$, la diferencia es 0.15 unidades *mayor*
  que en $k = -1$"

### 6.2 ¿Por qué $k = -1$ y no otro?

| Alternativa | Problema |
|-------------|----------|
| $k = 0$ | Es el primer periodo con tratamiento — ya tiene efecto, no es "limpio" |
| $k = -3$ | Desperdicias información — pierdes la capacidad de ver si $k = -2$ y $k = -1$ ya tenían diferencias |
| $k = -1$ | **Óptimo**: es el último periodo "limpio" antes del tratamiento. Si ahí hay diferencia → hay anticipación |

> **Estándar en la literatura:** Prácticamente toda la literatura de event studies
> usa $k = -1$ como referencia (Freyaldenhoven et al. 2019, Sun & Abraham 2021,
> Roth et al. 2023).

### 6.3 ¿Es lo mismo `REF_K = -1` en el código?

Sí. En `03_event_study.py`:

```python
REF_K = -1  # reference period

# Cuando se generan las dummies:
for k in range(min_k, max_k + 1):
    if k == REF_K:           # ← Se salta k=-1
        continue
    # ... crea dummy para todos los demás k
```

Además, al final se agrega manualmente el punto de referencia como $(k = -1, \mu = 0)$
para que aparezca en el gráfico:

```python
coefs.append({
    "k": REF_K,
    "coef": 0.0,    # ← Normalizado a cero
    "se": 0.0,
    "pval": 1.0,
    ...
})
```

---

## 7. Endpoint binning: ¿por qué agrupar los extremos?

### 7.1 El problema de los extremos

Nuestro panel tiene 17 trimestres. Un municipio tratado en el trimestre 10 tiene:
- 9 periodos pre-tratamiento ($k = -9$ a $k = -1$)
- 7 periodos post-tratamiento ($k = 0$ a $k = 7$)

Pero un municipio tratado en el trimestre 2 solo tiene:
- 1 periodo pre ($k = -1$)
- 15 periodos post ($k = 0$ a $k = 15$)

Si creamos dummies para todos los $k$ posibles (de $-16$ a $+16$), tendríamos 32
dummies y muchas estarían casi vacías (pocas observaciones en los extremos).

### 7.2 La solución: binning

**Endpoint binning** agrupa todos los periodos extremos en un solo "bin":

$$
\text{evt\_k\_le}{-K} = \mathbf{1}\{k \leq -K\} \quad \text{(bin izquierdo)}
$$
$$
\text{evt\_k\_ge}{+L} = \mathbf{1}\{k \geq +L\} \quad \text{(bin derecho)}
$$

En nuestra tesis: $K = 4$, $L = 8$, así que:

| Dummy | Agrupa | Nombre en código |
|-------|--------|------------------|
| Bin izquierdo | $k \leq -4$ | `evt_k_le-4` |
| Individuales | $k = -3, -2, 0, 1, 2, 3, 4, 5, 6, 7$ | `evt_k-3`, `evt_k-2`, `evt_k+0`, etc. |
| Referencia | $k = -1$ (omitida) | — |
| Bin derecho | $k \geq 8$ | `evt_k_ge8` |

**Total de dummies:** 12 (frente a potencialmente 32 sin binning)

### 7.3 ¿Cómo se implementa en el código?

```python
# En build_event_dummies():
min_k = -K_LEADS     # -4
max_k = L_LAGS       #  8

# Recortar extremos
df["evt_binned"] = df["event_time"].copy()
df.loc[df["evt_binned"] < min_k, "evt_binned"] = min_k   # k=-5,-6,... → -4
df.loc[df["evt_binned"] > max_k, "evt_binned"] = max_k   # k=9,10,...  → 8

# Nombrar las dummies
for k in range(min_k, max_k + 1):
    if k == REF_K:
        continue
    col = f"evt_k{k:+d}" if k != min_k and k != max_k else (
        f"evt_k_le{min_k}" if k == min_k else f"evt_k_ge{max_k}"
    )
```

### 7.4 ¿Es problemático el binning?

El bin extremo $k \leq -4$ mezcla municipios con distinta "profundidad" pretratamiento.
Esto puede crear ruido. Si el test de pre-trends está borderline (como pasó con
`numtar_cred_m`, p = 0.083), una estrategia es variar el binning (ver
`docs/15_EVENT_STUDY_SENSIBILIDAD.md`).

---

## 8. Cómo leer un gráfico de event study

### 8.1 Anatomía del gráfico

```
    μ_k (coeficiente)
     |
     |                                    ● ← Bin k≥8
+0.08|                              ●   /   (efecto acumulado)
     |                         ●   / ●
+0.04|                    ●   /        ← Efecto creciente
     |               ●   /               post-tratamiento
     |              / ●
   0 |----●----●--●----|--●----|----|----|--→
     |   ↑              |
     |   bin k≤-4       |   ← Línea vertical roja:
     |                  |     momento del tratamiento
-0.04|                  |
     |                  |
     k:  ≤-4  -3  -2  -1   0   +1  +2   ≥8

     ←── PRE-tratamiento ──→←── POST-tratamiento ──→

     ── línea de coeficientes (puntos)
     ░░ banda de confianza al 95% (área sombreada)
     ── línea horizontal en y=0 (referencia)
     ¦  línea vertical en k=-0.5 (separador pre/post)
```

### 8.2 Los 5 elementos del gráfico

| Elemento | Qué es | Qué buscamos |
|----------|--------|---------------|
| **Puntos ($\bullet$)** | Coeficientes $\mu_k$ estimados | La trayectoria del efecto |
| **Banda sombreada** | Intervalo de confianza al 95% | Si incluye 0 → no significativo |
| **Línea horizontal en 0** | "No hay efecto" | Los pre-trends deben estar cerca |
| **Línea vertical roja** | Momento del tratamiento ($k = -0.5$) | Separa diagnóstico de resultados |
| **Anotación** | p-value del test conjunto de pre-trends | $p > 0.10$ → tendencias paralelas OK |

### 8.3 ¿Cómo interpretar cada zona?

#### Zona pre-tratamiento ($k < -1$)

**Lo que esperamos:** Todos los coeficientes estadísticamente iguales a cero (la banda
de confianza cruza la línea horizontal en 0).

**Lo que significaría si NO se cumple:**
- Si hay una tendencia ascendente → los tratados ya estaban mejorando antes → sesgo
  positivo en el DiD
- Si hay una tendencia descendente → los tratados ya estaban empeorando antes → sesgo
  negativo en el DiD
- Si hay un "salto" en un solo periodo → posible shock confusor o error en los datos

#### Zona del tratamiento ($k = 0$)

**Lo que esperamos (si hay efecto):** Un salto positivo (o negativo).

**En nuestra tesis:** Esperamos $\mu_0 > 0$ para outcomes de inclusión financiera
— la alcaldesa empieza a tener efecto inmediatamente o en los periodos siguientes.

#### Zona post-tratamiento ($k > 0$)

**Patrones comunes y su interpretación:**

| Patrón | Significado |
|--------|-------------|
| $\mu_0 < \mu_1 < \mu_2 < \cdots$ (creciente) | El efecto se acumula con el tiempo |
| $\mu_0 \approx \mu_1 \approx \mu_2$ (plano) | El efecto es constante |
| $\mu_0 > \mu_1 > \mu_2 \to 0$ (decreciente) | El efecto se diluye |
| $\mu_0 = 0, \mu_1 = 0, \ldots, \mu_3 > 0$ (retardado) | El efecto tarda en materializarse |

### 8.4 Ejemplo con nuestros datos

Para **saldo total** (`saldocont_total_m`), el event study muestra:
- $k \leq -1$: coeficientes no significativos (pre-trends planos ✅)
- $k = 0$: efecto pequeño y no significativo (el efecto no es instantáneo)
- $k \geq 1$: coeficientes crecientes y significativos (el efecto se acumula)

Esto es consistente con la teoría: una alcaldesa no cambia la inclusión financiera
de la noche a la mañana. Toma tiempo implementar políticas, que se abran sucursales,
que las mujeres accedan a servicios financieros.

---

## 9. El test formal de pre-trends

### 9.1 ¿Por qué no basta con "mirar el gráfico"?

Porque el ojo humano es subjetivo. Un coeficiente de -0.02 con un intervalo de
confianza de [-0.06, +0.02] puede "verse" como cero... pero ¿lo es *estadísticamente*?

Necesitamos un **test formal** que evalúe todos los coeficientes pre-tratamiento
conjuntamente.

### 9.2 El test conjunto $\chi^2$ (Wald test)

La hipótesis nula es:

$$
H_0: \mu_{-K} = \mu_{-3} = \mu_{-2} = 0
$$

(Recuerda: $\mu_{-1} = 0$ por normalización, así que no se incluye en el test.)

El estadístico de prueba es:

$$
\chi^2 = \hat{\boldsymbol{\mu}}_{\text{pre}}' \; \hat{\mathbf{V}}_{\text{pre}}^{-1} \; \hat{\boldsymbol{\mu}}_{\text{pre}}
$$

donde:
- $\hat{\boldsymbol{\mu}}_{\text{pre}} = (\hat{\mu}_{-K}, \hat{\mu}_{-3}, \hat{\mu}_{-2})'$ es el vector de coeficientes pre-tratamiento estimados
- $\hat{\mathbf{V}}_{\text{pre}}$ es la submatriz de varianza-covarianza de esos coeficientes

Bajo $H_0$, este estadístico sigue una distribución $\chi^2$ con $q$ grados de libertad,
donde $q$ es el número de restricciones (= número de coeficientes pre, típicamente 3 en
nuestro caso: $k = -4, -3, -2$).

### 9.3 Implementación en el código

```python
# En run_event_study():

# 1. Identificar columnas pre-tratamiento
pre_cols = [c for c in dummy_cols if any(
    c.endswith(f"k{kk:+d}") for kk in range(-K_LEADS, 0) if kk != REF_K
) or "_le" in c]
# Resultado: ['evt_k_le-4', 'evt_k-3', 'evt_k-2']

# 2. Extraer coeficientes y varianza-covarianza
pre_coefs = np.array([res.params[c] for c in pre_cols])
vcov = res.cov.loc[pre_cols, pre_cols].values

# 3. Calcular estadístico chi-cuadrado
chi2_stat = pre_coefs @ np.linalg.solve(vcov, pre_coefs)

# 4. Calcular p-value
chi2_pval = 1 - stats.chi2.cdf(chi2_stat, df=len(pre_cols))
```

### 9.4 ¿Cómo interpretar el p-value?

| p-value | Interpretación | Acción |
|---------|---------------|--------|
| $p > 0.10$ | No se rechaza $H_0$ → pre-trends planos | ✅ Proceder con DiD |
| $0.05 < p \leq 0.10$ | Borderline → posible señal débil | ⚠️ Reportar, hacer sensibilidad |
| $p \leq 0.05$ | Se rechaza $H_0$ → pre-trends no planos | ❌ Revisar especificación |

### 9.5 Nuestros resultados

| Outcome | $\chi^2$ | p-value | Restricciones | ¿Pasa? |
|---------|----------|---------|---------------|--------|
| Contratos totales (`ncont_total_m`) | 5.491 | 0.139 | 3 | ✅ Sí |
| Tarjetas débito (`numtar_deb_m`) | — | > 0.10 | 3 | ✅ Sí |
| Tarjetas crédito (`numtar_cred_m`) | 6.671 | 0.083 | 3 | ⚠️ Borderline |
| Créditos hipotecarios (`numcontcred_hip_m`) | — | > 0.10 | 3 | ✅ Sí |
| Saldo total (`saldocont_total_m`) | — | > 0.10 | 3 | ✅ Sí |

> **Nota sobre tarjetas de crédito:** El p = 0.083 borderline se analiza en detalle
> en `docs/15_EVENT_STUDY_SENSIBILIDAD.md`. Al cambiar la ventana a K=6 leads
> (reduciendo el efecto del binning), el p-value sube a 0.212. Conclusión: el valor
> borderline viene de la acumulación heterogénea en el bin $k \leq -4$, no de una
> violación real de tendencias paralelas.

---

## 10. Nuestra implementación concreta en Python

### 10.1 Estructura de archivos

| Archivo | Función | Cuándo se ejecuta |
|---------|---------|-------------------|
| `src/models/03_event_study.py` | Event study principal (5 outcomes) | Paso 3 del pipeline |
| `src/models/utils.py` | Definiciones: outcomes, carga de datos, helpers | Importado por todos |
| `src/tesis_alcaldesas/models/event_study.py` | Versión paquete (idéntica) | Cuando se instala con `pip install -e .` |
| `src/tesis_alcaldesas/models/event_study_sensitivity.py` | Sensibilidad K=3/K=6 | Paso de robustez |

### 10.2 Flujo completo paso a paso

```python
# ==========================================
# PASO 1: Cargar el panel analítico
# ==========================================
df = load_panel()
# → DataFrame con ~41,905 filas (2,471 muni × 17 trimestres)
# → Índice: (cve_mun, t_index)
# → Columnas clave: event_time, cohort_type, first_treat_t, alcaldesa_final

# ==========================================
# PASO 2: Construir dummies de event time
# ==========================================
df_es, dummy_cols = build_event_dummies(df)
# → Excluye always-treated (394 municipios sin pre-período)
# → Crea 12 dummies: evt_k_le-4, evt_k-3, evt_k-2, evt_k+0, ..., evt_k+7, evt_k_ge8
# → Never-treated tienen todas las dummies = 0 (grupo de control)

# ==========================================
# PASO 3: Estimar para cada outcome
# ==========================================
for out_name in PRIMARY_5:
    depvar = f"{out_name}_pc_asinh"
    res = run_event_study(df_es, depvar, dummy_cols)
    # → res["coefs"]: DataFrame con k, coef, se, pval, ci_lo, ci_hi
    # → res["pretrend"]: dict con chi2_stat, chi2_pval
    # → res["nobs"]: número de observaciones efectivas
    # → res["r2w"]: R² within

# ==========================================
# PASO 4: Graficar
# ==========================================
plot_event_study(all_results, OUT / "figura_1_event_study.pdf")
# → Panel 2×3 con los 5 outcomes + celdas vacías
# → Cada subplot: puntos + banda IC + línea cero + línea roja + anotación p-value
```

### 10.3 Anatomía de `build_event_dummies()`

Esta función es el corazón del event study. Veamos qué hace, línea por línea:

```python
def build_event_dummies(df):
    df = df.copy()                          # No modificar el original

    min_k = -K_LEADS     # -4              # Límite izquierdo
    max_k = L_LAGS       #  8              # Límite derecho

    # --- Binning ---
    df["evt_binned"] = df["event_time"].copy()
    df.loc[df["evt_binned"] < min_k, "evt_binned"] = min_k   # k=-5,-6 → -4
    df.loc[df["evt_binned"] > max_k, "evt_binned"] = max_k   # k=9,10  → +8

    # --- Exclusión de always-treated ---
    df = df[df["cohort_type"] != "always-treated"].copy()
    # Estos 394 muni no tienen pre-período → no contribuyen al event study

    # --- Creación de dummies ---
    dummy_cols = []
    for k in range(min_k, max_k + 1):    # k = -4, -3, -2, -1, 0, ..., 8
        if k == REF_K:                     # Saltar k=-1 (referencia)
            continue

        # Naming: bins extremos tienen nombre especial
        col = f"evt_k{k:+d}" if k != min_k and k != max_k else (
            f"evt_k_le{min_k}" if k == min_k else f"evt_k_ge{max_k}"
        )

        # Dummy = 1 si (evt_binned == k) AND (no es NaN)
        # Para never-treated: evt_binned es NaN → dummy = 0 ✓
        df[col] = ((df["evt_binned"] == k) & df["evt_binned"].notna()).astype(float)
        dummy_cols.append(col)

    return df, dummy_cols
```

### 10.4 Anatomía de `run_event_study()`

```python
def run_event_study(df, depvar, dummy_cols):
    # Variables explicativas: 12 dummies + log_pob
    exog = dummy_cols + ["log_pob"]

    # Eliminar filas con NaN en cualquier variable necesaria
    cols_needed = [depvar] + exog
    mask = df[cols_needed].notna().all(axis=1)
    sub = df.loc[mask].copy()

    # Estimar OLS con efectos fijos de municipio Y tiempo
    mod = PanelOLS(
        sub[depvar],           # Y (variable dependiente)
        sub[exog],             # X (dummies + control)
        entity_effects=True,   # α_i (efectos fijos de municipio)
        time_effects=True,     # γ_t (efectos fijos de tiempo)
        check_rank=False,      # No verificar rango (puede haber colinealidad menor)
    )

    # Errores estándar clustered por municipio
    res = mod.fit(cov_type="clustered", cluster_entity=True)

    # ... extracción de coeficientes y test de pre-trends (ver Sección 9.3)
```

### 10.5 Outputs generados

| Archivo | Descripción | Ubicación |
|---------|-------------|-----------|
| `figura_1_event_study.pdf` | Gráfico panel 2×3 con los 5 outcomes | `outputs/paper/` |
| `pretrends_tests.csv` | Tabla con $\chi^2$, p-value por outcome | `outputs/paper/` |
| `event_study_coefs_{outcome}.csv` | Coeficientes individuales por outcome | `outputs/paper/` |

### 10.7 Cómo leer `pretrends_tests.csv` — paso a paso

Este archivo contiene una fila por outcome con el resultado del test conjunto de
tendencias paralelas. Cada columna te dice algo específico:

| Columna | Significado | Cómo interpretarla |
|---------|------------|-------------------|
| `outcome` | El nombre de la variable dependiente | Identifica cuál de los 5 outcomes estás viendo |
| `chi2_stat` | Estadístico $\chi^2$ del test de Wald | Más alto = más evidencia *contra* tendencias paralelas. No tiene escala intuitiva — usa el p-valor |
| `chi2_pval` | p-valor del test conjunto | **La columna más importante.** Si $p > 0.10$, "pasa" el test: no hay evidencia de diferencias pre-tratamiento |
| `n_restrictions` | Grados de libertad del test | Número de coeficientes pre testeados ($K - 1 = 3$: los leads $k=-4, -3, -2$, omitiendo la referencia $k=-1$) |
| `pass_10pct` | ¿El p-valor supera 0.10? | "Yes" = las tendencias paralelas se sostienen a nivel 10%; "No" = hay una violación (al menos marginal) |
| `nobs` | Observaciones usadas en la regresión | 35,203 tras excluir always-treated y switchers left-censored |

**Ejemplo de lectura para saldo total:**
> $\chi^2 = 3.26$, $p = 0.353$ → "Con p = 0.353, **no rechazamos** la hipótesis nula
> de que los coeficientes pre-tratamiento ($k=-4, -3, -2$) son **conjuntamente cero**.
> Conclusión: no hay evidencia de tendencias diferenciales pre-tratamiento para el
> saldo total."

**¿Y si el p-valor es bajo (p < 0.10)?** Eso ocurre con tarjetas crédito ($p = 0.067$).
Significa que *hay alguna señal* en los leads — posiblemente los municipios que luego
tendrían alcaldesa ya mostraban diferencias en tarjetas de crédito antes del evento.
No invalida todo el análisis, pero exige cautela al interpretar ese outcome específico.

### 10.8 Cómo leer `figura_1_event_study.pdf` — guía visual paso a paso

El gráfico contiene **5 subpaneles** (uno por outcome), dispuestos en una cuadrícula 2×3.
Cada subpanel es un "event study plot" con la siguiente anatomía:

**Paso 1 — Identifica los ejes:**
- **Eje horizontal (x):** "Event time" $k$, o sea, trimestres relativos al tratamiento.
  $k = 0$ es el trimestre donde llega la primera alcaldesa. Los valores negativos
  ($k = -4, -3, -2$) son *antes* del tratamiento. Los positivos ($k = 0, +1, ..., +8$)
  son *después*.
- **Eje vertical (y):** El coeficiente $\mu_k$ estimado. Mide la diferencia en el
  outcome entre municipios tratados y de control, relativo al periodo de referencia
  ($k = -1$, que está normalizado a cero).

**Paso 2 — Encuentra la línea de referencia cero:**
- Hay una **línea horizontal punteada en $y = 0$**. Esto marca "sin efecto".
  Si un punto está sobre esta línea, el tratamiento no tiene efecto detectable en
  ese periodo.

**Paso 3 — Lee los coeficientes pre-tratamiento (izquierda de la línea roja):**
- Los puntos en $k = -4, -3, -2$ deberían estar **cerca de cero**. Si lo están,
  las tendencias paralelas se sostienen: antes de que llegara la alcaldesa, los
  tratados y controles evolucionaban igual.
- **Buena señal:** Puntos cercanos a cero, con intervalos de confianza que cruzan
  la línea $y = 0$.
- **Mala señal:** Puntos que se alejan sistemáticamente de cero, con tendencia
  ascendente o descendente — eso sugeriría que ya había diferencias previas.

**Paso 4 — Identifica la línea roja vertical en $k = 0$:**
- Esta marca el momento del tratamiento (primera alcaldesa).
- Todo lo que está a la izquierda es "pre" (debería ser ≈ 0).
- Todo lo que está a la derecha es "post" (aquí es donde buscamos el efecto).

**Paso 5 — Lee los coeficientes post-tratamiento (derecha de la línea roja):**
- Si los puntos **saltan hacia arriba** después de $k = 0$, hay un efecto positivo.
- Si los puntos **suben gradualmente**, el efecto se acumula con el tiempo.
- Si **permanecen cerca de cero**, no hay efecto detectable (esto es lo que ocurre
  con tarjetas de débito, crédito e hipotecarios).

**Paso 6 — Lee los intervalos de confianza (las bandas o "bigotes"):**
- Cada punto tiene una **banda vertical** que representa el IC al 95%.
- Si la banda **cruza la línea $y = 0$**, el coeficiente es *no significativo* en
  ese periodo individual.
- Si la banda queda **completamente por arriba de cero**, el efecto es *positivo
  y significativo* en ese periodo.

**Paso 7 — Lee la anotación del test de pre-trends:**
- En la esquina del subpanel aparece "Pre-trend p = X.XX".
- Si $p > 0.10$: los coeficientes pre son conjuntamente no significativos → ✅
- Si $p < 0.10$: hay una violación marginal → ⚠️ (como tarjetas crédito, $p=0.067$)

**¿Qué buscamos en nuestros resultados?**

| Outcome | Pre-trends | Post-treatment | Conclusión |
|---------|-----------|---------------|-----------|
| **Contratos totales** | ≈ 0 ✅ | ≈ 0 | Sin efecto detectable en TWFE event study |
| **Tarjetas débito** | ≈ 0 ✅ | ≈ 0 | Sin efecto |
| **Tarjetas crédito** | $k=-4$ algo negativo ⚠️ | ≈ 0 | Borderline pre-trend; sin efecto post |
| **Créditos hipotecarios** | ≈ 0 ✅ | ≈ 0 | Sin efecto |
| **Saldo total** | ≈ 0 ✅ | ≈ 0 | Sin efecto detectable en TWFE event study |

> **Nota importante:** La Figura 1 es el event study *TWFE*, que corre sobre la
> muestra completa. Se recomienda como extensión futura implementar un event study
> dentro del diseño Stacked DiD (ver `docs/10_EXPLICACION_MODELADO.md` §11) para
> verificar si las comparaciones contaminadas afectan los coeficientes.

### 10.6 Ejecución

```bash
# Desde la raíz del proyecto:
python -m tesis_alcaldesas.models.event_study

# O directamente:
python src/models/03_event_study.py
```

---

## 11. ¿Qué pasa con los always-treated y never-treated?

### 11.1 Always-treated (394 municipios)

Son los municipios que tenían alcaldesa desde el primer trimestre del panel (2018Q3).
Para ellos, $g_i = 0$ (trimestre 0) y **no existe periodo pre-tratamiento**.

- **Problema:** Sin periodos pre, las dummies $k = -4, -3, -2$ nunca valen 1 para
  estos municipios. No contribuyen al diagnóstico de pre-trends.
- **Solución:** Se excluyen del event study (`df["cohort_type"] != "always-treated"`).
- **¿Se pierden para siempre?** No. Vuelven a incluirse en los modelos TWFE y Stacked
  DiD, donde contribuyen a la estimación del efecto promedio.

### 11.2 Never-treated (1,577 municipios)

Son los municipios que nunca tuvieron alcaldesa en todo el panel. Para ellos,
$g_i = \infty$ y `event_time = NaN`.

- **Rol:** Forman el **grupo de control implícito**. Como todas sus dummies de event
  time son 0, definen la "línea base" contra la cual se miden los coeficientes $\mu_k$.
- **¿Se incluyen en la regresión?** Sí. Sus observaciones entran con todas las dummies
  en 0, lo que ayuda a identificar los efectos fijos de tiempo ($\gamma_t$) y
  proporciona el contrafactual.

### 11.3 Resumen de participación

| Grupo | N municipios | ¿En event study? | ¿En TWFE? |
|-------|-------------|-------------------|-----------|-------------------|
| Always-treated | 394 | ❌ Excluidos | ✅ |
| Switchers | 500 | ✅ (generan dummies) | ✅ |
| Never-treated | 1,577 | ✅ (grupo control) | ✅ |

---

## 12. Los 5 outcomes primarios

### 12.1 ¿Qué estamos midiendo?

El event study se corre 5 veces, una por cada variable dependiente de inclusión
financiera femenina:

| # | Variable original | Código | ¿Qué mide? |
|---|-------------------|--------|-------------|
| 1 | `ncont_total_m` | Contratos totales (mujeres) | Número de contratos bancarios per cápita |
| 2 | `numtar_deb_m` | Tarjetas de débito (mujeres) | Número de tarjetas de débito per cápita |
| 3 | `numtar_cred_m` | Tarjetas de crédito (mujeres) | Número de tarjetas de crédito per cápita |
| 4 | `numcontcred_hip_m` | Créditos hipotecarios (mujeres) | Número de créditos de vivienda per cápita |
| 5 | `saldocont_total_m` | Saldo total (mujeres) | Saldo total en cuentas per cápita |

### 12.2 Transformación aplicada

Cada variable se transforma a **per cápita + asinh**:

$$
Y_{it} = \text{asinh}\left(\frac{\texttt{variable\_m}_{it}}{\texttt{pob\_tot}_{it}}\right)
$$

El nombre resultante en los datos es: `{variable}_pc_asinh`

Ejemplo: `saldocont_total_m_pc_asinh`

### 12.3 ¿Por qué estas 5 y no otras?

Fueron seleccionadas en `docs/09_MODELADO_PROPUESTA.md` por representar las dimensiones
clave de la inclusión financiera:

| Outcome | Dimensión de inclusión financiera |
|---------|-----------------------------------|
| Contratos totales | Acceso general al sistema financiero |
| Tarjetas débito | Uso básico de servicios bancarios |
| Tarjetas crédito | Acceso a crédito de consumo |
| Créditos hipotecarios | Acceso a crédito de largo plazo / vivienda |
| Saldo total | Profundidad financiera (cuánto dinero manejan) |

---

## 13. ¿Qué hacer según el resultado del event study?

### 13.1 Árbol de decisión

```
Event Study completado
        │
        ▼
¿Todos los coeficientes pre son ≈ 0?
(test conjunto p > 0.10 para TODOS los outcomes)
        │
   ┌────┴────┐
   │         │
  SÍ        NO
   │         │
   ▼         ▼
 ✅ Pro-     ¿Cuántos outcomes fallan?
   ceder      │
   con       ┌┴──────────┐
   TWFE      │            │
             1-2          3+
             ⚠️ Análisis   ❌ Problema
             de sensibi-   serio:
             lidad         revisar
             (variar K,    identificación
             excluir       completa
             cohortes)
             │
             ▼
        ¿Sensibilidad resuelve?
        ┌─────┴─────┐
        SÍ          NO
        │            │
        ▼            ▼
   ✅ Proceder   ❌ Reportar
   (reportar la    como
   sensibilidad)   limitación
```

### 13.2 Nuestro caso

- 4 de 5 outcomes pasan limpiamente (p > 0.10) ✅
- 1 outcome borderline (tarjetas crédito, p = 0.083) → se hizo análisis de sensibilidad
  → variante K=6 resuelve → ✅ se procede

**Conclusión:** Las tendencias paralelas se sostienen para los 5 outcomes. La evidencia
empírica respalda la estrategia de identificación DiD.

---

## 14. Limitaciones y debates actuales

### 14.1 Roth (2022): el problema del poder estadístico

Jonathan Roth (2022, *AER: Insights*) señala un problema fundamental:

> Un test de pre-trends que "no rechaza" puede simplemente carecer de poder
> estadístico para detectar una violación real.

En otras palabras: que p > 0.10 no **prueba** que las tendencias eran paralelas.
Solo dice que no tenemos evidencia suficiente para rechazarlo.

**Implicación para nuestra tesis:** Nuestro panel tiene 17 trimestres con K=4 leads,
lo que da solo 3 coeficientes pre-tratamiento para el test. El poder para detectar
violaciones pequeñas es limitado.

**Mitigación:** Se reporta un análisis MDES (Minimum Detectable Effect Size) en
`docs/16_MDES_PODER.md` que establece el tamaño mínimo de violación que podemos
descartar con 80% de poder.

### 14.2 Problemas con TWFE en staggered designs

Cuando el tratamiento es escalonado, los coeficientes $\mu_k$ del event study TWFE
pueden estar contaminados por "comparaciones prohibidas" (tratados tempranos como
control de tratados tardíos). Sun & Abraham (2021) proponen un estimador robusto.

**En nuestra tesis:** Se recomienda como extensión futura complementar el event
study TWFE con un Stacked DiD que evite estas comparaciones problemáticas
(ver `docs/10_EXPLICACION_MODELADO.md` §11).

### 14.3 ¿Event study = test de causalidad?

No. El event study es una **condición necesaria** pero no suficiente para la
causalidad. Podría haber:
- Anticipación perfecta (los actores se ajustan antes del tratamiento)
- Variables omitidas que cambian exactamente al mismo tiempo que el tratamiento
- Violaciones futuras que el pre-trend no captura

El event study es parte de un **paquete de evidencia** junto con la teoría, el
diseño institucional, y las pruebas de robustez.

---

## 15. Conexión con el resto del pipeline

### 15.1 ¿Qué viene después del event study?

```
 Event Study (este documento)
       │
       ▼
 ┌──────────────────────────────┐
 │ TWFE (02_twfe.py)            │ ← Modelo principal: un β por outcome
 │ → docs/13_MODELADO_ECONOMETRICO.md │
 └──────────┬───────────────────┘
            │
            ▼
 ┌──────────────────────────────┐
 │ Sensibilidad (event_study_   │ ← Robustez del event study
 │ sensitivity.py)              │
 │ → docs/15_EVENT_STUDY_SENSIBILIDAD.md │
 └──────────┬───────────────────┘
            │
            ▼
 ┌──────────────────────────────┐
 │ Robustez (04_robustness.py)  │ ← Pruebas de sensibilidad del TWFE
 └──────────┬───────────────────┘
            │
            ▼
 ┌──────────────────────────────┐
 │ Heterogeneidad               │ ← ¿El efecto varía por subgrupo?
 │ (05_heterogeneity.py)        │
 └──────────────────────────────┘
```

### 15.2 Mapa de archivos completo del event study

| Paso | Archivo | Input | Output |
|------|---------|-------|--------|
| Carga datos | `utils.py` → `load_panel()` | `analytical_panel_features.parquet` | DataFrame en memoria |
| Dummies | `03_event_study.py` → `build_event_dummies()` | DataFrame | DataFrame + lista de dummies |
| Estimación | `03_event_study.py` → `run_event_study()` | DataFrame + dummies | Coeficientes + test pre-trends |
| Gráfico | `03_event_study.py` → `plot_event_study()` | Coeficientes | `figura_1_event_study.pdf` |
| Tests | `03_event_study.py` → `main()` | — | `pretrends_tests.csv` |
| Sensibilidad | `event_study_sensitivity.py` → `main()` | — | `pretrends_tests_sens.csv`, `figura_2_event_study_sens.pdf` |

### 15.3 Referencias cruzadas en la documentación

| Documento | Relación con este tutorial |
|-----------|---------------------------|
| `09_MODELADO_PROPUESTA.md` §4 | Ecuación formal del event study |
| `10_EXPLICACION_MODELADO.md` §9 | Resumen breve (este doc es la versión extendida) |
| `13_MODELADO_ECONOMETRICO.md` | Cómo se implementa el TWFE que validamos aquí |
| `15_EVENT_STUDY_SENSIBILIDAD.md` | Qué hacer cuando un pre-trend es borderline |
| `16_MDES_PODER.md` | Poder estadístico del test de pre-trends |

---

## Glosario rápido

| Término | Definición |
|---------|-----------|
| **Event time** ($k$) | Tiempo relativo al tratamiento: $k = t - g_i$ |
| **Cohorte** ($g_i$) | Primer periodo de tratamiento del municipio $i$ |
| **Lead** | Periodo pre-tratamiento ($k < 0$) |
| **Lag** | Periodo post-tratamiento ($k \geq 0$) |
| **Endpoint binning** | Agrupar periodos extremos en un solo bin ($k \leq -K$ o $k \geq L$) |
| **Pre-trend** | Tendencia previa al tratamiento |
| **Test conjunto** | Test Wald $\chi^2$ de que todos los coeficientes pre = 0 |
| **TWFE** | Two-Way Fixed Effects |
| **Staggered treatment** | Tratamiento que se aplica en momentos diferentes a diferentes unidades |
| **Always-treated** | Municipios tratados desde el inicio del panel |
| **Never-treated** | Municipios sin tratamiento en todo el panel |
| **Switchers** | Municipios que cambian de estado durante el panel |
| **asinh** | Seno hiperbólico inverso: $\text{asinh}(x) = \ln(x + \sqrt{x^2 + 1})$ |

---

> **Próximo paso:** Una vez confirmado que las tendencias paralelas se sostienen,
> procedemos al modelo principal (TWFE). Ver `docs/13_MODELADO_ECONOMETRICO.md`.
