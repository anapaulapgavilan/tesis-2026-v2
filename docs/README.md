> **Archivos fuente:**
> - `src/tesis_alcaldesas/config.py`
> - `src/tesis_alcaldesas/run_all.py`
> - `notebooks/eda.ipynb`
> - `notebooks/tesis_analisis.ipynb`
> - `src/eda/run_eda.py`
> - `src/transformaciones_criticas.py`
> - `src/transformaciones_altas.py`
> - `src/transformaciones_medias.py`

# Alcaldesas e Inclusión Financiera de las Mujeres en México

> **Pregunta de investigación:** ¿Cuál es el efecto de la representación política
> a nivel municipal (alcaldesas) en la inclusión financiera de las mujeres en México?

**Autora:** Ana Paula Pérez Gavilán  
**Tipo:** Tesis de grado

---

## Descripción general

Este repositorio contiene el código, la documentación metodológica y los outputs
del análisis empírico de la tesis. La investigación estima el efecto causal de
que una mujer ocupe la presidencia municipal (alcaldesa) sobre indicadores de
inclusión financiera femenina, utilizando datos administrativos de la Comisión
Nacional Bancaria y de Valores (CNBV) e información del género de la autoridad
municipal.

**Estrategia empírica:**

- Panel municipal-trimestral: 2,471 municipios × 17 trimestres (2018-T3 a 2022-T3).
- Diseño de **diferencias-en-diferencias (DiD)** con efectos fijos de municipio
  y trimestre (TWFE), errores estándar agrupados a nivel municipal.
- **Event study** (4 leads, 8 lags) para diagnosticar tendencias paralelas.
- **Robustez:** transformación funcional alternativa (log1p), winsorización,
  exclusión de transiciones, placebo temporal (+4 trimestres) y placebo de género
  (outcomes masculinos).
- **DiD moderno:** Stacked DiD (Cengiz et al. 2019) para corregir posibles sesgos
  TWFE bajo adopción escalonada.
- **MDES:** Minimum Detectable Effect Size al 80% de poder para cuantificar
  qué efectos descarta el resultado nulo.
- **Sensibilidad event study:** Variantes de ventana y bin extremo para blindar
  el borderline p=0.083 en tarjetas de crédito.
- **Sample policy:** Main sample (panel balanceado) + robustez con full sample.
- **Heterogeneidad** por tipo de localidad (CONAPO) y tercil de población,
  con corrección Benjamini-Hochberg por múltiples pruebas.
- **Extensión:** Margen extensivo (LPM para any>0) y composición de género
  (share mujeres), como extensión exploratoria pre-especificada.

Los cinco outcomes primarios (contratos totales, tarjetas de débito, tarjetas
de crédito, créditos hipotecarios y saldo total de mujeres) se miden en tasas
per cápita por cada 10,000 mujeres adultas, en escala asinh (seno hiperbólico
inverso).

---

## Estructura del repositorio

```
├── src/
│   ├── tesis_alcaldesas/              # ← Paquete principal (activo)
│   │   ├── __init__.py
│   │   ├── config.py                  #   Rutas, get_engine(), constantes
│   │   ├── run_all.py                 #   Entrypoint: pipeline completo
│   │   ├── data/
│   │   │   ├── extract_panel.py       #   PostgreSQL → parquet (61 cols)
│   │   │   └── build_features.py      #   Per cápita, asinh, winsor → 170 cols
│   │   └── models/
│   │       ├── utils.py               #   load_panel, run_panel_ols, formateo
│   │       ├── table1_descriptives.py #   Tabla 1: descriptivos pre-tratamiento
│   │       ├── twfe.py                #   Tabla 2: TWFE baseline
│   │       ├── event_study.py         #   Figura 1 + pre-trends tests
│   │       ├── robustness.py          #   Tabla 3: robustez
│   │       ├── heterogeneity.py       #   Tabla 4: heterogeneidad + BH
│   │       ├── mdes_power.py          #   Tabla 6: MDES / poder estadístico
│   │       ├── event_study_sensitivity.py  # Figura 2: sensibilidad bin extremo
│   │       ├── sample_policy.py       #   Sample policy: main vs full
│   │       └── extensive_margin.py    #   Tabla 7: extensivo + share
│   │
│   ├── did_moderno/                   # DiD moderno (stacked DiD)
│   │   ├── run_stacked_did.py         #   Tabla 5 + Figura 3
│   │   └── README.md
│   │
│   ├── eda/                           # Pipeline EDA automatizado
│   │   └── run_eda.py
│   ├── transformaciones_criticas.py   # Recs 1-4 EDA (per cápita, constantes)
│   ├── transformaciones_altas.py      # Recs 5-9 EDA (log pob, winsor, ratios)
│   ├── transformaciones_medias.py     # Recs 10-12 EDA (acumulados, asinh)
│   ├── tests/                         # 43 tests de validación del EDA
│   ├── db.py                          # Conexión legacy a PostgreSQL
│   ├── catalog.py                     # Catálogo programático de variables
│   ├── plot_style.py                  # Estilo de gráficos
│   ├── adhoc/                         # Scripts exploratorios (one-off)
│   ├── data/   [LEGACY]              # Originales — ver tesis_alcaldesas/data/
│   └── models/ [LEGACY]              # Originales — ver tesis_alcaldesas/models/
│
├── sql/
│   └── 00_schema_discovery.sql        # 12 queries QC (read-only)
│
├── data/
│   └── processed/                     # Parquets analíticos (en .gitignore)
│       ├── analytical_panel.parquet
│       └── analytical_panel_features.parquet
│
├── docs/                              # Documentación secuencial (01–23)
│   ├── README.md                      #   ← ESTE ARCHIVO (README principal)
│   ├── 01_BRIEF.md                    #   Brief del proyecto
│   ├── 02–05_EDA_EXPLICACION*.md      #   Notas del EDA (4 partes)
│   ├── 06_ANALISIS_DESCRIPTIVO_TESIS.md # Análisis descriptivo
│   ├── 07_DATA_CONTRACT.md            #   Contrato de datos (348 columnas)
│   ├── 08_DATASET_CONSTRUCCION.md     #   Construcción del dataset analítico
│   ├── 09_MODELADO_PROPUESTA.md       #   Propuesta de modelado (técnica)
│   ├── 10_EXPLICACION_MODELADO.md     #   Tutorial explicativo del modelado
│   ├── 11_TABLA1_ESTADISTICAS_DESCRIPTIVAS.md # Tutorial Tabla 1 descriptiva
│   ├── 12_EXPLICACION_EVENT_STUDY.md  #   Tutorial completo del event study
│   ├── 13_MODELADO_ECONOMETRICO.md    #   Ecuaciones, supuestos, decisiones
│   ├── 14_DID_MODERNO.md             #   DiD moderno: stacked DiD
│   ├── 15_EVENT_STUDY_SENSIBILIDAD.md #   Sensibilidad del event study
│   ├── 16_MDES_PODER.md              #   MDES y poder estadístico
│   ├── 17_RESULTADOS_EMPIRICOS.md     #   Sección de resultados (texto tesis)
│   ├── 18_EXTENSION_OUTCOMES.md      #   Extensión: extensivo + composición
│   ├── 19_APENDICE.md                #   Índice del apéndice estadístico
│   ├── 20_BIBLIOGRAFIA.md            #   Bibliografía DiD moderno + BibTeX
│   ├── 21_ONE_PAGER_ASESOR.md        #   Resumen ejecutivo (~1 pág)
│   ├── 22_CHECKLIST_DEFENSA.md       #   Checklist para defensa
│   └── 23_FREEZE_RELEASE.md          #   Freeze & release de resultados
│
├── notebooks/
│   ├── tesis_analisis.ipynb           # Notebook exploratorio principal
│   └── eda.ipynb                      # EDA interactivo
│
├── outputs/
│   ├── eda/                           # Figuras y tablas del EDA (13 archivos)
│   ├── paper/                         # Tablas (.csv/.tex), figuras, coeficientes
│   │   ├── tabla_1_descriptiva.*
│   │   ├── tabla_2_twfe.*
│   │   ├── tabla_3_robustez.*
│   │   ├── tabla_4_heterogeneidad.*
│   │   ├── tabla_5_did_moderno.csv
│   │   ├── tabla_6_mdes.*
│   │   ├── tabla_7_extensive.*
│   │   ├── figura_1_event_study.pdf/.png
│   │   ├── figura_2_event_study_sens.pdf
│   │   ├── figura_3_did_moderno_eventstudy.pdf
│   │   ├── pretrends_tests.csv
│   │   └── event_study_coefs_*.csv
│   └── qc/                            # Perfiles y chequeos de calidad
│
├── requirements.txt                   # Dependencias Python
├── pyproject.toml                     # Empaquetado (pip install -e .)
├── Makefile                           # Atajos: make models, make clean
├── .env.example                       # Template de variables de entorno
├── .gitignore
└── README.md                          # Puntero → docs/README.md
```

---

## Base de datos

### Conexión

| Campo | Valor |
|---|---|
| **Motor** | PostgreSQL 17.8 (Homebrew) |
| **Host** | `localhost` |
| **Port** | `5432` |
| **Database** | `tesis_db` |
| **Username** | `anapaulaperezgavilan` |
| **Password** | *(vacío — autenticación peer/trust)* |
| **Encoding** | UTF-8 |
| **Collation** | en_US.UTF-8 |
| **Tamaño total BD** | 1,013 MB |

**Desde Python:**
```python
from sqlalchemy import create_engine
engine = create_engine("postgresql://anapaulaperezgavilan@localhost:5432/tesis_db")
```

**Variables de entorno** (ver `.env.example`):
```bash
PGHOST=localhost
PGPORT=5432
PGDATABASE=tesis_db
PGUSER=tu_usuario
PGPASSWORD=
```

### Tablas

| Tabla | Filas | Columnas | Tamaño | Descripción |
|---|---|---|---|---|
| `inclusion_financiera` | 41,905 | 175 | 887 MB | Datos crudos (carga directa del Excel) |
| `inclusion_financiera_clean` | 41,905 | 348 | 112 MB | Datos transformados (per cápita, asinh, ratios, flags) |

Ambas tablas comparten la misma **llave primaria compuesta**: `PRIMARY KEY (cve_mun, periodo_trimestre)`.

### Cobertura del panel

| Dimensión | Detalle |
|---|---|
| **Municipios** | 2,471 (clave: `cve_mun`) |
| **Estados** | 32 |
| **Periodo** | 2018Q3 – 2022Q3 (17 trimestres) |
| **Observaciones** | 41,905 (panel ligeramente desbalanceado: 42,007 − 102 = 41,905) |
| **Regiones** | Occidente y Bajio, Noroeste, Sur, Noreste, Ciudad de Mexico, Centro Sur y Oriente |

---

## Diccionario de variables — `inclusion_financiera` (175 columnas)

### Bloque 1: Identificadores (9 cols)

| Columna | Tipo | Descripción |
|---|---|---|
| `cve_mun` | INTEGER | **PK.** Clave del municipio (INEGI) |
| `trim` | INTEGER | Trimestre codificado (ej. 318 = Q3 2018) |
| `cve_edo` | INTEGER | Clave del estado (1–32) |
| `cve_ent` | TEXT | Clave de entidad zero-padded AGEE (ej. "01") |
| `cve_mun3` | TEXT | Clave municipal zero-padded AGEM (ej. "001") |
| `cvegeo_mun` | TEXT | Clave geoestadística canónica INEGI (ej. "01001") |
| `region` | TEXT | Región geográfica |
| `estado` | TEXT | Nombre del estado |
| `municipio` | TEXT | Nombre del municipio |

### Bloque 2: Demográficas (5 cols)

| Columna | Tipo | Descripción |
|---|---|---|
| `pob` | INTEGER | Población total del municipio |
| `pob_adulta` | INTEGER | Población adulta |
| `pob_adulta_m` | INTEGER | Población adulta mujeres |
| `pob_adulta_h` | INTEGER | Población adulta hombres |
| `tipo_pob` | TEXT | Categoría: Rural, Semi-urbano, En Transicion, Urbano, Semi-metropoli, Metropoli |

### Bloque 3: Inclusión financiera – CNBV (95 cols)

Desagregación por sexo: `_m` = mujeres, `_h` = hombres, `_pm` = persona moral, `_t` = total.

#### Número de contratos (`ncont_*`) — 28 cols, tipo INTEGER

| Prefijo | Producto |
|---|---|
| `ncont_ahorro_` | Cuentas de ahorro |
| `ncont_plazo_` | Depósitos a plazo |
| `ncont_n1_` | Cuentas nivel 1 |
| `ncont_n2_` | Cuentas nivel 2 |
| `ncont_n3_` | Cuentas nivel 3 |
| `ncont_tradic_` | Cuentas tradicionales |
| `ncont_total_` | Total de contratos |

#### Saldo de contratos (`saldocont_*`) — 28 cols, tipo INTEGER/BIGINT

| Prefijo | Producto | Nota |
|---|---|---|
| `saldocont_ahorro_` | Saldo en ahorro | INTEGER |
| `saldocont_plazo_` | Saldo a plazo | **BIGINT** (valores > 2 mil millones) |
| `saldocont_n1_` | Saldo nivel 1 | INTEGER |
| `saldocont_n2_` | Saldo nivel 2 | BIGINT parcial |
| `saldocont_n3_` | Saldo nivel 3 | INTEGER |
| `saldocont_tradic_` | Saldo tradicional | **BIGINT** |
| `saldocont_total_` | Saldo total | **BIGINT** |

#### Saldo promedio (`saldoprom_*`) — 28 cols, tipo FLOAT (NULLable)

Saldo promedio por contrato. Mismos sufijos que arriba.

> **Nota:** Los valores originales con `"-"` (sin dato) fueron convertidos a `NULL`. Estos NULLs son **indefiniciones estructurales** (0 contratos → saldo promedio = ÷0), no datos faltantes. Las columnas `flag_undef_saldoprom_*` marcan cuáles son (ver Bloque 6). Tasas de NULL van del 1.4% (`total_t`) al 99.9% (`n1_pm`).

#### Créditos y tarjetas (11 cols, tipo INTEGER)

| Columna(s) | Descripción |
|---|---|
| `numcontcred_hip_m/h/t` | Número de créditos hipotecarios |
| `numtar_deb_m/h/pm/t` | Número de tarjetas de débito |
| `numtar_cred_m/h/pm/t` | Número de tarjetas de crédito |

### Bloque 4: Auxiliares temporales (5 cols)

| Columna | Tipo | Descripción |
|---|---|---|
| `cve_mun_int` | INTEGER | Clave municipal (solo parte municipal) |
| `cve_edo_int` | INTEGER | Clave estatal (solo parte estatal) |
| `year` | INTEGER | Año (2018–2022) |
| `quarter` | INTEGER | Trimestre del año (1–4) |
| `periodo_trimestre` | TEXT | **PK.** Periodo en formato "2019Q1" |

### Bloque 5: Indicador Alcaldesa (33 cols)

#### Construcción del indicador

| Columna | Tipo | Descripción |
|---|---|---|
| `days_total` | INTEGER | Días totales del trimestre (90–92) |
| `days_female` | INTEGER | Días con mujer como autoridad |
| `days_male` | INTEGER | Días con hombre como autoridad |
| `days_missing` | INTEGER | Días sin cobertura en el histórico |

#### Indicadores principales

| Columna | Tipo | Descripción | NULLs |
|---|---|---|---|
| `alcaldesa` | INTEGER | 1 si days_female > days_male (mayoría de días) | 4.7% |
| `alcaldesa_end` | INTEGER | 1 si mujer al cierre del trimestre | 4.3% |
| `alcaldesa_final` | INTEGER | **Variable recomendada.** Versión final con llenado manual | **0%** |

#### Marcadores de transición

| Columna | Tipo | Descripción |
|---|---|---|
| `alcaldesa_transition` | INTEGER | 1 si hubo cambio de autoridad en el trimestre |
| `alcaldesa_transition_gender` | INTEGER | 1 si además hubo cambio de género |

#### Variantes excluyendo transiciones

| Columna | Tipo | Descripción |
|---|---|---|
| `alcaldesa_excl_trans` | INTEGER | alcaldesa = NULL en trimestres de transición |
| `alcaldesa_end_excl_trans` | INTEGER | alcaldesa_end = NULL en trimestres de transición |

#### Rezagos (lags) y adelantos (forwards)

| Columna | Tipo | Descripción |
|---|---|---|
| `alcaldesa_l1`, `alcaldesa_l2` | INTEGER | Rezagos de `alcaldesa` (t-1, t-2) |
| `alcaldesa_end_l1`, `alcaldesa_end_l2` | INTEGER | Rezagos de `alcaldesa_end` |
| `alcaldesa_excl_trans_l1/l2` | INTEGER | Rezagos excluyendo transiciones |
| `alcaldesa_end_excl_trans_l1/l2` | INTEGER | Rezagos de end excluyendo transiciones |
| `alcaldesa_final_l1/l2/l3` | INTEGER | Rezagos de `alcaldesa_final` (t-1, t-2, t-3) |
| `alcaldesa_final_f1/f2/f3` | INTEGER | Adelantos de `alcaldesa_final` (t+1, t+2, t+3) |

#### Calidad del panel

| Columna | Tipo | Descripción |
|---|---|---|
| `hist_mun_available` | INTEGER | 1 si el municipio tiene histórico de autoridades |
| `quarters_in_base` | INTEGER | Trimestres del municipio en la base (17 = completo) |
| `ok_panel_completo` | INTEGER | 1 si el panel original estaba completo |
| `filled_by_manual` | INTEGER | 1 si `alcaldesa_final` fue llenado manualmente |
| `t_index` | INTEGER | Índice temporal (0–16) |

### Bloque 6: Flags de missingness estructural (28 cols)

Patrón: `flag_undef_saldoprom_{producto}_{sexo}` — tipo INTEGER (0/1).

Marcan con `1` los registros donde el saldo promedio es NULL por indefinición estructural (0 contratos → ÷0). Productos: ahorro, plazo, n1, n2, n3, tradic, total. Sufijos: m, h, pm, t.

| Producto | % undefined (sufijo `_t`) |
|---|---|
| `ahorro` | 92.7% |
| `n1` | 90.6% |
| `n3` | 82.0% |
| `plazo` | 56.9% |
| `tradic` | 56.1% |
| `n2` | 1.5% |
| `total` | 1.4% |

> **Uso:** Para regresiones sobre `saldoprom_*`, filtrar `flag_undef_saldoprom_* = 0`.

### Resumen de tipos — `inclusion_financiera`

| Tipo | Columnas | Ejemplos |
|---|---|---|
| INTEGER | 149 | Conteos, indicadores, población, flags |
| BIGINT | 15 | Saldos monetarios (`saldocont_plazo_*`, `saldocont_tradic_*`, `saldocont_total_*`) |
| TEXT | 8 | `region`, `estado`, `municipio`, `tipo_pob`, `periodo_trimestre`, `cve_ent`, `cve_mun3`, `cvegeo_mun` |
| FLOAT | 3 | `saldoprom_*` (NULLable por indefinición estructural) |
| **Total** | **175** | |

### Columnas adicionales en `inclusion_financiera_clean` (+173 cols)

La tabla `_clean` conserva las 175 columnas originales (con tipos promovidos a `bigint`/`double precision`) y añade 173 columnas derivadas:

| Familia | Sufijo | Ejemplo | Cols | Descripción |
|---|---|---|---|---|
| Per cápita | `_pc` | `ncont_total_m_pc` | 51 | Variable / pob_adulta × 10,000 |
| Winsorized | `_pc_w` | `ncont_total_m_pc_w` | 51 | Per cápita + winsorización p1/p99 |
| Asinh | `_pc_asinh` | `ncont_total_m_pc_asinh` | 51 | asinh(per cápita) — escala para modelos |
| Log-población | `log_` | `log_pob`, `log_pob_adulta` | 4 | ln(pob + 1) |
| Ratios M/H | `ratio_mh_` | `ratio_mh_ncont_total` | 17 | Brecha de género: var_m / var_h |
| Tratamiento | — | `ever_alcaldesa`, `alcaldesa_acumulado` | 2 | Indicadores derivados |

---

## Requisitos y entorno

### Python

- **Versión mínima:** Python 3.10+
- **Paquetes clave:**

| Paquete | Uso |
|---|---|
| `pandas`, `numpy` | Manipulación de datos |
| `pyarrow` | Lectura/escritura parquet |
| `sqlalchemy`, `psycopg2-binary` | Conexión PostgreSQL |
| `linearmodels` | PanelOLS (TWFE, event study) |
| `statsmodels` | Diagnósticos, corrección BH |
| `scipy` | Tests chi-cuadrado |
| `matplotlib`, `seaborn` | Figuras |
| `jinja2` | Exportación LaTeX |

### Base de datos

- **PostgreSQL 17+** con la base `tesis_db` poblada (tabla `inclusion_financiera_clean`,
  41,905 filas × 348 columnas).
- Para iniciar: `brew services start postgresql@17`

---

## Orden de ejecución desde cero (pipeline)

### Paso 0 — Preparar entorno

```bash
git clone https://github.com/<tu-usuario>/tesis-2026.git
cd tesis-2026/Code

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .                   # instala tesis_alcaldesas como paquete
```

Configurar las variables de entorno para PostgreSQL (ver `.env.example`).

### Paso 1 — Perfil de la base y data contract *(opcional)*

El resultado ya está documentado en `docs/07_DATA_CONTRACT.md` y los queries en
`sql/00_schema_discovery.sql`. Si se necesita regenerar:

```bash
psql -d tesis_db -f sql/00_schema_discovery.sql
```

### Paso 2 — EDA y transformaciones *(solo si la tabla limpia no existe)*

Si `inclusion_financiera_clean` no existe en PostgreSQL, ejecutar:

```bash
# EDA automatizado (diagnóstico sobre tabla cruda)
python src/eda/run_eda.py

# Transformaciones derivadas del EDA
python src/transformaciones_criticas.py    # Recs 1-4: per cápita, excluir constantes
python src/transformaciones_altas.py       # Recs 5-9: log pob, winsor, ratios, ever_alcaldesa
python src/transformaciones_medias.py      # Recs 10-12: acumulado, asinh, tipo_pob
```

Validar con:
```bash
python -m pytest src/tests/ -v             # 43 tests
```

### Paso 3 — Construir dataset analítico

```bash
python -m tesis_alcaldesas.data.extract_panel     # → data/processed/analytical_panel.parquet
python -m tesis_alcaldesas.data.build_features    # → data/processed/analytical_panel_features.parquet
```

Esto genera el panel analítico final (41,905 × ~170 cols) y diagnósticos en `outputs/qc/`.

### Paso 4 — Correr modelos econométricos

```bash
python -m tesis_alcaldesas.models.table1_descriptives   # Tabla 1: descriptivos
python -m tesis_alcaldesas.models.twfe                  # Tabla 2: TWFE baseline
python -m tesis_alcaldesas.models.event_study           # Figura 1 + pre-trends
python -m tesis_alcaldesas.models.robustness            # Tabla 3: robustez
python -m tesis_alcaldesas.models.heterogeneity         # Tabla 4: heterogeneidad
```

### Paso 5 — Extensiones robustas

```bash
PYTHONPATH=src python -m did_moderno.run_stacked_did              # Tabla 5 + Figura 3: DiD moderno
python -m tesis_alcaldesas.models.mdes_power                      # Tabla 6: MDES
python -m tesis_alcaldesas.models.event_study_sensitivity          # Figura 2: sensibilidad
python -m tesis_alcaldesas.models.sample_policy                    # Sample policy: main vs full
python -m tesis_alcaldesas.models.extensive_margin                 # Tabla 7: extensivo + composición
PYTHONPATH=src python -m did_moderno.window_robustness            # Tabla A1: robustez de ventana
```

### Paso 5b — Pipeline completo automático (alternativa)

```bash
PYTHONPATH=src python -m tesis_alcaldesas.run_all     # Corre TODO en orden
# o bien:
make models                                            # Via Makefile
```

Los resultados (tablas `.csv` / `.tex` y figuras) se depositan en `outputs/paper/`.

### Paso 6 — Usar resultados para la tesis

Las tablas y figuras en `outputs/paper/` son las que se incluyen directamente en
el capítulo de resultados de la tesis. La lógica metodológica está documentada en:

- `docs/08_DATASET_CONSTRUCCION.md` — cómo se construyó el dataset analítico
- `docs/13_MODELADO_ECONOMETRICO.md` — ecuaciones, supuestos, decisiones
- `docs/17_RESULTADOS_EMPIRICOS.md` — texto de la sección de resultados

---

## Estado actual del proyecto

| Fase | Estado |
|---|---|
| EDA | ✅ Completado (12/12 recomendaciones, 43/43 tests) |
| Propuesta de modelado | ✅ docs/09_MODELADO_PROPUESTA.md |
| Contrato de datos | ✅ docs/07_DATA_CONTRACT.md (348 columnas) |
| Dataset analítico | ✅ 41,905 × ~170 features |
| Modelos econométricos | ✅ TWFE, event study, robustez, heterogeneidad |
| DiD moderno (Stacked DiD) | ✅ Tabla 5 + Figura 3 |
| MDES / poder estadístico | ✅ Tabla 6 + resumen |
| Sensibilidad event study | ✅ Figura 2 + tests |
| Sample policy | ✅ Main vs full |
| Extensión: extensivo + share | ✅ Tabla 7 |
| Resultados empíricos | ✅ docs/17_RESULTADOS_EMPIRICOS.md |
| Checklist defensa | ✅ docs/22_CHECKLIST_DEFENSA.md |

### Resultado principal

> El **TWFE convencional** no detecta efectos significativos en ninguno de los
> cinco indicadores. Sin embargo, el **Stacked DiD** (Cengiz et al. 2019)
> —diseñado para corregir sesgos bajo adopción escalonada— revela efectos
> positivos y significativos en **contratos totales** (β̂ = 0.082, p = 0.003)
> y **saldo total** (β̂ = 0.274, p < 0.001), con SE clustered a nivel
> municipio original.
>
> Para tarjetas de débito, crédito e hipotecarios, ambos estimadores coinciden
> en la ausencia de efectos. El MDES al 80% de poder indica que el diseño
> permite detectar efectos ≥ 0.04–0.10 en escala asinh, descartando
> efectos grandes en los outcomes nulos.
>
> Los resultados son robustos a transformaciones funcionales, exclusión de
> transiciones, placebos (temporal y de género), y no se modifican al explorar
> heterogeneidad por urbanización o tamaño poblacional (corrección BH).

---

## Historial de cambios en la base de datos

### 20/02/2026 — Carga inicial
- Origen: `Base_20_02_2026.xlsx` (32.9 MB, 1 hoja)
- Se leyó el Excel con pandas y se cargó a PostgreSQL vía SQLAlchemy
- Columnas `saldoprom_*` con `"-"` se convirtieron a `NULL` numérico

### 22/02/2026 — Tipificación de columnas
- **`double precision` → `INTEGER`** en 62 columnas (población, indicadores binarios, etc.)
- **`double precision` → `BIGINT`** en 15 columnas de saldos monetarios que exceden 2,147,483,647
- **`bigint` → `INTEGER`** en 62 columnas donde el máximo cabía en 32 bits
- **`boolean` → `INTEGER`** en 1 columna (`ok_panel_completo_final`)
- Resultado post-tipificación: `INTEGER` (124 cols), `BIGINT` (15 cols) y `TEXT` (5 cols)
- Resultado actual (post claves INEGI + flags): `INTEGER` (149), `BIGINT` (15), `TEXT` (8), `FLOAT` (3) = **175 cols**

### 22/02/2026 — Llave primaria
- Se verificó unicidad: 41,905 filas = 41,905 combinaciones únicas de `(cve_mun, periodo_trimestre)`
- Se creó constraint `pk_inclusion_financiera PRIMARY KEY (cve_mun, periodo_trimestre)`
- Esto impide duplicados por construcción y crea un índice B-tree automático

### 22/02/2026 — Claves geográficas canónicas INEGI
- Se crearon 3 columnas nuevas:
  - `cve_ent` (TEXT, 2 chars): clave de entidad zero-padded (AGEE), ej. `"01"`
  - `cve_mun3` (TEXT, 3 chars): clave municipal zero-padded (AGEM), ej. `"001"`
  - `cvegeo_mun` (TEXT, 5 chars): clave geográfica canónica = `cve_ent || cve_mun3`, ej. `"01001"`
- Las 3 columnas tienen constraint `NOT NULL`
- 2,471 municipios únicos verificados con formato estándar INEGI de 5 dígitos

### 22/02/2026 — Flags de missingness estructural
- **Problema:** `saldoprom_*` contenían `"-"` cuando `ncont_* = 0` (saldo promedio indefinido ÷0)
- **Verificación:** 100% de NULLs en `saldoprom_*` corresponden a `ncont_* = 0`
- **Solución:** 28 columnas `flag_undef_saldoprom_{producto}_{sexo}` (INTEGER, 0/1)

### 23/02/2026 — Auditoría del diccionario
- Se cruzó diccionario Excel (148 vars) vs base real PostgreSQL (175 cols)
- 31 columnas faltantes agregadas, 4 variables fantasma eliminadas
- 61 tipos corregidos, 28 conteos de NULLs corregidos

---

## Licencia

Proyecto académico — uso personal.
