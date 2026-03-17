> **Archivos fuente:**
> - `src/models/01_table1_descriptives.py` — implementación principal
> - `src/tesis_alcaldesas/models/table1_descriptives.py` — versión paquete
> - `src/models/utils.py` — definición de outcomes, `load_panel()`, helpers
>
> **Prerequisitos para entender este documento:**
> - `docs/08_DATASET_CONSTRUCCION.md` (cómo se construyó la muestra analítica)
> - `docs/09_MODELADO_PROPUESTA.md` §1 (estrategia de identificación) y §8.1 (Tabla 1 spec)
> - `docs/06_ANALISIS_DESCRIPTIVO_TESIS.md` (análisis descriptivo general del panel)
>
> **Lectura que continúa después de este documento:**
> - `docs/12_EXPLICACION_EVENT_STUDY.md` (event study: el diagnóstico de pre-trends)

# 11 — Tabla 1: Estadísticas Descriptivas (Tutorial Completo)

---

## Tabla de contenidos

| Sección | Tema | Pregunta que responde |
|---------|------|----------------------|
| 1 | ¿Por qué la Tabla 1 es el primer paso? | ¿Qué nos dice antes de estimar nada? |
| 2 | ¿Qué es una tabla descriptiva? | Definición e intuición para principiantes |
| 3 | Los tres grupos del diseño DiD | Never-treated, switchers, always-treated |
| 4 | ¿Qué variables se reportan? | Outcomes, controles, tamaño de muestra |
| 5 | ¿Cómo se define el periodo "pre-tratamiento"? | ¿Qué observaciones entran? |
| 6 | Nuestros resultados: la Tabla 1 completa | Los números reales de la tesis |
| 7 | Cómo leer la tabla: guía columna por columna | Interpretación para principiantes |
| 8 | ¿Qué buscamos? Balance y señales de alerta | Criterios de evaluación |
| 9 | Interpretación de nuestros resultados | ¿Los grupos son comparables? |
| 10 | La implementación en Python | Código paso a paso |
| 11 | ¿Qué hacer según el resultado? | Árbol de decisión |
| 12 | Conexión con el event study | ¿Por qué la Tabla 1 va primero? |

---

## 1. ¿Por qué la Tabla 1 es el primer paso?

### 1.1 El contexto en el pipeline

```
 Muestra analítica                            ← 08_DATASET_CONSTRUCCION
       │
       ▼
 ┌──────────────────────┐
 │ PASO 1: TABLA 1      │ ← 🔎 ESTÁS AQUÍ
 │ (Descriptivos)       │   ¿Los datos tienen sentido?
 └──────────┬───────────┘   ¿Los grupos son comparables?
            │
            ▼
 ┌──────────────────────┐
 │ PASO 2: Event Study  │ ← docs/12_EXPLICACION_EVENT_STUDY.md
 │ (Diagnóstico)        │   ¿Es creíble el DiD?
 └──────────┬───────────┘
            │
            ▼
 ┌──────────────────────┐
 │ PASO 3: TWFE         │ ← Modelo principal
 └──────────────────────┘
```

### 1.2 ¿Qué nos dice antes de estimar nada?

La Tabla 1 no estima ningún efecto causal. Es un **diagnóstico previo** que responde
tres preguntas fundamentales:

1. **¿Los datos son razonables?** ¿Las medias y desviaciones estándar tienen sentido
   económico? ¿Hay valores extremos o ceros masivos?

2. **¿Los grupos son comparables?** ¿Los municipios que eventualmente tendrán alcaldesa
   se parecen a los que no, antes de que el tratamiento ocurra?

3. **¿Tenemos suficientes observaciones?** ¿La muestra por grupo es lo bastante grande
   para hacer inferencia estadística?

> **Analogía:** No puedes comparar la efectividad de un medicamento si un grupo tiene
> 20 años promedio y el otro tiene 70 años. Primero tienes que verificar que los grupos
> son "comparables" — eso es la Tabla 1.

### 1.3 ¿Qué pasa si te la saltas?

- Podrías estimar un event study perfecto... sobre datos con errores.
- Podrías concluir que "no hay efecto" cuando en realidad un outcome tiene 95% de
  ceros y simplemente no hay variación.
- Podrías no darte cuenta de que los grupos son radicalmente diferentes en tamaño o
  composición.

---

## 2. ¿Qué es una tabla descriptiva?

### 2.1 Definición para principiantes

Una **tabla de estadísticas descriptivas** resume las características principales de
tus datos *sin hacer ninguna estimación causal*. Típicamente reporta:

| Estadístico | ¿Qué mide? | Fórmula |
|-------------|-----------|---------|
| **Media** ($\bar{x}$) | El valor "típico" o promedio | $\bar{x} = \frac{1}{N}\sum_{i=1}^N x_i$ |
| **Desviación estándar** ($s$) | Qué tan dispersos están los datos | $s = \sqrt{\frac{1}{N-1}\sum(x_i - \bar{x})^2}$ |
| **N** (observaciones) | Cuántos datos tenemos | Conteo de filas válidas |

### 2.2 ¿Por qué se separa por grupos?

En un diseño de diferencias en diferencias, no basta con reportar las estadísticas
para *todo* el panel junto. Necesitas ver los grupos **por separado** porque quieres
evaluar si el grupo de tratamiento y el de control son razonablemente parecidos
*antes* de que ocurra el tratamiento.

Si los grupos son muy diferentes en el baseline (pre-tratamiento), cualquier efecto
que estimes podría deberse a esas diferencias preexistentes y no al tratamiento.

### 2.3 ¿Cuál es el estándar en la literatura?

En economía empírica (y en la mayoría de ciencias sociales), la Tabla 1 es la
**primera tabla del paper**. Casi siempre tiene esta estructura:

```
                  | Full     | Control  | Tratamiento | Diferencia
                  | sample   | (pre)    | (pre)       | (p-value)
──────────────────|──────────|──────────|─────────────|──────────
Variable 1        | μ (σ)    | μ (σ)    | μ (σ)       | Δ (p)
Variable 2        | μ (σ)    | μ (σ)    | μ (σ)       | Δ (p)
...               |          |          |             |
──────────────────|──────────|──────────|─────────────|──────────
N observaciones   | N₁       | N₂       | N₃          |
N unidades        | n₁       | n₂       | n₃          |
```

---

## 3. Los tres grupos del diseño DiD

### 3.1 Definición de cada grupo

Nuestro panel tiene **2,471 municipios** observados durante 17 trimestres. Según
su relación con el tratamiento (tener alcaldesa), se clasifican en tres grupos:

| Grupo | Definición | N municipios | ¿Cuándo se observan? |
|-------|-----------|--------------|----------------------|
| **Never-treated** | Nunca tuvieron alcaldesa en todo el panel | 1,476 | Todos los 17 trimestres |
| **Switchers (pre)** | Cambian de tratamiento Y tienen `first_treat_t > 0` | 600 | Solo periodos pre-tratamiento (event_time < 0) |
| **Always-treated** | Tenían alcaldesa desde el inicio del panel (2018Q3) y nunca la pierden | 101 | Todos los trimestres (sin periodo pre) |

> **¿Por qué 600 y no 894?** El panel tiene **894 switchers** en total (municipios
> cuyo `alcaldesa_final` cambia al menos una vez). Pero **294 de ellos están
> "left-censored"**: ya tenían alcaldesa en 2018Q3 (`first_treat_t = 0`) y por lo
> tanto no tienen **ninguna** observación pre-tratamiento (`event_time < 0`). Los
> 294 comenzaron tratados y en algún momento pierden la alcaldesa — sus trayectorias
> típicas son `1111111111111 0000` o `1000000000000 1111`.
>
> Estos 294 se excluyen de la Tabla 1 (columna "Switchers pre") porque no hay nada
> que reportar en su periodo pre. También se excluyen del event study porque sin
> contrafactual pre-tratamiento, no pueden anclar la estimación causal.
>
> **Resumen:**
> | Sub-grupo | N muni | En la Tabla 1 | En event study / DiD |
> |-----------|--------|:---:|:---:|
> | Switchers con pre (`first_treat_t > 0`) | 600 | ✅ | ✅ |
> | Switchers left-censored (`first_treat_t = 0`) | 294 | ❌ | ❌ |
> | Total switchers | 894 | — | — |

### 3.2 ¿Por qué estos tres grupos y no dos?

| ¿Por qué separar always-treated? | Explicación |
|---|---|
| No tienen periodo pre-tratamiento | No podemos ver cómo eran "antes" de la alcaldesa — ya la tenían al inicio |
| No contribuyen al diagnóstico | En el event study se excluyen porque no generan leads ($k < 0$) |
| Pero son informativos | Sus medias nos dicen cómo es un municipio "siempre tratado" |

### 3.3 ¿Qué es el periodo "pre-tratamiento" para cada grupo?

| Grupo | Periodos que se reportan en Tabla 1 | Justificación |
|-------|--------------------------------------|---------------|
| Never-treated | **Todos** (17 trimestres) | Nunca reciben tratamiento, todos los periodos son "pre" |
| Switchers | Solo donde `event_time < 0` | Antes de que la alcaldesa llegue al poder |
| Always-treated | **Todos** (17 trimestres) | No tienen pre, se reporta todo (con nota) |

En el código:

```python
mask_never     = df["cohort_type"] == "never-treated"
mask_switch_pre = (df["cohort_type"] == "switcher") & (df["event_time"] < 0)
mask_always    = df["cohort_type"] == "always-treated"
```

### 3.4 Tratamiento no absorbente e interpretación ITT

Un detalle importante: en nuestro panel, el tratamiento **no es absorbente**. Un
municipio puede ganar una alcaldesa y después perderla (por nuevas elecciones). De
los 600 switchers con pre-periodo:

| Sub-tipo | N muni | Descripción |
|----------|--------|-------------|
| **Absorbing** (0→1, se mantiene) | 409 | Caso canónico para DiD |
| **Con reversal** (gana y pierde) | 191 | Tratamiento no permanente |

In the Stacked DiD, `D_stack = 1` para todos los periodos post-`first_treat_t`,
incluso si la alcaldesa fue reemplazada. Esto genera un **12.5% de mismatch** entre
`D_stack` y `alcaldesa_final` real en periodos post.

> **Implicación:** Las estimaciones del TWFE y event study son robustas a esta
> definición de tratamiento. El mismatch de 12.5% implica que las estimaciones
> se interpretan como **ITT (Intent-to-Treat)**, midiendo el efecto de
> *haber recibido una alcaldesa por primera vez*, no el efecto de *tener actualmente*
> una alcaldesa. Esto es estándar en economía política — las elecciones definen
> la asignación al tratamiento, y el análisis sigue esa asignación inicial.

---

## 4. ¿Qué variables se reportan?

### 4.1 Variables de tratamiento

| Variable | Descripción | ¿Por qué reportarla? |
|----------|------------|----------------------|
| `alcaldesa_final` (D) | = 1 si hay alcaldesa en el municipio-trimestre | Confirma que never-treated tiene media 0, switchers pre tiene media 0, y always-treated tiene media 1 |

### 4.2 Variables de control / contexto

| Variable | Descripción | ¿Por qué reportarla? |
|----------|------------|----------------------|
| `log_pob` | ln(Población total) | Controla por tamaño del municipio. Si los switchers son sistemáticamente más grandes, el efecto podría capturar "tamaño" y no "alcaldesa" |
| `pob_adulta_m` | Población adulta femenina | Denominador de las tasas per cápita |

### 4.3 Los 5 outcomes primarios

Se reportan en **dos escalas** para cada outcome:

| Outcome | Variable _pc (per cápita) | Variable _pc_asinh (asinh) |
|---------|--------------------------|---------------------------|
| Contratos totales | `ncont_total_m_pc` | `ncont_total_m_pc_asinh` |
| Tarjetas débito | `numtar_deb_m_pc` | `numtar_deb_m_pc_asinh` |
| Tarjetas crédito | `numtar_cred_m_pc` | `numtar_cred_m_pc_asinh` |
| Créditos hipotecarios | `numcontcred_hip_m_pc` | `numcontcred_hip_m_pc_asinh` |
| Saldo total | `saldocont_total_m_pc` | `saldocont_total_m_pc_asinh` |

### 4.4 ¿Por qué reportar ambas escalas?

- **Per cápita (pc):** Escala interpretable — "3,324 contratos por cada 10,000 mujeres
  adultas". Permite al lector tener intuición económica.
- **asinh:** Escala del modelo — los modelos econométricos usan la transformación
  asinh. Al reportar ambas, el lector puede comparar la escala "real" con la escala
  "estadística".

---

## 5. ¿Cómo se define el periodo "pre-tratamiento"?

### 5.1 La lógica formal

Para la Tabla 1, usamos una definición conservadora:

$$
\text{Pre-tratamiento}_{it} = \begin{cases}
\text{Todos los } t & \text{si } i \in \text{Never-treated} \\
t : \text{event\_time}_{it} < 0 & \text{si } i \in \text{Switchers} \\
\text{Todos los } t & \text{si } i \in \text{Always-treated (con nota)}
\end{cases}
$$

### 5.2 ¿Por qué $<$ 0 y no $\leq$ 0?

Porque $k = 0$ es el **primer periodo con tratamiento**. Si incluyéramos $k = 0$,
estaríamos contaminando las estadísticas "pre" con el efecto del tratamiento.

### 5.3 Implicación para el tamaño de muestra

| Grupo | N observaciones | Explicación |
|-------|----------------|-------------|
| Never-treated | 25,016 | 1,476 muni × 17 trimestres (aprox.) |
| Switchers (pre) | 4,036 | 600 muni × variable (depende de cuándo llega la alcaldesa) |
| Always-treated | 1,704 | 101 muni × ~17 trimestres |

> **Nota:** Los switchers tienen pocas observaciones pre porque muchos entraron en
> cohortes tempranas (2018Q4), dejando pocos trimestres antes del tratamiento.

---

## 6. Nuestros resultados: la Tabla 1 completa

### 6.1 Panel A — Variables de contexto

| Variable | Never-treated | Switchers (pre) | Always-treated |
|----------|:------------:|:---------------:|:--------------:|
| **Alcaldesa (D)** | 0.000 (0.000) | 0.000 (0.000) | 1.000 (0.000) |
| **ln(Población)** | 9.436 (1.622) | 9.947 (1.501) | 9.158 (1.700) |
| **Pob. adulta mujeres** | 17,823 (52,245) | 28,564 (72,825) | 24,854 (89,176) |

### 6.2 Panel B — Outcomes en escala asinh (escala del modelo)

| Variable | Never-treated | Switchers (pre) | Always-treated |
|----------|:------------:|:---------------:|:--------------:|
| **Contratos totales** | 6.977 (2.448) | 7.672 (2.026) | 6.832 (2.282) |
| **Tarjetas débito** | 7.002 (2.335) | 7.315 (2.545) | 6.734 (2.261) |
| **Tarjetas crédito** | 5.785 (2.376) | 6.315 (2.236) | 5.689 (2.236) |
| **Créditos hipotecarios** | 2.088 (2.007) | 2.641 (1.955) | 1.850 (2.199) |
| **Saldo total** | 13.635 (5.377) | 15.078 (4.470) | 13.426 (4.815) |

### 6.3 Panel C — Outcomes en per cápita (escala interpretable)

| Variable | Never-treated | Switchers (pre) | Always-treated |
|----------|:------------:|:---------------:|:--------------:|
| **Contratos totales** | 3,324 (6,415) | 4,022 (7,055) | 3,476 (11,638) |
| **Tarjetas débito** | 3,404 (7,424) | 4,329 (7,859) | 2,806 (7,915) |
| **Tarjetas crédito** | 792 (1,436) | 1,055 (2,353) | 791 (6,359) |
| **Créditos hipotecarios** | 39 (289) | 34 (74) | 46 (172) |
| **Saldo total** | 77.5M (206.8M) | 91.6M (176.7M) | 63.8M (172.0M) |

### 6.4 Panel D — Tamaños de muestra

| | Never-treated | Switchers (pre) | Always-treated |
|---|:---:|:---:|:---:|
| **N municipios** | 1,476 | 600 | 101 |
| **N observaciones** | 25,016 | 4,036 | 1,704 |

> **Formato:** Media (Desviación estándar). Los switchers se evalúan solo en periodos
> pre-tratamiento. Los always-treated no tienen periodo pre; se reportan todos sus
> periodos.

> **📖 Cómo leer la Tabla 1 completa — los 4 paneles juntos (paso a paso)**
>
> **Paso 1 — Panel A (contexto): ¿Los grupos son comparables?**
> Compara las columnas horizontalmente. Los switchers son ligeramente más grandes
> (ln(Pob) = 9.95 vs 9.44) → municipios más urbanos eligen más alcaldesas.
> ¿Es problemático? No: los FE de municipio absorben diferencias permanentes.
>
> **Paso 2 — Panel B (asinh): ¿Las escalas del modelo están bien?**
> Estas son las variables que entran al TWFE / Stacked DiD. Verifica:
> - ¿Hay medias negativas? No → transformación asinh funciona correctamente.
> - ¿Hay medias cercanas a 0? Créditos hipotecarios = 2.09 → baja actividad.
> - ¿Las SD son del mismo orden que las medias? Sí → dispersión razonable.
>
> **Paso 3 — Panel C (per cápita): ¿Los números tienen sentido económico?**
> Contratos = 3,324 por 10K mujeres ≈ 33% tienen contrato. ¿Razonable? Sí.
> Hipotecarios = 39 por 10K ≈ 0.4% → muchos municipios rurales sin hipotecas.
> Saldo = $77.5M promedio → amplia dispersión (SD = $206.8M).
>
> **Paso 4 — Panel D (tamaño de muestra): ¿Hay poder estadístico?**
> Never-treated: 25,016 obs (amplio). Switchers pre: 4,036 (adecuado).
> Always-treated: 1,704 (suficiente para referencia, no para estimación).
>
> **Paso 5 — Busca señales de alerta (§8 del documento):**
> ✅ Medias razonables, ✅ Diferencias explicables, ⚠️ Hipotecarios bajos.
> Veredicto: datos listos para el event study.

---

## 7. Cómo leer la tabla: guía columna por columna

### 7.1 Columna "Never-treated"

Estos son los **1,476 municipios** que nunca tuvieron alcaldesa durante todo el panel.
Son el grupo de **control natural**. Sus estadísticas representan el "baseline" contra
el cual comparamos todo.

**¿Qué leer aquí?**
- ¿Las medias tienen sentido económico? ¿3,324 contratos por 10K mujeres parece razonable?
- ¿Las desviaciones son muy grandes? (Sí — hay mucha heterogeneidad entre municipios)
- ¿Hay variables con medias cercanas a cero? (créditos hipotecarios: media 39 ← muchos municipios rurales sin hipotecas)

### 7.2 Columna "Switchers (pre)"

Estos son los **600 municipios** que eventualmente tendrán alcaldesa, evaluados
*antes* de que eso ocurra. Son el grupo de **tratamiento futuro, en su estado pre**.

**¿Qué leer aquí?**
- ¿Se parecen a los never-treated? Si son muy diferentes, el DiD podría estar
  capturando diferencias preexistentes, no el efecto de la alcaldesa.
- ¿Las medias son sistemáticamente más altas o más bajas?

### 7.3 Columna "Always-treated"

Los **101 municipios** que tenían alcaldesa desde 2018Q3. No tienen periodo pre,
así que se reporta todo el panel. Sirven como referencia informativa.

### 7.4 ¿Y la columna "Diferencia"?

Nuestra implementación actual no incluye un test formal de diferencia de medias
(t-test) entre never-treated y switchers (pre). Esto se podría agregar, pero
las diferencias son visibles directamente comparando las columnas. En la versión
de la tesis final, se puede añadir una columna con $\Delta$ y p-value.

---

## 8. ¿Qué buscamos? Balance y señales de alerta

### 8.1 El concepto de "balance"

En un experimento aleatorizado (RCT), el tratamiento se asigna al azar, así que
los grupos tratado y control son, en expectativa, idénticos en todas las variables
observables e inobservables. La Tabla 1 del RCT debería mostrar medias similares
en todo.

En un estudio observacional como el nuestro (DiD), **no esperamos balance perfecto**
porque el tratamiento no es aleatorio — hay municipios que, por razones políticas,
culturales o demográficas, son más propensos a tener alcaldesa. Lo que buscamos es:

1. **No hay diferencias dramáticas** que invaliden la comparación
2. **Las diferencias tienen sentido** y se pueden explicar
3. **Los efectos fijos del DiD** (municipio + tiempo) absorben las diferencias permanentes

### 8.2 Señales verdes (✅)

| Señal | ¿Qué indica? |
|-------|-------------|
| Medias del mismo orden de magnitud | Los grupos viven en "mundos similares" |
| Desviaciones estándar similares | La dispersión es comparable |
| N observaciones suficientes | Tenemos poder estadístico para las estimaciones |
| Tratamiento = 0 en pre | Confirma que la definición de pre-tratamiento funciona |

### 8.3 Señales amarillas (⚠️)

| Señal | ¿Qué indica? | ¿Qué hacer? |
|-------|-------------|-------------|
| Diferencias moderadas en medias (10-30%) | Los switchers son algo diferentes | Documentar, pero los FE del DiD absorben esto |
| Un outcome con media muy baja | Poca actividad (ej. hipotecas en municipios rurales) | Precaución al interpretar, reportar como limitación |
| N observaciones desbalanceado | Un grupo tiene muchas más obs | Normal en DiD — never-treated suele ser más grande |

### 8.4 Señales rojas (❌)

| Señal | ¿Qué indica? | ¿Qué hacer? |
|-------|-------------|-------------|
| Diferencias de órdenes de magnitud | Los grupos son incomparables | Revisar la definición de tratamiento/control |
| Un outcome con 80%+ de ceros | Sin variación para estimar | Considerar excluir o usar modelo diferente (LPM) |
| N municipios muy pequeño en un grupo | Poca representatividad | Agrupar cohortes o redefinir grupos |

---

## 9. Interpretación de nuestros resultados

### 9.1 Variables de contexto

**ln(Población):**
- Never-treated: 9.44 → Switchers: 9.95 → Always-treated: 9.16
- Los switchers son **ligeramente más grandes** (exp(9.95) ≈ 21,000 vs exp(9.44) ≈ 12,600)
- Los always-treated son los más pequeños
- **Interpretación:** Los municipios que eligen alcaldesas tienden a ser un poco más
  urbanos. Esto es consistente con la literatura: municipios urbanos tienen más
  participación política femenina.
- **¿Es problemático?** No gravemente. El control `log_pob` en la regresión y los
  efectos fijos de municipio absorben esta diferencia.

**Población adulta femenina:**
- Never-treated: 17,823 → Switchers: 28,564 → Always-treated: 24,854
- Consistente con que los switchers son más grandes
- Las desviaciones estándar son enormes (52K–89K) → mucha heterogeneidad

### 9.2 Outcomes en escala asinh (la que usa el modelo)

| Outcome | Never-treated | Switchers (pre) | Δ aprox. | ¿Preocupante? |
|---------|:---:|:---:|:---:|:---:|
| Contratos totales | 6.98 | 7.67 | +10% | ⚠️ Moderado |
| Tarjetas débito | 7.00 | 7.32 | +4.5% | ✅ Menor |
| Tarjetas crédito | 5.78 | 6.32 | +9% | ⚠️ Moderado |
| Créditos hipotecarios | 2.09 | 2.64 | +26% | ⚠️ Notable |
| Saldo total | 13.63 | 15.08 | +10.6% | ⚠️ Moderado |

**Patrón general:** Los switchers tienen medias **sistemáticamente más altas** en
todos los outcomes. Esto tiene sentido: los municipios con más actividad económica
(más contratos, más tarjetas) también tienden a tener mayor participación política
femenina.

**¿Es problemático para el DiD?** No, por dos razones:

1. **Los efectos fijos de municipio** ($\alpha_i$) absorben *todas* las diferencias
   permanentes entre municipios. La variación que el DiD explota es *within* (dentro
   de cada municipio a lo largo del tiempo).

2. **Lo que importa no es el nivel, sino la tendencia.** El supuesto de tendencias
   paralelas no requiere que los grupos tengan las mismas medias — requiere que sus
   *trayectorias* sean paralelas. Dos municipios pueden tener niveles muy diferentes
   de inclusión financiera y aún así seguir trayectorias paralelas.

### 9.3 Observación sobre créditos hipotecarios

La media de créditos hipotecarios es notablemente baja en todos los grupos (2.09
en asinh, 39 per cápita para never-treated). Esto refleja que **muchos municipios
rurales tienen cero o casi cero créditos hipotecarios**. La alta desviación estándar
relativa (289 vs media de 39 en per cápita) confirma que la distribución es muy
sesgada a la derecha.

> **Implicación:** Los resultados del event study y TWFE para créditos hipotecarios
> deben interpretarse con cautela. La transformación asinh ayuda precisamente con
> este tipo de distribución (acepta ceros), pero el poder estadístico para detectar
> efectos puede ser limitado dado que hay poca variación.

### 9.4 Observación sobre always-treated

Los always-treated tienen medias **menores** que los switchers y similares a los
never-treated en la mayoría de outcomes. Esto sugiere que los municipios que tenían
alcaldesa desde el inicio del panel no son municipios particularmente más ricos o
urbanos — son un grupo heterogéneo. Esto es informativo pero no afecta al DiD,
ya que los always-treated se excluyen del event study y tienen un rol limitado en
el Stacked DiD.

---

## 10. La implementación en Python

### 10.1 Flujo completo paso a paso

```python
# ==========================================
# PASO 1: Cargar el panel analítico
# ==========================================
df = load_panel()
# → DataFrame con ~41,905 filas (2,471 muni × 17 trimestres)
# → Índice: (cve_mun, t_index)
# → Columnas clave: cohort_type, event_time, alcaldesa_final

# ==========================================
# PASO 2: Definir los grupos pre-tratamiento
# ==========================================
mask_never     = df["cohort_type"] == "never-treated"
mask_switch_pre = (df["cohort_type"] == "switcher") & (df["event_time"] < 0)
mask_always    = df["cohort_type"] == "always-treated"

groups = {
    "Never-treated":   df.loc[mask_never],       # 25,016 obs
    "Switchers (pre)": df.loc[mask_switch_pre],   # 4,036 obs
    "Always-treated":  df.loc[mask_always],       # 1,704 obs
}

# ==========================================
# PASO 3: Definir variables a describir
# ==========================================
vars_desc = {
    "alcaldesa_final": "Alcaldesa (D)",
    "log_pob": "ln(Población)",
    "pob_adulta_m": "Pob. adulta mujeres",
}
# Agregar los 5 outcomes primarios en ambas escalas
for out in PRIMARY_5:
    vars_desc[f"{out}_pc_asinh"] = f"{OUTCOME_DEFS[out]['label']} (asinh)"
    vars_desc[f"{out}_pc"]       = f"{OUTCOME_DEFS[out]['label']} (pc)"

# ==========================================
# PASO 4: Calcular media y SD por grupo
# ==========================================
rows = []
for var, label in vars_desc.items():
    row = {"Variable": label}
    for gname, gdf in groups.items():
        vals = gdf[var].dropna()
        row[f"{gname} Mean"] = vals.mean()
        row[f"{gname} SD"]   = vals.std()
        row[f"{gname} N"]    = len(vals)
    rows.append(row)

# ==========================================
# PASO 5: Agregar N municipios por grupo
# ==========================================
mun_row = {"Variable": "N municipios"}
for gname, gdf in groups.items():
    mun_row[f"{gname} Mean"] = gdf.reset_index()["cve_mun"].nunique()
rows.append(mun_row)

tab = pd.DataFrame(rows).set_index("Variable")

# ==========================================
# PASO 6: Exportar CSV y LaTeX
# ==========================================
tab.to_csv("outputs/paper/tabla_1_descriptiva.csv")
# + versión LaTeX formateada (ver código fuente para detalles)
```

### 10.2 Detalles del formateo LaTeX

El script genera automáticamente una tabla LaTeX lista para incluir en el paper:

- Números grandes (> 1M) se formatean con comas: `77,482,761`
- Números medianos (100–1M) con 1 decimal: `3,324.3`
- Números pequeños con 3 decimales: `9.436`
- Desviación estándar entre paréntesis: `9.436 (1.622)`

### 10.3 Outputs generados

| Archivo | Descripción | Ubicación |
|---------|-------------|-----------|
| `tabla_1_descriptiva.csv` | Tabla completa en formato CSV | `outputs/paper/` |
| `tabla_1_descriptiva.tex` | Tabla LaTeX formateada para el paper | `outputs/paper/` |

### 10.4 Ejecución

```bash
# Desde la raíz del proyecto:
python -m tesis_alcaldesas.models.table1_descriptives

# O directamente:
python src/models/01_table1_descriptives.py
```

---

## 11. ¿Qué hacer según el resultado?

### 11.1 Árbol de decisión

```
Tabla 1 completada
        │
        ▼
¿Las medias tienen sentido económico?
(no hay negativos, no hay NaN masivos,
 órdenes de magnitud razonables)
        │
   ┌────┴────┐
   │         │
  SÍ        NO
   │         │
   ▼         ▼
¿Las diferencias   Revisar pipeline
entre grupos son   de construcción
"razonables"?      del dataset
(no hay un grupo   (08_DATASET_CONSTRUCCION)
 10x mayor)
   │
   ┌────┴────┐
   │         │
  SÍ        NO
   │         │
   ▼         ▼
¿Hay outcomes   Redefinir grupos
con medias      o revisar
≈ 0?            tratamiento
   │
   ┌────┴────┐
   │         │
  NO        SÍ
   │         │
   ▼         ▼
 ✅ Pro-   Documentar como
   ceder   limitación; considerar
   al      modelo alternativo
   EVENT   (LPM para extensivo)
   STUDY
```

### 11.2 Nuestro diagnóstico

| Criterio | Resultado | Conclusión |
|----------|-----------|------------|
| ¿Medias con sentido económico? | ✅ Sí | Todos los outcomes en rangos razonables |
| ¿Diferencias entre grupos razonables? | ✅ Sí | Switchers ~10-25% más altos, explicable |
| ¿Outcomes con media ≈ 0? | ⚠️ Créditos hipotecarios bajos | Documentar, pero asinh maneja ceros |
| ¿N suficiente por grupo? | ✅ Sí | Mínimo 1,704 obs (always-treated) |

**Veredicto:** ✅ Proceder al event study (`docs/12_EXPLICACION_EVENT_STUDY.md`).

---

## 12. Conexión con el event study

### 12.1 ¿Por qué la Tabla 1 va antes?

```
 Tabla 1                          Event Study
 ───────                          ───────────
 "¿Los datos son sensatos?"       "¿El DiD es creíble?"
 "¿Los grupos son comparables?"   "¿Las tendencias eran paralelas?"

 Compara NIVELES                  Compara TENDENCIAS
 en el pre-tratamiento            a lo largo del tiempo

 Sin regresión                    Con regresión (PanelOLS)
 (solo medias y SD)               (coeficientes estimados)

 Si falla → datos malos           Si falla → estrategia inválida
 PARAR y limpiar                  PARAR y replantear
```

### 12.2 ¿Qué información de la Tabla 1 usa el event study?

1. **Los 5 outcomes primarios:** El event study estima un coeficiente para cada uno.
   La Tabla 1 te dice qué esperar en términos de magnitud y variación.

2. **La composición de grupos:** El event study excluye a los always-treated (101 muni).
   La Tabla 1 confirma que los restantes (never-treated + switchers) tienen suficientes
   observaciones.

3. **Señales de precaución:** Si la Tabla 1 muestra que créditos hipotecarios tiene
   media muy baja, el event study para ese outcome puede tener poco poder. Esto prepara
   tu expectativa.

### 12.3 Lo que la Tabla 1 NO puede hacer

| Lo que NO hace | Por qué |
|----------------|---------|
| Probar tendencias paralelas | Solo muestra niveles, no trayectorias |
| Probar causalidad | Es puramente descriptiva |
| Garantizar que el DiD funciona | Es necesaria pero no suficiente |

> **Próximo paso:** Con la Tabla 1 confirmando que los datos son sensatos y los grupos
> son razonablemente comparables, procedemos al event study — la prueba diagnóstica
> de tendencias paralelas. Ver `docs/12_EXPLICACION_EVENT_STUDY.md`.

---

## Glosario rápido

| Término | Definición |
|---------|-----------|
| **Media** ($\bar{x}$) | Promedio aritmético de los valores |
| **Desviación estándar** ($s$) | Medida de dispersión: qué tan lejos están los datos del promedio |
| **Balance** | Similaridad de las características observables entre grupos |
| **Pre-tratamiento** | Periodo antes de que el municipio reciba tratamiento |
| **Never-treated** | Municipios sin alcaldesa en todo el panel |
| **Switchers** | Municipios que cambian de estado durante el panel |
| **Always-treated** | Municipios con alcaldesa desde el inicio |
| **Per cápita** | Dividido entre la población (×10,000 mujeres adultas en nuestro caso) |
| **asinh** | Seno hiperbólico inverso: $\text{asinh}(x) = \ln(x + \sqrt{x^2 + 1})$ |
| **Tabla 1** | Primera tabla del paper: estadísticas descriptivas por grupo |
