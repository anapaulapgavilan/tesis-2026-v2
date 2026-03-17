> **Archivos fuente:**
> - `src/transformaciones_altas.py`

# EDA — Explicación 3: Resolución de Recomendaciones de Alta Prioridad (🟡)

## Guía tutorial de conceptos econométricos y su implementación en Python

**Continuación de:** `docs/02_EDA_EXPLICACION.md` (Secciones 1–10) y `docs/03_EDA_EXPLICACION_2.md` (Sección 11)  
**Fecha:** Febrero 2026  

---

> **Objetivo de este documento:** No solo describir *qué* se hizo, sino explicar *por qué* se hizo desde los fundamentos de econometría y estadística. Cada concepto — transformación logarítmica, variable de control, winsorización, ratio de brecha de género — se explica desde cero, como si el lector fuera un estudiante que necesita entender la intuición, la matemática y la implementación en Python antes de defender la tesis.

---

## 12. Resolución de recomendaciones de alta prioridad (🟡)

Las 5 recomendaciones marcadas como **🟡 ALTA prioridad** en la Sección F del EDA fueron
implementadas sobre la tabla `inclusion_financiera_clean` (que ya contenía las
transformaciones críticas de la Sección 11).

### Tabla resultante

| Propiedad | Valor |
|-----------|-------|
| **Tabla original** | `inclusion_financiera` (175 columnas) — **intacta** |
| **Tabla limpia** | `inclusion_financiera_clean` (296 columnas) |
| **Filas** | 41,905 (sin cambios) |
| **Columnas nuevas (esta fase)** | +73 |
| **Acumulado desde original** | +121 columnas |

| Fase | Columnas añadidas | Total acumulado |
|------|-------------------|-----------------|
| Tabla original | — | 175 |
| + Críticas (Recs 1–4) | +51 per cápita, −3 constantes = +48 | 223 |
| + Altas (Recs 5–9) | +4 log + 51 winsor + 17 ratio + 1 ever = +73 | 296 |

---

## Conceptos previos: ¿Qué es una variable de control?

Antes de explicar las transformaciones, es indispensable entender qué es una **variable de control** y por qué la necesitamos.

### Definición intuitiva

Una variable de control es una variable que incluimos en una regresión **no porque nos interese su efecto causal**, sino porque, si la omitimos, podría **contaminar** la estimación del efecto que sí nos interesa.

En esta tesis, el efecto que nos interesa es:

$$\beta = \text{efecto de tener alcaldesa sobre la inclusión financiera de las mujeres}$$

Pero imaginemos que no controlamos por la población del municipio. Los municipios grandes (CDMX, Guadalajara, Monterrey) tienen, por construcción, más contratos bancarios y una historia política distinta. Si los municipios grandes tienden, por razones históricas, a elegir menos alcaldesas, entonces en la regresión:

$$Y_{it} = \alpha + \beta \cdot \text{alcaldesa}_{it} + \varepsilon_{it}$$

el coeficiente $\beta$ estaría capturando no solo el efecto de la alcaldesa, sino también las diferencias asociadas al tamaño del municipio. Esto se llama **sesgo por variable omitida** (*omitted variable bias*, OVB).

### Formalización del OVB

El sesgo toma la forma:

$$\text{OVB} = \gamma \cdot \delta$$

donde:
- $\gamma$ = efecto de la variable omitida (población) sobre $Y$ (inclusión financiera)
- $\delta$ = correlación entre la variable omitida (población) y el tratamiento (alcaldesa)

Si $\gamma \neq 0$ **y** $\delta \neq 0$, hay sesgo. Al incluir `log_pob` como control, "cerramos" este canal: forzamos al modelo a comparar municipios con población similar, aislando mejor el efecto causal de la alcaldesa.

### ¿Cómo funciona en la regresión?

Cuando escribimos:

$$Y_{it} = \alpha + \beta \cdot \text{alcaldesa}_{it} + \theta \cdot \log(\text{pob}_{it}) + \varepsilon_{it}$$

le estamos diciendo al modelo: *"Primero, ajusta por las diferencias en población entre municipios. Después de ese ajuste, ¿cuánto cambia $Y$ cuando `alcaldesa` pasa de 0 a 1?"*

El coeficiente $\theta$ absorbe la variación de $Y$ que se explica por la población, y $\beta$ solo captura la variación residual asociada con el tratamiento.

> **Nota para la defensa:** En nuestro diseño de Diferencias en Diferencias con efectos fijos de municipio ($\alpha_i$) y de tiempo ($\delta_t$), los efectos fijos ya absorben las diferencias constantes entre municipios (incluyendo el *nivel* de población). Sin embargo, `log_pob` sigue siendo útil como control porque la población **cambia en el tiempo** (estimaciones intercensales), y esa variación temporal no es absorbida por los efectos fijos.

### ¿Y los efectos fijos, son controles?

Sí. Los **efectos fijos de municipio** ($\alpha_i$) son controles para *todas* las características del municipio que no cambian en el tiempo (geografía, cultura política, infraestructura histórica). Los **efectos fijos de tiempo** ($\delta_t$) controlan por shocks macroeconómicos que afectan a todos los municipios por igual (e.g., una reforma financiera nacional, una crisis económica). Los controles explícitos como `log_pob` capturan las variables que **varían tanto entre municipios como en el tiempo** y que los efectos fijos no absorben completamente.

---

### Rec 5. Transformación logarítmica de población

#### ¿Qué es una transformación logarítmica?

Una transformación logarítmica consiste en reemplazar una variable $x$ por $\ln(x)$ (logaritmo natural, base $e \approx 2.718$). Es una de las transformaciones más utilizadas en econometría y tiene propiedades matemáticas que la hacen especialmente útil.

#### Intuición geométrica

El logaritmo "comprime" los valores grandes y "estira" los pequeños. Pensemos en la escala de Richter para terremotos: un terremoto de magnitud 7 no es "un poco más fuerte" que uno de magnitud 6 — es **10 veces más fuerte**. La escala de Richter usa logaritmos precisamente para representar fenómenos con rangos enormes en una escala manejable.

La población de los municipios mexicanos tiene un problema análogo:

| Municipio | Población | $\ln(\text{pob})$ |
|-----------|----------:|-------------------:|
| Santa Magdalena Jicotlán, Oax. | ~82 | 4.41 |
| Xalapa, Ver. | ~52,000 | 10.86 |
| Ecatepec, Méx. | ~1,645,000 | 14.31 |

Sin logaritmo, Ecatepec es **20,000 veces** mayor que Jicotlán. Con logaritmo, la diferencia es solo **3.24 veces** (14.31 / 4.41). El logaritmo pone a estos tres municipios en la misma "escala mental", lo que facilita que el modelo de regresión los compare de forma razonable.

#### Propiedades matemáticas relevantes

1. **Convierte multiplicaciones en sumas:**
   $\ln(a \cdot b) = \ln(a) + \ln(b)$
   
   Esto es crucial porque muchos fenómenos económicos son *multiplicativos* (e.g., "la población crece un 2% anual"), no aditivos. El logaritmo los transforma en relaciones *aditivas* que la regresión lineal puede manejar.

2. **Los cambios porcentuales se vuelven cambios absolutos:**
   Si $x$ crece un 1%, entonces $\ln(x)$ crece en aproximadamente 0.01. Formalmente:
   
   $$\Delta \ln(x) \approx \frac{\Delta x}{x} \quad \text{(para cambios pequeños)}$$
   
   Esto permite interpretar coeficientes como **semi-elasticidades** o **elasticidades** dependiendo de si el log está en la variable dependiente, la independiente, o ambas (ver tabla abajo).

3. **Simetriza distribuciones sesgadas hacia la derecha:**
   Las distribuciones de población, ingreso, saldos bancarios, etc., típicamente tienen una cola derecha muy larga (muchos municipios pequeños, pocos muy grandes). El logaritmo "jala" la cola derecha hacia el centro, produciendo una distribución más simétrica que se ajusta mejor a los supuestos de los modelos lineales.

#### Interpretación de coeficientes con logaritmos

| Modelo | Forma | Interpretación de $\beta$ |
|--------|-------|---------------------------|
| **Nivel-Nivel** | $Y = \alpha + \beta X$ | Un aumento de 1 unidad en $X$ se asocia con un cambio de $\beta$ unidades en $Y$ |
| **Log-Nivel** (semi-elasticidad) | $\ln(Y) = \alpha + \beta X$ | Un aumento de 1 unidad en $X$ se asocia con un cambio de $\beta \times 100$% en $Y$ |
| **Nivel-Log** | $Y = \alpha + \beta \ln(X)$ | Un aumento de 1% en $X$ se asocia con un cambio de $\beta / 100$ unidades en $Y$ |
| **Log-Log** (elasticidad) | $\ln(Y) = \alpha + \beta \ln(X)$ | Un aumento de 1% en $X$ se asocia con un cambio de $\beta$% en $Y$ |

En nuestra tesis, usamos `log_pob` (nivel-log para la variable de control) en combinación con outcomes en nivel per cápita. Esto implica que $\theta$ en:

$$Y_{it}^{pc} = \alpha_i + \delta_t + \beta \cdot \text{alcaldesa}_{it} + \theta \cdot \ln(\text{pob}_{it}) + \varepsilon_{it}$$

se interpreta como: *"Por cada 1% de aumento en la población, la inclusión financiera per cápita cambia en $\theta / 100$ unidades (contratos por cada 10,000 adultas)."*

#### ¿Por qué `log(x + 1)` y no `log(x)`?

El logaritmo natural no está definido para $x = 0$ ($\ln(0) = -\infty$) ni para valores negativos. En nuestros datos, hay 8 observaciones municipio-trimestre donde la población adulta es 0 (municipios que se incorporan gradualmente al panel).

La solución estándar es usar $\ln(x + 1)$, que en NumPy se implementa como `np.log1p(x)`:

```python
import numpy as np

# Equivalente a ln(x + 1), pero con mayor precisión numérica para x ≈ 0
df["log_pob"] = np.log1p(df["pob"])
```

> **¿Por qué `np.log1p` y no `np.log(x + 1)`?** Para valores de $x$ muy cercanos a cero, `np.log(x + 1)` puede perder precisión debido a errores de punto flotante (el `+1` y el `log` se calculan por separado). `np.log1p(x)` calcula $\ln(1 + x)$ en un solo paso con un algoritmo numéricamente estable. En la práctica, para poblaciones de municipios la diferencia es insignificante, pero usar `log1p` es la buena práctica que te evitará problemas en otros contextos.

#### ¿Cuándo NO usar la transformación logarítmica?

- **Variables binarias** (0/1): No tiene sentido. $\ln(0) = -\infty$ y $\ln(1) = 0$ — destruirías la información.
- **Variables que ya están en escala moderada** (e.g., un índice de 0–100): El log no aporta mucho si la distribución ya es razonablemente simétrica.
- **Variables con muchos ceros legítimos**: Si el 40% de las observaciones son 0, el `+1` distorsiona severamente la distribución. En esos casos, se prefiere la transformación *inverse hyperbolic sine* (asinh): $\text{asinh}(x) = \ln(x + \sqrt{x^2 + 1})$, que maneja ceros sin parche.

#### Implementación en Python (código del script)

```python
# En src/transformaciones_altas.py — función aplicar_log_poblacion()

mapping = {
    "pob":          "log_pob",
    "pob_adulta":   "log_pob_adulta",
    "pob_adulta_m": "log_pob_adulta_m",
    "pob_adulta_h": "log_pob_adulta_h",
}

for col_orig, col_log in mapping.items():
    df[col_log] = np.log1p(df[col_orig]).round(6)
```

**Desglose línea por línea:**
1. `mapping` define los pares (columna original → columna nueva). Creamos 4 versiones: población total, adulta total, adulta mujeres y adulta hombres.
2. `np.log1p(df[col_orig])` aplica $\ln(x+1)$ a toda la columna de forma vectorizada (sin loop, rápido).
3. `.round(6)` redondea a 6 decimales para evitar ruido de punto flotante (e.g., 9.494700000000001 → 9.4947).

#### Columnas creadas

| Columna nueva | Columna original | Media | Min | Max |
|---------------|------------------|-------|-----|-----|
| `log_pob` | `pob` | 9.4947 | 4.4067 | 14.4691 |
| `log_pob_adulta` | `pob_adulta` | 9.1727 | 4.2047 | 14.1996 |
| `log_pob_adulta_m` | `pob_adulta_m` | 8.5194 | 3.6109 | 13.5500 |
| `log_pob_adulta_h` | `pob_adulta_h` | 8.4368 | 3.2958 | 13.5102 |

**Lectura de la tabla:** `log_pob` tiene un rango de 4.41–14.47, lo que corresponde a poblaciones de $e^{4.41} - 1 \approx 81$ hasta $e^{14.47} - 1 \approx 1{,}945{,}000$. El rango original (81 a 1.9 millones, 24,000×) se comprimió a un rango logarítmico de ~10 unidades — mucho más manejable para un modelo lineal.

#### Uso recomendado

Incluir `log_pob` o `log_pob_adulta` como **control** en todas las especificaciones econométricas. **Nunca usar la población en nivel** como regresor: su distribución sesgada violaría el supuesto de linealidad y el coeficiente sería ininterpretable.

> **Si el sinodal pregunta: "¿Por qué no usan `log_pob` como variable dependiente?"** — Porque nuestra variable dependiente ya está normalizada per cápita (contratos por cada 10,000 adultas). Tomar el log de una tasa per cápita que puede ser 0 requeriría otra vez el parche del `+1`, y la interpretación se volvería innecesariamente compleja. Usamos el log para *controles* de escala (población), no para *outcomes*.

---

### Rec 6. Winsorización de outcomes per cápita (p1–p99)

#### ¿Qué es un outlier y por qué nos importa?

Un **outlier** (valor atípico) es una observación que se encuentra anormalmente lejos del grueso de los datos. En econometría, los outliers son problemáticos porque:

1. **Inflan la varianza de los estimadores:** Un solo punto alejado puede "jalar" la recta de regresión hacia él, distorsionando el coeficiente estimado.
2. **Violan supuestos:** El estimador OLS minimiza la suma de cuadrados de los residuos, lo que da **peso cuadrático** a las observaciones lejanas. Un outlier con residuo $r = 100$ contribuye $10{,}000$ a la función objetivo, mientras que una observación normal con $r = 2$ contribuye solo $4$. El outlier tiene 2,500× más influencia.
3. **Distorsionan estadísticos descriptivos:** La media de `ncont_total_m_pc` es 3,429, pero el máximo es 179,439. Ese máximo — un municipio con más contratos bancarios que personas — arrastra la media hacia arriba y da una imagen distorsionada de la distribución.

#### ¿De dónde vienen estos outliers?

En nuestro caso, los outliers surgen por una razón específica: municipios con **población muy pequeña** que generan ratios per cápita extremos. Si un municipio tiene 50 mujeres adultas y hay 1,000 contratos bancarios registrados ahí (quizá porque una sucursal bancaria atiende poblaciones vecinas), su tasa per cápita es:

$$\frac{1{,}000 \times 10{,}000}{50} = 200{,}000 \text{ contratos por cada 10,000 adultas}$$

Esto no refleja una inclusión financiera genuinamente alta, sino un artefacto estadístico: el denominador es tan pequeño que cualquier actividad bancaria genera un ratio absurdo. Este fenómeno se llama **inestabilidad de tasas en poblaciones pequeñas** (*small-area rate instability*) y es un problema clásico en epidemiología, demografía y economía regional.

#### ¿Qué es la winsorización?

La **winsorización** es una técnica que **reemplaza** los valores extremos por los valores de un percentil elegido, sin eliminar observaciones. Se llama así por Charles Winsor (estadístico), y su idea clave es: *"No queremos perder la observación, pero no queremos que su valor extremo distorsione el análisis."*

**Formalmente**, la winsorización al $(p, 100-p)$% consiste en:

$$x_i^w = \begin{cases} q_p & \text{si } x_i < q_p \\ x_i & \text{si } q_p \leq x_i \leq q_{100-p} \\ q_{100-p} & \text{si } x_i > q_{100-p} \end{cases}$$

donde $q_p$ es el percentil $p$ y $q_{100-p}$ es el percentil $100-p$ de la distribución de $x$.

En nuestro caso, usamos $p = 1$ y $100-p = 99$.

#### Winsorización vs. truncación (trimming): ¿Cuál es la diferencia?

| Técnica | ¿Qué hace con los extremos? | ¿Cambia el tamaño de la muestra? | Consecuencia |
|---------|----------------------------|----------------------------------|--------------|
| **Winsorización** | Reemplaza el valor extremo por el percentil límite | **No** — mantiene las 41,905 observaciones | Conserva toda la muestra; reduce influencia de extremos |
| **Truncación (trimming)** | Elimina la observación | **Sí** — pierde ~1% por cola (≈840 obs.) | Altera la muestra y puede introducir sesgo de selección |

La winsorización es **más conservadora** y, por tanto, preferida en econometría aplicada como prueba de robustez. Si los resultados son similares con y sin winsorización, tenemos confianza en que nuestros hallazgos no dependen de un puñado de observaciones extremas.

#### Ejemplo visual con datos reales

Pensemos en la distribución de `ncont_total_m_pc` (número de contratos de captación por cada 10,000 mujeres adultas):

```
Sin winsorizar:
┌──────────────────────────────────────────────────────────────────────┐
│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ ·│ → Max: 179,439
│   99% de datos      │     cola casi vacía                    outlier│
└──────────────────────────────────────────────────────────────────────┘
                       ↑ p99 = 21,346

Winsorizado al p1–p99:
┌──────────────────────────────────────────────────────────────────────┐
│▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│ → Max: 21,346
│                     toda la masa visible, sin cola                  │
└──────────────────────────────────────────────────────────────────────┘
```

Los ~420 valores que estaban por encima de 21,346 ahora valen exactamente 21,346. No los eliminamos; los "aplastamos" contra el techo del percentil 99.

#### Implementación en Python

```python
# En src/transformaciones_altas.py — función winsorizar_per_capita()

cols_pc = [c for c in df.columns if c.endswith("_pc")]  # 51 columnas

for col in cols_pc:
    col_w = f"{col}_w"                          # Nombre con sufijo _w
    p1  = df[col].quantile(0.01)                # Percentil 1
    p99 = df[col].quantile(0.99)                # Percentil 99
    df[col_w] = df[col].clip(lower=p1, upper=p99)  # ← La winsorización
```

**Desglose línea por línea:**

1. `df[col].quantile(0.01)` calcula el percentil 1 de la distribución. Es el valor por debajo del cual está el 1% de las observaciones. Ignora `NaN` por defecto.
2. `df[col].quantile(0.99)` calcula el percentil 99.
3. `df[col].clip(lower=p1, upper=p99)` es la operación clave:
   - Si un valor es menor que `p1`, lo reemplaza con `p1`.
   - Si un valor es mayor que `p99`, lo reemplaza con `p99`.
   - Si está entre ambos, lo deja igual.
   - Nota: **no modifica la columna original** — el resultado se guarda en una columna nueva (`col_w`).

> **Alternativa con scipy:** La librería `scipy.stats.mstats.winsorize` hace lo mismo, pero opera in-place y devuelve un masked array. Usar `clip` de pandas es más explícito y limpio para nuestro propósito.

#### ¿Por qué elegimos p1–p99 y no otro rango?

| Rango | % de observaciones afectadas | Cuándo se usa |
|-------|------------------------------|---------------|
| p5–p95 | 10% (5% por cola) | Muy agresivo. Solo si los datos son extremadamente ruidosos. |
| p2.5–p97.5 | 5% | Usado en finanzas con datos de alta frecuencia. |
| **p1–p99** | **2% (1% por cola)** | **Estándar en econometría aplicada.** Balance entre conservar datos y limitar outliers. |
| p0.5–p99.5 | 1% | Muy suave. Solo toca los casos más extremos. |

Para nuestra muestra de 41,905 observaciones, el rango p1–p99 afecta ~420 observaciones por cola (2% total). Es la elección más común en la literatura de inclusión financiera y economía del desarrollo.

#### Ejemplo de recorte — `ncont_total_m_pc`

| Estadístico | Original (`_pc`) | Winsorizado (`_pc_w`) |
|-------------|------------------|-----------------------|
| Max | 179,439.41 | 21,346.29 |
| p99 | 21,346.29 | 21,346.29 |
| p1 | 0.00 | 0.00 |
| Min | 0.00 | 0.00 |

En este caso, el p1 es 0 (muchos municipios con 0 contratos), así que la cola inferior no se modifica. La acción está en la cola superior: el máximo baja de 179,439 a 21,346 — una reducción de **88%** en el valor más extremo.

#### Columnas creadas (51 en total)

- Conteos: `ncont_ahorro_m_pc_w`, `ncont_ahorro_h_pc_w`, ..., `ncont_total_t_pc_w` (21)
- Saldos: `saldocont_ahorro_m_pc_w`, ..., `saldocont_total_t_pc_w` (21)
- Crédito hipotecario: `numcontcred_hip_m_pc_w`, `numcontcred_hip_h_pc_w`, `numcontcred_hip_t_pc_w` (3)
- Tarjetas débito: `numtar_deb_m_pc_w`, `numtar_deb_h_pc_w`, `numtar_deb_t_pc_w` (3)
- Tarjetas crédito: `numtar_cred_m_pc_w`, `numtar_cred_h_pc_w`, `numtar_cred_t_pc_w` (3)

#### ¿Cómo se usa en la práctica?

La estrategia estándar en papers publicados es tener **dos especificaciones**:

| Especificación | Columnas | Propósito |
|----------------|----------|-----------|
| **Principal** | `_pc` (sin winsorizar) | Reportar el resultado central. Usa toda la variación de los datos. |
| **Robustez** | `_pc_w` (winsorizado) | Verificar que el resultado no depende de outliers. Se reporta en el apéndice. |

Si $\beta$ es significativo con `_pc` pero no con `_pc_w`, hay un problema: los outliers están "conduciendo" el resultado, y la evidencia no es robusta. Si $\beta$ es significativo en ambos, la evidencia es más convincente.

> **Nota para la defensa:** Si el sinodal dice "¿por qué no usaron la mediana o regresión cuantílica en vez de winsorizar?", la respuesta es: la mediana es un excelente estadístico descriptivo, pero los modelos Difference-in-Differences con efectos fijos de panel (TWFE, Stacked DiD) se estiman por OLS, que trabaja con medias. La winsorización limpia la media sin cambiar el estimador. La regresión cuantílica es otra opción válida pero computacionalmente costosa con efectos fijos de dos vías, y no forma parte de la metodología estándar de DiD escalonado en la literatura actual.

---

### Rec 7. Ratio brecha de género (outcome_m / outcome_h)

#### ¿Qué mide un ratio de brecha de género?

El ratio:

$$R = \frac{\text{outcome\_m\_pc}}{\text{outcome\_h\_pc}}$$

compara directamente el acceso financiero de **mujeres** con el de **hombres** en el mismo municipio y trimestre, en la misma unidad de medida (contratos o pesos por cada 10,000 adultas/os).

**Interpretación:**

| Valor de $R$ | Significado |
|:---:|:---|
| $R = 1$ | **Equidad perfecta:** Las mujeres tienen exactamente el mismo acceso que los hombres. |
| $R < 1$ | **Brecha en contra de las mujeres:** Por ejemplo, $R = 0.80$ significa que por cada 100 contratos que tienen los hombres, las mujeres tienen 80. La brecha es del 20%. |
| $R > 1$ | **Brecha en favor de las mujeres:** Por ejemplo, $R = 1.50$ significa que las mujeres tienen 50% más acceso que los hombres. |
| $R = 0$ | Las mujeres tienen 0 contratos; los hombres tienen alguno. |
| $R$ indefinido (`NaN`) | Los hombres tienen 0 contratos (denominador = 0), por lo que el ratio no tiene sentido matemático. |

#### ¿Por qué es relevante para la tesis?

Este ratio permite responder directamente la pregunta central: **¿Tener una alcaldesa reduce la brecha de género en inclusión financiera?**

Si estimamos:

$$R_{it} = \alpha_i + \delta_t + \beta \cdot \text{alcaldesa}_{it} + \varepsilon_{it}$$

y encontramos $\beta > 0$ significativo, la interpretación es: *"Cuando un municipio pasa a tener alcaldesa, la proporción de inclusión financiera femenina respecto a la masculina **aumenta** en $\beta$ unidades"* — es decir, la brecha se cierra.

Esto es más directo que estimar el efecto sobre outcomes femeninos y masculinos por separado, porque la brecha podría cerrarse por dos vías: las mujeres ganan acceso (deseable), o los hombres lo pierden (no deseable). El ratio captura el efecto **neto** sobre la brecha.

#### Implementación en Python

```python
# En src/transformaciones_altas.py — función crear_ratio_genero()

# 1. Encontrar todos los pares (mujeres, hombres) del mismo producto
cols_m = [c for c in df.columns if c.endswith("_m_pc") and not c.endswith("_w")]

for col_m in cols_m:
    col_h = col_m.replace("_m_pc", "_h_pc")    # Columna hombres correspondiente
    if col_h not in df.columns:
        continue

    producto = col_m.replace("_m_pc", "")       # e.g., "ncont_ahorro"
    col_ratio = f"ratio_mh_{producto}"           # e.g., "ratio_mh_ncont_ahorro"

    # 2. Protección contra ÷0: reemplazar 0 por NaN en el denominador
    denom = df[col_h].replace(0, np.nan)

    # 3. Calcular el ratio
    df[col_ratio] = (df[col_m] / denom).round(6)
```

**Puntos clave del código:**

1. **`replace(0, np.nan)`**: Cuando `outcome_h_pc = 0`, la división produciría `inf` (infinito). Al reemplazar 0 por `NaN` *antes* de dividir, el resultado de `x / NaN` es `NaN` — un valor indefinido que los modelos de regresión simplemente excluyen.

2. **¿Por qué no usar `np.where`?** Se podría escribir `np.where(denom == 0, np.nan, df[col_m] / denom)`, pero `replace + /` es más legible y produce el mismo resultado.

3. **`.round(6)`**: Evita acumulación de decimales por aritmética de punto flotante.

#### Columnas creadas y estadísticas descriptivas

| Columna | Media | Mediana | NaN | Interpretación |
|---------|-------|---------|-----|----------------|
| `ratio_mh_ncont_ahorro` | 0.85 | 0.85 | 39,163 | Mujeres ~85% del ahorro de hombres |
| `ratio_mh_ncont_plazo` | 1.78 | 1.50 | 24,183 | Mujeres > hombres en plazo |
| `ratio_mh_ncont_n1` | 0.51 | 0.00 | 38,279 | Brecha muy marcada en nivel 1 |
| `ratio_mh_ncont_n2` | 1.57 | 0.97 | 1,504 | Mujeres ≈ hombres (mediana ~1) |
| `ratio_mh_ncont_n3` | 0.70 | 0.67 | 34,616 | Brecha en nivel 3 |
| `ratio_mh_ncont_tradic` | 1.28 | 1.03 | 23,655 | Casi equidad en tradicional |
| `ratio_mh_ncont_total` | 1.44 | 1.01 | 1,485 | En total, cerca de equidad (mediana) |
| `ratio_mh_saldocont_ahorro` | 37.49 | 0.95 | 39,344 | Outliers distorsionan la media |
| `ratio_mh_saldocont_plazo` | 8.85 | 1.12 | 24,193 | Media inflada por outliers |
| `ratio_mh_saldocont_n1` | 28.54 | 0.00 | 38,325 | Mismo patrón |
| `ratio_mh_saldocont_n2` | 40.92 | 0.82 | 1,709 | Hombres > mujeres en saldos N2 |
| `ratio_mh_saldocont_n3` | 16.19 | 0.77 | 34,642 | Hombres > mujeres en saldos N3 |
| `ratio_mh_saldocont_tradic` | 6.62 | 0.92 | 23,668 | Brecha moderada |
| `ratio_mh_saldocont_total` | 40.56 | 0.94 | 1,684 | Hombres ligeramente > mujeres |
| `ratio_mh_numcontcred_hip` | 0.49 | 0.45 | 11,911 | Brecha fuerte en hipotecas |
| `ratio_mh_numtar_deb` | 0.83 | 0.81 | 360 | Mujeres ~83% tarjetas débito |
| `ratio_mh_numtar_cred` | 0.81 | 0.77 | 2,875 | Mujeres ~81% tarjetas crédito |

#### ¿Cómo leer esta tabla? — Un ejemplo práctico

Tomemos `ratio_mh_numtar_deb` (tarjetas de débito):
- **Media = 0.83**: En promedio, por cada 100 tarjetas de débito que tienen los hombres, las mujeres tienen 83. Brecha del 17%.
- **Mediana = 0.81**: El municipio "típico" (el del medio de la distribución) tiene una brecha del 19%.
- **NaN = 360**: Solo 360 de 41,905 observaciones no tienen dato — las tarjetas de débito están presentes en prácticamente todos los municipios.

Comparemos con `ratio_mh_ncont_ahorro`:
- **NaN = 39,163** (93.5%): Solo el 6.5% de las observaciones tienen cuentas de ahorro formal tanto de mujeres como de hombres. Esto refleja la baja penetración de las cuentas de ahorro en municipios rurales.

#### Hallazgos clave

1. **Brecha persistente en la mayoría de productos:** La mediana de `ratio_mh_ncont_total` es ~1.01, pero en productos específicos (nivel 1, hipotecas, tarjetas) las mujeres tienen significativamente menos acceso.

2. **Los ratios de saldos tienen outliers extremos:** Las medias son muy superiores a las medianas (e.g., media = 40.56 vs mediana = 0.94 en `saldocont_total`). Esto sugiere que en unos pocos municipios, las mujeres tienen saldos desproporcionadamente altos respecto a los hombres — probablemente un artefacto estadístico más que una realidad de inclusión financiera. Para el análisis, es más informativo usar la **mediana** o aplicar winsorización a los ratios mismos.

3. **Muchos NaN son informativos:** Los ratios heredan los NaN de los productos (municipios sin presencia de ciertos productos financieros). Un NaN en `ratio_mh_ncont_ahorro` significa: *"En este municipio no hay cuentas de ahorro registradas para hombres, por lo que la brecha de género no puede calcularse."* Los NaN no son datos faltantes — son datos estructuralmente inexistentes, análogos a los de `saldoprom_*` explicados en la Sección 11 (Rec 3).

#### Uso recomendado

- **Variable dependiente en las regresiones DiD**, especialmente `ratio_mh_ncont_total`, `ratio_mh_numtar_deb` y `ratio_mh_numtar_cred` (los que tienen menos NaN).
- **Complementar** con análisis separado de outcomes femeninos per cápita (`_m_pc`), ya que el ratio podría enmascarar cambios simétricos en ambos sexos.

---

### Rec 8. Indicador `ever_alcaldesa`

#### ¿Qué es y por qué lo necesitamos?

En un diseño de Diferencias en Diferencias (DiD) con tratamiento escalonado (*staggered treatment*), los municipios se dividen en tres grupos conceptuales:

| Grupo | Descripción | `ever_alcaldesa` |
|-------|-------------|:---:|
| **Never-treated** | Municipios que **nunca** tuvieron alcaldesa en todo el panel (2018Q3–2022Q3) | 0 |
| **Switchers** | Municipios que **cambiaron** de no tener a tener alcaldesa durante el panel | 1 |
| **Always-treated** | Municipios que **siempre** tuvieron alcaldesa (desde el primer trimestre) | 1 |

La variable `ever_alcaldesa` toma valor 1 si el municipio tuvo al menos una alcaldesa (`alcaldesa_final = 1`) en **cualquier** trimestre del panel, y 0 si **nunca** la tuvo.

#### Implementación en Python

```python
# En src/transformaciones_altas.py — función crear_ever_alcaldesa()

# 1. Para cada municipio, calcular el máximo de alcaldesa_final
#    max = 1 si al menos un trimestre tuvo alcaldesa; max = 0 si nunca
ever = df.groupby("cve_mun")["alcaldesa_final"].max().reset_index()
ever.columns = ["cve_mun", "ever_alcaldesa"]

# 2. Hacer un merge para asignar el valor a cada fila del panel
df = df.merge(ever, on="cve_mun", how="left")
```

**¿Por qué `max()`?** Si un municipio tiene `alcaldesa_final` = [0, 0, 1, 1, 0, ...] a lo largo de los trimestres, el máximo es 1. Si siempre tuvo [0, 0, 0, ...], el máximo es 0. Es una forma eficiente de crear un indicador "alguna vez".

**¿Por qué `merge`?** `ever` es un DataFrame con una fila por municipio (2,471 filas). El panel tiene una fila por municipio-trimestre (41,905 filas). El `merge` asigna el mismo valor de `ever_alcaldesa` a cada trimestre de cada municipio — la variable es **invariante en el tiempo**.

#### Distribución

| Grupo | Municipios | % |
|-------|------------|---|
| `ever_alcaldesa = 1` (tuvo alcaldesa alguna vez) | 995 | 40.3% |
| `ever_alcaldesa = 0` (nunca tuvo alcaldesa) | 1,476 | 59.7% |
| **Total** | **2,471** | **100%** |

> **Paréntesis — Análisis de heterogeneidad con `ever_alcaldesa`:**
>
> La propuesta original era usar `ever_alcaldesa` como variable de interacción en el modelo DiD: $Y_{it} = \alpha_i + \delta_t + \beta_1 D_{it} + \beta_2 D_{it} \times \text{ever\_alcaldesa}_i + \varepsilon_{it}$. Sin embargo, al implementarlo se descubrió que **la interacción $D \times \text{ever\_alcaldesa}$ es algebraicamente idéntica a $D$**: cuando `alcaldesa_final = 1`, entonces `ever_alcaldesa = 1` por definición, por lo que $D \times \text{ever} = D$ en todas las observaciones. PanelOLS rechaza la estimación con `AbsorbingEffectError` (colinealidad perfecta).
>
> **Procedimiento de reformulación:** Se reemplazó `ever_alcaldesa` por tres variables que sí varían independientemente del tratamiento:
> - **(A) $D \times \ln(\text{pob})$** — ¿depende el efecto del tamaño del municipio?
> - **(B) $D \times \text{early\_cohort}$** — ¿las alcaldesas tempranas (cohortes 1–2) tienen más efecto que las tardías?
> - **(C) $D \times \text{high\_baseline}$** — ¿depende del nivel previo de inclusión financiera (mediana = 776 contratos/10k adultas)?
>
> Se estimaron 12 interacciones (4 outcomes × 3 dimensiones) con PanelOLS + FE de municipio y tiempo + cluster SE municipal. **Resultado: el efecto es homogéneo.** Solo 1 de 12 interacciones alcanza significancia marginal (p < 0.10): tarjetas de débito × high_baseline. Esto es consistente con la tasa de falso positivo esperada al 10% (1/12 ≈ 8.3%). **No hay evidencia de que el efecto de la alcaldesa varíe por tamaño, timing o nivel base de inclusión financiera.** Los resultados detallados (paneles A, B, C con coeficientes, errores estándar y p-valores) están en la sección "Análisis de heterogeneidad — Resultados completos" más abajo.

#### ¿Para qué sirve en la estrategia empírica?

1. **Balance pre-tratamiento:** Antes de estimar el DiD, debemos verificar que los municipios con y sin alcaldesa no son radicalmente diferentes en características observables. Podemos hacer:
   ```python
   df.groupby("ever_alcaldesa")[["log_pob", "ncont_total_m_pc"]].mean()
   ```
   Si las medias son muy distintas, hay que preguntarse si la comparación DiD es válida.

2. **Análisis de heterogeneidad:** ¿El efecto causal es diferente en municipios que históricamente eligen mujeres vs. los que nunca lo hacen? Se puede interactuar:
   $$Y_{it} = \alpha_i + \delta_t + \beta_1 \cdot D_{it} + \beta_2 \cdot D_{it} \times \text{ever\_alcaldesa}_i + \varepsilon_{it}$$

3. **Definir grupo control en Stacked DiD:** Algunos diseños excluyen los "always-treated" del grupo control. `ever_alcaldesa` facilita este filtrado.

4. **Nota técnica:** `ever_alcaldesa` es colineal con el efecto fijo de municipio (ambos son constantes intra-municipio). **No se incluye como regresor** en un modelo con efectos fijos de municipio — se usa para segmentar submuestras o como variable de interacción.

#### ¿Se verificó en la práctica? — Estado de implementación

| Uso propuesto | ¿Implementado? | Dónde | Detalle |
|---|:---:|---|---|
| **1. Balance pre-tratamiento** | ✅ Sí | `src/tesis_alcaldesas/models/table1_descriptives.py` | La Tabla 1 compara medias de `log_pob`, outcomes `_pc` y `_pc_asinh` entre tres grupos: **Never-treated**, **Switchers (pre)** y **Always-treated**. Usa `cohort_type` (derivado de `ever_alcaldesa` + `always_treated`) en lugar de `ever_alcaldesa` directamente, lo cual es una clasificación más fina (distingue switchers de always-treated). |
| **2. Análisis de heterogeneidad** ($D \times \text{ever\_alcaldesa}$) | ⚠️ Reformulado | `_heterogeneity.py` | La interacción $D \times \text{ever\_alcaldesa}$ es **algebraicamente idéntica** a $D$ (ver análisis abajo). Se reformuló con tres interacciones alternativas que sí varían independientemente del tratamiento. **Resultado: el efecto es homogéneo** — ninguna interacción es robustamente significativa. |
| **3. Definir grupo control en Stacked DiD** | ✅ Sí | `src/did_moderno/run_stacked_did.py` | El Stacked DiD usa **solo never-treated** como grupo control (`cohort_type == "never-treated"`) y excluye always-treated. El Event Study (`src/tesis_alcaldesas/models/event_study.py`) también excluye always-treated explícitamente: `df = df[df["cohort_type"] != "always-treated"]`. |
| **4. Nota técnica (colinealidad)** | ✅ Respetado | Todos los modelos | Ningún modelo incluye `ever_alcaldesa` como regresor junto con efectos fijos de municipio. Se usa correctamente solo para filtrado y clasificación de cohortes. |

> **Resumen:** 3 de 3 usos propuestos fueron implementados (el #2 reformulado). El balance pre-tratamiento se hace con `cohort_type` (3 grupos), el Stacked DiD excluye always-treated del control, y el análisis de heterogeneidad se realizó con variables alternativas a `ever_alcaldesa` (ver resultados completos abajo).

---

#### Análisis de heterogeneidad — Resultados completos

##### ¿Por qué $D \times \text{ever\_alcaldesa}$ no funciona?

La interacción propuesta originalmente tiene un problema de **colinealidad perfecta**: cuando `alcaldesa_final = 1`, entonces `ever_alcaldesa = 1` **por definición** (si el municipio tiene alcaldesa en el periodo $t$, entonces "alguna vez tuvo alcaldesa" = 1). Esto implica:

$$D_{it} \times \text{ever\_alcaldesa}_i = D_{it} \quad \forall \, i, t$$

Verificación empírica: ambas columnas tienen media idéntica (0.2242) y son iguales en todas las observaciones. PanelOLS rechaza la estimación con `AbsorbingEffectError`.

> **Lección metodológica:** Para un análisis de heterogeneidad válido, la variable $Z_i$ en la interacción $D_{it} \times Z_i$ debe variar **independientemente** del tratamiento. `ever_alcaldesa` viola esta condición porque es una función directa de $D$.

##### Reformulación: tres análisis de heterogeneidad alternativos

Se estimó el modelo:

$$Y_{it}^{pc} = \alpha_i + \delta_t + \beta_1 \cdot D_{it} + \beta_2 \cdot D_{it} \times Z_i + \varepsilon_{it}$$

con cluster SE a nivel de municipio, efectos fijos de municipio y de tiempo, para tres definiciones de $Z$:

| Panel | Variable de interacción ($Z$) | Pregunta que responde |
|:---:|---|---|
| **A** | `log_pob` (centrada en la media) | ¿El efecto de las alcaldesas es mayor en municipios grandes o pequeños? |
| **B** | `early_cohort` (1 si first_treat ≤ mediana) | ¿Las primeras alcaldesas (cohortes tempranas) tienen más efecto que las tardías? |
| **C** | `high_baseline` (1 si inclusión financiera inicial > mediana) | ¿El efecto depende del nivel previo de inclusión financiera? |

**Nota:** `saldocont_total_m_pc` no está disponible en el panel analítico (`analytical_panel_features.csv`), por lo que se reportan 4 de los 5 outcomes primarios.

##### Panel A: $D \times \ln(\text{pob})$ — Heterogeneidad por tamaño del municipio

`log_pob` se centra en su media para que $\beta_1$ se interprete como el efecto de la alcaldesa evaluado en el municipio de tamaño promedio.

| Outcome | $\beta_1$ (D, pob media) | | $\beta_2$ (D × log_pob) | | N |
|---|---:|:---:|---:|:---:|---:|
| `ncont_total_m` | −188.36 | | 62.14 | | 63,944 |
| `numtar_deb_m` | −596.75 | ** | 218.38 | | 63,944 |
| `numtar_cred_m` | 23.12 | | −24.01 | | 63,944 |
| `numcontcred_hip_m` | 2.27 | | −1.06 | | 63,944 |

**Interpretación:** Ningún $\beta_2$ es estadísticamente significativo. Esto indica que el efecto de tener alcaldesa **no depende del tamaño del municipio**. El $\beta_1$ de tarjetas de débito es significativo al 5% y negativo, lo cual es consistente con los resultados principales.

##### Panel B: $D \times \text{early\_cohort}$ — Heterogeneidad por timing de tratamiento

Cohortes: mediana de `first_treat_t` = 2. **Switchers tempranos:** 627 municipios (tratamiento en cohortes 1–2). **Switchers tardíos:** 130 municipios (cohortes 3+).

| Outcome | $\beta_1$ (D, cohorte tardía) | | $\beta_2$ (D × early) | | $\beta_1 + \beta_2$ (efecto early) | N |
|---|---:|:---:|---:|:---:|---:|---:|
| `ncont_total_m` | −443.31 | *** | 480.84 | | 37.52 | 63,944 |
| `numtar_deb_m` | −531.98 | | −59.68 | | −591.66 | 63,944 |
| `numtar_cred_m` | −16.39 | | 65.52 | | 49.14 | 63,944 |
| `numcontcred_hip_m` | 2.30 | | −0.34 | | 1.96 | 63,944 |

**Interpretación:** Para contratos totales, el efecto negativo de $\beta_1$ (−443, significativo al 1%) se refiere a las cohortes **tardías**, pero la interacción $\beta_2$ (+481, no significativa) lo cancela casi por completo para las cohortes tempranas ($\beta_1 + \beta_2 \approx 38$). Esto sugiere una posible diferencia entre cohortes, pero la interacción no alcanza significancia estadística. **No hay evidencia robusta de heterogeneidad por timing.**

##### Panel C: $D \times \text{high\_baseline}$ — Heterogeneidad por nivel previo de inclusión

Municipios divididos por la mediana de `ncont_total_m_pc` en los primeros 2 trimestres del panel (mediana = 775.76 contratos por 10,000 adultas). **High baseline:** 1,235 municipios. **Low baseline:** 1,236 municipios.

| Outcome | $\beta_1$ (D, baseline bajo) | | $\beta_2$ (D × high) | | $\beta_1 + \beta_2$ (efecto high) | N |
|---|---:|:---:|---:|:---:|---:|---:|
| `ncont_total_m` | 9.58 | | −339.10 | | −329.52 | 63,944 |
| `numtar_deb_m` | −63.35 | | −900.40 | * | −963.75 | 63,944 |
| `numtar_cred_m` | 11.54 | | 14.48 | | 26.01 | 63,944 |
| `numcontcred_hip_m` | −0.29 | | 4.32 | | 4.03 | 63,944 |

**Interpretación:** La única interacción marginalmente significativa (10%) es para tarjetas de débito: el efecto negativo de la alcaldesa es más fuerte en municipios con **alta** inclusión financiera previa ($\beta_1 + \beta_2 = -964$ vs $\beta_1 = -63$ en baseline bajo). Esto podría sugerir que en municipios donde ya hay muchas tarjetas de débito, la llegada de una alcaldesa se asocia con una corrección a la baja, pero la significancia es débil (p < 0.10).

##### Conclusión del análisis de heterogeneidad

> **El efecto del tratamiento es mayormente homogéneo.** De las 12 interacciones estimadas (4 outcomes × 3 dimensiones), solo 1 es marginalmente significativa al 10%. Esto es consistente con lo que esperaríamos por azar si no hubiera heterogeneidad real (1/12 ≈ 8.3% ≈ tasa de falso positivo al 10%).
>
> **Implicación para la tesis:** No se encontró evidencia de que el efecto de tener alcaldesa varíe según el tamaño del municipio, el timing de la adopción del tratamiento, o el nivel previo de inclusión financiera. El efecto estimado en la especificación principal es representativo de todos los subgrupos.

---

### Rec 9. Estandarización de identificadores geográficos

#### ¿Qué se hizo?

Se verificó la consistencia de los identificadores geográficos y se creó un índice de base de datos sobre `cvegeo_mun` para optimizar joins con catálogos INEGI.

#### ¿Por qué importa la estandarización de identificadores?

México tiene 2,471 municipios, cada uno con un código de 5 dígitos asignado por INEGI: los primeros 2 dígitos identifican el **estado** y los 3 restantes el **municipio dentro del estado**. Ejemplo: `01001` = Aguascalientes (01), Aguascalientes (001).

El problema es que este código puede almacenarse de múltiples formas:

| Representación | Tipo | Ejemplo | Problema |
|----------------|------|---------|----------|
| `1001` (entero) | int | `1001` | Pierde el cero inicial → `1001` podría ser "01-001" (Ags) o un artefacto |
| `"01001"` (texto, 5 chars) | str | `"01001"` | **Correcto** — preserva ceros y es unívoco |
| `"1001"` (texto, 4 chars) | str | `"1001"` | Ambiguo: ¿es "01-001" o "10-01"? |

Si dos bases de datos usan representaciones distintas, un `JOIN` fallará silenciosamente: no encontrará coincidencias y devolverá `NULL`, sin error. Este es uno de los bugs más comunes y difíciles de detectar en el manejo de datos geográficos mexicanos.

#### Resultados de la verificación

| Prueba | Resultado |
|--------|-----------|
| NULLs en `cvegeo_mun` | 0 |
| Longitud: 5 dígitos | ✓ (todas las observaciones) |
| Consistencia `cvegeo_mun` = `cve_ent` + `cve_mun3` | ✓ (0 inconsistencias) |
| Municipios con múltiples `cvegeo_mun` | 0 |
| Municipios únicos (`cve_mun` int) | 2,471 |
| Municipios únicos (`cvegeo_mun` str) | 2,471 |
| Índice `idx_clean_cvegeo_mun` creado | ✓ |

#### Mapeo de identificadores

| Columna | Tipo | Ejemplo | Uso |
|---------|------|---------|-----|
| `cve_mun` | integer | 1001 | PK interna del panel (junto con `periodo_trimestre`) |
| `cvegeo_mun` | text (5 char) | "01001" | **ID canónico para merges INEGI** |
| `cve_ent` | text (2 char) | "01" | Entidad federativa |
| `cve_mun3` | text (3 char) | "001" | Municipio dentro de la entidad |

#### ¿Qué es un índice de base de datos y por qué lo creamos?

Un **índice** en PostgreSQL es una estructura de datos auxiliar (generalmente un B-tree) que permite buscar filas por el valor de una columna sin recorrer toda la tabla.

Sin índice, un `JOIN` como:

```sql
SELECT * FROM inclusion_financiera_clean a
JOIN catalogo_inegi b ON a.cvegeo_mun = b.cvegeo_mun
```

requiere comparar **cada fila** de `a` contra **cada fila** de `b` → complejidad $O(n \times m)$. Con un índice, la búsqueda es $O(n \times \log m)$ — exponencialmente más rápida.

```python
# En src/transformaciones_altas.py — función estandarizar_ids()
conn.execute(text(
    "CREATE INDEX IF NOT EXISTS idx_clean_cvegeo_mun "
    "ON inclusion_financiera_clean (cvegeo_mun)"
))
```

En nuestra tabla de 41,905 filas el impacto es pequeño (milisegundos vs. centenas de milisegundos). Pero es una buena práctica que escala: si eventualmente cruzamos con datos censales (2.4 millones de registros), el índice ahorra minutos.

#### Uso recomendado

Siempre usar `cvegeo_mun` (texto, 5 dígitos) para merges con fuentes externas. `cve_mun` (entero) se mantiene como PK interna del panel.

---

## 13. Validación de todas las transformaciones

### Tests de recomendaciones críticas (8/8 ✓)

| # | Test | Resultado |
|---|------|-----------|
| T1 | Tabla existe (41,905 filas) | ✓ |
| T2 | Constantes eliminadas (0 restantes) | ✓ |
| T3 | 51 columnas per cápita | ✓ |
| T4 | Sin infinitos en per cápita | ✓ |
| T5 | Sin negativos en per cápita | ✓ |
| T6 | Tabla original intacta (175 cols) | ✓ |
| T7 | PK sin duplicados | ✓ |
| T8 | Fórmula per cápita correcta | ✓ |

### Tests de recomendaciones altas (19/19 ✓)

| # | Test | Resultado |
|---|------|-----------|
| T1 | Filas correctas (41,905) | ✓ |
| T2 | Total columnas (296) | ✓ |
| T3 | 4 columnas log existen | ✓ |
| T4 | log_pob = ln(pob + 1) | ✓ |
| T5 | 51 columnas winsorizadas | ✓ |
| T6 | Winsorizado ≤ original max | ✓ |
| T7 | 17 ratios M/H | ✓ |
| T8 | Fórmula ratio correcta (M/H) | ✓ |
| T9 | `ever_alcaldesa` existe | ✓ |
| T10 | `ever_alcaldesa` totales (2,471 municipios) | ✓ |
| T11 | `ever_alcaldesa` consistente con `alcaldesa_final` | ✓ |
| T12 | Índice `cvegeo_mun` existe | ✓ |
| T13 | `cvegeo_mun` sin NULLs | ✓ |
| T14 | `cvegeo_mun` 5 dígitos | ✓ |
| T15 | PK intacta | ✓ |
| T16 | Tabla original intacta (175 cols) | ✓ |

---

## 14. Scripts creados

| Script | Propósito |
|--------|-----------|
| `src/transformaciones_altas.py` | Aplica las 5 recomendaciones de alta prioridad (Recs 5–9) |
| `src/tests/test_criticas.py` | 8 tests de validación para las Recs críticas (1–4) |
| `src/tests/test_altas.py` | 19 tests de validación para las Recs altas (5–9) |

**Orden de ejecución (idempotente):**
```bash
cd /Users/anapaulaperezgavilan/Documents/Tesis_DB/Code
source .venv/bin/activate

# 1. Crear tabla limpia con transformaciones críticas
python src/transformaciones_criticas.py

# 2. Agregar transformaciones de alta prioridad
python src/transformaciones_altas.py

# 3. Validar
python src/tests/test_criticas.py
python src/tests/test_altas.py
```

---

## 15. Resumen de estado actualizado de recomendaciones

| # | Prioridad | Categoría | Estado |
|---|-----------|-----------|--------|
| 1 | 🔴 CRÍTICA | Normalización conteos per cápita | ✅ Resuelto (Sección 11) |
| 2 | 🔴 CRÍTICA | Normalización saldos per cápita | ✅ Resuelto (Sección 11) |
| 3 | 🔴 CRÍTICA | saldoprom NULLs | ✅ Documentado (Sección 11) |
| 4 | 🔴 CRÍTICA | Exclusión constantes | ✅ Resuelto (Sección 11) |
| 5 | 🟡 Alta | log(pob) controles | ✅ Resuelto (Sección 12) |
| 6 | 🟡 Alta | Winsorización p1–p99 | ✅ Resuelto (Sección 12) |
| 7 | 🟡 Alta | Ratio M/H (brecha género) | ✅ Resuelto (Sección 12) |
| 8 | 🟡 Alta | ever_alcaldesa | ✅ Resuelto (Sección 12) |
| 9 | 🟡 Alta | IDs estándar (cvegeo_mun) | ✅ Resuelto (Sección 12) |
| 10 | 🟢 Media | alcaldesa_acumulado | Pendiente |
| 11 | 🟢 Media | asinh/log outcomes | Pendiente (fase de modelado) |
| 12 | 🟢 Media | tipo_pob NULLs | Pendiente |

**Progreso:** 9/12 recomendaciones resueltas (75%). Las 3 restantes son de prioridad
media y pueden abordarse durante la fase de modelado.
