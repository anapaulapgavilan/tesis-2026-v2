> **Archivos fuente:**
> - `notebooks/eda.ipynb`
> - `src/eda/run_eda.py`

# Explicación Detallada del Análisis Exploratorio de Datos (EDA)

**Proyecto:** Efecto causal de las alcaldesas en la inclusión financiera de las mujeres en México  
**Base de datos:** `tesis_db` (PostgreSQL 17.8) · Tabla: `inclusion_financiera`  
**Panel:** 2,471 municipios × 17 trimestres (2018Q3 – 2022Q3) = 41,905 observaciones  
**Fecha de generación:** Junio 2025  

---

## Índice

1. [Objetivo del EDA](#1-objetivo-del-eda)  
2. [Estructura del análisis](#2-estructura-del-análisis)  
3. [Sección A — Diccionario observado](#3-sección-a--diccionario-observado)  
4. [Sección B — Calidad e integridad](#4-sección-b--calidad-e-integridad)  
5. [Sección C — Distribuciones univariadas](#5-sección-c--distribuciones-univariadas)  
6. [Sección D — Relaciones bivariadas](#6-sección-d--relaciones-bivariadas)  
7. [Sección E — Sesgo y leakage](#7-sección-e--sesgo-y-leakage)  
8. [Sección F — Recomendaciones](#8-sección-f--recomendaciones)  
9. [Archivos generados](#9-archivos-generados)  
10. [Conclusiones y próximos pasos](#10-conclusiones-y-próximos-pasos)  

---

## 1. Objetivo del EDA

El EDA tiene un objetivo doble:

1. **Conocer la base de datos a profundidad** — entender qué variables existen, su distribución, calidad, valores faltantes y posibles problemas antes de cualquier modelado.
2. **Orientar la estrategia de estimación causal** — validar supuestos clave (como tendencias paralelas para Difference-in-Differences), identificar variables con riesgo de leakage o sesgo, y definir las transformaciones necesarias para que los modelos sean válidos.

La pregunta de investigación que guía todo el análisis es:

> **¿Cuál es el efecto de tener una alcaldesa (mujer como autoridad municipal) en la inclusión financiera de las mujeres en los municipios de México?**

El tratamiento es la variable `alcaldesa_final` (1 = mujer como autoridad municipal, 0 = hombre).

---

## 2. Estructura del análisis

El EDA se organizó en **6 secciones** siguiendo una guía práctica para datos tabulares en panel:

| Sección | Nombre | Propósito |
|---------|--------|-----------|
| **A** | Diccionario observado | Catalogar todas las 175 variables con tipo, NAs, distribución |
| **B** | Calidad e integridad | Validar llave primaria, balance del panel, consistencia |
| **C** | Distribuciones univariadas | Visualizar cada variable clave de forma individual |
| **D** | Relaciones bivariadas | Comparar tratamiento vs. control; validar supuestos causales |
| **E** | Sesgo / leakage | Identificar variables peligrosas para el modelo |
| **F** | Recomendaciones | Listar transformaciones necesarias antes del modelado |

Antes de las secciones, hay un bloque de **configuración (Sección 0)** que:
- Carga las librerías necesarias (pandas, numpy, matplotlib, seaborn, sqlalchemy)
- Establece la semilla de reproducibilidad (`SEED = 42`)
- Configura el estilo visual de los gráficos
- Conecta a la base de datos PostgreSQL
- Define constantes del análisis (variable de tratamiento, llave primaria, columnas de outcomes)
- Carga la tabla completa a un DataFrame de pandas (41,905 filas × 175 columnas)
- Crea una función `per_capita()` para normalizar conteos por población adulta (× 10,000)

---

## 3. Sección A — Diccionario observado

### ¿Qué se hizo?

Se generó un **perfil automático de cada una de las 175 variables** de la base de datos. Para cada variable se calculó:

- **dtype**: Tipo de dato (int64, float64, str, etc.)
- **na_n / na_pct**: Número y porcentaje de valores nulos
- **n_unique**: Número de valores únicos
- Para variables **numéricas**: min, p25, p50 (mediana), p75, max, media, desviación estándar, coeficiente de variación (CV)
- Para variables **categóricas**: valor más frecuente (moda) y su conteo
- **Comentarios automáticos**: alertas si la variable tiene >60% NAs, es constante (1 solo valor), o tiene alta dispersión (CV > 5)

### Resultados clave

| Métrica | Valor |
|---------|-------|
| Variables totales | 175 |
| Con valores nulos | 47 |
| Constantes (std = 0) | 3 (`hist_state_available`, `missing_quarters_alcaldesa`, `ok_panel_completo_final`) |
| Con >60% NAs | Variables `saldoprom_*` — son NULLs **estructurales** (resultado de ÷0 cuando no hay contratos) |
| Alta dispersión (CV > 5) | Mayoría de outcomes financieros — esperado dado la enorme variación en tamaño de municipios |

**Interpretación:** La base tiene buena cobertura general. Los NULLs no son aleatorios sino estructurales (municipios sin contratos no pueden tener saldo promedio). Las 3 constantes deben excluirse de cualquier modelo. La alta dispersión en outcomes confirma que la normalización per cápita es imprescindible.

### Archivo generado: `outputs/eda/A_diccionario_observado.csv`

Este archivo es el **catálogo completo de las 175 variables** de la tabla `inclusion_financiera`. Piensa en él como una "radiografía" de toda la base de datos: para cada variable te dice qué tipo de dato es, si tiene huecos, qué tan dispersa está, y cuáles son sus valores extremos. A continuación se explica todo lo que contiene, columna por columna y fila por fila.

---

#### ¿Qué es cada COLUMNA del CSV?

El archivo tiene **15 columnas**. Cada una mide algo distinto sobre cada variable:

| Columna del CSV | ¿Qué significa? | Ejemplo con `pob` (población total) |
|---|---|---|
| `variable` | **Nombre de la variable** en la base de datos. Es el nombre exacto de la columna en PostgreSQL. | `pob` |
| `dtype` | **Tipo de dato** que Python detectó al leer la tabla. `int64` = número entero, `float64` = número con decimales (o con NULLs), `str` = texto. | `int64` |
| `na_n` | **Número de valores faltantes (NULLs).** Cuántas de las 41,905 filas no tienen dato en esta variable. Si es 0, la variable está completa. | `0` (ningún municipio sin dato de población) |
| `na_pct` | **Porcentaje de NULLs.** Es `na_n / 41,905 × 100`. Te dice qué fracción de la base está vacía. | `0.0%` |
| `n_unique` | **Valores únicos.** Cuántos valores distintos hay. Si es 1, la variable es constante (siempre vale lo mismo). Si es 2, es binaria (ej. 0/1). | `8,735` (hay 8,735 valores distintos de población) |
| `min` | **Valor mínimo.** El número más pequeño observado. Solo aplica a variables numéricas; para texto está vacío. | `81` (el municipio más pequeño tiene 81 habitantes) |
| `p25` | **Percentil 25 (primer cuartil).** El 25% de los municipios tienen un valor igual o menor a este. | `4,552` (1 de cada 4 municipios tiene ≤ 4,552 habitantes) |
| `p50` | **Percentil 50 (mediana).** El valor que divide la base en dos mitades iguales. Es más robusto que la media porque no lo distorsionan los extremos. | `13,701` (la mitad de los municipios tiene ≤ 13,701 habitantes) |
| `p75` | **Percentil 75 (tercer cuartil).** El 75% de los municipios tienen un valor igual o menor. | `35,905` |
| `max` | **Valor máximo.** El número más grande observado. | `1,922,523` (CDMX u otra metrópoli) |
| `mean` | **Media (promedio aritmético).** Suma de todos los valores ÷ número de observaciones. | `51,115.76` |
| `std` | **Desviación estándar.** Mide qué tan dispersos están los datos respecto a la media. Si es grande respecto a la media, los datos varían mucho. | `146,944.81` (¡casi 3× la media!) |
| `cv` | **Coeficiente de variación.** Es `std / mean`. Mide la dispersión relativa. Si CV > 1, la dispersión es mayor que la media (mucha variación). Si CV > 5, es **extrema**. | `2.87` (alta variación, esperada porque hay municipios de 81 hab y de casi 2 millones) |
| `top` | **Valor más frecuente** (solo para variables de texto). El nombre, categoría o texto que más se repite. | Para `region`: `Sur`; para `estado`: `Oaxaca` |
| `top_n` | **Frecuencia del valor más común.** Cuántas veces aparece `top`. | Para `region`: `15,632` (filas donde la región es "Sur") |
| `comentario` | **Nota automática del EDA.** El script marca automáticamente problemas detectados: `alta dispersión` si CV > 5, `⚠ >60% NA` si más del 60% son NULLs, `constante` si `n_unique = 1`. Si está vacío, no se detectó ningún problema. | Para `pob` está vacío (CV = 2.87 < 5, sin NULLs) |

---

#### ¿Qué es cada FILA del CSV?

Cada fila representa **una variable** (columna) de la tabla `inclusion_financiera`. Hay **175 filas** (+ 1 encabezado = 176 líneas en el archivo), una por cada columna de la base. Las filas están organizadas en los mismos 6 bloques del diccionario:

##### Bloque 1 — Identificadores (filas 2-7): `cve_mun`, `trim`, `cve_edo`, `region`, `estado`, `municipio`

Son las "etiquetas" de cada observación. No se analizan estadísticamente; solo sirven para saber **a qué municipio y trimestre pertenece** cada fila.

- **¿Cómo leerlas?** Fíjate en `n_unique`: `cve_mun` tiene 2,471 valores únicos (= 2,471 municipios), `trim` tiene 17 (= 17 trimestres). `region` solo tiene 6.
- **¿Tienen NULLs?** No (`na_n = 0` en todas). Buena señal: toda fila tiene su municipio identificado.

##### Bloque 2 — Demográficas (filas 8-12): `pob`, `pob_adulta`, `pob_adulta_m`, `pob_adulta_h`, `tipo_pob`

Son las variables de **población** del municipio. Son cruciales porque se usan para calcular tasas per cápita (ej. contratos por cada 10,000 mujeres adultas).

- **¿Qué buscar?** Compara `mean` vs `p50` (mediana). Si la media es mucho mayor que la mediana, la distribución está **sesgada a la derecha** (pocos municipios gigantes jalan la media). 
  - `pob`: media = 51,116 vs mediana = 13,701 → la media es 3.7× la mediana. Esto confirma que hay pocos municipios enormes (CDMX, Guadalajara, etc.) que inflan el promedio.
- **¿Por qué importa?** Esto justifica normalizar los outcomes por población (per cápita), porque sin normalizar, un municipio de 2 millones dominaría la estadística.

##### Bloque 3 — Inclusión financiera CNBV (filas 13-108): `ncont_*`, `saldocont_*`, `saldoprom_*`, `numcontcred_*`, `numtar_*`

Este es el **corazón de la base**: 95 variables con los datos financieros de la CNBV, desagregados por producto y sexo.

**Subgrupos de variables:**

| Prefijo | Qué mide | Ejemplo |
|---|---|---|
| `ncont_*` | **Número de contratos** (cuentas de captación) | `ncont_total_m` = total de contratos de mujeres |
| `saldocont_*` | **Saldo total** en pesos de esos contratos | `saldocont_total_m` = pesos en todas las cuentas de mujeres |
| `saldoprom_*` | **Saldo promedio** por contrato (= saldocont / ncont) | `saldoprom_total_m` = pesos promedio por contrato de mujer |
| `numcontcred_hip_*` | **Créditos hipotecarios** | `numcontcred_hip_m` = hipotecas de mujeres |
| `numtar_deb_*` | **Tarjetas de débito** | `numtar_deb_m` = tarjetas débito de mujeres |
| `numtar_cred_*` | **Tarjetas de crédito** | `numtar_cred_m` = tarjetas crédito de mujeres |

**Sufijos de sexo:** `_m` = mujeres, `_h` = hombres, `_pm` = persona moral (empresas), `_t` = total.

**¿Qué buscar en estas filas?**

1. **`cv` (coeficiente de variación):** Casi todas dicen `alta dispersión` en el comentario porque su CV > 5. Esto es **esperado** — un municipio rural de 500 personas tiene 0 contratos, mientras que la CDMX tiene millones. La solución es la transformación per cápita (paso siguiente del pipeline).

2. **`p25` y `p50` en ceros:** Muchas variables tienen `p25 = 0` y `p50 = 0` (ej. `ncont_ahorro_m`). Esto significa que **más de la mitad de los municipios tienen cero** en ese producto. Ejemplo: al menos 75% de los municipios no tienen cuentas de ahorro (los 4 percentiles son 0).

3. **`saldoprom_*` con muchos NULLs:** Las variables de saldo promedio tienen `na_pct` del 1.4% al 99.9%. Estos NULLs son **estructurales**: si un municipio tiene 0 contratos, no se puede calcular un promedio (÷0). Las flags `flag_undef_saldoprom_*` marcan exactamente estos casos (ver sección anterior).

4. **`max` enormes:** Los máximos son cifras astronómicas (ej. `saldocont_plazo_t` max = 252 mil millones de pesos). Estos son municipios metropolitanos. Los outliers extremos se tratan más adelante con **winsorización** (cortar al percentil 1 y 99).

##### Bloque 4 — Auxiliares temporales (filas 109-113): `cve_mun_int`, `cve_edo_int`, `year`, `quarter`, `periodo_trimestre`

Variables auxiliares para identificar el tiempo:

- `year`: 5 valores únicos (2018–2022), media ≈ 2020 → el panel está centrado alrededor de 2020.
- `quarter`: 4 valores (1–4), media ≈ 2.53 → distribución aproximadamente uniforme.
- `periodo_trimestre`: 17 valores únicos (los 17 trimestres). El más frecuente es `2021Q4` con 2,471 filas — que es exactamente el número total de municipios (como debe ser en un panel balanceado).

##### Bloque 5 — Indicador Alcaldesa (filas 114-148): `days_*`, `alcaldesa*`, `hist_*`, etc.

Variables sobre si el municipio tiene alcaldesa. Las más importantes:

- **`alcaldesa_final`**: La variable de tratamiento principal. `n_unique = 2` (0 o 1), `mean = 0.2227` → **22.3% de las observaciones** municipio-trimestre tienen alcaldesa. `na_n = 0` (sin NULLs). Es la variable que usamos en los modelos.

- **`alcaldesa` (sin "final")**: Versión anterior con **4.7% de NULLs** (`na_n = 1,986`). Por eso se creó `alcaldesa_final` con llenado manual.

- **`days_female`**: Promedio = 19.96 días (de ~91 días por trimestre) → los municipios con alcaldesa son minoría y a veces solo parte del trimestre.

- **`alcaldesa_transition`**: `mean = 0.0446` → solo el 4.5% de las observaciones son trimestres donde hubo cambio de autoridad.

- **Variables `_l1`, `_l2`, `_l3` (lags) y `_f1`, `_f2`, `_f3` (forwards)**: Son rezagos y adelantos de la variable de tratamiento. Se usan en el event study. Sus `na_pct` crece con cada lag (5.9%, 11.8%, 17.7%) porque al retroceder en el tiempo se pierden las primeras observaciones del panel.

- **`hist_state_available`**: `n_unique = 1`, comentario = `constante` → vale 1 para todos. Es inútil en cualquier modelo (no varía, no explica nada). Lo mismo para `missing_quarters_alcaldesa` (siempre 0) y `ok_panel_completo_final` (siempre 1).

##### Bloque 6 — Flags de missingness (filas 149-176): `flag_undef_saldoprom_*`

Las 28 banderas binarias explicadas en la sección anterior. En el CSV se ven así:

- `n_unique = 2` → solo toman valores 0 o 1
- `mean` = proporción de 1s (ej. `flag_undef_saldoprom_ahorro_t` tiene mean = 0.9268 → el 92.7% son indefinidos)
- `na_n = 0` → las flags mismas nunca tienen NULLs

### Variables `flag_undef_saldoprom_*` (28 columnas)

Las columnas `saldoprom_*` (saldo promedio por contrato) se calculan como:

$$\text{saldoprom} = \frac{\text{saldo total de contratos}}{\text{número de contratos}}$$

Cuando un municipio tiene **0 contratos** de cierto producto, la división es ÷0 → indefinido. En el Excel original de la CNBV estos casos aparecían como `"-"` (guión como texto); al cargar a PostgreSQL se convirtieron a `NULL`.

Las 28 columnas `flag_undef_saldoprom_{producto}_{sexo}` son **banderas binarias (0/1)** que marcan con **1** los registros donde el `NULL` en `saldoprom_*` es por **indefinición estructural** (0 contratos), no por dato faltante real.

| Componente | Valores posibles |
|---|---|
| `{producto}` | `ahorro`, `plazo`, `n1`, `n2`, `n3`, `tradic`, `total` |
| `{sexo}` | `m` (mujeres), `h` (hombres), `pm` (persona moral), `t` (total) |

**Ejemplo:** `flag_undef_saldoprom_plazo_t = 1` → el municipio tiene 0 contratos a plazo ese trimestre, por lo tanto `saldoprom_plazo_t` es NULL porque no se puede calcular un promedio de 0 contratos.

#### Tasas de indefinición por producto (sufijo `_t`)

| Producto | % con flag = 1 | Interpretación |
|---|---|---|
| `ahorro` | 92.7% | Casi ningún municipio tiene cuentas de ahorro |
| `n1` | 90.6% | Cuentas nivel 1 muy raras |
| `n3` | 82.0% | Cuentas nivel 3 poco comunes |
| `plazo` | 56.9% | Poco más de la mitad sin depósitos a plazo |
| `tradic` | 56.1% | Similar a plazo |
| `n2` | 1.5% | Casi todos los municipios tienen cuentas nivel 2 |
| `total` | 1.4% | Casi todos tienen al menos algún contrato |

> **Nota:** En la tesis, los 5 outcomes primarios son conteos y saldos totales per cápita (no promedios), por lo que este problema de indefinición **no afecta** las variables dependientes. Los flags son relevantes solo si se quisiera usar `saldoprom_*` como variable dependiente o control (en cuyo caso se debe filtrar `flag = 0`).

---

#### Guía rápida de lectura: ¿Cómo interpretar una fila?

Tomemos como ejemplo la variable **`ncont_total_m`** (número total de contratos financieros de **mujeres**):

```
variable:     ncont_total_m
dtype:        int64          → Es un número entero
na_n:         0              → No tiene NULLs (dato completo ✓)
na_pct:       0.0            → 0% faltante
n_unique:     13,796         → 13,796 valores distintos (mucha variación)
min:          0              → Hay municipios con CERO contratos de mujeres
p25:          25             → 25% de los municipios tienen ≤ 25 contratos
p50:          210            → La mitad tiene ≤ 210 contratos (¡pocos!)
p75:          5,794          → 75% tiene ≤ 5,794
max:          4,839,046      → El municipio más grande tiene casi 5 millones
mean:         21,166         → El promedio es ~21 mil...
std:          121,497        → ...pero la desviación es 6× la media
cv:           5.74           → CV > 5 → "alta dispersión" (confirmado en comentario)
comentario:   alta dispersión
```

**¿Qué nos dice esto en español?** El municipio típico (mediana) tiene solo 210 contratos de mujeres, pero el promedio es 21 mil porque unos pocos municipios enormes (CDMX) tienen hasta 5 millones.  Esta diferencia enorme entre media y mediana (100×) es la razón por la que necesitamos:
1. **Normalizar per cápita** (dividir por población)
2. **Transformar con asinh** (comprimir la escala)
3. **Winsorizar** (recortar extremos)

---

#### Resumen: ¿Para qué sirve este archivo?

| Pregunta de diagnóstico | Columnas a consultar |
|---|---|
| ¿A esta variable le faltan datos? | `na_n`, `na_pct` |
| ¿Es constante (inútil para modelos)? | `n_unique` (si = 1, es constante) |
| ¿Tiene outliers extremos? | Comparar `max` vs `p75`, o ver `cv` |
| ¿La distribución está sesgada? | Comparar `mean` vs `p50` |
| ¿Es binaria (0/1)? | `n_unique = 2` + `min = 0` + `max = 1` |
| ¿Qué categoría domina? (solo texto) | `top`, `top_n` |
| ¿Necesita transformación? | `comentario` = "alta dispersión" → sí |



---

## 4. Sección B — Calidad e integridad

### ¿Qué se hizo?

Se ejecutaron **6 pruebas de calidad** sobre la base de datos:

#### B1. Validación de llave primaria
- Se verificó que no existen **duplicados** en la combinación `(cve_mun, periodo_trimestre)`.
- **Resultado: ✓ 0 duplicados.** Cada municipio-trimestre aparece exactamente una vez.

#### B2. Balance del panel
- Se contó cuántos trimestres tiene cada municipio para verificar si el panel está **100% balanceado**.
- **Resultado: Panel casi balanceado.** 2,463 municipios tienen los 17 trimestres completos. 8 municipios se incorporan gradualmente (2 en 2020Q1, 4 en 2021Q1, 2 en 2021Q4). Esto es normal — son municipios creados durante el periodo.

#### B3. Completitud por periodo
- Se generó una tabla con el número de municipios, filas y porcentaje de alcaldesas por cada trimestre.
- **Resultado:** El % de alcaldesas se estabiliza alrededor de 22-23% a partir de 2019Q1, con un inicio más bajo (16%) en 2018Q3.

| Trimestre | Municipios | % Alcaldesa |
|-----------|------------|-------------|
| 2018Q3 | 2,463 | 16.0% |
| 2019Q1 | 2,463 | 22.9% |
| 2020Q1 | 2,465 | 22.8% |
| 2021Q1 | 2,469 | 22.7% |
| 2022Q3 | 2,463 | 22.4% |

#### B4. Consistencia geográfica
- Se verificó que ningún municipio **cambia de estado** entre trimestres.
- **Resultado: ✓ 0 municipios inconsistentes.**

#### B5. NULLs en tipo_pob
- Se identificaron **2 observaciones** con `tipo_pob` nulo.
- **Resultado: ⚠ Impacto mínimo.** Solo 2 de 41,905 filas.

#### B6. Valores negativos
- Se buscaron valores negativos en todas las columnas numéricas (no debería haber en conteos financieros).
- **Resultado: ✓ 0 columnas con negativos.**

### Resumen de calidad

| Check | Resultado | Status |
|-------|-----------|--------|
| Duplicados PK | 0 | ✓ |
| Panel 100% balanceado | Casi (8 municipios incorporados tarde) | ✗ (tolerable) |
| Municipios cambian estado | 0 | ✓ |
| NULLs en tipo_pob | 2 | ⚠ |
| Columnas con negativos | 0 | ✓ |
| Periodos cubiertos | 2018Q3–2022Q3 (17) | ✓ |

### Archivos generados
- `outputs/eda/B_calidad_integridad.csv` — Tabla resumen de las 6 pruebas
- `outputs/eda/B_completitud_panel.csv` — Municipios y % tratamiento por trimestre

---

## 5. Sección C — Distribuciones univariadas

### ¿Qué se hizo?

Se visualizaron las **distribuciones individuales** de las variables más importantes. Se generaron 5 gráficos:

#### C1. Proporción de alcaldesas por trimestre
- **Gráfico de línea** mostrando el % de municipios con alcaldesa en cada trimestre.
- **Resultado:** El tratamiento empieza en 16% (2018Q3) y sube a ~23% para 2019, manteniéndose estable hasta 2022Q3 (~22.4%). La media global es ~22%.
- **Interpretación:** El salto de 16% a 22.9% entre 2018Q3 y 2019Q1 refleja los cambios de gobierno municipal tras las elecciones. La estabilidad posterior sugiere que los cambios de tratamiento son de elección a elección, con poca variación dentro del mandato.

#### C2. Clasificación de municipios por exposición al tratamiento
- **Gráfico de barras** con tres categorías: switchers, nunca tratados, siempre tratados.
- **Resultado:**
  - **Nunca tratado:** 1,476 municipios (59.7%) — nunca tuvieron alcaldesa
  - **Switcher:** 894 municipios (36.2%) — cambiaron de tratamiento al menos una vez
  - **Siempre tratado:** 101 municipios (4.1%) — siempre tuvieron alcaldesa
- **Interpretación:** Los 894 **switchers son clave** para la identificación causal. Son los municipios que proporcionan variación within (dentro del mismo municipio) que los modelos de efectos fijos aprovechan.

> **Nota (precisión marzo 2026):** De los 894 switchers, **294 están left-censored**:
> ya tenían alcaldesa en 2018Q3 (primer trimestre del panel), por lo que `first_treat_t = 0`
> y no cuentan con observaciones pre-tratamiento (`event_time < 0`). Solo **600 switchers**
> tienen al menos un periodo pre-tratamiento y se incluyen en el event study.
> Los 294 left-censored se excluyen de los análisis causales. Ver `docs/11_TABLA1_ESTADISTICAS_DESCRIPTIVAS.md` §3.

#### C3. Distribución de población (escala log)
- **Histogramas** en escala logarítmica para: población total, población adulta mujeres, población adulta hombres.
- **Resultado:** Las tres distribuciones son **log-normales** con cola derecha fuerte. La mediana de población total es ~13,700 pero el rango va de 81 a 1,922,523.
- **Interpretación:** El uso de `log(pob)` como control en regresiones es indispensable. La enorme variación en tamaño (CV = 2.87) hace que las comparaciones en niveles sean inválidas.

#### C4. Boxplot de outcomes per cápita (mujeres)
- **Boxplots** (sin outliers) para los 10 outcomes de inclusión financiera de mujeres, normalizados por 10,000 mujeres adultas.
- **Resultado:** Los outcomes con mayor magnitud per cápita son depósitos a plazo (`plazo_m_pc`) y contratos nivel 2 (`n2_m_pc`). Variables como ahorro, nivel 1 y nivel 3 tienen medianas cercanas a cero.
- **Interpretación:** Hay gran heterogeneidad en los productos financieros. Los productos más "básicos" (nivel 2, débito) tienen mayor penetración; los más sofisticados (hipotecas, crédito) son mucho más escasos.

#### C5. Distribución de categóricas clave
- **Tres subgráficos:**
  - (a) Municipios por región: la región Sur concentra más municipios (Oaxaca tiene 570 municipios)
  - (b) Municipios por tipo de población: predominan Semi-urbano y Rural
  - (c) % trimestres con alcaldesa por región: variación regional significativa
- **Interpretación:** La distribución desigual de municipios por región es importante para los efectos fijos. Oaxaca, con sus usos y costumbres, tiene dinámicas especiales que los FE de municipio absorberán.

### Archivos generados
- `outputs/eda/C1_tratamiento_por_trimestre.png`
- `outputs/eda/C2_distribucion_poblacion.png`
- `outputs/eda/C3_boxplot_outcomes_mujeres_pc.png`
- `outputs/eda/C4_categoricas_clave.png`
- `outputs/eda/C5_tipo_pob_tratamiento.png`

---

## 6. Sección D — Relaciones bivariadas

### ¿Qué se hizo?

Se analizaron las **relaciones entre variables**, orientadas directamente a la pregunta de investigación. Se generaron 7 gráficos y tablas:

#### D1. Outcomes per cápita por tratamiento (boxplot)
> 📊 `outputs/eda/D1_outcomes_por_tratamiento.png`

- **6 boxplots** comparando municipios con y sin alcaldesa para: ahorro, total contratos, tarjetas débito, tarjetas crédito, créditos hipotecarios, depósitos a plazo.
- **Resultado:** Descriptivamente, los municipios **sin alcaldesa** tienden a tener outcomes per cápita **ligeramente mayores o similares** a los municipios con alcaldesa.
- **Interpretación CRUCIAL:** Esto NO significa que las alcaldesas "reduzcan" la inclusión financiera. Los municipios con alcaldesa tienden a ser **más pequeños y rurales** (sesgo de selección). La diferencia cruda está confundida por características observables e inobservables del municipio. Por eso se necesitan efectos fijos y controles.

#### D2. Brecha de género: tendencia temporal mujeres vs. hombres
> 📊 `outputs/eda/D2_brecha_genero_temporal.png`

- **6 gráficos de línea** mostrando la evolución temporal de outcomes per cápita de mujeres vs. hombres para cada producto financiero.
- **Resultado:** En casi todos los productos, los hombres tienen **más contratos per cápita** que las mujeres. La brecha es más pronunciada en créditos hipotecarios y tarjetas de crédito.
- **Interpretación:** Existe una brecha de género persistente en inclusión financiera. Ambos sexos muestran tendencias crecientes similares, pero la brecha se mantiene o se reduce lentamente.

#### D3. Tendencias paralelas (clave para DiD)
> 📊 `outputs/eda/D3_tendencia_por_tratamiento.png`

- **3 gráficos de línea** comparando la evolución de outcomes per cápita entre municipios tratados y controles para: contratos totales, tarjetas débito, ahorro.
- **Resultado:** Las tendencias de municipios tratados y controles se mueven de forma **aproximadamente paralela** antes del tratamiento para la mayoría de productos.
- **Interpretación:** Este es el **supuesto más importante** para la estimación por Difference-in-Differences. Si las tendencias fueran paralelas antes del tratamiento, cualquier divergencia posterior podría atribuirse al efecto de tener alcaldesa. La validación visual es un primer paso; el event study confirmará formalmente.

#### D4. Ratio Mujer/Hombre por tratamiento
> 📊 `outputs/eda/D4_ratio_MH_por_tratamiento.png`

- **3 gráficos de línea** mostrando la evolución del ratio M/H (mediana) para municipios tratados vs. controles.
- **Resultado:** Los ratios oscilan entre 0.8 y 1.1 dependiendo del producto. No se observa una divergencia clara entre tratados y controles.
- **Interpretación:** Si las alcaldesas mejoran la inclusión financiera de mujeres **relativamente** a hombres, el ratio M/H debería subir más en municipios tratados. La evidencia descriptiva es ambigua — el modelo causal formal lo resolverá.

#### D5. Correlaciones de Spearman
> 📊 `outputs/eda/D5_correlaciones_spearman.png`

- **Heatmap** de correlaciones de Spearman entre tratamiento, población, y los 7 principales outcomes de mujeres.
- **Resultado:**
  - Correlación outcomes-población: **0.60–0.70** (muy alta)
  - Correlación tratamiento-outcomes: baja en niveles (precisamente porque la relación cruda está confundida)
  - Correlaciones cruzadas entre outcomes: altas (0.40–0.85), lo que sugiere un factor latente de "tamaño del sistema financiero"
- **Interpretación:** La alta correlación outcomes-población **confirma que normalizar per cápita es CRÍTICA**. Sin normalización, los modelos capturarían el efecto del tamaño poblacional, no del tratamiento.

#### D6. Balance pre-tratamiento
> 📊 `outputs/eda/D6_balance_pre_tratamiento.png`

- **3 boxplots** comparando switchers, nunca-tratados y siempre-tratados en el periodo base (2018Q3) para: población total, población adulta mujeres, contratos totales mujeres.
- **Resultado:** Los municipios **siempre tratados** son en promedio más pequeños que los nunca-tratados. Los switchers se ubican en un punto intermedio.
- **Interpretación:** Hay **diferencias sistemáticas entre grupos**, lo que refuerza la necesidad de efectos fijos de municipio (que absorben diferencias de nivel permanentes). El modelo TWFE aprovecha solo la variación **within** (cambios dentro del mismo municipio a lo largo del tiempo).

> **Nota:** El visor por estado/año (D7: heatmap de alcaldesas por estado y año)
> se describió originalmente pero **no fue implementado** en el script `run_eda.py`.
> La variación geográfica reportada en la narrativa (BC ~51%, EdoMex ~10%) se
> calculó ad hoc. Si se necesita como output formal, debe añadirse al script.

### Archivos generados
- `outputs/eda/D1_outcomes_por_tratamiento.png`
- `outputs/eda/D2_brecha_genero_temporal.png`
- `outputs/eda/D3_tendencia_por_tratamiento.png`
- `outputs/eda/D4_ratio_MH_por_tratamiento.png`
- `outputs/eda/D5_correlaciones_spearman.png`
- `outputs/eda/D6_balance_pre_tratamiento.png`

---

## 7. Sección E — Sesgo y leakage

### ¿Qué se hizo?

Se identificaron **54 variables** que podrían causar problemas si se usan como controles en el modelo causal. Se clasificaron en 6 categorías:

#### E1. Leakage temporal (3 variables)
- Variables: `alcaldesa_final_f1`, `alcaldesa_final_f2`, `alcaldesa_final_f3`
- **Problema:** Son "adelantos" (forwards) del tratamiento — contienen información del futuro (t+1, t+2, t+3). Usarlas como controles violaría la temporalidad causal.
- **Acción:** EXCLUIR de regresiones como regresores; usar SOLO en event studies para testear pre-trends.

#### E2. Variables endógenas (2 variables)
- Variables: `alcaldesa_transition`, `alcaldesa_transition_gender`
- **Problema:** Son contemporáneas al tratamiento y potencialmente correlacionadas con outcomes. Si un cambio de gobierno afecta simultáneamente la inclusión financiera, incluirlas como controles absorbería parte del efecto que queremos medir.
- **Acción:** Usar variantes `*_excl_trans` como análisis de robustez, no como control principal.

#### E3. Artefactos de construcción (7 variables)
- Variables: `hist_mun_available`, `hist_state_available`, `ok_panel_completo`, `ok_panel_completo_final`, `missing_quarters_alcaldesa`, `filled_by_manual`, `quarters_in_base`
- **Problema:** Son variables de proceso/calidad usadas durante la construcción de la base de datos. No existían antes del tratamiento y no representan confusores causales.
- **Acción:** NO usar como controles en regresiones.

#### E4. Constantes (3 variables)
- Variables: `hist_state_available`, `missing_quarters_alcaldesa`, `ok_panel_completo_final`
- **Problema:** Tienen varianza = 0 (mismo valor en todas las observaciones). No aportan ninguna información al modelo.
- **Acción:** EXCLUIR de regresiones (serían automáticamente eliminadas por colinealidad).

#### E5. Flags de proceso (~20 variables)
- Variables: Todas las que empiezan con `flag_undef_saldoprom_*`
- **Problema:** Son indicadoras de missingness estructural (marcan si el saldo promedio es indefinido porque no hay contratos). Son útiles para filtrar pero no son confusores causales.
- **Acción:** Usar solo para filtrar muestras analíticas (e.g., filtrar `flag_undef_saldoprom_ahorro_m = 0` para analizar solo municipios con ahorro).

#### E6. Rezagos del tratamiento (~19 variables)
- Variables: `alcaldesa_*_l1`, `alcaldesa_*_l2`, `alcaldesa_*_l3`
- **Problema:** Son rezagos del tratamiento mismo. Usarlos como controles absorberían mecánicamente el efecto del tratamiento.
- **Acción:** Usar SOLO en la especificación de event study, no como controles.

### Archivo generado
- `outputs/eda/E_sesgo_leakage.csv` — 54 variables clasificadas con tipo de riesgo, razón y acción recomendada

---

## 8. Sección F — Recomendaciones

### ¿Qué se hizo?

Se compilaron **12 recomendaciones priorizadas** para las transformaciones necesarias antes del modelado causal, organizadas por urgencia:

### 🔴 CRÍTICAS (resolver antes de modelar)

| # | Categoría | Variables | Transformación |
|---|-----------|-----------|----------------|
| 1 | Normalización | `ncont_*`, `numtar_*`, `numcontcred_*` | Dividir entre `pob_adulta_m` (mujeres) o `pob_adulta_h` (hombres) × 10,000 |
| 2 | Normalización | `saldocont_*` | Dividir entre `pob_adulta_*` × 10,000 |
| 3 | Imputación | `saldoprom_*` (NULLs estructurales) | NO imputar. Filtrar con `flag_undef_saldoprom_* = 0` |
| 4 | Exclusión | Constantes (3 variables) | EXCLUIR — varianza = 0 |

### 🟡 ALTA prioridad

| # | Categoría | Variables | Transformación |
|---|-----------|-----------|----------------|
| 5 | Escala | `pob`, `pob_adulta_*` | `log(x)` como control en regresiones |
| 6 | Outliers | Outcomes per cápita | Winsorizar al p1–p99 como robustez |
| 7 | Feature eng. | `brecha_genero_*` (nueva) | Crear ratio = `outcome_m / outcome_h` |
| 8 | Feature eng. | `ever_alcaldesa` (nueva) | 1 si el municipio tuvo alcaldesa en cualquier trimestre |
| 9 | IDs | `cve_mun`, `cvegeo_mun` | Usar `cvegeo_mun` (5 dígitos, texto) para merges con INEGI |

### 🟢 Prioridad MEDIA

| # | Categoría | Variables | Transformación |
|---|-----------|-----------|----------------|
| 10 | Feature eng. | `alcaldesa_acumulado` (nueva) | Nº trimestres acumulados con alcaldesa hasta t |
| 11 | Escala | Outcomes per cápita | Evaluar `asinh(x)` o `log(1+x)` para distribuciones muy asimétricas |
| 12 | Imputación | `tipo_pob` (2 NULLs) | Asignar categoría por rango de población |

### Archivo generado
- `outputs/eda/F_recomendaciones.csv` — 12 recomendaciones con prioridad, categoría, variables, transformación y razón

---

## 9. Guía detallada de archivos generados

El EDA produce **16 archivos** en `outputs/eda/` (5 CSV + 11 PNG).
A continuación se describe cada uno con instrucciones de lectura e interpretación.

> **⚠️ Nota de corrección (marzo 2026):** Los gráficos D2 y D3 se generaban
> originalmente con paneles en blanco (sin datos) debido a un bug de doble
> sufijo en los nombres de columnas per cápita
> (`total_m_m_pc` en vez de `total_m_pc`). El bug fue corregido en
> `src/eda/run_eda.py` y ambos archivos se regeneraron con datos correctos.

---

### 9.1 `A_diccionario_observado.csv` — Perfil completo de las 175 variables

| Campo | Detalle |
|---|---|
| **Filas** | 175 (una por variable de la tabla `inclusion_financiera`) |
| **Columnas** | `variable`, `dtype`, `na_n`, `na_pct`, `n_unique`, `min`, `p25`, `p50`, `p75`, `max`, `mean`, `std`, `cv`, `top`, `top_n`, `comentario` |

**Cómo leerlo:**

1. Abre el CSV en Excel/Sheets o `pd.read_csv()`.
2. Ordena por `na_pct` descendente para encontrar las variables con más datos faltantes.
3. Filtra `comentario == "constante"` para identificar variables inútiles (std = 0).
4. Compara `mean` vs `p50`: si la media es ≫ mediana, la distribución está sesgada a la derecha.
5. Busca `cv > 5` para variables con dispersión extrema que necesitan transformación.

**Interpretación:**
- Las variables `saldoprom_*` tienen 1–99% NULLs → son estructurales (÷0), no datos faltantes reales.
- 3 variables constantes: `hist_state_available`, `missing_quarters_alcaldesa`, `ok_panel_completo_final` → excluir de modelos.
- Los outcomes financieros tienen CV > 5 → la normalización per cápita y la transformación asinh son imprescindibles.

Ver la [sección 3](#3-sección-a--diccionario-observado) para la explicación columna por columna y fila por fila.

---

### 9.2 `B_calidad_integridad.csv` — Checklist de validación

| Campo | Detalle |
|---|---|
| **Filas** | 6 (una por prueba de calidad) |
| **Columnas** | `check`, `resultado`, `status` (`✓` / `✗` / `⚠`) |

**Cómo leerlo:**

Cada fila es un test binario: pasó (`✓`), no pasó (`✗`), o advertencia (`⚠`).

| Fila | `check` | `resultado` | `status` | Lectura |
|---|---|---|---|---|
| 1 | Duplicados PK | `0` | ✓ | Ninguna observación (cve_mun, trimestre) está repetida |
| 2 | Panel 100% balanceado | `False` | ✗ | 8 municipios se incorporan tarde (2020–2021); tolerable |
| 3 | Municipios cambian estado | `0` | ✓ | Consistencia geográfica perfecta |
| 4 | NULLs en tipo_pob | `2` | ⚠ | Solo 2 de 41,905 filas; impacto despreciable |
| 5 | Columnas con negativos | `0` | ✓ | Ningún conteo financiero es negativo |
| 6 | Periodos cubiertos | `2018Q3–2022Q3 (17)` | ✓ | Panel completo de 17 trimestres |

**Interpretación:** La base pasa 4 de 6 checks sin problema. Los 2 issues restantes son menores (8 municipios nuevos, 2 NAs en tipo_pob). La base es apta para estimación causal.

---

### 9.3 `B_completitud_panel.csv` — Cobertura por trimestre

| Campo | Detalle |
|---|---|
| **Filas** | 17 (una por trimestre) |
| **Columnas** | `periodo_trimestre`, `n_mun`, `n_rows`, `pct_alcaldesa` |

**Cómo leerlo:**

- `n_mun`: Número de municipios presentes en ese trimestre. Debe ser ~2,463–2,471.
- `pct_alcaldesa`: Porcentaje de municipios con `alcaldesa_final = 1` en ese trimestre.

**Qué buscar:**

1. **¿Hay trimestres con caída abrupta de `n_mun`?** → No. La cobertura es estable.
2. **¿El `pct_alcaldesa` tiene saltos grandes?** → Sí: de 16.0% en 2018Q3 a 21.6% en 2018Q4 (primeras elecciones capturadas). Luego se estabiliza en ~22–23%.
3. **¿`n_rows == n_mun`?** → Sí en todos los trimestres. Confirma que no hay duplicados.

**Interpretación:** El salto 2018Q3→2018Q4 corresponde al ciclo electoral. La estabilidad posterior indica que la variación en tratamiento es primordialmente cross-sectional (entre municipios), con cambios discretos en fechas electorales.

---

### 9.4 `C1_tratamiento_por_trimestre.png` — Evolución temporal del tratamiento

**Tipo de gráfico:** Línea con marcadores (`o-`), un solo panel.

**Ejes:**
- Eje X: Trimestres (2018Q3 – 2022Q3)
- Eje Y: % de municipios con alcaldesa (0–100%)

**Cómo leerlo:**

1. Sigue la línea de izquierda a derecha. El punto más bajo es 2018Q3 (~16%).
2. El salto ocurre entre 2018Q3 y 2019Q1 (paso de ~16% a ~23%).
3. De 2019Q1 en adelante, la línea es casi plana (~22–23%).

**Interpretación:** La proporción de alcaldesas es estable dentro de cada ciclo electoral y cambia solo en fechas de transición. Esto es consistente con un diseño de tratamiento escalonado (staggered) donde los switches ocurren en momentos conocidos (elecciones). La prevalencia de ~22% implica que el grupo de control es sustancialmente mayor que el tratado.

---

### 9.5 `C2_distribucion_poblacion.png` — Histogramas de población (log)

**Tipo de gráfico:** 2 histogramas lado a lado.

**Paneles:**
- Izquierda: `log(1 + pob)` — población total
- Derecha: `log(1 + pob_adulta_m)` — población adulta de mujeres

**Ejes:**
- Eje X: log(1 + población) → escala continua
- Eje Y: Frecuencia (número de observaciones municipio-trimestre)

**Cómo leerlo:**

1. Busca la **forma de campana**: ambos histogramas son aproximadamente normales en escala log → la distribución original es **log-normal**.
2. El pico (moda) indica el tamaño "típico" de municipio.
3. La cola derecha (valores altos) corresponde a las metrópolis.

**Interpretación:** La distribución log-normal justifica usar `log(pob)` como control en las regresiones (no `pob` en niveles). Sin la transformación logarítmica, las metrópolis dominarían la estimación.

---

### 9.6 `C3_boxplot_outcomes_mujeres_pc.png` — Distribución de outcomes per cápita

**Tipo de gráfico:** Boxplots (sin outliers) para 10 outcomes financieros de mujeres.

**Ejes:**
- Eje X: Nombre del outcome (abreviatura: `ahorro_m_pc`, `total_m_pc`, etc.)
- Eje Y: Contratos por 10,000 mujeres adultas

**Cómo leerlo:**

1. La **línea dentro de la caja** es la mediana.
2. Los **bordes de la caja** son p25 y p75 (rango intercuartil, IQR).
3. Los **bigotes** se extienden hasta 1.5 × IQR (outliers ocultos con `showfliers=False`).
4. Compara el **ancho vertical** de las cajas: cajas altas = más dispersión.

**Qué buscar:**
- `n2_m_pc` y `total_m_pc` tienen las cajas más altas → mayor penetración y variación.
- `ahorro_m_pc`, `n1_m_pc`, `n3_m_pc` tienen cajas pegadas a cero → la mayoría de municipios tienen 0 contratos de estos productos.
- `t_deb_m_pc` (tarjetas débito) tiene un rango intermedio → es un indicador más universal.

**Interpretación:** La heterogeneidad entre productos financieros es enorme. Los productos "masivos" (nivel 2, total) son los mejores candidatos como outcome principal porque tienen más variación informativa. Los productos escasos (ahorro, n1, n3) tienen poca variación → baja potencia estadística para detectar efectos.

---

### 9.7 `C4_categoricas_clave.png` — Distribución de variables categóricas

**Tipo de gráfico:** 3 subgráficos horizontales de barras.

**Paneles:**
- (a) **C4a**: Municipios por región (6 regiones). La región Sur domina (~920 municipios, concentrados en Oaxaca).
- (b) **C4b**: Municipios por tipo de población. Predominan Semi-urbano y Rural.
- (c) **C4c**: Top 10 estados por número de municipios. Oaxaca lidera con 570.

**Cómo leerlo:**

Son conteos simples: la longitud de la barra indica el número de municipios (contados una sola vez, no por trimestre). Busca desbalances fuertes.

**Interpretación:** El desbalance geográfico es importante. Oaxaca aporta ~23% de todos los municipios, lo que significa que los resultados promedio del panel están fuertemente influidos por la dinámica oaxaqueña. Los efectos fijos de municipio controlan esto, pero para la heterogeneidad regional se necesitan interacciones explícitas.

---

### 9.8 `C5_tipo_pob_tratamiento.png` — Tipo de población × tratamiento

**Tipo de gráfico:** Barras horizontales apiladas al 100%.

**Ejes:**
- Eje Y: Categoría de tipo de población (Rural, Semi-urbano, Urbano, etc.)
- Eje X: % municipios (0–100%)
- Colores: Naranja = Nunca alcaldesa, Verde = Al menos 1 trimestre con alcaldesa

**Cómo leerlo:**

Cada barra muestra qué fracción de municipios de ese tipo tuvo alguna vez una alcaldesa. Si las barras verdes son similares en todas las categorías, el tratamiento no está correlacionado con el tipo de población.

**Interpretación:** Si los municipios rurales tienen menos verde (menos alcaldesas), esto sugiere un sesgo de selección: los municipios con alcaldesa tienden a ser más urbanos. Este sesgo se captura mediante los efectos fijos de municipio (diferencias permanentes de urbanización).

---

### 9.9 `D1_outcomes_por_tratamiento.png` — Boxplots tratados vs. control

**Tipo de gráfico:** 6 boxplots (2×3), cada uno con dos cajas (sin/con alcaldesa).

**Ejes:**
- Eje X: "Sin alcaldesa" / "Con alcaldesa"
- Eje Y: Outcome per cápita (×10,000 mujeres adultas)

**Paneles:** Ahorro, Total contratos, Tarjetas débito, Tarjetas crédito, Créditos hipotecarios, Depósitos a plazo.

**Cómo leerlo:**

1. Compara la **posición vertical de las medianas** (línea en la caja) entre Sin y Con alcaldesa.
2. Si la caja "Con alcaldesa" está más abajo → los municipios con alcaldesa tienen **menos** inclusión financiera per cápita.

**Interpretación:**

> **⚠️ CUIDADO:** Esta es una comparación **cruda** (sin controles). Los municipios con alcaldesa tienden a ser más pequeños y rurales, por lo que las diferencias reflejan **sesgo de selección**, no efecto causal. Este gráfico motiva el uso de efectos fijos — NO se puede citar como evidencia de efecto.

---

### 9.10 `D2_brecha_genero_temporal.png` — Brecha de género en el tiempo

> **Corregido marzo 2026:** Este gráfico se generaba en blanco debido a un bug
> de nombres de columna. Ahora muestra correctamente las tendencias M vs H.

**Tipo de gráfico:** 6 gráficos de línea (2×3), cada uno con dos series (mujeres y hombres).

**Ejes:**
- Eje X: Trimestres (2018Q3 – 2022Q3)
- Eje Y: Outcome per cápita (×10,000 adultas/os)
- Línea sólida con `o` = Mujeres
- Línea punteada con `□` = Hombres

**Paneles:** Contratos totales, Ahorro, Tarjetas débito, Tarjetas crédito, Créditos hipotecarios, Depósitos a plazo.

**Cómo leerlo:**

1. Si la línea de hombres está **por encima** de la de mujeres → existe brecha de género en ese producto.
2. Si las líneas se **acercan** con el tiempo → la brecha se reduce.
3. Si ambas líneas suben en paralelo → tendencia nacional de crecimiento, sin cierre de brecha.

**Interpretación:** En la mayoría de los productos, los hombres tienen más contratos per cápita que las mujeres. La brecha es más marcada en créditos hipotecarios y tarjetas de crédito (productos que requieren historial crediticio y formalidad laboral, donde las mujeres enfrentan más barreras). Esta brecha es el contexto que motiva la pregunta de investigación: ¿puede la representación política femenina reducirla?

---

### 9.11 `D3_tendencia_por_tratamiento.png` — Tendencias paralelas (clave para DiD)

> **Corregido marzo 2026:** Este gráfico se generaba en blanco debido al mismo
> bug de nombres de columna que D2. Ahora muestra correctamente las tendencias
> por grupo de tratamiento.

**Tipo de gráfico:** 3 gráficos de línea, cada uno con dos series (con/sin alcaldesa).

**Ejes:**
- Eje X: Trimestres
- Eje Y: Outcome per cápita (media del grupo)
- Línea sólida = Con alcaldesa
- Línea punteada = Sin alcaldesa

**Paneles:** Contratos totales (M), Tarjetas débito (M), Ahorro (M).

**Cómo leerlo:**

1. **Antes del tratamiento** (primeros trimestres): ¿las dos líneas se mueven en paralelo? Si sí, el supuesto de tendencias paralelas parece cumplirse visualmente.
2. **Después del tratamiento**: ¿las líneas divergen? Si la línea "Con alcaldesa" sube más que la de control → evidencia descriptiva de un efecto positivo.

**¿Por qué es el gráfico más importante?**

El diseño de Difference-in-Differences (DiD) requiere que, **en ausencia de tratamiento**, los grupos tratado y control habrían seguido la misma tendencia. Este gráfico es la primera validación visual de ese supuesto. Si las líneas fueran claramente no paralelas antes del tratamiento, toda la estrategia causal se cuestionaría.

**Interpretación:** Las tendencias son aproximadamente paralelas en contratos totales y tarjetas de débito. Esto es prometedor para el DiD. Sin embargo, esta validación visual es preliminar — el event study (sección D del pipeline de modelado) proporciona el test formal con intervalos de confianza.

> **Nota:** Este gráfico compara medias de grupos con composición cambiante (los
> municipios con alcaldesa en 2019 no son los mismos que en 2022). El event study
> y los estimadores modernos (recomendados como extensión futura) resuelven esto al comparar cada cohorte con su propio grupo
> de control limpio.

---

### 9.12 `D4_ratio_MH_por_tratamiento.png` — Ratio Mujer/Hombre por tratamiento

**Tipo de gráfico:** 3 gráficos de línea, cada uno con dos series (tratados vs. control).

**Ejes:**
- Eje X: Trimestres
- Eje Y: Mediana del ratio M/H (donde 1.0 = paridad)
- Línea horizontal gris punteada en 1.0 = referencia de paridad

**Paneles:** Contratos totales M/H, Tarjetas débito M/H, Ahorro M/H.

**Cómo leerlo:**

1. Si el ratio < 1, las mujeres tienen **menos** que los hombres en ese producto.
2. Si la línea de "Con alcaldesa" está **por encima** de la de "Sin alcaldesa" → los municipios con alcaldesa tienen ratios de género más favorables a mujeres.
3. Si las líneas divergen a lo largo del tiempo → posible efecto del tratamiento sobre la equidad de género.

**Interpretación:** Los ratios oscilan entre 0.8 y 1.1 según el producto. No se observa una divergencia clara y sostenida → la evidencia descriptiva es ambigua sobre si las alcaldesas mejoran la posición relativa de las mujeres. El modelo causal formal (con efectos fijos) es necesario para separar el efecto real del ruido.

---

### 9.13 `D5_correlaciones_spearman.png` — Heatmap de correlaciones

**Tipo de gráfico:** Mapa de calor triangular inferior con anotación numérica.

**Ejes:**
- Filas y columnas: `alcaldesa_final`, `pob`, `pob_adulta_m`, y los 7 outcomes de mujeres (`ncont_ahorro_m`, ..., `ncont_total_m`).
- Color: Escala **Rojo–Blanco–Azul** (RdBu_r), centrada en 0.
  - Rojo intenso = correlación negativa fuerte
  - Blanco = sin correlación
  - Azul intenso = correlación positiva fuerte
- Número en cada celda: Coeficiente de Spearman (–1 a +1).

**Cómo leerlo:**

1. Busca la fila/columna de `alcaldesa_final` → ¿cuál es su correlación con cada outcome? (Debería ser baja en niveles, ~-0.05 a 0.05.)
2. Busca la fila/columna de `pob` o `pob_adulta_m` → correlaciones con outcomes de 0.60–0.70 indican que la población domina la variación.
3. Las correlaciones entre outcomes (esquina inferior derecha) son altas (0.40–0.85) → existe un factor latente de "tamaño del sistema financiero".

**¿Por qué se usa Spearman y no Pearson?** Spearman mide correlaciones **monótonas** (no necesariamente lineales). Es más robusta a outliers y a las distribuciones sesgadas de nuestros datos.

**Interpretación:** La correlación casi nula entre `alcaldesa_final` y outcomes **no descarta un efecto causal**: los efectos fijos de municipio (que absorben el sesgo de selección) revelarán la variación within que esta correlación cruda no captura. La alta correlación población-outcomes confirma que la normalización per cápita es indispensable.

---

### 9.14 `D6_balance_pre_tratamiento.png` — Balance en el periodo base

**Tipo de gráfico:** 3 boxplots, cada uno con 3 cajas (Nunca, Switcher, Siempre).

**Ejes:**
- Eje X: Grupo de exposición (Nunca tratado, Switcher, Siempre tratado)
- Eje Y: Valor del indicador en el periodo base (2018Q3)

**Paneles:** Población total, Población adulta mujeres, Contratos totales (M).

**Cómo leerlo:**

1. Compara las **medianas** (línea central de cada caja) entre los tres grupos.
2. Si la mediana de "Siempre" es más baja que la de "Nunca" → los municipios siempre tratados son más pequeños.
3. Si las cajas de "Switcher" están entre las otras dos → los switchers son un grupo intermedio.

**Interpretación:** Hay diferencias **sistemáticas** de tamaño entre grupos: los municipios con alcaldesa tienden a ser más pequeños. Esto confirma el sesgo de selección observado en D1 y motiva el uso de efectos fijos de municipio (que eliminan estas diferencias de nivel al comparar cada municipio consigo mismo en el tiempo).

---

### 9.15 `E_sesgo_leakage.csv` — Variables con riesgo

| Campo | Detalle |
|---|---|
| **Filas** | 54 variables problemáticas |
| **Columnas** | `variable`, `tipo_riesgo`, `razon`, `accion` |

**Categorías de `tipo_riesgo`:**

| `tipo_riesgo` | Count | Descripción | Ejemplo |
|---|---|---|---|
| `leakage_temporal` | 3 | Forwards del tratamiento (info futura) | `alcaldesa_final_f1` |
| `endogeneidad` | 2 | Contemporáneas al tratamiento | `alcaldesa_transition` |
| `artefacto_construccion` | 7 | Variables de proceso/calidad | `filled_by_manual` |
| `constante` | 3 | Varianza = 0 | `hist_state_available` |
| `flag_proceso` | 28 | Flags de missingness estructural | `flag_undef_saldoprom_*` |
| `lag_tratamiento` | 11 | Rezagos del tratamiento | `alcaldesa_final_l1` |

**Cómo leerlo:**

1. Filtra por `tipo_riesgo == "leakage_temporal"` → estas variables **nunca** deben usarse como controles en regresiones causales.
2. La columna `accion` indica exactamente qué hacer con cada variable.

**Interpretación:** De las 175 variables originales, 54 (31%) tienen algún riesgo. Esto no significa que la base sea problemática — la mayoría son flags de proceso o rezagos que simplemente no deben usarse como controles. Las 3 de leakage temporal son las más peligrosas; incluirlas como regresores invalidaría la estimación causal.

---

### 9.16 `F_recomendaciones.csv` — Transformaciones pre-modelado

| Campo | Detalle |
|---|---|
| **Filas** | 12 recomendaciones |
| **Columnas** | `categoria`, `variable(s)`, `transformacion`, `razon`, `prioridad` |

**Valores de `prioridad`:**

| Prioridad | Significado | Ejemplos |
|---|---|---|
| `CRÍTICA` | Resolver **antes** de cualquier modelo | Normalización per cápita, exclusión de constantes |
| `Alta` | Resolver antes de resultados definitivos | log(pob), winsorización, ratio M/H |
| `Media` | Deseable pero no bloqueante | asinh, alcaldesa_acumulado |
| `Baja` | Nice-to-have | Imputar 2 NAs en tipo_pob |

**Cómo leerlo:**

1. Ordena por `prioridad` para priorizar el trabajo.
2. La columna `transformacion` indica exactamente qué operación aplicar.
3. La columna `razon` explica por qué es necesaria.

**Interpretación:** Las 4 recomendaciones CRÍTICAS (normalización per cápita de conteos y saldos, no imputar saldoprom, excluir constantes) ya fueron implementadas en el pipeline de features (`src/data/02_build_features.py`). Las de prioridad Alta (log, winsorización, ratio M/H) también están implementadas. Este archivo sirve como checklist de auditoría para verificar que todas las transformaciones se aplicaron.

---

### 9.17 `README.md` — Resumen ejecutivo

Archivo de documentación en Markdown con:
- Estructura del EDA (tabla sección→output)
- Hallazgos clave (5 bloques)
- Variables propuestas para el modelo
- Instrucciones de reproducción (`python -m src.eda.run_eda`)
- Tabla de archivos generados

---

### Resumen de status de archivos (marzo 2026)

| Archivo | Status | Nota |
|---------|--------|------|
| `A_diccionario_observado.csv` | ✅ Correcto | 175 filas completas |
| `B_calidad_integridad.csv` | ✅ Correcto | 6 checks, todos con resultado |
| `B_completitud_panel.csv` | ✅ Correcto | 17 trimestres documentados |
| `C1_tratamiento_por_trimestre.png` | ✅ Correcto | Línea temporal clara |
| `C2_distribucion_poblacion.png` | ✅ Correcto | 2 histogramas con datos |
| `C3_boxplot_outcomes_mujeres_pc.png` | ✅ Correcto | 10 boxplots con datos |
| `C4_categoricas_clave.png` | ✅ Correcto | 3 subgráficos con barras |
| `C5_tipo_pob_tratamiento.png` | ✅ Correcto | Barras apiladas con datos |
| `D1_outcomes_por_tratamiento.png` | ✅ Correcto | 6 boxplots comparativos |
| `D2_brecha_genero_temporal.png` | ✅ **Corregido** | Antes vacío; ahora muestra 6 paneles M vs H |
| `D3_tendencia_por_tratamiento.png` | ✅ **Corregido** | Antes vacío; ahora muestra tendencias paralelas |
| `D4_ratio_MH_por_tratamiento.png` | ✅ Correcto | 3 paneles con ratios |
| `D5_correlaciones_spearman.png` | ✅ Correcto | Heatmap anotado |
| `D6_balance_pre_tratamiento.png` | ✅ Correcto | 3 boxplots por grupo |
| `E_sesgo_leakage.csv` | ✅ Correcto | 54 variables clasificadas |
| `F_recomendaciones.csv` | ✅ Correcto | 12 recomendaciones con prioridad |

---

## 10. Conclusiones y próximos pasos

### Hallazgos principales del EDA

1. **La base de datos está limpia y bien estructurada.** Panel casi 100% balanceado, sin duplicados, sin negativos en conteos, consistencia geográfica perfecta.

2. **~22% de municipios-trimestre tienen alcaldesa.** La variación es primordialmente cross-sectional (entre municipios), con switches asociados a los ciclos electorales.

3. **894 switchers (36.2%)** proporcionan variación within. De estos, **600 tienen periodo pre-tratamiento** y son los que efectivamente identifican el efecto causal en el event study. Los 294 restantes (left-censored, `first_treat_t = 0`) se excluyen.

4. **La normalización per cápita es indispensable.** La correlación de 0.67–0.70 entre población y outcomes significa que sin normalizar, el modelo captura tamaño del municipio, no inclusión financiera.

5. **Existe una brecha de género persistente** en casi todos los productos financieros (hombres > mujeres per cápita).

6. **La diferencia cruda tratamiento-outcome es confusa.** Los municipios con alcaldesa tienden a ser más pequeños y rurales, generando un sesgo de selección negativo que los efectos fijos deben absorber.

7. **Las tendencias paralelas parecen cumplirse** visualmente para la mayoría de productos financieros, lo cual es prometedor para DiD.

8. **54 variables tienen riesgo de sesgo/leakage** y deben manejarse con cuidado (excluir, usar solo en event study, o solo para filtrar).

### Próximos pasos recomendados

1. **Crear muestra analítica** con variables per cápita, ratio M/H, y nuevas features (`ever_alcaldesa`, `alcaldesa_acumulado`)
2. **Estimar modelo TWFE** (Two-Way Fixed Effects) con efectos fijos de municipio + tiempo usando `pyfixest` o `linearmodels`
3. **Event study** con rezagos y adelantos para validación formal de tendencias paralelas
4. **Análisis de heterogeneidad** por región, tipo de población y tamaño del municipio
5. **Robustez:** excluir transiciones, winsorizar, diferentes medidas de outcome, estimadores robustos a heterogeneidad

---

## Apéndice: Herramientas técnicas utilizadas

| Componente | Herramienta | Versión |
|------------|-------------|---------|
| Base de datos | PostgreSQL | 17.8 (Homebrew) |
| Lenguaje | Python | 3.12 |
| DataFrames | pandas | 3.0.1 |
| Conexión DB | SQLAlchemy + psycopg2 | 2.0.46 |
| Visualización | matplotlib + seaborn | — |
| Entorno | VS Code + Jupyter Notebook | — |
| Reproducibilidad | Semilla `SEED = 42` | — |
