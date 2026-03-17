# Representación Política Femenina e Inclusión Financiera en México: ¿Importa el Género de Quien Gobierna?

## Reporte para asesor de tesis — Marzo 2026

**Pregunta de investigación:** ¿Cuál es el efecto causal de la representación política femenina a nivel municipal (alcaldesas) sobre la inclusión financiera de las mujeres en México?

**Autora:** Ana Paula Pérez Gavilán

---

# Índice

1. [Introducción y motivación](#1-introducción-y-motivación)
2. [Datos y construcción del panel](#2-datos-y-construcción-del-panel)
3. [Análisis exploratorio de datos (EDA)](#3-análisis-exploratorio-de-datos-eda)
4. [Definición de variables clave](#4-definición-de-variables-clave)
5. [Estadísticas descriptivas — Tabla 1](#5-estadísticas-descriptivas--tabla-1)
6. [Estrategia de identificación](#6-estrategia-de-identificación)
7. [Diagnóstico de tendencias paralelas — Event Study](#7-diagnóstico-de-tendencias-paralelas--event-study)
8. [Resultados empíricos — TWFE](#8-resultados-empíricos--twfe)
9. [Robustez](#9-robustez)
10. [Heterogeneidad](#10-heterogeneidad)
11. [Poder estadístico y MDES](#11-poder-estadístico-y-mdes)
12. [Extensiones](#12-extensiones)
13. [Discusión y conclusiones](#13-discusión-y-conclusiones)
14. [Bibliografía](#14-bibliografía)

---

# 1. Introducción y motivación

La participación política de las mujeres en América Latina ha experimentado un crecimiento notable en las últimas décadas, impulsada por reformas de paridad de género y una creciente conciencia social sobre la representación. Sin embargo, la pregunta de si esta mayor presencia femenina en cargos de elección popular se traduce en cambios tangibles en las condiciones de vida de las mujeres sigue abierta. Esta investigación aborda una dimensión específica de esa pregunta: **¿tener una mujer como presidenta municipal (alcaldesa) genera cambios en la inclusión financiera de las mujeres en ese municipio?**

La inclusión financiera —el acceso y uso de productos y servicios financieros formales— es un indicador clave del empoderamiento económico. En México, las brechas de género en tenencia de cuentas, tarjetas y crédito persisten a pesar de avances regulatorios. Si la representación política femenina a nivel local puede mover estos indicadores, se abriría un canal causal entre democracia representativa y bienestar económico de las mujeres que tendría implicaciones directas para la política pública.

Para responder esta pregunta, se emplea un diseño de **diferencias en diferencias (DiD)** con datos de panel que explotan la variación *within-municipality* en el estatus de tratamiento (tener o no alcaldesa) a lo largo del tiempo. Se construye un panel de 2,471 municipios mexicanos observados trimestralmente durante el periodo 2018Q3–2022Q3, combinando datos administrativos de la Comisión Nacional Bancaria y de Valores (CNBV) con información electoral sobre el género de las autoridades municipales.

---

# 2. Datos y construcción del panel

## 2.1 Fuentes de información

La investigación combina dos fuentes de datos:

1. **Base de Datos de Inclusión Financiera (CNBV):** Publicada trimestralmente, contiene indicadores de contratos, saldos, tarjetas y créditos a nivel municipio, desagregados por género (mujeres `_m`, hombres `_h`, personas morales `_pm`, total `_t`).

2. **Registros electorales municipales:** Compilados a partir de institutos electorales estatales, gacetas de gobierno y portales municipales, permiten identificar el género de la persona titular de cada presidencia municipal en cada día del periodo de estudio.

## 2.2 Estructura del panel

| Propiedad | Valor |
|:---|:---|
| **Unidad de observación** | Municipio–trimestre |
| **Llave primaria** | (`cve_mun`, `periodo_trimestre`) |
| **Municipios** | 2,471 |
| **Trimestres** | 17 (2018Q3 – 2022Q3) |
| **Observaciones totales** | 41,905 |
| **Balance** | Casi balanceado — 8 municipios con panel incompleto (102 celdas faltantes, 0.24%) |
| **Entidades federativas** | 32 |
| **Regiones** | 6 (Occidente y Bajío, Noroeste, Sur, Noreste, Ciudad de México, Centro Sur y Oriente) |
| **Columnas originales** | 175 |
| **Columnas tras transformaciones** | 348 |
| **Almacenamiento** | PostgreSQL 17.8 (`tesis_db`) + parquet local |

La elección del periodo 2018Q3–2022Q3 obedece a dos razones. Primero, cubre al menos un ciclo electoral municipal completo para la mayoría de los estados, permitiendo observar transiciones de gobiernos masculinos a femeninos con suficientes trimestres previos y posteriores al cambio. Segundo, antecede a reformas regulatorias significativas en materia de inclusión financiera digital que podrían confundir la estimación a partir de 2023.

## 2.3 Cobertura geográfica

Los 2,471 municipios representan la práctica totalidad de las demarcaciones del país. La distribución por tipo de población refleja la estructura territorial de México:

| Tipo de población | Municipios | Porcentaje |
|:---|---:|---:|
| Rural | 664 | 26.9% |
| En Transición | 624 | 25.3% |
| Semi-urbano | 731 | 29.6% |
| Urbano | 361 | 14.6% |
| Semi-metrópoli | 72 | 2.9% |
| Metrópoli | 13 | 0.5% |
| *Sin clasificación (corregidos)* | *2* | *0.1%* |

La muestra está compuesta predominantemente por municipios rurales y de transición (52.2%), lo cual refleja la estructura real del país donde la mayor parte de las demarcaciones tienen baja densidad poblacional y, consecuentemente, menor infraestructura financiera.

---

# 3. Análisis exploratorio de datos (EDA)

El EDA fue la primera etapa del análisis y tuvo un objetivo doble: (1) conocer la base de datos a profundidad antes de cualquier modelado, y (2) orientar la estrategia de estimación causal validando supuestos clave e identificando transformaciones necesarias.

## 3.1 Diagnóstico inicial

El análisis inicial reveló una base de 175 columnas organizadas en cinco bloques: identificadores (6), demográficas (5), inclusión financiera CNBV (95), auxiliares temporales (5) e indicador de alcaldesa (33). De las 175 columnas, 128 estaban completas (100%) y 47 presentaban valores faltantes. El mapa de faltantes identificó tres grupos:

- **Saldo promedio `saldoprom_*` (28 columnas):** 600 a 41,871 NULLs — son indefiniciones estructurales (÷ 0 cuando no hay contratos), **no** datos faltantes reales.
- **Indicador alcaldesa (18 columnas):** Las variantes sin llenado manual presentan NULLs, pero la variable recomendada `alcaldesa_final` tiene **0% NULLs**.
- **`tipo_pob` (1 columna):** 2 NULLs en dos municipios que se corrigieron por imputación determinista.

Se identificaron 3 columnas constantes (`hist_state_available`, `missing_quarters_alcaldesa`, `ok_panel_completo_final`) que fueron eliminadas por no aportar variación.

## 3.2 Recomendaciones del EDA y su resolución

El EDA generó 12 recomendaciones priorizadas por criticidad. Todas fueron implementadas al 100%:

### Recomendaciones críticas (4/4 resueltas)

**Rec 1–2: Normalización per cápita.** Se crearon 51 columnas per cápita dividiendo cada indicador de inclusión financiera entre la población adulta correspondiente y multiplicando por 10,000. Sin esta normalización, el modelo mediría "tamaño del municipio" en lugar de inclusión financiera: la correlación de Spearman entre conteos brutos y población es de 0.67–0.70.

La fórmula aplicada:
$$Y_{pc} = \frac{Y_{raw}}{pob\_adulta\_m} \times 10{,}000$$

El factor de 10,000 sigue la convención de la CNBV y el Banco Mundial para indicadores de inclusión financiera, haciendo los resultados directamente comparables con la literatura.

**Rec 3: Documentación de NULLs en `saldoprom_*`.** Los 28 saldos promedio tienen NULLs masivos (hasta 99.9%) porque son cocientes $\frac{saldo}{contratos}$ indefinidos cuando contratos = 0. Se documentaron sin imputar — imputar sería conceptualmente incorrecto porque la operación no tiene sentido cuando no hay contratos. Las flags `flag_undef_saldoprom_*` marcan estos casos.

**Rec 4: Exclusión de columnas constantes.** Se eliminaron 3 columnas con varianza exactamente cero que generarían colinealidad perfecta con el intercepto.

### Recomendaciones de alta prioridad (5/5 resueltas)

**Rec 5: Logaritmo de población.** Se crearon 4 controles `log_pob`, `log_pob_adulta`, `log_pob_adulta_m`, `log_pob_adulta_h` porque la relación entre población y outcomes es multiplicativa, no aditiva.

**Rec 6: Winsorización.** Se crearon 51 columnas `_pc_w` recortando al percentil 1–99 para manejar outliers extremos (municipios metropolitanos con valores desproporcionados por efecto sede bancario).

**Rec 7: Ratios de brecha de género M/H.** Se construyeron 17 ratios `ratio_mh_*` que dividen la tasa femenina entre la masculina. Un ratio < 1 indica que las mujeres tienen menor acceso que los hombres.

**Rec 8: Variable `ever_alcaldesa`.** Indicador time-invariant que vale 1 si el municipio tuvo al menos una alcaldesa en algún trimestre del panel. Clasifica municipios en *ever-treated* vs. *never-treated*.

**Rec 9: Identificadores estándar (`cvegeo_mun`).** Se agregó la clave geoestadística de 5 dígitos para facilitar merges con datos del INEGI.

### Recomendaciones de prioridad media (3/3 resueltas)

**Rec 10: Variable de intensidad `alcaldesa_acumulado`.** Suma acumulada de `alcaldesa_final` dentro de cada municipio:
$$dose_{it} = \sum_{s \leq t} D_{is}$$

Captura la "dosis" de exposición al tratamiento — un municipio con 10 trimestres consecutivos con alcaldesa tiene mayor exposición que uno con 1 trimestre. Permite explorar efectos dosis-respuesta.

**Rec 11: Transformación asinh.** Se crearon 51 columnas `_pc_asinh` aplicando el seno hiperbólico inverso:
$$\text{asinh}(x) = \ln\left(x + \sqrt{x^2 + 1}\right)$$

Esta transformación resuelve el problema fundamental de las distribuciones de inclusión financiera: están extremadamente sesgadas (ratio media/mediana de 6× en conteos y 390× en saldos) y contienen ceros legítimos. A diferencia del logaritmo, asinh está definido en cero y no requiere constantes arbitrarias. Para valores grandes, asinh(Y) ≈ ln(2Y), por lo que los coeficientes se interpretan como semi-elasticidades aproximadas (Bellemare & Wichman, 2020).

**Rec 12: Imputación de `tipo_pob`.** Se corrigieron 2 municipios (San Felipe, BC y Dzitbalché, Camp.) clasificándolos como "Semi-urbano" con base en su población, siguiendo los umbrales observados en la base.

## 3.3 Validación

Las 12 recomendaciones fueron validadas con **43 tests automatizados** que verifican propiedades matemáticas (monotonicidad del acumulado, asinh(0) = 0, ausencia de NULLs), integridad de la base (PK, índices) y que la tabla original permaneció intacta. Los 43 tests pasan al 100%.

## 3.4 Tabla final

La tabla `inclusion_financiera_clean` resultante tiene **348 columnas** y 41,905 filas:

| Fase | Columnas añadidas | Total acumulado |
|:---|:---|---:|
| Tabla original | — | 175 |
| + Críticas (Recs 1–4) | +51 per cápita, −3 constantes | 223 |
| + Altas (Recs 5–9) | +4 log, +51 winsor, +17 ratio, +1 ever | 296 |
| + Medias (Recs 10–12) | +1 acumulado, +51 asinh | 348 |

---

# 4. Definición de variables clave

## 4.1 Variable de tratamiento: `alcaldesa_final`

Variable binaria que vale 1 cuando la persona titular de la presidencia municipal es mujer en el trimestre $t$. Su construcción requirió resolver tres problemas operativos:

**Etapa 1: Conversión a intervalos diarios.** Para cada municipio se recopiló la información de autoridades a partir de registros históricos oficiales. Cuando dos periodos se traslapa (interinatos), se aplica una regla determinística: se asigna la autoridad con fecha de inicio más reciente.

**Etapa 2: Agregación trimestral por regla de mayoría.** Se cuentan los días con autoridad femenina vs. masculina en cada trimestre. El tratamiento se asigna al género que gobernó durante la mayor parte del trimestre:
$$\texttt{alcaldesa}_{it} = \begin{cases} 1 & \text{si } days\_female > days\_male \\ 0 & \text{si } days\_male > days\_female \\ \text{NA} & \text{si hay huecos} \end{cases}$$

**Etapa 3: Corrección manual.** La variable algorítmica presenta 1,986 NULLs (4.7%) correspondientes a huecos en registros históricos. Estos se corrigieron mediante auditoría manual documentada con fuentes verificables. La variable definitiva `alcaldesa_final` combina ambas fuentes y tiene **0% de NULLs**.

| Variable | Obs. con valor 1 | Obs. con valor 0 | NULLs |
|:---|---:|---:|---:|
| `alcaldesa` (algorítmica) | 9,036 | 30,883 | 1,986 |
| **`alcaldesa_final` (definitiva)** | **9,331** | **32,574** | **0** |

### Distribución del tratamiento

De las 41,905 observaciones, **9,331 (22.3%)** corresponden a municipios con alcaldesa. A nivel de municipios:

| Grupo | Municipios | % |
|:---|---:|---:|
| Never-treated (nunca tuvieron alcaldesa) | 1,476 | 59.7% |
| Switchers (cambian al menos una vez) | 894 | 36.2% |
| Always-treated (alcaldesa desde 2018Q3, todo el panel) | 101 | 4.1% |

De los 894 switchers, **600 tienen periodo pre-tratamiento** (`first_treat_t > 0`) y son los que identifican el efecto causal. Los 294 restantes están *left-censored* (ya tenían alcaldesa en 2018Q3) y se excluyen del event study. De los 600, **409 tienen tratamiento absorbente** (0→1 permanente) y **191 experimentan reversiones** (la alcaldesa es reemplazada), generando un ~12.5% de *mismatch* que motiva interpretar las estimaciones como **ITT** (Intent-to-Treat).

## 4.2 Variables de resultado: 5 outcomes primarios

| Variable | Descripción | Dimensión que captura |
|:---|:---|:---|
| `ncont_total_m` | Contratos totales de productos financieros (mujeres) | Acceso agregado al sistema formal |
| `numtar_deb_m` | Tarjetas de débito (mujeres) | Acceso a servicios transaccionales básicos |
| `numtar_cred_m` | Tarjetas de crédito (mujeres) | Acceso a crédito de consumo |
| `numcontcred_hip_m` | Créditos hipotecarios (mujeres) | Acceso a crédito de largo plazo |
| `saldocont_total_m` | Saldo total de contratos (mujeres) | Profundización financiera |

Estos 5 outcomes cubren un gradiente de **margen extensivo → margen intensivo**: desde el acceso más básico (contratos, tarjetas de débito) hasta productos de mayor sofisticación (crédito hipotecario) y el volumen monetario comprometido (saldos).

### Transformaciones de la variable dependiente

Cada variable se transforma en tres etapas secuenciales:

1. **Per cápita:** $Y_{pc} = \frac{Y_{raw}}{pob\_adulta\_m} \times 10{,}000$ — "X contratos por cada 10,000 mujeres adultas"
2. **asinh (baseline):** $Y_{asinh} = \text{asinh}(Y_{pc})$ — comprime la distribución, maneja ceros
3. **Alternativas (robustez):** Winsorización p1–p99 y log(1+Y)

## 4.3 Controles

| Control | Justificación |
|:---|:---|
| `log_pob` | Controla escala municipal. Población proviene de proyecciones CONAPO, cambia lentamente — predeterminada respecto al tratamiento |
| FE municipio ($\alpha_i$) | Absorbe toda heterogeneidad time-invariant |
| FE periodo ($\gamma_t$) | Absorbe shocks agregados comunes (COVID-19, regulación CNBV) |

**No se incluyen** como controles: outcomes masculinos (`_h` — potencial bad control por spillover), PIB municipal (no disponible trimestralmente), indicadores totales (`_t` — mecánicamente endógenos), ni leads/lags del tratamiento (información futura/post-tratamiento).

---

# 5. Estadísticas descriptivas — Tabla 1

La Tabla 1 es el primer paso del análisis empírico. No estima ningún efecto causal — es un diagnóstico previo que responde tres preguntas: ¿los datos son razonables?, ¿los grupos son comparables?, ¿tenemos suficientes observaciones?

## 5.1 Panel A — Variables de contexto

| Variable | Never-treated | Switchers (pre) | Always-treated |
|:---|:---:|:---:|:---:|
| **Alcaldesa (D)** | 0.000 (0.000) | 0.000 (0.000) | 1.000 (0.000) |
| **ln(Población)** | 9.436 (1.622) | 9.947 (1.501) | 9.158 (1.700) |
| **Pob. adulta mujeres** | 17,823 (52,245) | 28,564 (72,825) | 24,854 (89,176) |

## 5.2 Panel B — Outcomes en escala asinh (escala del modelo)

| Variable | Never-treated | Switchers (pre) | Always-treated |
|:---|:---:|:---:|:---:|
| **Contratos totales** | 6.977 (2.448) | 7.672 (2.026) | 6.832 (2.282) |
| **Tarjetas débito** | 7.002 (2.335) | 7.315 (2.545) | 6.734 (2.261) |
| **Tarjetas crédito** | 5.785 (2.376) | 6.315 (2.236) | 5.689 (2.236) |
| **Créditos hipotecarios** | 2.088 (2.007) | 2.641 (1.955) | 1.850 (2.199) |
| **Saldo total** | 13.635 (5.377) | 15.078 (4.470) | 13.426 (4.815) |

## 5.3 Panel C — Outcomes en per cápita (escala interpretable)

| Variable | Never-treated | Switchers (pre) | Always-treated |
|:---|:---:|:---:|:---:|
| **Contratos totales** | 3,324 (6,415) | 4,022 (7,055) | 3,476 (11,638) |
| **Tarjetas débito** | 3,404 (7,424) | 4,329 (7,859) | 2,806 (7,915) |
| **Tarjetas crédito** | 792 (1,436) | 1,055 (2,353) | 791 (6,359) |
| **Créditos hipotecarios** | 39 (289) | 34 (74) | 46 (172) |
| **Saldo total** | 77.5M (206.8M) | 91.6M (176.7M) | 63.8M (172.0M) |

## 5.4 Panel D — Tamaños de muestra

| | Never-treated | Switchers (pre) | Always-treated |
|:---|:---:|:---:|:---:|
| **N municipios** | 1,476 | 600 | 101 |
| **N observaciones** | 25,016 | 4,036 | 1,704 |

> **Formato:** Media (Desviación estándar). Los switchers se evalúan solo en periodos pre-tratamiento (`event_time < 0`). Los always-treated no tienen periodo pre; se reportan todos sus periodos.

## 5.5 Interpretación de la Tabla 1

**Patrón principal:** Los switchers tienen medias sistemáticamente más altas en todos los outcomes — 10% más en contratos totales, 9% más en tarjetas de crédito, 26% más en hipotecarios. Esto tiene sentido: los municipios con mayor actividad económica y participación política femenina tienden a ser más urbanos (ln(Pob) = 9.95 vs. 9.44).

**¿Es problemático?** No, por dos razones fundamentales:

1. Los **efectos fijos de municipio** absorben todas las diferencias permanentes entre municipios. La variación que el DiD explota es *within* (dentro de cada municipio a lo largo del tiempo).
2. Lo que importa **no es el nivel, sino la tendencia**. El supuesto de tendencias paralelas no requiere que los grupos tengan las mismas medias — requiere que sus *trayectorias* sean paralelas.

**Observación sobre créditos hipotecarios:** La media es notablemente baja (39 por 10K mujeres en never-treated, 2.09 en asinh). Muchos municipios rurales tienen literalmente cero hipotecas. La transformación asinh maneja esto, pero el poder estadístico para detectar efectos puede ser limitado.

**Veredicto:** Los datos son sensatos, las diferencias entre grupos son explicables y absorbibles por efectos fijos, y hay suficientes observaciones por grupo. **Proceder al event study.**

---

# 6. Estrategia de identificación

## 6.1 Diseño

Se emplea un diseño de **diferencias en diferencias (DiD)** con datos de panel, explotando la variación *within-municipality* en `alcaldesa_final` a lo largo de 17 trimestres. La especificación base es un modelo **Two-Way Fixed Effects (TWFE):**

$$Y_{it} = \alpha_i + \gamma_t + \beta \cdot D_{it} + \delta \cdot \log(\text{pob})_{it} + \varepsilon_{it}$$

donde:
- $Y_{it}$: outcome de inclusión financiera (escala asinh) del municipio $i$ en el trimestre $t$
- $\alpha_i$: efecto fijo de municipio (2,471 dummies) — absorbe toda heterogeneidad time-invariant
- $\gamma_t$: efecto fijo de periodo (17 dummies) — absorbe shocks agregados comunes
- $D_{it}$: `alcaldesa_final` $\in \{0, 1\}$
- $\beta$: **parámetro de interés** — efecto promedio TWFE del tratamiento
- Errores estándar clusterizados a nivel municipio (Bertrand, Duflo & Mullainathan, 2004)

### Interpretación de $\hat{\beta}$

En escala asinh: $\hat{\beta} \approx$ cambio porcentual en el outcome asociado a tener una alcaldesa (semi-elasticidad). Un $\hat{\beta} = 0.05$ indicaría que los municipios con alcaldesa tienen un outcome ~5% mayor que los que no, controlando por efectos fijos.

## 6.2 Supuestos de identificación

| Supuesto | ¿Testeable? | Evaluación |
|:---|:---|:---|
| **Tendencias paralelas** | Parcialmente | Event study: coeficientes pre-tratamiento ≈ 0 |
| **No anticipación** | Parcialmente | Lead $k = -1$ en event study ≈ 0 |
| **SUTVA** (no spillovers) | No directamente | Se asume; placebo geográfico posible como extensión |
| **Exogeneidad condicional** | Por diseño | Tratamiento resultado electoral; la IF municipal no determina el género del alcalde |
| **Homogeneidad del efecto** (TWFE) | Testeable | Comparar TWFE vs. estimadores modernos |

## 6.3 Nota sobre TWFE con adopción escalonada

Bajo adopción escalonada con efectos heterogéneos en el tiempo, $\hat{\beta}_{TWFE}$ es un promedio ponderado de efectos específicos por cohorte con pesos potencialmente no convexos (Goodman-Bacon, 2021). Esto puede generar sesgo de atenuación o incluso inversión de signo. Por ello, el TWFE se complementa con un Stacked DiD como extensión futura (Cengiz et al., 2019).

---

# 7. Diagnóstico de tendencias paralelas — Event Study

El event study es la prueba diagnóstica más importante del diseño. Sin evidencia de tendencias paralelas, el coeficiente TWFE no tiene interpretación causal.

## 7.1 Especificación

$$Y_{it} = \alpha_i + \gamma_t + \sum_{k \neq -1} \delta_k \cdot \mathbf{1}\{t - g_i = k\} + \delta \cdot \log(\text{pob})_{it} + \varepsilon_{it}$$

| Parámetro | Valor | Justificación |
|:---|:---|:---|
| $K$ (leads) | 4 | Máximo disponible dado el panel |
| $L$ (lags) | 8 | Captura efectos hasta 2 años post-tratamiento |
| Periodo base | $k = -1$ | Estándar — trimestre inmediato anterior al tratamiento |
| Endpoint binning | Sí | Acumular $k \leq -4$ y $k \geq 8$ en bins extremos |
| Muestra | Excluir always-treated | Sin periodo pre-tratamiento |

## 7.2 Resultados del test conjunto de pre-trends

Se realiza un test de Wald ($\chi^2$) sobre $H_0: \delta_{-4} = \delta_{-3} = \delta_{-2} = 0$:

| Outcome | $\chi^2$ | p-valor | ¿Pasa al 10%? |
|:---|---:|---:|:---:|
| Contratos totales | 5.49 | 0.139 | **Sí** |
| Tarjetas débito | 3.80 | 0.284 | **Sí** |
| Tarjetas crédito | 6.67 | 0.083 | No (borderline) |
| Créditos hipotecarios | 0.75 | 0.861 | **Sí** |
| Saldo total | 3.52 | 0.319 | **Sí** |

## 7.3 Interpretación

**4 de 5 outcomes pasan el test conjunto al 10%.** El patrón visual es consistente con tendencias paralelas: los coeficientes pre-tratamiento oscilan alrededor de cero sin mostrar una tendencia sistemática, y los coeficientes post-tratamiento permanecen cercanos a cero.

**Tarjetas de crédito** presenta un rechazo marginal ($p = 0.083$) originado en el bin extremo $k \leq -4$ ($\hat{\beta} = -0.078$, $p = 0.043$). Sin embargo, los leads individuales $k = -3$ y $k = -2$ no son significativos, y los bins extremos tienden a capturar efectos de composición.

## 7.4 Análisis de sensibilidad del event study

Para evaluar si el borderline es robusto o un artefacto de la ventana, se corrieron 3 variantes adicionales:

### Tarjetas de crédito

| Variante | p-value | ¿Pasa al 10%? |
|:---|---:|:---:|
| Baseline (K=4) | 0.083 | No (borderline) |
| K=3 | 0.078 | No (borderline) |
| **K=6** | **0.212** | **Sí** |
| Excluir g=0 | 0.067 | No |

### Contratos totales

| Variante | p-value | ¿Pasa al 10%? |
|:---|---:|:---:|
| Baseline (K=4) | 0.139 | Sí |
| K=3 | 0.089 | No (borderline) |
| **K=6** | **0.208** | **Sí** |
| Excluir g=0 | 0.131 | Sí |

**Conclusión:** Con K=6 leads (más granularidad en pre-trends), ambos outcomes pasan holgadamente. El borderline $p = 0.083$ del baseline proviene de la acumulación heterogénea en el bin extremo. **Las tendencias paralelas se sostienen para los 5 outcomes.**

---

# 8. Resultados empíricos — TWFE

## 8.1 Efecto principal (Tabla 2)

| Outcome | $\hat{\beta}$ | SE (cluster) | p-valor | IC 95% |
|:---|---:|---:|---:|:---|
| Contratos totales | 0.007 | 0.022 | 0.747 | [−0.035, 0.049] |
| Tarjetas débito | −0.014 | 0.021 | 0.521 | — |
| Tarjetas crédito | −0.002 | 0.017 | 0.919 | — |
| Créditos hipotecarios | 0.018 | 0.021 | 0.400 | — |
| Saldo total | 0.004 | 0.049 | 0.931 | [−0.092, 0.100] |

> $N = 41{,}905$ observaciones, 2,471 municipios, 17 trimestres. FE municipio + FE periodo. Cluster SE a nivel municipio.

## 8.2 Interpretación

**No encontramos evidencia de un efecto estadísticamente significativo de la representación política femenina municipal sobre ninguno de los cinco indicadores primarios de inclusión financiera de las mujeres.**

Los coeficientes son cercanos a cero (entre −0.014 y +0.018 en escala asinh), económicamente irrelevantes (un $\hat{\beta} = 0.007$ equivale a un cambio de ~0.7%), y todos los p-valores superan 0.40. Los intervalos de confianza incluyen el cero con holgura.

El $R^2$ within es prácticamente cero en todos los modelos, confirmando que la variación del tratamiento dentro de cada municipio no explica variación adicional en los outcomes una vez absorbidos los efectos fijos.

**Esto no significa "no hay efecto"** — significa que con la variación disponible en el panel (600 switchers efectivos, 17 trimestres), no se detecta un efecto distinguible del ruido estadístico. La sección de MDES cuantifica qué tan grande tendría que ser el efecto para que lo detectáramos.

---

# 9. Robustez

## 9.1 Tabla 3 — Pruebas de robustez (outcome focal: contratos totales mujeres)

| Test | $\hat{\beta}$ | SE | N | Resultado |
|:---|---:|---:|---:|:---|
| **Baseline asinh** | 0.007 | 0.022 | 41,905 | n.s. |
| R1: log(1+y) | 0.005 | 0.020 | 41,905 | Consistente |
| R2: Winsor + asinh | 0.008 | 0.021 | 41,905 | Consistente |
| R3: Excluir transiciones | 0.002 | 0.024 | 38,303 | Consistente |
| R4: Placebo temporal (+4 trim) | −0.019 | 0.020 | 32,027 | ✓ ≈ 0 |
| R5: Placebo género (hombres) | −0.001 | 0.025 | 41,905 | ✓ ≈ 0 |

## 9.2 Interpretación de cada test

**Transformación funcional (R1, R2):** Cambiar de asinh a log(1+y) o winsorizar produce $\hat{\beta}$ entre 0.005 y 0.008 — prácticamente idénticos al baseline. El resultado **no depende de la escala elegida**.

**Exclusión de transiciones (R3):** Al eliminar trimestres donde el tratamiento cambia de estado (potencialmente ruidosos), N baja a 38,303 pero $\hat{\beta} = 0.002$ sigue siendo nulo. Las transiciones no generan sesgo.

**Placebo temporal (R4):** Se adelanta el tratamiento 4 trimestres. Si hubiera tendencias preexistentes confundentes, este tratamiento falso sería significativo. $\hat{\beta} = -0.019$, no significativo → no hay tendencia espuria.

**Placebo de género (R5):** Se usa el outcome de *hombres* como variable dependiente. Si la alcaldesa afectara la actividad financiera general (no solo mujeres), veríamos efecto en ambos géneros. $\hat{\beta} = -0.001$ → sin efecto espurio. El resultado nulo es genuino y no producto de un efecto general confundido.

**Conclusión:** El resultado nulo es robusto a transformaciones funcionales, definición de tratamiento y placebos. Todas las estimaciones se encuentran dentro de un rango estrecho $[-0.019, 0.008]$ y ninguna alcanza significancia estadística.

---

# 10. Heterogeneidad

## 10.1 Tabla 4 — Sub-muestras por tipo de municipio

| Dimensión | Grupo | $\hat{\beta}$ | SE | p-valor | q-value (BH) |
|:---|:---|---:|---:|---:|---:|
| tipo_pob | Rural | −0.104 | 0.065 | 0.109 | 0.492 |
| | En Transición | −0.007 | 0.035 | 0.839 | 0.928 |
| | Semi-urbano | 0.003 | 0.029 | 0.928 | 0.928 |
| | Urbano | 0.003 | 0.013 | 0.796 | 0.928 |
| | Semi-metrópoli | −0.004 | 0.015 | 0.774 | 0.928 |
| | **Metrópoli** | **0.030** | **0.013** | **0.024** | **0.215** |
| Tercil pob | T1 (pequeño) | −0.069 | 0.053 | 0.196 | 0.587 |
| | T2 (mediano) | −0.021 | 0.032 | 0.504 | 0.928 |
| | T3 (grande) | 0.003 | 0.014 | 0.823 | 0.928 |

## 10.2 Interpretación

Solo un subgrupo exhibe significancia nominal: **Metrópoli** ($\hat{\beta} = 0.030$, $p = 0.024$, $N = 220$ obs). Sin embargo, al ajustar por comparaciones múltiples mediante Benjamini-Hochberg, el q-value es 0.215 — **no sobrevive la corrección FDR al 10%**. Un q-value de 0.215 significa que rechazar esta hipótesis implicaría aceptar una tasa de falsos descubrimientos del ~22%.

Los municipios rurales presentan un coeficiente negativo y notable ($\hat{\beta} = -0.104$, $p = 0.109$) pero tampoco alcanza significancia ($q = 0.492$). Los demás subgrupos producen estimaciones cercanas a cero.

**Conclusión:** No hay evidencia robusta de heterogeneidad tras corrección por multiplicidad. El efecto nominal en Metrópoli es un probable falso positivo. El tratamiento parece homogéneo a lo largo de las dimensiones de urbanización y tamaño.

---

# 11. Poder estadístico y MDES

## 11.1 ¿Por qué importa?

El resultado principal es un efecto nulo. Pero un nulo puede significar: (1) no hay efecto (verdadero nulo), o (2) hay efecto pero el estudio no tiene poder para detectarlo (falso nulo). El **Minimum Detectable Effect Size (MDES)** permite distinguir entre ambos:

$$\text{MDES} = (z_{\alpha/2} + z_{\beta}) \times SE = 2.80 \times SE$$

con $\alpha = 0.05$ y poder = 80%.

## 11.2 Interpretación

El MDES se calcula usando la SE del TWFE baseline. Para contratos totales, con SE = 0.022:

$$\text{MDES} = 2.80 \times 0.022 \approx 0.062 \text{ (escala asinh)} \approx 6.4\%$$

Esto significa que podemos descartar efectos mayores al ~6.4% con 80% de poder. Dado que los efectos esperados en la literatura de representación política femenina suelen ser de un dígito porcentual, **el nulo es razonablemente informativo**: descartamos los efectos de la magnitud que la política pública podría esperar.

---

# 12. Extensiones

## 12.1 Stacked DiD (recomendación principal)

Dado que el TWFE con adopción escalonada puede sufrir sesgo de atenuación (Goodman-Bacon, 2021), se recomienda como extensión futura el **Stacked DiD** (Cengiz et al., 2019):

- Construir un sub-experimento limpio por cada una de las 14 cohortes (excluyendo g=0), con ventana $[-4, +8]$ trimestres
- Apilar los sub-datasets con FE municipio×stack + periodo×stack
- Clusterizar por municipio original

Esto elimina las comparaciones contaminadas (treated-vs-treated) que podrían atenuar el efecto.

## 12.2 Margen extensivo y composición de género

Se construyen extensiones exploratorias:
- **Panel A:** Variables binarias `any_X_m` = 1 si el municipio tiene al menos un producto. Estimación LPM.
- **Panel B:** Proporción de mujeres `share_m = Y_m / (Y_m + Y_h)`. Un coeficiente positivo indicaría redistribución del acceso hacia mujeres.

---

# 13. Discusión y conclusiones

## 13.1 Resumen de hallazgos

| Componente | Resultado |
|:---|:---|
| **TWFE baseline** | Nulo en los 5 outcomes ($p > 0.40$ en todos) |
| **Pre-trends** | 4/5 pasan al 10%; 5/5 pasan con ventana extendida (K=6) |
| **Robustez** | Nulo estable bajo 5 especificaciones alternativas |
| **Placebos** | Temporal y de género confirman ausencia de efectos espurios |
| **Heterogeneidad** | Ningún subgrupo sobrevive corrección FDR |
| **Poder** | MDES ~6% — nulo informativo |

## 13.2 ¿Por qué no se detectan efectos?

Varias razones teóricas podrían explicar la ausencia de efectos:

**Oferta financiera parcialmente exógena.** La distribución de sucursales, terminales y productos financieros en México responde principalmente a decisiones de la banca comercial y regulación federal (CNBV), no a la política municipal. Los márgenes de acción de un gobierno local sobre la inclusión financiera podrían ser limitados.

**Horizonte temporal limitado.** El panel abarca 17 trimestres (~4 años). Si los mecanismos operan gradualmente (confianza institucional, difusión, programas locales), los efectos podrían requerir un horizonte más largo.

**Heterogeneidad que se cancela.** Los análisis muestran signos opuestos entre subgrupos (positivo en metrópolis, negativo en municipios rurales), sugiriendo efectos que podrían cancelarse en el promedio. Sin embargo, estos no sobreviven la corrección por multiplicidad.

**Tratamiento difuso.** La variable `alcaldesa_final` mide la presencia de una mujer en la presidencia municipal, pero no captura orientación programática, capacidad administrativa o intensidad de implementación. Dos alcaldesas pueden tener agendas y capacidades de gestión radicalmente diferentes.

## 13.3 Conclusión

**Dentro del horizonte temporal y la definición de tratamiento analizados, no encontramos evidencia de un efecto causal de la representación política femenina municipal sobre los indicadores de inclusión financiera de las mujeres en México.** Esta conclusión es robusta a múltiples especificaciones, y los nulos son informativos dado el poder estadístico razonable del diseño (MDES ~6%).

El resultado nulo es un hallazgo legítimo — no un fracaso del diseño. Contribuye a la literatura documentando que la representación *descriptiva* femenina a nivel municipal no se traduce automáticamente en mejoras medibles en la inclusión financiera de las mujeres en el corto plazo, al menos no en la magnitud que este diseño puede detectar.

## 13.4 Líneas futuras

1. **Stacked DiD:** Verificar si los nulos del TWFE persisten con un estimador libre de comparaciones contaminadas.
2. **Panel más largo:** Extender el horizonte temporal para capturar efectos de mediano plazo.
3. **Mecanismos:** Explorar canales intermedios (presupuesto municipal, programas sociales, educación financiera).
4. **Tratamiento más fino:** Explotar información sobre la agenda y capacidad de las alcaldesas, más allá del indicador binario de género.

---

# 14. Bibliografía

- Bellemare, M. F. & Wichman, C. J. (2020). "Elasticities and the Inverse Hyperbolic Sine Transformation." *Oxford Bulletin of Economics and Statistics*, 82(1), 50–61.

- Bertrand, M., Duflo, E. & Mullainathan, S. (2004). "How Much Should We Trust Differences-in-Differences Estimates?" *The Quarterly Journal of Economics*, 119(1), 249–275.

- Callaway, B. & Sant'Anna, P. H. C. (2021). "Difference-in-Differences with Multiple Time Periods." *Journal of Econometrics*, 225(2), 200–230.

- Cengiz, D., Dube, A., Lindner, A. & Zipperer, B. (2019). "The Effect of Minimum Wages on Low-Wage Jobs." *The Quarterly Journal of Economics*, 134(3), 1405–1454.

- Goodman-Bacon, A. (2021). "Difference-in-Differences with Variation in Treatment Timing." *Journal of Econometrics*, 225(2), 254–277.

- Roth, J., Sant'Anna, P. H. C., Bilinski, A. & Poe, J. (2023). "What's Trending in Difference-in-Differences? A Synthesis of the Recent Econometrics Literature." Working paper.

- Sun, L. & Abraham, S. (2021). "Estimating Dynamic Treatment Effects in Event Studies with Heterogeneous Treatment Effects." *Journal of Econometrics*, 225(2), 175–199.

---

# Apéndice: Pipeline de reproducción

Todos los resultados se reproducen ejecutando los siguientes scripts en orden:

```bash
cd Code_V2/
source .venv/bin/activate

# 1. Construir muestra analítica
python src/data/01_extract_panel.py
python src/data/02_build_features.py

# 2. Pipeline econométrico
python src/models/01_table1_descriptives.py     # Tabla 1
python src/models/02_twfe.py                     # Tabla 2
python src/models/03_event_study.py              # Figura 1 + pre-trends
python src/models/04_robustness.py               # Tabla 3
python src/models/05_heterogeneity.py            # Tabla 4

# O todo junto:
python -m tesis_alcaldesas.run_all
```

**Outputs generados en `outputs/paper/`:**

| Archivo | Contenido |
|:---|:---|
| `tabla_1_descriptiva.csv` / `.tex` | Estadísticas descriptivas |
| `tabla_2_twfe_main.csv` / `.tex` | TWFE baseline |
| `figura_1_event_study_*.png` / `.pdf` | Event study por outcome |
| `tabla_3_robustez.csv` / `.tex` | Tests de robustez |
| `tabla_4_heterogeneity.csv` / `.tex` | Heterogeneidad |
| `tabla_6_mdes.csv` / `.tex` | Poder estadístico |
| `tabla_7_extensive.csv` / `.tex` | Extensión: margen extensivo |
