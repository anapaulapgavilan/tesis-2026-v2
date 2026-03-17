> **Archivos fuente:**
> - `src/tesis_alcaldesas/config.py`
> - `src/db.py`

# Brief Analítico — Tesis: Inclusión Financiera y Alcaldesas

**Pregunta de investigación:** ¿Cuál es el efecto de la representación política a nivel municipal en la inclusión financiera de las mujeres en México?

**Base de datos:** `tesis_db` (PostgreSQL 17.8) · Tabla: `inclusion_financiera`

---

## 1. Unidad de análisis

**Municipio-trimestre.**

Cada registro representa un municipio de México en un trimestre específico. La llave primaria es `(cve_mun, periodo_trimestre)`, donde:

- `cve_mun` (INTEGER): clave INEGI del municipio (2,471 municipios únicos).
- `periodo_trimestre` (TEXT): trimestre en formato `"2019Q1"` (17 trimestres únicos).

Total de registros: **41,905** = 2,471 municipios × 17 trimestres.

---

## 2. Granularidad temporal

**Trimestral.**

- **Periodo cubierto:** 2018-Q3 a 2022-Q3 (17 trimestres completos).
- **Variables auxiliares:** `year` (2018–2022), `quarter` (1–4), `trim` (codificación numérica, ej. 318 = Q3 2018), `t_index` (índice temporal 0–16).
- **Periodos completos:** Sí — el panel está **100% balanceado**; todos los municipios tienen exactamente 17 trimestres.

---

## 3. Cobertura

### Geográfica
- **32 estados** y **2,471 municipios** cubiertos.
- **6 regiones:** Occidente y Bajío, Noroeste, Sur, Noreste, Ciudad de México, Centro Sur y Oriente.

### Temporal
- **No faltan periodos.** El panel es 100% balanceado (cada municipio tiene 17 trimestres).
- La columna `quarters_in_base` siempre vale 17; `ok_panel_completo_final` siempre vale 1.

### Cambios en definiciones / calidad
- **Inclusión financiera (CNBV):** Los valores originales con `"-"` (sin dato) fueron convertidos a `NULL` numérico. No se reportan cambios metodológicos de la CNBV en el periodo.
- **Indicador de alcaldesa:** Tiene tres variantes con distintos niveles de completitud:
  - `alcaldesa`: 4.7% de NULLs (basada en mayoría de días con mujer al frente).
  - `alcaldesa_end`: 4.3% de NULLs (basada en quién estaba al cierre del trimestre).
  - `alcaldesa_final`: **0% NULLs** — versión recomendada, con llenado manual donde faltaba dato.
- Las columnas `hist_mun_available`, `hist_state_available`, `filled_by_manual` documentan la calidad del dato de género de la autoridad.

---

## 4. Diccionario de variables

La base tiene **144 columnas** organizadas en 5 bloques:

| Bloque | Columnas | Descripción |
|---|---|---|
| **Identificadores** | 6 | `cve_mun`, `trim`, `cve_edo`, `region`, `estado`, `municipio` |
| **Demográficas** | 5 | `pob`, `pob_adulta`, `pob_adulta_m`, `pob_adulta_h`, `tipo_pob` |
| **Inclusión financiera (CNBV)** | 95 | Contratos (`ncont_*`), saldos (`saldocont_*`), saldos promedio (`saldoprom_*`), créditos hipotecarios (`numcontcred_hip_*`), tarjetas de débito/crédito (`numtar_deb_*`, `numtar_cred_*`) |
| **Auxiliares temporales** | 5 | `cve_mun_int`, `cve_edo_int`, `year`, `quarter`, `periodo_trimestre` |
| **Indicador Alcaldesa** | 33 | Días por género, indicadores binarios, transiciones, rezagos/adelantos, calidad del panel |

### Tipos de datos
- **INTEGER:** 124 columnas (indicadores binarios, conteos, población, saldos promedio).
- **BIGINT:** 15 columnas (saldos monetarios que exceden 2,147 millones).
- **TEXT:** 5 columnas (`region`, `estado`, `municipio`, `tipo_pob`, `periodo_trimestre`).

### Desagregación por sexo (CNBV)
Los sufijos indican: `_m` = mujeres, `_h` = hombres, `_pm` = persona moral, `_t` = total.

### Reglas de negocio clave
- `alcaldesa_final` = 1 si la autoridad municipal es mujer (variable recomendada, sin NULLs).
- `alcaldesa_transition` = 1 si hubo cambio de autoridad en el trimestre.
- `alcaldesa_transition_gender` = 1 si además hubo cambio de género.
- Variantes `*_excl_trans` anulan el indicador (NULL) en trimestres de transición.
- Rezagos (`_l1`, `_l2`, `_l3`) y adelantos (`_f1`, `_f2`, `_f3`) disponibles para `alcaldesa_final`.

---

## 5. Uso esperado

**Inferencia causal.**

El objetivo es estimar el **efecto causal** de tener una alcaldesa sobre indicadores de inclusión financiera de las mujeres a nivel municipal. Esto implica:

- **Estructura de panel:** Se aprovecha la variación within-municipality a lo largo del tiempo (efectos fijos de municipio + efectos fijos de tiempo).
- **Variable de tratamiento:** `alcaldesa_final` (binaria, 0/1), con rezagos disponibles para evaluar efectos dinámicos.
- **Variables de resultado:** Indicadores de inclusión financiera desagregados por sexo (contratos, saldos, tarjetas) — especialmente los sufijos `_m` (mujeres).
- **Controles necesarios:** Población (`pob`, `pob_adulta_m`), tipo de municipio (`tipo_pob`), región, transiciones de gobierno.
- **Consideraciones:**
  - Las variantes `*_excl_trans` permiten excluir trimestres de transición política (potencialmente endógenos).
  - Los rezagos (`_l1`, `_l2`, `_l3`) y adelantos (`_f1`, `_f2`, `_f3`) permiten estudiar pre-trends y efectos dinámicos (event study).
  - El panel está 100% balanceado, lo que facilita la estimación de modelos de efectos fijos.

---

## 6. Inspección estructural mínima (23/02/2026)

### 6.1 `df.info()` — Tipos, conteos no-NA y memoria

| Parámetro | Valor |
|---|---|
| Filas | 41,905 |
| Columnas | 175 |
| Tipos | `int64` (121), `float64` (46), `object` (8) |
| Memoria | **71.4 MB** (deep) |
| Columnas 100% completas (non-null = 41,905) | 128 de 175 |
| Columnas con algún NULL | 47 de 175 |

### 6.2 `df.describe()` — Estadística descriptiva

- **167 columnas numéricas** procesadas (excluye 8 `object`).
- `count` varía de **34** (columnas con muchos NULLs, ej. `saldoprom_n1_pm`) a **41,905** (completas).
- **46 columnas** tienen `count < 41,905` (son las que tienen NULLs).
- **3 columnas constantes** (std = 0):
  - `hist_state_available` → siempre 1 (todos los estados tienen histórico).
  - `missing_quarters_alcaldesa` → siempre 0 (panel final completo).
  - `ok_panel_completo_final` → siempre 1 (panel final completo).
  - *Nota:* Estas 3 columnas no aportan variación y pueden excluirse de modelos.
- **0 columnas con valores negativos** → no se detectan errores de signo.

### 6.3 `df.isna()` — Mapa de faltantes

| Métrica | Valor |
|---|---|
| Celdas totales | 7,333,375 |
| Celdas NA | **830,549** (11.33%) |
| Columnas con NULLs | 47 de 175 |
| Columnas 100% completas | 128 de 175 |

#### Desglose por grupo de variables con NULLs:

**a) Saldo promedio `saldoprom_*` (28 cols): 600 – 41,871 NULLs**
- Son **indefiniciones estructurales** (÷0), no datos faltantes reales.
- Las columnas `flag_undef_saldoprom_*` ya marcan estos casos.
- Rango de tasas: 1.4% (`saldoprom_total_t`) a 99.9% (`saldoprom_n1_pm`).

**b) Indicador alcaldesa `alcaldesa_*` (18 cols): 1,781 – 8,185 NULLs**
- Variantes sin llenado manual (`alcaldesa`, `alcaldesa_end`, `*_excl_trans`) y sus rezagos.
- La variable recomendada `alcaldesa_final` tiene **0 NULLs**.
- Los rezagos `_l1`, `_l2`, `_l3` pierden observaciones por construcción (primeros trimestres).
- Las variantes `*_excl_trans` tienen NULLs adicionales por diseño (trimestres de transición).

**c) Otras (1 col):**
- `tipo_pob`: **2 NULLs** (0.005%) — 2 municipios sin clasificación de tipo de población.

#### Columnas categóricas (`object`):

| Columna | Únicos | Ejemplo |
|---|---|---|
| `region` | 6 | Sur |
| `estado` | 32 | Oaxaca |
| `municipio` | 2,424 | San Juan Yatzona |
| `tipo_pob` | 6 | Rural, Semi-urbano, En Transicion, Urbano, Semi-metropoli, Metropoli |
| `periodo_trimestre` | 17 | 2021Q2 |
| `cve_ent` | 32 | 20 |
| `cve_mun3` | 570 | 223 |
| `cvegeo_mun` | 2,471 | 20223 |

> **Nota:** `municipio` tiene 2,424 únicos vs 2,471 `cve_mun` → hay **47 municipios con nombre repetido** en distintos estados (ej. "San Juan" aparece en varios estados). Siempre usar `cve_mun` o `cvegeo_mun` como identificador, nunca `municipio`.

### 6.4 Alertas y acciones derivadas

| # | Hallazgo | Impacto | Acción sugerida |
|---|---|---|---|
| 1 | 3 columnas constantes | No aportan variación → ruido en modelos | Excluir de regresiones |
| 2 | `tipo_pob` tiene 2 NULLs | Mínimo, pero impide usar como factor sin tratar | Investigar qué 2 municipios son y asignar categoría |
| 3 | 47 nombres de municipio repetidos | Riesgo de merge incorrecto | Siempre usar `cve_mun` o `cvegeo_mun` |
| 4 | `saldoprom_*` con hasta 99.9% NULLs | Muchas obs no usables para margen intensivo | Filtrar con `flag_undef_saldoprom_* = 0` |
| 5 | Rezagos `_l1/l2/l3` con NULLs por diseño | Primeros trimestres sin rezago | Documentado, no requiere acción |

---

## 7. Auditoría del diccionario (23/02/2026)

Se cruzó el diccionario (`Diccionario_y_QC_Base_CNBV_alcaldesa_v2.xlsx`, hoja `01_diccionario`, 148 variables) contra la tabla real en PostgreSQL (175 columnas). Hallazgos:

### 7.1 Conteo de columnas desactualizado

| Fuente | Columnas |
|---|---|
| Diccionario (Excel) | 148 |
| README.md | 144 |
| Base real (PostgreSQL) | **175** |

**Acción:** Actualizar diccionario y README a 175 columnas.

### 7.2 Columnas en la base que NO están en el diccionario (31)

#### Identificadores nuevos (3)
| Columna | Tipo real | Posible definición |
|---|---|---|
| `cve_ent` | object | Clave de entidad (texto, ej. "01") |
| `cve_mun3` | object | Clave municipal de 3 dígitos (texto) |
| `cvegeo_mun` | object | Clave geoestadística municipal completa (5 dígitos, texto) |

#### Flags de saldo promedio indefinido (28)
Patrón: `flag_undef_saldoprom_{producto}_{sexo}` — 28 columnas binarias.
Marcan con 1 los registros donde el saldo promedio original era `"-"` (sin dato) antes de la conversión a NULL. Productos: ahorro, plazo, n1, n2, n3, tradic, total. Sufijos: m, h, pm, t.

**Acción:** Agregar las 31 columnas al diccionario con sus definiciones.

### 7.3 Variables en el diccionario que NO están en la base (4)

| Variable | Observación |
|---|---|
| `alcaldesa_manual` | Fue eliminada o renombrada en la carga a PostgreSQL |
| `fuente_manual` | Ídem |
| `pm_nombre_manual` | Ídem |
| `reason_detailed` | Ídem |

**Acción:** Eliminarlas del diccionario o documentar que fueron eliminadas y por qué.

### 7.4 Discrepancias de tipos (61 columnas)

Se identificaron dos patrones:

#### a) Diccionario dice `float64`, la base tiene `int64` (33 columnas)
Incluye: `pob`, `pob_adulta`, `pob_adulta_m`, `pob_adulta_h`, todos los `saldocont_*`, y `alcaldesa_final`.
**Causa:** Estas columnas se tipificaron a INTEGER/BIGINT en PostgreSQL el 22/02/2026 (ver changelog en README). El diccionario refleja el estado **anterior** a esa limpieza.

#### b) Diccionario dice `object`, la base tiene `float64` (28 columnas)
Todas son `saldoprom_*`. 
**Causa:** Originalmente contenían `"-"` como texto, por lo que eran `object`. Se convirtieron a numérico (NULL donde había `"-"`). El diccionario refleja el estado **anterior**.

**Acción:** Actualizar los 61 tipos en el diccionario para que reflejen los tipos actuales de PostgreSQL.

### 7.5 Discrepancias de NULLs (28 columnas)

Todas las 28 columnas `saldoprom_*` muestran `missing_n = 0` en el diccionario, pero en la base real tienen NULLs masivos (entre 600 y 41,871).

| Columna | NULLs dict | NULLs real | % real |
|---|---|---|---|
| `saldoprom_n1_pm` | 0 | 41,871 | 99.9% |
| `saldoprom_ahorro_pm` | 0 | 41,721 | 99.6% |
| `saldoprom_n3_pm` | 0 | 41,569 | 99.2% |
| `saldoprom_n1_m` | 0 | 40,586 | 96.9% |
| `saldoprom_total_t` | 0 | 600 | 1.4% |

**Causa:** El diccionario se creó cuando los `"-"` se contaban como valores válidos (`object`). Al convertirlos a NULL numérico, los conteos de missing cambiaron dramáticamente. Las columnas `flag_undef_saldoprom_*` probablemente se crearon para preservar esta información.

**Acción:** Actualizar `missing_n` y `missing_pct` para las 28 columnas `saldoprom_*`.

### 7.6 Hoja `00_resumen` desactualizada

La hoja de resumen reporta 148 columnas, pero la base real tiene 175.
Menciona columnas eliminadas (`fuente_manual`, `pm_nombre_manual`).

**Acción:** Actualizar conteo a 175 y ajustar las referencias.

---

## Resumen de acciones necesarias

| # | Acción | Estado |
|---|---|---|
| 1 | Agregar 31 columnas faltantes al diccionario | ✅ Hecho → v3 |
| 2 | Eliminar 4 variables ya inexistentes del diccionario | ✅ Hecho → v3 |
| 3 | Actualizar 61 tipos de datos en el diccionario | ✅ Hecho → v3 |
| 4 | Actualizar 28 conteos de NULLs en columnas `saldoprom_*` | ✅ Hecho → v3 |
| 5 | Actualizar hoja `00_resumen` (148 → 175 columnas) | ✅ Hecho → v3 |
| 6 | Actualizar README.md (144 → 175 columnas, nuevos bloques) | ✅ Hecho |

---

*Última actualización: 23/02/2026*
