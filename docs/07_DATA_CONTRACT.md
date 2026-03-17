> **Archivos fuente:**
> - `src/adhoc/schema_discovery.py`

# Data Contract — `inclusion_financiera_clean`

**Base de datos:** `tesis_db` (PostgreSQL 17, local)  
**Esquema:** `public`  
**Generado:** Febrero 2026  
**Fuente de verdad:** `outputs/qc/db_profile_summary.csv` (348 columnas perfiladas)

---

## 1. Unidad de análisis

| Propiedad | Valor |
|-----------|-------|
| **Granularidad** | Municipio × trimestre |
| **PK** | `(cve_mun, periodo_trimestre)` — validada sin duplicados |
| **Filas** | 41,905 |
| **Municipios** | 2,471 |
| **Periodos** | 17 (2018Q3 – 2022Q3) |
| **Balance** | **Casi-balanceado** — 8 municipios con panel incompleto (ver §2) |
| **N esperado si 100% balanceado** | 42,007 (2,471 × 17) |
| **Celdas faltantes** | 102 (0.24%) |

---

## 2. Balance del panel

8 municipios no tienen los 17 trimestres completos:

| `cve_mun` | Periodos observados | Faltantes | Nota |
|-----------|--------------------:|----------:|------|
| 2007 (San Felipe, BC) | 1 | 16 | Imputado tipo_pob; presencia marginal |
| 4013 (Dzitbalché, Camp.) | 1 | 16 | Imputado tipo_pob; presencia marginal |
| 2006 (Playas de Rosarito, BC) | 4 | 13 | |
| 4012 (Candelaria, Camp.) | 4 | 13 | |
| 7125 (Chiapas) | 4 | 13 | |
| 17036 (Morelos) | 4 | 13 | |
| 17034 (Morelos) | 8 | 9 | |
| 17035 (Morelos) | 8 | 9 | |

**Decisión para modelado:** Estos 8 municipios (102 obs. presentes) pueden incluirse o
excluirse como prueba de sensibilidad. Con sólo 1–8 periodos, su contribución al
estimador within es mínima.

---

## 3. Columnas — 348 total

### Índices y restricciones

| Índice | Columnas | Tipo |
|--------|----------|------|
| `pk_inclusion_financiera_clean` | `(cve_mun, periodo_trimestre)` | PK (unique, not null) |
| `idx_clean_cvegeo_mun` | `cvegeo_mun` | B-tree |

---

### 3.1 Identificadores geográficos (9 cols)

| Columna | Tipo | %NULL | Únicos | Rango / Valores | Nota |
|---------|------|------:|-------:|-----------------|------|
| `cve_mun` | bigint | 0% | 2,471 | 1001 – 32058 | PK (parte 1); ID entero INEGI |
| `periodo_trimestre` | text | 0% | 17 | "2018Q3" – "2022Q3" | PK (parte 2) |
| `cvegeo_mun` | text | 0% | 2,471 | "01001" – "32058" | Clave INEGI 5 dígitos (str); **usar para merges externos** |
| `cve_ent` | text | 0% | 32 | "01" – "32" | Entidad federativa (2 dígitos str) |
| `cve_mun3` | text | 0% | 570 | "001" – "570" | Municipio dentro de entidad (3 dígitos str) |
| `cve_edo` | bigint | 0% | 32 | 1 – 32 | Entidad (entero) |
| `trim` | bigint | 0% | 17 | 119 – 421 | Índice interno de trimestre |
| `estado` | text | 0% | 32 | — | Nombre de la entidad |
| `municipio` | text | 0% | 2,424 | — | Nombre del municipio (47 nombres compartidos entre estados) |

### 3.2 Variables de tratamiento (23 cols)

| Columna | Tipo | %NULL | Min | p50 | Max | Uso |
|---------|------|------:|----:|----:|----:|-----|
| **`alcaldesa_final`** | bigint | **0%** | 0 | 0 | 1 | **Tratamiento principal** |
| `ever_alcaldesa` | bigint | 0% | 0 | 0 | 1 | Indicador invariante en t; absorbido por FE mun. |
| `alcaldesa_acumulado` | bigint | 0% | 0 | 0 | 17 | Dosis acumulada; tratamiento alternativo |
| `alcaldesa` | float | 4.7% | 0 | 0 | 1 | Sin imputar; **no usar** |
| `alcaldesa_end` | float | 4.3% | 0 | 0 | 1 | Sin imputar; **no usar** |
| `alcaldesa_transition` | bigint | 0% | 0 | 0 | 1 | ⚠ Endógena |
| `alcaldesa_transition_gender` | bigint | 0% | 0 | 0 | 1 | ⚠ Endógena |
| `alcaldesa_excl_trans` | float | 8.6% | 0 | 0 | 1 | NULL en transiciones; robustez |
| `alcaldesa_end_excl_trans` | float | 8.5% | 0 | 0 | 1 | NULL en transiciones; robustez |
| `alcaldesa_final_f1` | float | 5.9% | 0 | 0 | 1 | ⚠ **LEAD** — leakage futuro |
| `alcaldesa_final_f2` | float | 11.8% | 0 | 0 | 1 | ⚠ **LEAD** — leakage futuro |
| `alcaldesa_final_f3` | float | 17.7% | 0 | 0 | 1 | ⚠ **LEAD** — leakage futuro |
| `alcaldesa_final_l1` | float | 5.9% | 0 | 0 | 1 | LAG; sólo event study |
| `alcaldesa_final_l2` | float | 11.8% | 0 | 0 | 1 | LAG; sólo event study |
| `alcaldesa_final_l3` | float | 17.7% | 0 | 0 | 1 | LAG; sólo event study |
| `alcaldesa_l1` | float | 10.3% | 0 | 0 | 1 | LAG (sin imputar) |
| `alcaldesa_l2` | float | 15.8% | 0 | 0 | 1 | LAG (sin imputar) |
| `alcaldesa_end_l1` | float | 9.8% | 0 | 0 | 1 | LAG (sin imputar) |
| `alcaldesa_end_l2` | float | 15.3% | 0 | 0 | 1 | LAG (sin imputar) |
| `alcaldesa_excl_trans_l1` | float | 14.0% | 0 | 0 | 1 | LAG (excl trans) |
| `alcaldesa_excl_trans_l2` | float | 19.5% | 0 | 0 | 1 | LAG (excl trans) |
| `alcaldesa_end_excl_trans_l1` | float | 13.9% | 0 | 0 | 1 | LAG (excl trans) |
| `alcaldesa_end_excl_trans_l2` | float | 19.4% | 0 | 0 | 1 | LAG (excl trans) |

**Distribución del tratamiento principal:**

| `alcaldesa_final` | N | % |
|-------------------:|------:|------:|
| 0 | 32,574 | 77.73% |
| 1 | 9,331 | 22.27% |

### 3.3 Población (8 cols)

| Columna | Tipo | %NULL | Min | p50 | Max | Nota |
|---------|------|------:|----:|----:|----:|------|
| `pob` | bigint | 0% | 81 | 13,701 | 1,922,523 | Población total |
| `pob_adulta` | bigint | 0% | 66 | 9,873 | 1,468,256 | Población adulta total |
| `pob_adulta_m` | bigint | 0% | 36 | 5,133 | 766,847 | **Denominador para outcomes _m** |
| `pob_adulta_h` | bigint | 0% | 26 | 4,767 | 736,875 | Denominador para outcomes _h |
| `log_pob` | float | 0% | 4.41 | 9.53 | 14.47 | ln(pob + 1); **control en regresiones** |
| `log_pob_adulta` | float | 0% | 4.20 | 9.20 | 14.20 | ln(pob_adulta + 1) |
| `log_pob_adulta_m` | float | 0% | 3.61 | 8.54 | 13.55 | ln(pob_adulta_m + 1) |
| `log_pob_adulta_h` | float | 0% | 3.30 | 8.47 | 13.51 | ln(pob_adulta_h + 1) |

**Nota:** `pob_m`, `pob_h` y `pob_total` **no existen** en la tabla. Los denominadores
correctos son `pob_adulta_m` / `pob_adulta_h` / `pob_adulta`. La población cambia
lentamente (proyecciones intercensales CONAPO); se trata como predeterminada.

### 3.4 Categóricas (2 cols)

| Columna | Tipo | %NULL | Únicos | Valores |
|---------|------|------:|-------:|---------|
| `tipo_pob` | text | 0% | 6 | Rural, En Transicion, Semi-urbano, Urbano, Semi-metropoli, Metropoli |
| `region` | text | 0% | 6 | Centro Sur y Oriente, Ciudad de Mexico, Noreste, Noroeste, Occidente y Bajio, Sur |

**Distribución de `tipo_pob`:**

| Categoría | N obs |
|-----------|------:|
| Rural | 11,288 |
| En Transicion | 10,613 |
| Semi-urbano | 12,455 |
| Urbano | 6,138 |
| Semi-metropoli | 1,223 |
| Metropoli | 220 |

**Distribución de `region`:**

| Región | N obs |
|--------|------:|
| Sur | 15,632 |
| Centro Sur y Oriente | 12,447 |
| Occidente y Bajio | 6,817 |
| Noroeste | 3,507 |
| Noreste | 3,230 |
| Ciudad de Mexico | 272 |

### 3.5 Outcomes primarios — per cápita (51 cols, sufijo `_pc`)

Fórmula: `outcome_pc = outcome_raw / pob_adulta_{m|h|t} × 10,000`

Todos tienen **0% NULL** y tipo `double precision`. Rango: 0 al valor máximo (outliers
extremos en municipios pequeños).

**Outcomes core para la tesis (mujeres):**

| Columna | p50 | Max | Interpretación |
|---------|----:|----:|----------------|
| `ncont_total_m_pc` | 575 | 179,439 | Contratos totales mujeres / 10k adultas |
| `numtar_deb_m_pc` | 495 | 2,839,566 | Tarjetas débito mujeres / 10k adultas |
| `numtar_cred_m_pc` | 243 | 258,990 | Tarjetas crédito mujeres / 10k adultas |
| `numcontcred_hip_m_pc` | 4.3 | 9,464 | Créditos hipotecarios mujeres / 10k adultas |
| `saldocont_total_m_pc` | 196,374 | 6,594,807,478 | Saldo total mujeres / 10k adultas |
| `ncont_ahorro_m_pc` | 0 | 7,138 | Contratos ahorro mujeres / 10k adultas |

Las 51 columnas siguen el patrón: `{ncont|saldocont|numtar|numcontcred}_{producto}_{m|h|t}_pc`

### 3.6 Outcomes winsorizados (51 cols, sufijo `_pc_w`)

Fórmula: `clip(outcome_pc, percentil_1, percentil_99)`

Todos tienen **0% NULL** y tipo `double precision`. Máximos recortados al p99.

### 3.7 Outcomes asinh (51 cols, sufijo `_pc_asinh`)

Fórmula: `asinh(outcome_pc) = ln(x + √(x² + 1))`

Todos tienen **0% NULL** y tipo `double precision`. **Escala recomendada para modelado.**

> **Verificación empírica (marzo 2026):** Se ejecutaron tests R6 (`_pc_w` en nivel)
> y R7 (`_pc` en nivel crudo) comparando con el baseline asinh. Las especificaciones
> en nivel son inestables (signos inconsistentes, magnitudes dominadas por outliers
> metropolitanos). Los resultados **confirman asinh como especificación principal**.
> Detalles en `docs/05_EDA_EXPLICACION_4.md`, sección 11.9.

**Outcomes core en escala asinh:**

| Columna | p50 | Max |
|---------|----:|----:|
| `ncont_total_m_pc_asinh` | 7.05 | 12.79 |
| `numtar_deb_m_pc_asinh` | 6.90 | 15.55 |
| `numtar_cred_m_pc_asinh` | 6.19 | 13.16 |
| `numcontcred_hip_m_pc_asinh` | 2.16 | 9.85 |
| `saldocont_total_m_pc_asinh` | 12.88 | 23.30 |

### 3.8 Ratios brecha de género (17 cols, prefijo `ratio_mh_`)

Fórmula: `ratio_mh_X = X_m_pc / X_h_pc` (NaN cuando denominador = 0)

| Columna | %NULL | p50 | Max | Nota |
|---------|------:|----:|----:|------|
| `ratio_mh_ncont_total` | 3.5% | 1.01 | 65.79 | ←outcome secundario |
| `ratio_mh_numtar_deb` | 0.9% | 0.81 | 12.23 | ←outcome secundario |
| `ratio_mh_numtar_cred` | 6.9% | 0.77 | 11.60 | ←outcome secundario |
| `ratio_mh_numcontcred_hip` | 28.4% | 0.45 | 7.97 | Brecha fuerte |
| `ratio_mh_ncont_ahorro` | 93.5% | 0.85 | 29.30 | Alto %NULL |
| `ratio_mh_ncont_plazo` | 57.7% | 1.50 | 206.62 | |
| `ratio_mh_ncont_n1` | 91.3% | 0.00 | 86.30 | |
| `ratio_mh_ncont_n2` | 3.6% | 0.97 | 74.14 | |
| `ratio_mh_ncont_n3` | 82.6% | 0.67 | 8.44 | |
| `ratio_mh_ncont_tradic` | 56.4% | 1.03 | 208.82 | |
| `ratio_mh_saldocont_ahorro` | 93.9% | 0.95 | 27,069 | Outliers extremos |
| `ratio_mh_saldocont_plazo` | 57.7% | 1.12 | 92,002 | |
| `ratio_mh_saldocont_n1` | 91.5% | 0.00 | 5,984 | |
| `ratio_mh_saldocont_n2` | 4.1% | 0.82 | 90,237 | |
| `ratio_mh_saldocont_n3` | 82.7% | 0.77 | 19,379 | |
| `ratio_mh_saldocont_tradic` | 56.5% | 0.92 | 60,247 | |
| `ratio_mh_saldocont_total` | 4.0% | 0.94 | 90,237 | |

**Precaución:** Los ratios de saldos tienen outliers extremos (max > 90,000). Esto
refleja municipios donde el denominador masculino es cercano a 0 pero no exactamente
0. Los ratios de conteos son más estables. Para modelado, preferir los de conteos
(ncont) o aplicar winsorización previa a los ratios.

### 3.9 Saldoprom y flags (56 cols) — **NO USAR como outcomes**

| Grupo | Cols | %NULL rango | Nota |
|-------|-----:|-------------|------|
| `saldoprom_*` | 28 | 1.4% – 99.9% | Saldo promedio = saldo/contratos; indefinido cuando contratos = 0 |
| `flag_undef_saldoprom_*` | 28 | 0% | Marcadores de indefinición (1 = saldoprom es ÷0) |

**Decisión:** Excluir ambos grupos del modelado. Los `saldocont_*` (saldo total) son
la alternativa válida y ya están normalizados per cápita.

### 3.10 Outcomes raw (67 cols) — conteos y saldos en nivel

Prefijos: `ncont_` (28), `saldocont_` (28), `numtar_deb_` (4), `numtar_cred_` (4), `numcontcred_hip_` (3).

Todos tienen **0% NULL**, tipo `bigint`. Estos son los valores originales sin
normalizar. Cada uno tiene sufijo `_m` (mujeres), `_h` (hombres), `_pm` (persona
moral) y `_t` (total). No usar en regresiones excepto para cálculos intermedios.

### 3.11 Otras variables (15 cols)

| Columna | Tipo | %NULL | Min | p50 | Max | Nota |
|---------|------|------:|----:|----:|----:|------|
| `cve_mun_int` | bigint | 0% | 1001 | 20228 | 32058 | Duplicidad con `cve_mun` |
| `cve_edo_int` | bigint | 0% | 1 | 20 | 32 | Duplicidad con `cve_edo` |
| `year` | bigint | 0% | 2018 | 2020 | 2022 | Año calendario |
| `quarter` | bigint | 0% | 1 | 3 | 4 | Trimestre (1–4) |
| `t_index` | bigint | 0% | 0 | 8 | 16 | Índice temporal 0-based (0 = 2018Q3) |
| `days_total` | bigint | 0% | 90 | 92 | 92 | Días en el trimestre |
| `days_female` | bigint | 0% | 0 | 0 | 92 | Días con alcaldesa |
| `days_male` | bigint | 0% | 0 | 91 | 92 | Días con alcalde |
| `days_missing` | bigint | 0% | 0 | 0 | 92 | Días sin dato de autoridad |
| `hist_mun_available` | bigint | 0% | 0 | 1 | 1 | ¿Histórico disponible? |
| `quarters_in_base` | bigint | 0% | 1 | 17 | 17 | Trimestres presentes |
| `ok_panel_completo` | bigint | 0% | 0 | 1 | 1 | 1 si 17 trimestres |
| `filled_by_manual` | bigint | 0% | 0 | 0 | 1 | 1 si autoridad fue imputada manualmente |

---

## 4. Alertas de leakage y riesgo

### 4.1 Variables con información futura (LEADS)

| Columna | Riesgo | Regla |
|---------|--------|-------|
| `alcaldesa_final_f1` | 🔴 Lead +1 trimestre | **Nunca como control**; sólo event study |
| `alcaldesa_final_f2` | 🔴 Lead +2 trimestres | **Nunca como control**; sólo event study |
| `alcaldesa_final_f3` | 🔴 Lead +3 trimestres | **Nunca como control**; sólo event study |

### 4.2 Variables post-tratamiento (LAGS)

| Columna | Riesgo | Regla |
|---------|--------|-------|
| `alcaldesa_final_l1` | 🟡 Lag −1 | Sólo event study / placebos |
| `alcaldesa_final_l2` | 🟡 Lag −2 | Sólo event study / placebos |
| `alcaldesa_final_l3` | 🟡 Lag −3 | Sólo event study / placebos |
| `alcaldesa_l1`, `_l2` | 🟡 Lags sin imputar | No usar |
| `alcaldesa_end_l1`, `_l2` | 🟡 Lags sin imputar | No usar |

### 4.3 Variables endógenas al tratamiento

| Columna | Riesgo | Regla |
|---------|--------|-------|
| `alcaldesa_transition` | 🔴 Mecanismo del tratamiento | Excluir como control; se puede usar para definir robustez R2 |
| `alcaldesa_transition_gender` | 🔴 Función directa del tratamiento | Excluir |
| `days_female` / `days_male` | 🟡 Intensidad del tratamiento | Usar sólo como alternativa exploratoria a `alcaldesa_final` |

### 4.4 Variables absorbidas por FE

| Columna | Nota |
|---------|------|
| `ever_alcaldesa` | Time-invariant → absorbida por FE municipio; usar sólo para balance y descriptivos. **No usar como interacción** con `alcaldesa_final`: $D_{it} \times \text{ever}_i \equiv D_{it}$ (colinealidad perfecta, ya que cuando $D=1$ siempre $\text{ever}=1$). Ver `docs/04_EDA_EXPLICACION_3.md`, sección 15.1. |
| `tipo_pob` | Time-invariant → absorbida; usar para interacciones |
| `region` | Time-invariant → absorbida; usar para interacciones |

---

## 5. Jerarquía de especificaciones verificada

Basado en los tests de robustez R1–R7 (ver `src/tesis_alcaldesas/models/robustness.py`
y `docs/05_EDA_EXPLICACION_4.md` §11.9), las especificaciones de la variable
dependiente se ordenan así:

| Prioridad | Especificación | Sufijo | Resultado R6/R7 | Uso |
|-----------|---------------|--------|-----------------|-----|
| **1. Principal** | asinh(per cápita) | `_pc_asinh` | Estable, interpretable | Tabla principal |
| **2. Robustez funcional** | winsor p1-p99 + asinh | `_pc_w` + `np.arcsinh()` | β=+0.008 (consistente) | Tabla robustez |
| **3. Robustez de escala** | log(1 + per cápita) | `_pc_log1p` | β=+0.005 (consistente) | Tabla robustez |
| 4. Apéndice | winsor en nivel | `_pc_w` | Signos inestables entre outcomes | Solo apéndice |
| 5. Apéndice | per cápita cruda | `_pc` | Dominada por outliers | Solo apéndice |

**Regla:** Si las prioridades 1–3 coinciden en signo y significancia → resultados robustos.
Las prioridades 4–5 documentan por qué la transformación asinh es *necesaria*.

---

## 6. Resumen de conteos por grupo

| Grupo | N cols | %NULL rango | Tipo predominante | Uso en modelado |
|-------|-------:|-------------|-------------------|-----------------|
| ID / Geo | 9 | 0% | bigint, text | Identificación, merges |
| Tratamiento | 23 | 0%–19.5% | bigint, float | Variable independiente |
| Población | 8 | 0% | bigint, float | Controles |
| Categóricas | 2 | 0% | text | Heterogeneidad |
| Outcomes per cápita | 51 | 0% | float | Referencia |
| Outcomes winsorizados | 51 | 0% | float | Robustez |
| **Outcomes asinh** | **51** | **0%** | **float** | **Variable dependiente principal** |
| Ratios M/H | 17 | 0.9%–93.9% | float | Outcomes secundarios |
| Saldoprom + flags | 56 | 0%–99.9% | float, bigint | **Excluir** |
| Outcomes raw | 67 | 0% | bigint | Cálculos intermedios |
| Otras | 15 | 0% | bigint, text | Auxiliares |
| **Total** | **348** | | | |

---

## 7. Reproducción del perfil

Para regenerar el CSV de perfil (`outputs/qc/db_profile_summary.csv`):

```bash
cd <ruta_del_repo>
source .venv/bin/activate
python src/schema_discovery.py
```

Para ejecutar las queries de QC manualmente:

```bash
psql -d tesis_db -f sql/00_schema_discovery.sql
```

**Dependencias:** `sqlalchemy`, `pandas` (ya instalados en `.venv`).

---

## 8. Archivos generados

| Archivo | Contenido |
|---------|-----------|
| `sql/00_schema_discovery.sql` | 12 queries SQL de QC (solo lectura) |
| `docs/07_DATA_CONTRACT.md` | Este documento |
| `outputs/qc/db_profile_summary.csv` | Perfil completo: 348 filas × 8 campos (column, dtype, null_count, null_rate, n_unique, min, p50, max) |
| `src/schema_discovery.py` | Script Python que genera el CSV y reporta el inventario |
