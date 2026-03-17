> **Archivos fuente:**
> - `src/tesis_alcaldesas/config.py`
> - `src/tesis_alcaldesas/run_all.py`
> - `src/tesis_alcaldesas/data/extract_panel.py`
> - `src/tesis_alcaldesas/data/build_features.py`
> - `notebooks/eda.ipynb`
> - `notebooks/tesis_analisis.ipynb`
> - `src/eda/run_eda.py`
> - `src/models/*.py`
> - `src/tesis_alcaldesas/models/*.py`
> - `src/transformaciones_criticas.py`
> - `src/transformaciones_altas.py`
> - `src/transformaciones_medias.py`
> - `src/db.py`
> - `src/catalog.py`
> - `src/plot_style.py`

# Guía Completa de Estudio — Tesis: Efecto de las Alcaldesas en la Inclusión Financiera Municipal

> **Propósito**: Recorrer *todo* el código y la documentación de este proyecto de forma
> secuencial, como si estuvieras escribiendo la tesis desde cero.  
> **Formato**: Cada capítulo mapea archivos → conceptos → outputs.  
> **Líneas totales de código**: ~6,200 (Python) · ~2,700 (docs Markdown) · 139 (SQL).

---

## Índice

| Cap. | Tema | Archivos clave |
|------|------|---------------|
| 0 | Visión general del proyecto | `docs/01_BRIEF.md`, `docs/21_ONE_PAGER_ASESOR.md` |
| 1 | Infraestructura y configuración | `pyproject.toml`, `src/db.py`, `config.py`, `plot_style.py` |
| 2 | Carga de datos (Excel → PostgreSQL) | `docs/README.md`, `docs/07_DATA_CONTRACT.md` |
| 3 | Exploración (EDA) | `src/eda/run_eda.py`, `notebooks/eda.ipynb`, `docs/02_EDA_EXPLICACION.md` |
| 4 | Transformaciones de datos | `transformaciones_criticas/altas/medias.py`, `docs/03-05` |
| 5 | Tests unitarios | `src/tests/test_{criticas,altas,medias}.py` |
| 6 | Verificación ad-hoc y QC | `src/adhoc/*.py`, `sql/00_schema_discovery.sql` |
| 7 | Diseño econométrico | `docs/09_MODELADO_PROPUESTA.md`, `docs/13_MODELADO_ECONOMETRICO.md` |
| 8 | Dataset analítico | `src/data/01_extract_panel.py`, `02_build_features.py` |
| 9 | Estimación: Descriptivos y TWFE | `models/table1_descriptives.py`, `twfe.py`, `event_study.py` |
| 10 | Robustez y heterogeneidad | `robustness.py`, `heterogeneity.py`, `mdes_power.py`, … |
| 11 | Extensión futura: DiD moderno | `docs/17_RESULTADOS_EMPIRICOS.md` §4.6, `docs/10_EXPLICACION_MODELADO.md` §11 |
| 12 | Resultados y discusión | `docs/17_RESULTADOS_EMPIRICOS.md`, `outputs/paper/*` |
| 13 | Preparación para defensa | `docs/16-20`, `run_all.py` |
| A | Mapa de outputs | Tabla completa de archivos generados |
| E | Archivos legacy | `src/models/`, `src/data/` vs. `tesis_alcaldesas/` |
| F | Inventario completo | Verificación de 107 archivos |

---

## Capítulo 0 — Visión general del proyecto

### ¿Qué investiga esta tesis?

**Pregunta de investigación**: ¿Tener una alcaldesa (vs. alcalde) causa cambios en los
indicadores de inclusión financiera a nivel municipal en México?

**Estrategia empírica**: Diferencias-en-Diferencias (DiD) con entrada escalonada
(*staggered treatment*), donde el "tratamiento" es la fecha en que un municipio tiene
por primera vez una alcaldesa.

### Archivos para leer primero

| Orden | Archivo | Qué encontrarás |
|-------|---------|-----------------|
| 1 | `docs/21_ONE_PAGER_ASESOR.md` | Resumen ejecutivo de una página |
| 2 | `docs/01_BRIEF.md` (197 líneas) | Pregunta de investigación, auditoría estructural, discrepancias del diccionario |
| 3 | `src/tesis_alcaldesas/run_all.py` (103 líneas) | Pipeline completo de 11 pasos — te da el *big picture* de qué se ejecuta |

### Estructura del repositorio

```
Code/
├── README.md           ← Master README del repositorio
├── Makefile            ← Build automation (alternativa a run_all.py)
├── .env.example        ← Template de conexión PostgreSQL
├── .gitignore          ← Reglas de exclusión de git
├── docs/               ← 21 docs Markdown + 2 PDFs + 1 docx + 2 Excel
├── notebooks/          ← 2 Jupyter notebooks (EDA interactivo)
├── outputs/
│   ├── eda/            ← 17 archivos (CSVs + PNGs) + README.md
│   ├── paper/          ← 35 archivos (tablas .tex/.csv + figuras) + README_results.md
│   └── qc/             ← 3 archivos de control de calidad
├── sql/                ← 1 script SQL de descubrimiento
├── src/
│   ├── db.py, catalog.py, plot_style.py   ← utilidades base
│   ├── transformaciones_*.py              ← 3 scripts (1,079 líneas)
│   ├── eda/run_eda.py                     ← EDA automatizado (706 líneas)
│   ├── adhoc/                             ← 6 scripts de verificación
│   ├── tests/                             ← 3 suites + 1 script diagnóstico (500 líneas)
│   ├── data/                              ← Pipeline legacy (→ ver README_LEGACY.md)
│   ├── models/                            ← Modelos legacy (→ ver README_LEGACY.md)
│   ├── tesis_alcaldesas/                  ← Paquete instalable (ACTIVO)
│   │   ├── config.py                      ← Configuración central
│   │   ├── data/                          ← extract_panel + build_features
│   │   └── models/                        ← 10 scripts de estimación
└── pyproject.toml                         ← Metadatos del paquete
```

---

## Capítulo 1 — Infraestructura y configuración

### 1.1 — Entorno Python

| Archivo | Contenido |
|---------|-----------|
| `pyproject.toml` | Paquete `tesis_alcaldesas`, Python ≥ 3.12, dependencias: pandas, sqlalchemy, linearmodels, scipy, seaborn |
| `requirements.txt` | Lista de dependencias para `pip install -r` |
| `README.md` | Master README del repositorio: pregunta de investigación, estrategia empírica, árbol de directorios, instrucciones de setup y ejecución |
| `Makefile` | Alternativa a `run_all.py` con targets granulares (`make data`, `make models`, `make twfe`, `make clean`, etc.). Permite ejecutar partes individuales del pipeline sin correr todo |
| `.env.example` | Template de variables de entorno para la conexión a PostgreSQL (`PGHOST`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGPASSWORD`). Copiar a `.env` y ajustar |
| `.gitignore` | Define qué NO se versiona: `.venv/`, `__pycache__/`, `.env`, `data/processed/*.parquet`, el Excel fuente pesado, y archivos de IDE |
| `.venv/` | Entorno virtual local (no se versiona en git) |

**Cómo se instala**:
```bash
cd Code
source .venv/bin/activate
pip install -e ".[dev]"
```

**Alternativa con Make**:
```bash
# Ver todos los targets disponibles:
make -n all

# Ejecutar solo datos:
make data

# Ejecutar solo un modelo específico:
make twfe
make event_study

# Pipeline completo:
make all
```

### 1.2 — Conexión a base de datos (`src/db.py` — 44 líneas)

```python
# Funciones principales:
get_engine()       # → SQLAlchemy engine a postgresql://localhost:5432/tesis_db
load_table(name)   # → pd.DataFrame con toda la tabla
query(sql)         # → pd.DataFrame con resultado de SQL arbitrario
check_connection() # → imprime confirmación o error
```

**Estudia**: Cómo se construye el `connection_string` con variables que podrían venir
del entorno. La base se llama `tesis_db` en PostgreSQL 17 local.

### 1.3 — Catálogo de datos (`src/catalog.py` — 36 líneas)

```python
build_catalog(df)  # → DataFrame con columna, dtype, nulls, unique, ejemplo
null_summary(df)   # → DataFrame filtrado a solo columnas con nulls > 0
```

Útil para inspección rápida de cualquier tabla.

### 1.4 — Estilo visual (`src/plot_style.py` — 23 líneas)

```python
apply_style()  # → configura seaborn: whitegrid, palette Set2, figsize 10×6, DPI 150
```

Se invoca al inicio de todos los scripts de gráficas para asegurar consistencia visual.

### 1.5 — Configuración central (`src/tesis_alcaldesas/config.py` — 115 líneas)

**Este es uno de los archivos más importantes**. Define las constantes que usa todo el
pipeline de modelado:

| Constante | Valor | Uso |
|-----------|-------|-----|
| `DB_URI` | `postgresql://localhost:5432/tesis_db` | Conexión |
| `TABLE_CLEAN` | `"inclusion_financiera_clean"` | Tabla de 348 columnas |
| `DATA_DIR` | `data/processed/` | Parquets intermedios |
| `OUTPUT_DIR` | `outputs/paper/` | Resultados finales |
| `ENTITY_COL` | `"cve_mun"` | Identificador de municipio |
| `TIME_COL` | `"periodo"` | Identificador temporal (trimestre) |
| `TREAT_COL` | `"alcaldesa"` | Variable de tratamiento binaria |
| `COHORT_COL` | `"first_treat_period"` | Periodo de primer tratamiento |
| `RAW_OUTCOMES_M` | 17 variables | Outcomes sin transformar (sufijos `_m`, `_m_pc`) |
| `PRIMARY_OUTCOMES` | 5 variables | Los 5 outcomes principales del TWFE |
| `OUTCOME_LABELS` | dict | Etiquetas bonitas para tablas y figuras |
| `LEAKAGE_COLS` | list | Columnas excluidas por riesgo de leakage |
| `PERIOD_MAP` | dict | Mapeo `"YYYYQQ"` → int secuencial |

**Ejercicio clave**: Lee este archivo línea por línea. Cada modelo lo importa y usa
estas constantes. Entender `config.py` = entender la parametrización de toda la tesis.

---

## Capítulo 2 — Carga de datos (Excel → PostgreSQL)

### 2.1 — El archivo fuente

- **Archivo**: `docs/Base_de_Datos_de_Inclusion_Financiera_201812.xlsm`
- **Origen**: CNBV (Comisión Nacional Bancaria y de Valores)
- **Estructura original**: 175 columnas, ~42,000 filas (2,471 municipios × 17 trimestres)
- **Periodo**: 2018-Q3 a 2022-Q3

### 2.1b — PDFs de referencia en `docs/`

Además del Excel, la carpeta `docs/` contiene dos PDFs que sirvieron como guías
metodológicas durante el desarrollo del EDA:

| Archivo | Contenido |
|---------|----------|
| `Análisis de los outputs del EDA_ alcaldesas e inclusión financiera…pdf` | Interpretación narrativa de cada output del EDA: qué significa cada gráfico, qué patrones se observan, y qué decisiones de limpieza motiva |
| `Guía práctica y accionable de Análisis Exploratorio de Datos para una base tabular.pdf` | Marco metodológico general de EDA para datos tabulares: qué secciones incluir, qué métricas calcular, cómo priorizar hallazgos |

**Uso**: Estos PDFs no son generados por código sino documentos de referencia.
Léelos para entender *por qué* el EDA tiene la estructura que tiene.

### 2.1c — Documentos adicionales en `docs/`

Dos archivos de referencia adicionales que documentan la construcción de la variable
de tratamiento y el diccionario de calidad de la base:

| Archivo | Contenido |
|---------|----------|
| `Construcción del indicador de alcaldesa.docx` | Documento Word que explica la metodología para construir la variable binaria `alcaldesa`: fuentes de datos electorales, reglas de asignación, tratamiento de casos ambiguos (interinos, suplentes) |
| `Diccionario_y_QC_Base_CNBV_alcaldesa_v3.xlsx` | Excel con el diccionario de datos de la CNBV y controles de calidad (QC) aplicados a la base original. Versión 3, con validaciones cruzadas |

**Uso**: Estos documentos son insumos de referencia que precedieron al código.
El `.docx` explica *cómo se definió el tratamiento* y el `.xlsx` es el diccionario
formal con QC previo a las transformaciones automatizadas.

### 2.2 — Diccionario de la base (`docs/README.md` — 299 líneas)

**Lee este archivo completo**. Contiene:

1. **Inventario de las 175 columnas originales** agrupadas por categoría:
   - Identificadores geográficos (`cve_ent`, `cve_mun`, `nombre_mun`, …)
   - Indicadores de inclusión financiera (contratos, tarjetas, saldos, sucursales)
   - Sufijos `_m` (mujeres), `_h` (hombres), `_total` (totales)
   - Variable de tratamiento: `alcaldesa` (0/1)
   - Población: `pob_total`, `pob_mujeres`, `pob_hombres`
2. **Changelog completo** de todas las modificaciones hechas a la base

### 2.3 — Carga a PostgreSQL

La carga se hizo manualmente (no hay script de importación):
1. Se leyó el `.xlsm` con pandas
2. Se subió como tabla `inclusion_financiera` a `tesis_db` en PostgreSQL
3. Se verificó con `src/adhoc/schema_discovery.py`

**Tabla resultante**: `inclusion_financiera` — 175 columnas, ~42,000 filas.

### 2.4 — Contrato de datos (`docs/07_DATA_CONTRACT.md`)

Define las **348 columnas** de la tabla limpia (después de transformaciones).
Para cada columna especifica: tipo, rango válido, si puede ser NULL, y origen.

**Lee también**: `docs/08_DATASET_CONSTRUCCION.md` — explica las fórmulas exactas
con las que se construyó cada variable derivada.

---

## Capítulo 3 — Exploración de datos (EDA)

### 3.1 — EDA automatizado (`src/eda/run_eda.py` — 706 líneas)

Este es el script más largo de exploración. Ejecuta 6 secciones:

| Sección | Función | Output |
|---------|---------|--------|
| **A** — Diccionario | `seccion_a_diccionario()` | `A_diccionario_observado.csv` |
| **B** — Calidad | `seccion_b_calidad()` | `B_calidad_integridad.csv`, `B_completitud_panel.csv` |
| **C** — Univariado | `seccion_c_univariado()` | 5 PNGs: `C1` a `C5` |
| **D** — Bivariado | `seccion_d_bivariado()` | 6 PNGs: `D1` a `D6` |
| **E** — Leakage | `seccion_e_sesgo_leakage()` | `E_sesgo_leakage.csv` |
| **F** — Recomendaciones | `seccion_f_recomendaciones()` | `F_recomendaciones.csv` |

**Total**: 17 archivos en `outputs/eda/`.

#### Secciones en detalle

**Sección A** — Genera un catálogo automático de todas las columnas observadas:
dtype, n_valores únicos, % nulls, ejemplo de valor.

**Sección B** — Evalúa integridad:
- ¿Hay duplicados en `(cve_mun, periodo)`?
- ¿Cuántos municipios tienen panel balanceado (17 trimestres)?
- ¿Qué porcentaje de celdas está vacío por columna?

**Sección C** — Distribuciones univariadas:
- `C1`: Distribución del tratamiento (`alcaldesa`) por trimestre
- `C2`: Distribución de `pob_total` (log scale)
- `C3`: Boxplots de outcomes mujeres per cápita
- `C4`: Distribución de categóricas clave (`tipo_pob`, alcaldesa)
- `C5`: Cruce `tipo_pob` × `alcaldesa`

**Sección D** — Relaciones bivariadas y tendencias paralelas:
- `D1`: Outcomes promedio por grupo tratado/control a lo largo del tiempo
- `D2`: Brecha de género temporal
- `D3`: Tendencia por grupo de tratamiento (esto es clave para la hipótesis de
  tendencias paralelas)
- `D4`: Ratio M/H por grupo
- `D5`: Correlaciones de Spearman entre outcomes
- `D6`: Balance pre-tratamiento entre grupos

**Sección E** — Detección de leakage: identifica variables que podrían filtrar
información del futuro (post-tratamiento) al modelo.

**Sección F** — 12 recomendaciones priorizadas que alimentan los scripts de
transformación del Capítulo 4.

#### Cómo estudiar el EDA

1. Lee `docs/02_EDA_EXPLICACION.md` (310 líneas) — explicación narrativa completa
2. Ejecuta `python -m src.eda.run_eda` y examina cada output
3. Abre `notebooks/eda.ipynb` (1,060 líneas) — versión interactiva celda por celda
4. Cruza cada gráfico con su explicación en el doc
5. Lee `outputs/eda/README.md` — resumen de hallazgos del EDA: panel balanceado
   (2,471 × 17), distribución de tratamiento (~22% alcaldesa, 894 switchers totales / 600 efectivos),
   necesidad de normalización per cápita, flags de calidad, y variables recomendadas
   para el modelo

### 3.2 — Notebooks interactivos

| Notebook | Líneas | Contenido |
|----------|--------|-----------|
| `notebooks/tesis_analisis.ipynb` | 547 | Carga inicial, `info()`, `describe()`, `isna()`. Es el "primer vistazo" |
| `notebooks/eda.ipynb` | 1,060 | EDA completo interactivo. Replica y extiende `run_eda.py` |

**Orden recomendado**: `tesis_analisis.ipynb` → `eda.ipynb` → `run_eda.py`.

### 3.3 — Las 12 recomendaciones del EDA

El EDA produce 12 recomendaciones priorizadas que se implementan en el Capítulo 4:

| # | Prioridad | Recomendación |
|---|-----------|---------------|
| 1 | Crítica | Normalizar per cápita (÷ pob) |
| 2 | Crítica | Imputar saldoprom con docs=0 → saldo=0 |
| 3 | Crítica | Eliminar 3 columnas constantes |
| 4 | Crítica | Excluir columnas de leakage |
| 5 | Alta | Crear log(pob_total) |
| 6 | Alta | Winsorizar al percentil 1-99 |
| 7 | Alta | Crear ratios mujer/hombre |
| 8 | Alta | Crear `ever_alcaldesa` (absorbing treatment) |
| 9 | Alta | Estandarizar `cvegeo_mun` como índice |
| 10 | Media | Crear `alcaldesa_acumulado` (trimestres acumulados con alcaldesa) |
| 11 | Media | Transformar `asinh()` para variables con ceros |
| 12 | Media | Imputar `tipo_pob` faltante usando moda municipal |

---

## Capítulo 4 — Transformaciones de datos

Las 12 recomendaciones del EDA se implementan en 3 scripts que modifican la base
de datos PostgreSQL *in place*, transformando `inclusion_financiera` en
`inclusion_financiera_clean` (de 175 a 348 columnas).

### 4.1 — Transformaciones críticas (`src/transformaciones_criticas.py` — 327 líneas)

**Recomendaciones 1-4** (las que bloquean el análisis si no se hacen):

```
Rec 1: normalizar_per_capita()
  → Divide 51 indicadores entre su población correspondiente
  → Crea columnas con sufijo _pc (e.g., numtar_cred_m → numtar_cred_m_pc)
  → Usa pob_mujeres, pob_hombres o pob_total según el sufijo _m/_h/_total

Rec 2: imputar_saldoprom_null()
  → Si documentos = 0 y saldoprom es NULL → saldo = 0
  → Lógica: no hay contratos → no hay saldo

Rec 3: eliminar_constantes()
  → Identifica y elimina columnas con un solo valor único
  → Elimina 3 columnas constantes detectadas en el EDA

Rec 4: marcar_leakage()
  → Añade prefijo "LEAKAGE_" a columnas peligrosas
  → Columnas de leakage quedan en la tabla pero son fáciles de excluir
```

**Output**: Crea tabla `inclusion_financiera_clean` con ~224 columnas.

**Lee**: `docs/03_EDA_EXPLICACION_2.md` (139 líneas) — explica el razonamiento detrás
de cada decisión.

### 4.2 — Transformaciones altas (`src/transformaciones_altas.py` — 421 líneas)

**Recomendaciones 5-9**:

```
Rec 5: crear_log_pob()
  → log(pob_total + 1), log(pob_mujeres + 1), log(pob_hombres + 1)
  → El +1 evita log(0)

Rec 6: winsorizar()
  → Percentil 1-99 para todas las columnas numéricas (excepto IDs y población)
  → Crea columnas con sufijo _wins
  → Reduce impacto de outliers extremos

Rec 7: crear_ratios_mh()
  → ratio_X = X_m / X_h para cada par mujer/hombre
  → Maneja división por cero → NaN
  → Mide la brecha de género directamente

Rec 8: crear_ever_alcaldesa()
  → ever_alcaldesa = 1 si el municipio ALGUNA VEZ tuvo alcaldesa
  → Es el "treatment group" estático (absorbing)
  → first_treat_period = primer trimestre con alcaldesa=1

Rec 9: estandarizar_index()
  → Asegura que cvegeo_mun es string de 5 dígitos con pad de ceros
  → Limpia inconsistencias en el identificador municipal
```

**Output**: Actualiza `inclusion_financiera_clean` a ~296 columnas.

**Lee**: `docs/04_EDA_EXPLICACION_3.md` (246 líneas).

### 4.3 — Transformaciones medias (`src/transformaciones_medias.py` — 332 líneas)

**Recomendaciones 10-12**:

```
Rec 10: crear_alcaldesa_acumulado()
  → Suma acumulada de trimestres con alcaldesa por municipio
  → Permite medir "dosificación" del tratamiento

Rec 11: crear_asinh()
  → asinh(x) = ln(x + √(x²+1)) para 51 variables financieras
  → Similar a log pero maneja x=0 sin problemas
  → Crea columnas con sufijo _asinh

Rec 12: imputar_tipo_pob()
  → Imputa tipo_pob (rural/urbano) usando la moda del municipio
  → tipo_pob es time-invariant por municipio, pero algunos trimestres tienen NULL
```

**Output final**: `inclusion_financiera_clean` con **348 columnas**.

**Lee**: `docs/05_EDA_EXPLICACION_4.md` (265 líneas).

### 4.4 — Flujo de ejecución de transformaciones

```
inclusion_financiera (175 cols)
  │
  ▼  transformaciones_criticas.py (Recs 1-4)
  │
  inclusion_financiera_clean (224 cols)
  │
  ▼  transformaciones_altas.py (Recs 5-9)
  │
  inclusion_financiera_clean (296 cols)
  │
  ▼  transformaciones_medias.py (Recs 10-12)
  │
  inclusion_financiera_clean (348 cols)  ← tabla final
```

**Ejecución**:
```bash
python -m src.transformaciones_criticas
python -m src.transformaciones_altas
python -m src.transformaciones_medias
```

---

## Capítulo 5 — Tests unitarios

### 5.1 — Suite de tests (`src/tests/` — 500 líneas, 43 tests)

Cada script de transformación tiene su suite de tests:

| Suite | Archivo | Tests | Assertions | Qué verifica |
|-------|---------|-------|------------|-------------|
| Críticas | `test_criticas.py` (73 líneas) | 8 | 8 | Columnas `_pc` existen, NULLs imputados, constantes eliminadas, leakage marcado |
| Altas | `test_altas.py` (137 líneas) | 16 | 19 | `log_pob` > 0, winsorización dentro de p1-p99, ratios calculados, `ever_alcaldesa` consistente |
| Medias | `test_medias.py` (111 líneas) | 16 | 16+ | `alcaldesa_acumulado` monótona, `asinh` definida, `tipo_pob` sin NULLs |

**Ejecución**:
```bash
pytest src/tests/ -v
# → 43 passed ✓
```

### 5.1b — Script diagnóstico (`src/tests/context_medias.py`)

No es un test de pytest sino un script ad-hoc de diagnóstico que consulta PostgreSQL
directamente para recopilar contexto sobre las recomendaciones de prioridad media (10-12):

- Distribución de NULLs en `tipo_pob` por periodo
- Inspección de un municipio switcher ejemplo a lo largo del tiempo
- Estadísticas de asimetría (skewness) de outcomes per cápita

Se ejecutó una sola vez para informar las decisiones de `transformaciones_medias.py`.

### 5.2 — Qué estudiar de los tests

1. **Patrón**: Cada test carga la tabla `inclusion_financiera_clean` como fixture
2. **Nomenclatura**: `test_rec{N}_{descripcion}` — mapea directamente a las 12 recs
3. **Filosofía**: Los tests son *contratos* — si alguien cambia una transformación y
   rompe un test, se detecta inmediatamente
4. **Ejercicio**: Lee un test y la transformación correspondiente lado a lado

---

## Capítulo 6 — Verificación ad-hoc y QC

### 6.1 — Scripts ad-hoc (`src/adhoc/` — 412 líneas)

Son scripts pequeños para inspección manual. No son parte del pipeline principal
pero ayudan a entender y validar los datos:

| Script | Líneas | Qué hace |
|--------|--------|----------|
| `schema_discovery.py` (139) | Perfila las 348 columnas → `outputs/qc/db_profile_summary.csv` |
| `profile_report.py` (48) | Genera reporte agrupado legible del perfil |
| `validate_clean.py` (33) | Validación rápida: shape, dtypes, nulls de la tabla limpia |
| `check_balance.py` (29) | Verifica balance del panel: ¿todos los municipios tienen 17 trimestres? |
| `context_modelado.py` (68) | Consultas de contexto para modelado: leads/lags, timing de tratamiento, número de switchers |
| `_inspect_parquet.py` (42) | Inspecciona los archivos parquet generados por el pipeline |

### 6.2 — QC vía SQL (`sql/00_schema_discovery.sql` — 139 líneas)

12 consultas SQL de solo lectura para auditar la base en PostgreSQL directamente:

```sql
-- Ejemplo de las consultas incluidas:
Q1: Dimensiones (filas × columnas)
Q2: Muestreo de 5 filas
Q3: Tipos de datos de todas las columnas
Q4: Estadísticas de nulls y cardinalidad
Q5: Estadísticas descriptivas de numéricas
Q6: Conteos de categóricas top-5
Q7: Rango temporal de 'periodo'
Q8: Panel balance (municipios × trimestres)
Q9: Duplicados en clave primaria
Q10: Outliers con z-score > 3
Q11: Correlación simple entre outcomes
Q12: Resumen del campo 'alcaldesa'
```

### 6.3 — Outputs QC (`outputs/qc/`)

| Archivo | Contenido |
|---------|-----------|
| `db_profile_summary.csv` | Perfil de 348 columnas (dtype, nulls, min, max, unique) |
| `cohort_summary.csv` | Resumen de cohortes de tratamiento |
| `panel_checks.txt` | Resultados de verificación de panel balanceado |

---

## Capítulo 7 — Diseño econométrico

### 7.1 — Propuesta de modelado (`docs/09_MODELADO_PROPUESTA.md` — 549 líneas)

**Este es el documento de diseño más importante de la tesis.** Lee todo completo.

Contiene:
1. **Modelo base TWFE**: especificación formal de la ecuación
2. **5 outcomes principales**: `numtar_deb_m`, `numtar_cred_m`, `ncont_total_m`, `numcontcred_hip_m`, `saldocont_total_m`
3. **Controles**: `log_pob_total`, `tipo_pob` (rural/urbano)
4. **Efectos fijos**: municipio (`cve_mun`) + tiempo (`periodo`)
5. **Clustering**: errores estándar clustered a nivel de `cve_mun`
6. **Event study**: dinámica pre/post con K=4 leads y L=8 lags
7. **11 robustez planificadas**: log1p, winsorización, exclusión transición, placebo temporal, placebo género, heterogeneidad por tipo_pob, por tamaño, per cápita, sample splits, MDES
8. **Pipeline de 13 pasos**: el blueprint para `run_all.py`
9. **Criterios de aceptación**: pretrends tests p > 0.05, FDR-corrected significance

### 7.2 — Especificación formal (`docs/13_MODELADO_ECONOMETRICO.md`)

Formalización matemática:

$$Y_{it} = \alpha_i + \gamma_t + \beta \cdot D_{it} + X_{it}'\delta + \varepsilon_{it}$$

Donde:
- $Y_{it}$: outcome de inclusión financiera del municipio $i$ en trimestre $t$
- $\alpha_i$: efecto fijo de municipio
- $\gamma_t$: efecto fijo temporal
- $D_{it}$: indicador de tratamiento (alcaldesa = 1)
- $X_{it}$: controles (log población, tipo de población)
- $\varepsilon_{it}$: error, clustered por $i$

**Event study**:

$$Y_{it} = \alpha_i + \gamma_t + \sum_{k=-K}^{L} \beta_k \cdot \mathbb{1}[t - g_i = k] + X_{it}'\delta + \varepsilon_{it}$$

Con $k = -1$ como periodo de referencia (normalizado a 0).

### 7.3 — Extensiones documentadas

| Doc | Extensión |
|-----|-----------|
| `docs/10_EXPLICACION_MODELADO.md` §11 | Stacked DiD de Cengiz et al. — recomendado como extensión futura (ver también Doc 17 §4.6) |
| `docs/16_MDES_PODER.md` (62 líneas) | Mínimo efecto detectable — cuánto poder tiene nuestro diseño |
| `docs/15_EVENT_STUDY_SENSIBILIDAD.md` (72 líneas) | Análisis de sensibilidad para `numtar_cred_m` con p=0.083 |
| `docs/18_EXTENSION_OUTCOMES.md` (60 líneas) | Margen extensivo + composición de género |

> **Nota:** El contenido de `14_SAMPLE_POLICY.md` fue integrado en `08_DATASET_CONSTRUCCION.md` §1.3.

---

## Capítulo 8 — Construcción del dataset analítico

### 8.1 — Extracción del panel (`src/data/01_extract_panel.py` — 165 líneas)

**Función**: Extrae 61 de las 348 columnas de `inclusion_financiera_clean` y las
guarda como `data/processed/analytical_panel.parquet`.

```
Columnas extraídas:
- IDs: cve_mun, periodo
- Tratamiento: alcaldesa, ever_alcaldesa, first_treat_period
- 5 outcomes principales (_m_pc): tarjetas débito/crédito, contratos, hipotecarios, saldos
- Controles: log_pob_total, tipo_pob
- Variables de robustez: versiones _wins, _asinh, _log1p de los outcomes
- Variables de heterogeneidad: pob_total, tipo_pob
```

**Aliased en**: `src/tesis_alcaldesas/data/extract_panel.py` (188 líneas).

### 8.2 — Feature engineering (`src/data/02_build_features.py` — 400 líneas)

**6 etapas de transformación**:

```
Etapa 1: Cálculos per cápita
  → Recalcula _pc dividiendo entre población

Etapa 2: Transformaciones asinh
  → asinh() para variables con distribución sesgada

Etapa 3: Winsorización
  → Clip a percentiles 1-99

Etapa 4: Log transformaciones
  → log1p() para robustez

Etapa 5: Ratios y flags
  → Ratios mujer/hombre, flag de panel completo

Etapa 6: Cohort y event_time
  → cohort = first_treat_period (si ever_alcaldesa)
  → event_time = periodo - cohort
  → Necesarios para el event study
```

**Output**: `data/processed/analytical_panel_features.parquet` (~200+ columnas).

**Aliased en**: `src/tesis_alcaldesas/data/build_features.py` (402 líneas).

### 8.3 — Flujo de datos completo

```
PostgreSQL: inclusion_financiera_clean (348 cols, ~42k filas)
  │
  ▼  01_extract_panel.py
  │
  analytical_panel.parquet (61 cols, ~42k filas)
  │
  ▼  02_build_features.py
  │
  analytical_panel_features.parquet (~200+ cols, ~42k filas) ← input para modelos
```

---

## Capítulo 9 — Estimación: Descriptivos, TWFE y Event Study

### 9.0 — Utilidades compartidas (`models/utils.py` — 185 líneas)

Todas las estimaciones usan funciones de este módulo:

```python
load_panel()         # → Carga analytical_panel_features.parquet con MultiIndex (cve_mun, periodo)
run_panel_ols(y, X)  # → Ejecuta PanelOLS con EntityEffects + TimeEffects, clustering por ENTITY_COL
stars(p)             # → Convierte p-value en estrellas: *** (0.01), ** (0.05), * (0.10)
export_table_tex()   # → Guarda DataFrame como .tex con booktabs
plot_save(fig, name) # → Guarda figura como .pdf y .png
```

**Clave**: `run_panel_ols()` es la función central. Internamente:
1. Crea `PanelOLS(y, X, entity_effects=True, time_effects=True)`
2. Llama `.fit(cov_type='clustered', cluster_entity=True)`
3. Retorna objeto de resultados con coeficientes, std errors, p-values

### 9.1 — Tabla 1: Descriptivos (`models/table1_descriptives.py` — 146 líneas)

**Qué hace**: Genera estadísticas descriptivas **pre-tratamiento** comparando
municipios que tendrán alcaldesa vs. los que no.

```
Para cada outcome:
  - Media y desv. estándar del grupo control
  - Media y desv. estándar del grupo tratado
  - Diferencia de medias
  - t-test de diferencia con p-value
```

**Output**: `tabla_1_descriptiva.csv` + `tabla_1_descriptiva.tex`

**Estudia**: Cómo se filtra solo datos pre-tratamiento (`event_time < 0`), la
comparación `groupby(ever_alcaldesa)`, y el formato LaTeX.

### 9.2 — Tabla 2: TWFE base (`models/twfe.py` — 126 líneas)

**El modelo core de la tesis**. Para cada uno de los 5 outcomes:

$$Y_{it} = \alpha_i + \gamma_t + \beta \cdot alcaldesa_{it} + \delta_1 \cdot log\_pob_{it} + \delta_2 \cdot tipo\_pob_i + \varepsilon_{it}$$

```python
# Pseudocódigo simplificado:
for outcome in PRIMARY_OUTCOMES:
    y = panel[outcome]
    X = panel[['alcaldesa', 'log_pob_total', 'tipo_pob_numeric']]
    result = run_panel_ols(y, X)  # → entity + time FE, clustered SE
    # Guarda: β, SE, p-value, N, R², municipios, periodos
```

**Outputs**:
- `tabla_2_twfe.csv` / `.tex` — Muestra principal (sin always-treated)
- `tabla_2_twfe_raw.csv` — Coeficientes sin formatear
- `tabla_2_twfe_full.csv` / `.tex` — Muestra completa
- `tabla_2_twfe_main.csv` / `.tex` — Muestra principal (copia)

**Interpretación**: El coeficiente $\beta$ es el efecto promedio de tener alcaldesa sobre
el indicador financiero, controlando por tamaño municipal y características fijas.

### 9.3 — Figura 1: Event Study (`models/event_study.py` — 280 líneas)

Estima la dinámica temporal del efecto:

```
Configuración:
  K = 4 leads (periodos pre-tratamiento)
  L = 8 lags (periodos post-tratamiento)
  Referencia: k = -1 (normalizado a 0)

Para cada outcome:
  1. Crea dummies: event_time_-4, ..., event_time_-2, event_time_0, ..., event_time_8
  2. Regresión PanelOLS con todas las dummies + controles + FE
  3. Extrae coeficientes β_k con IC al 95%
  4. Test de pre-trends: H₀: β₋₄ = β₋₃ = β₋₂ = 0 (Wald/χ²)
```

**Outputs**:
- `figura_1_event_study.pdf` / `.png` — Gráfica con 5 paneles (uno por outcome)
- `event_study_coefs_{outcome}.csv` — Coeficientes para reproducibilidad
- `pretrends_tests.csv` — p-values del test de tendencias paralelas

**Estudia con especial cuidado**:
- La construcción de dummies de event_time
- El test de pre-trends (es la **identificación** de la estrategia DiD)
- Cómo se maneja el periodo de referencia (k = -1 omitido)

---

## Capítulo 10 — Robustez, heterogeneidad y extensiones

### 10.1 — Robustez (`models/robustness.py` — 239 líneas)

5 variantes de especificación para validar que los resultados no dependen de decisiones arbitrarias:

| # | Variante | Qué cambia |
|---|----------|-----------|
| 1 | Log(1+y) | Outcome en log1p en vez de nivel |
| 2 | Winsorizado | Outcome winsorizado al p1-p99 |
| 3 | Excluir transición | Quita municipios que cambian de alcaldesa a alcalde |
| 4 | Placebo temporal | Mueve el tratamiento 4 trimestres hacia atrás — debería dar β ≈ 0 |
| 5 | Placebo género | Reemplaza alcaldesa con variable aleatoria — debería dar β ≈ 0 |

**Output**: `tabla_3_robustez.csv` / `.tex`

**Estudia**: El diseño de cada placebo (temporal: ¿por qué 4 trimestres? género: ¿por qué
permutación?) y cómo se interpretan los no-resultados como evidencia positiva.

### 10.2 — Heterogeneidad (`models/heterogeneity.py` — 262 líneas)

¿El efecto varía según características del municipio?

```
Dimensión 1: tipo_pob (urbano vs. rural)
  → Interacción: alcaldesa × urbano, alcaldesa × rural

Dimensión 2: Terciles de población
  → Interacción: alcaldesa × {pequeño, mediano, grande}

Corrección: Benjamini-Hochberg FDR
  → Ajusta p-values por múltiples comparaciones
```

**Output**: `tabla_4_heterogeneidad.csv` / `.tex`

### 10.3 — MDES: Poder estadístico (`models/mdes_power.py` — 216 líneas)

*Minimum Detectable Effect Size*: ¿Cuál es el efecto más pequeño que nuestro
diseño puede detectar?

```
Parámetros:
  α = {0.05, 0.10}     (nivel de significancia)
  power = {0.80, 0.90}  (poder estadístico)

Fórmula:
  MDES = (z_α/2 + z_β) × SE(β̂) / SD(Y)

Resultado → % de desviación estándar del outcome
```

**Outputs**:
- `tabla_6_mdes.csv` / `.tex`
- `mdes_summary.txt` — Resumen legible

**Estudia**: La relación entre tamaño de muestra, poder y MDES. Si MDES > efecto
encontrado → el diseño no tiene suficiente poder para detectarlo.

### 10.4 — Sensibilidad del Event Study (`models/event_study_sensitivity.py` — 279 líneas)

3 variantes para `numtar_cred_m` (que mostró pre-trend borderline p=0.083):

| Variante | Cambio | Propósito |
|----------|--------|-----------|
| K=3 (en vez de K=4) | Menos leads | ¿El p=0.083 desaparece con ventana más corta? |
| K=6 | Más leads | ¿Es robusta con más historia? |
| Excluir g=0 | Quitar cohorte inmediata | ¿Es esa cohorte la que causa el borderline? |

**Outputs**:
- `figura_2_event_study_sens.pdf` / `.png`
- `pretrends_tests_sens.csv`

### 10.5 — Política de muestra (`models/sample_policy.py` — 188 líneas)

Compara resultados entre dos muestras:
- **Main sample**: Excluye always-treated y always-control atípicos
- **Full sample**: Todos los municipios

**Output**: `sample_sensitivity.txt`

### 10.6 — Margen extensivo (`models/extensive_margin.py` — 182 líneas)

Extiende el análisis a outcomes binarios y composición:

```
LPM (Linear Probability Model):
  Y = 1 si municipio tiene algún contrato/tarjeta de mujeres
  → ¿Alcaldesa aumenta la probabilidad de tener al menos un producto?

Gender share:
  Y = fracción de productos de mujeres / total
  → ¿Alcaldesa cambia la composición de género?
```

**Output**: `tabla_7_extensive.csv` / `.tex`

---

## Capítulo 11 — Extensión futura: DiD moderno (Stacked)

### 11.1 — El problema del TWFE con tratamiento escalonado

El estimador TWFE clásico puede estar sesgado cuando el tratamiento es escalonado
(*staggered*) porque usa already-treated como controles. La literatura DiD moderna
(Cengiz et al., Callaway & Sant'Anna, Sun & Abraham) propone alternativas.

### 11.2 — Recomendación: implementar Stacked DiD

Se recomienda como extensión futura implementar un estimador Stacked DiD
(Cengiz, Dube, Lindner & Zipperer 2019) que resolvería los potenciales sesgos
del TWFE con tratamiento escalonado. El algoritmo consiste en:

1. Construir sub-muestras limpias por cohorte de tratamiento (cada cohorte vs. never-treated)
2. Estimar TWFE dentro de cada sub-muestra
3. Agregar los efectos con un promedio ponderado

Ver la documentación detallada de esta recomendación en:
- `docs/17_RESULTADOS_EMPIRICOS.md` §4.6 — justificación y pasos de implementación
- `docs/10_EXPLICACION_MODELADO.md` §11 — contexto metodológico

> **Nota:** El repositorio `Code/` (versión completa) contiene una implementación
> funcional del Stacked DiD en `src/did_moderno/`. Esta versión (`Code_V2/`) se
> limita al análisis TWFE.

---

## Capítulo 12 — Resultados y discusión

### 12.1 — Narrativa de resultados (`docs/17_RESULTADOS_EMPIRICOS.md`)

**Lee también**: `outputs/paper/README_results.md` — resumen ejecutivo de los
resultados empíricos. Reporta el **hallazgo nulo principal** (ningún efecto
significativo de `alcaldesa` en los 5 outcomes), pre-trends pasando en 4/5,
consistencia de robustez, y el resultado nominalmente significativo en Metrópoli
que no sobrevive corrección BH. Incluye referencias a todas las tablas/figuras
y comandos de reproducción.

**Lee este documento como si fuera la sección de resultados de la tesis.** Contiene:

- §4.1: Estadísticas descriptivas (Tabla 1)
- §4.2: TWFE base (Tabla 2) — qué outcomes son significativos
- §4.3: Event study (Figura 1) — dinámica temporal, pre-trends
- §4.4: Robustez (Tabla 3) — todos los checks pasan
- §4.5: Discusión y conclusiones del análisis TWFE
- §4.6: Extensión recomendada: Stacked DiD

### 12.2 — Inventario completo de outputs

Archivos en `outputs/paper/`:

| Output | Formato | Generado por |
|--------|---------|-------------|
| `tabla_1_descriptiva` | .csv, .tex | `table1_descriptives.py` |
| `tabla_2_twfe` | .csv, .tex, _raw.csv, _main, _full | `twfe.py` |
| `tabla_3_robustez` | .csv, .tex | `robustness.py` |
| `tabla_4_heterogeneidad` | .csv, .tex | `heterogeneity.py` |
| `tabla_5_mdes` | .csv, .tex | `mdes_power.py` |
| `tabla_6_extensive` | .csv, .tex | `extensive_margin.py` |
| `figura_1_event_study` | .pdf, .png | `event_study.py` |
| `figura_2_event_study_sens` | .pdf, .png | `event_study_sensitivity.py` |
| `pretrends_tests` | .csv | `event_study.py` |
| `pretrends_tests_sens` | .csv | `event_study_sensitivity.py` |
| `event_study_coefs_*` | .csv (×5) | `event_study.py` |
| `mdes_summary` | .txt | `mdes_power.py` |
| `sample_sensitivity` | .txt | `sample_policy.py` |

### 12.3 — Cómo leer e interpretar cada tabla

**Tabla 1** (Descriptivos): Verifica que los grupos son comparables pre-tratamiento.
Si hay diferencias grandes, la estrategia DiD tiene problemas de selección.

**Tabla 2** (TWFE): El coeficiente de `alcaldesa` es el ATT. Si es positivo y
significativo (estrellas), las alcaldesas están asociadas con más inclusión financiera.

**Tabla 3** (Robustez): Todos los checks deben dar resultados cualitativamente
similares a la Tabla 2. Los placebos deben dar β ≈ 0 y no significativos.

**Tabla 4** (Heterogeneidad): ¿El efecto varía por tipo de municipio? P-values
corregidos por BH-FDR.

**Tabla 5** (MDES): Si el MDES es mayor que el efecto encontrado, necesitamos más
datos o el efecto es genuinamente pequeño.

**Tabla 6** (Extensivo): ¿El efecto es en el margen extensivo (más municipios con
productos) o intensivo (más productos donde ya hay)?

---

## Capítulo 13 — Preparación para defensa

### 13.1 — Pipeline completo (`run_all.py` — 103 líneas)

10 pasos secuenciales que reproducen todo:

```
Paso  1: 01_extract_panel.py        → analytical_panel.parquet
Paso  2: 02_build_features.py       → analytical_panel_features.parquet
Paso  3: table1_descriptives.py     → tabla_1_descriptiva
Paso  4: twfe.py                    → tabla_2_twfe
Paso  5: event_study.py             → figura_1, pretrends_tests
Paso  6: robustness.py              → tabla_3_robustez
Paso  7: heterogeneity.py           → tabla_4_heterogeneidad
Paso  8: mdes_power.py              → tabla_5_mdes
Paso  9: event_study_sensitivity.py → figura_2, pretrends_tests_sens
Paso 10: extensive_margin.py        → tabla_6_extensive
```

**Ejecución completa**:
```bash
cd Code
source .venv/bin/activate
python -m tesis_alcaldesas.run_all
# Tiempo estimado: ~5-10 minutos
```

### 13.2 — Documentos de defensa

| Doc | Contenido |
|-----|-----------|
| `docs/22_CHECKLIST_DEFENSA.md` | Checklist original de preparación |
| `docs/20_BIBLIOGRAFIA.md` (110 líneas) | Bibliografía DiD / econometría aplicada con BibTeX |
| `docs/19_APENDICE.md` | Índice del apéndice técnico |
| `docs/23_FREEZE_RELEASE.md` | Instrucciones para congelar resultados y reproducir |
| `docs/21_ONE_PAGER_ASESOR.md` | Resumen ejecutivo para el asesor |
| `docs/22_CHECKLIST_DEFENSA.md` | Checklist final actualizado |

### 13.3 — Freeze y reproducibilidad

```bash
# Verificar tag de congelamiento:
git tag -l "v1.0*"
# → v1.0-thesis-results

# Reproducir desde cero:
git checkout v1.0-thesis-results
pip install -e ".[dev]"
python -m src.tesis_alcaldesas.run_all
# Comparar outputs con los versionados
```

---

## Apéndice E — Archivos legacy y su relación con el paquete activo

El repositorio tiene dos ubicaciones para scripts de datos y modelos.
Solo una es la activa:

| Directorio legacy | Directorio activo | Relación |
|---|---|---|
| `src/data/` | `src/tesis_alcaldesas/data/` | Misma lógica, imports distintos |
| `src/models/` | `src/tesis_alcaldesas/models/` | Misma lógica para 01-05; activo tiene 4 scripts adicionales |

### ¿Por qué existen dos versiones?

Originalmente los scripts vivían en `src/data/` y `src/models/` con imports
mediante `sys.path.insert(0, ...)`. Cuando se reestructuró el proyecto como
paquete instalable (`tesis_alcaldesas`), se copiaron a `src/tesis_alcaldesas/`
con imports limpios (`from tesis_alcaldesas.models.utils import ...`).

Los archivos legacy se mantuvieron como referencia con un `README_LEGACY.md`
en cada directorio que dice:

> *"Los scripts activos viven en `src/tesis_alcaldesas/`. Usa `python -m
> tesis_alcaldesas.models.twfe` (etc.)"*

### Scripts legacy en `src/models/` (solo lectura)

| Legacy | Activo equivalente | Líneas |
|--------|-------------------|--------|
| `01_table1_descriptives.py` | `table1_descriptives.py` | ~150 |
| `02_twfe.py` | `twfe.py` | ~129 |
| `03_event_study.py` | `event_study.py` | ~283 |
| `04_robustness.py` | `robustness.py` | ~242 |
| `05_heterogeneity.py` | `heterogeneity.py` | ~265 |
| `utils.py` (207 lín.) | `utils.py` (185 lín.) | Activo es más limpio |
| — | `mdes_power.py` | Solo en activo |
| — | `event_study_sensitivity.py` | Solo en activo |
| — | `sample_policy.py` | Solo en activo |
| — | `extensive_margin.py` | Solo en activo |

**Regla**: Nunca ejecutes los scripts de `src/models/`. Usa siempre
`python -m tesis_alcaldesas.models.<script>`.

---

## Apéndice A — Mapa de dependencias

### A.1 — Flujo de datos completo

```
Excel (.xlsm)
  │
  ▼  [carga manual a PostgreSQL]
  │
inclusion_financiera (175 cols)
  │
  ├─▶ src/eda/run_eda.py ──▶ outputs/eda/ (17 archivos)
  │
  ▼  transformaciones_criticas.py
  ▼  transformaciones_altas.py
  ▼  transformaciones_medias.py
  │
inclusion_financiera_clean (348 cols)
  │
  ├─▶ src/adhoc/*.py ──▶ outputs/qc/ (3 archivos)
  │
  ▼  01_extract_panel.py
  │
analytical_panel.parquet (61 cols)
  │
  ▼  02_build_features.py
  │
analytical_panel_features.parquet (~200+ cols)
  │
  ├─▶ table1_descriptives.py ──▶ tabla_1
  ├─▶ twfe.py ──────────────────▶ tabla_2
  ├─▶ event_study.py ──────────▶ figura_1, pretrends
  ├─▶ robustness.py ────────────▶ tabla_3
  ├─▶ heterogeneity.py ────────▶ tabla_4
  ├─▶ mdes_power.py ───────────▶ tabla_5
  ├─▶ event_study_sensitivity.py▶ figura_2
  ├─▶ sample_policy.py ────────▶ sample_sensitivity
  └─▶ extensive_margin.py ─────▶ tabla_6
```

### A.2 — Dependencias entre módulos

```
config.py ←── TODOS los scripts de models/
    │
    ├── DB_URI, TABLE_CLEAN
    ├── PRIMARY_OUTCOMES, RAW_OUTCOMES_M
    ├── ENTITY_COL, TIME_COL, TREAT_COL, COHORT_COL
    ├── OUTCOME_LABELS
    └── OUTPUT_DIR, DATA_DIR

models/utils.py ←── TODOS los scripts de models/
    │
    ├── load_panel()     ← lee parquet
    ├── run_panel_ols()  ← PanelOLS + clustering
    ├── export_table_tex()
    └── plot_save()

db.py ←── transformaciones_*.py, eda/run_eda.py, adhoc/*.py
    │
    └── get_engine(), load_table(), query()
```

### A.3 — Imports clave por archivo

| Archivo | Imports internos |
|---------|-----------------|
| `transformaciones_criticas.py` | `db.get_engine` |
| `transformaciones_altas.py` | `db.get_engine` |
| `transformaciones_medias.py` | `db.get_engine` |
| `run_eda.py` | `db.load_table`, `catalog.build_catalog`, `plot_style.apply_style` |
| `01_extract_panel.py` | `config.DB_URI`, `config.TABLE_CLEAN` |
| `02_build_features.py` | `config.*` (casi todo) |
| `twfe.py` | `config.*`, `models/utils.*` |
| `event_study.py` | `config.*`, `models/utils.*` |
| Todos los `models/*.py` | `config.*`, `models/utils.*` |

---

## Apéndice B — Orden de lectura recomendado

### Para entender la tesis (orden conceptual)

```
1. docs/21_ONE_PAGER_ASESOR.md          ← resumen de 1 página
2. docs/01_BRIEF.md                      ← pregunta y estructura
3. docs/09_MODELADO_PROPUESTA.md         ← diseño econométrico
4. docs/13_MODELADO_ECONOMETRICO.md      ← especificación formal
5. docs/17_RESULTADOS_EMPIRICOS.md       ← resultados
6. docs/10_EXPLICACION_MODELADO.md §11   ← extensión futura recomendada
```

### Para entender el código (orden de ejecución)

```
 1. src/tesis_alcaldesas/config.py       ← configuración central
 2. src/db.py                            ← conexión a BD
 3. docs/README.md                    ← diccionario de datos
 4. src/eda/run_eda.py                   ← EDA (leer con docs/02)
 5. src/transformaciones_criticas.py     ← recs 1-4 (leer con docs/03)
 6. src/transformaciones_altas.py        ← recs 5-9 (leer con docs/04)
 7. src/transformaciones_medias.py       ← recs 10-12 (leer con docs/05)
 8. src/tests/test_*.py                  ← verificación
 9. src/data/01_extract_panel.py         ← extracción panel
10. src/data/02_build_features.py        ← feature engineering
11. src/tesis_alcaldesas/models/utils.py ← utilidades de estimación
12. src/tesis_alcaldesas/models/table1_descriptives.py
13. src/tesis_alcaldesas/models/twfe.py
14. src/tesis_alcaldesas/models/event_study.py
15. src/tesis_alcaldesas/models/robustness.py
16. src/tesis_alcaldesas/models/heterogeneity.py
18. src/tesis_alcaldesas/models/mdes_power.py
19. src/tesis_alcaldesas/models/event_study_sensitivity.py
20. src/tesis_alcaldesas/models/extensive_margin.py
22. src/tesis_alcaldesas/run_all.py      ← pipeline completo
```

### Para leer toda la documentación

```
docs/README.md → 01 → 02 → 03 → 04 → 05 → 06 → 07 → 08 → 09 → 10
  → 11 → 12 → 13 → 15 → 16 → 17 → 17b → 18 → 19 → 20
```

---

## Apéndice C — Glosario de variables clave

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `cve_mun` | str (5 dígitos) | Clave del municipio (INEGI) |
| `periodo` | str (YYYYQQ) | Trimestre: 201803, 201901, ..., 202203 |
| `alcaldesa` | int (0/1) | 1 si alcaldesa actual es mujer |
| `ever_alcaldesa` | int (0/1) | 1 si municipio alguna vez tuvo alcaldesa |
| `first_treat_period` | str/NaN | Primer periodo con alcaldesa (NaN si nunca) |
| `event_time` | int | Trimestres desde primer tratamiento |
| `cohort` | str | = `first_treat_period` para matching |
| `numtar_deb_m` | float | Tarjetas de débito, mujeres |
| `numtar_cred_m` | float | Tarjetas de crédito, mujeres |
| `ncont_total_m` | float | Número total de contratos, mujeres |
| `numcontcred_hip_m` | float | Contratos de crédito hipotecario, mujeres |
| `saldocont_total_m` | float | Saldo total de contratos, mujeres |
| `*_pc` | float | Per cápita (÷ pob_mujeres) |
| `*_asinh` | float | Transformada asinh |
| `*_wins` | float | Winsorizada p1-p99 |
| `*_log1p` | float | log(1 + x) |
| `ratio_*_mh` | float | Ratio mujer/hombre |
| `log_pob_total` | float | log(pob_total + 1) |
| `tipo_pob` | str | "urbano" / "rural" |
| `pob_total` | int | Población total del municipio |

---

## Apéndice D — Preguntas de estudio por capítulo

### Capítulo 2 (Datos)
- ¿Cuántas columnas tiene la tabla original vs. la limpia?
- ¿Por qué se normalizan las variables por población?

### Capítulo 3 (EDA)
- ¿Qué evidencia hay de tendencias paralelas en el gráfico D3?
- ¿Qué columnas se marcaron como leakage y por qué?

### Capítulo 4 (Transformaciones)
- ¿Por qué se usa `asinh()` en vez de `log()`?
- ¿Qué pasa si no se winsoriza?

### Capítulo 7 (Diseño)
- ¿Por qué se clusterea a nivel municipio y no entidad?
- ¿Cuál es la diferencia entre efectos fijos de entidad y de tiempo?

### Capítulo 9 (TWFE)
- ¿Cómo se interpreta β = 0.05 en `numtar_deb_m_pc`?
- ¿Qué significan los pre-trends en el event study?

### Capítulo 10 (Robustez)
- ¿Por qué el placebo temporal debería dar β ≈ 0?
- ¿Qué implica que el MDES sea mayor que el efecto estimado?

### Capítulo 11 (Extensión futura)
- ¿Por qué el TWFE puede estar sesgado con tratamiento escalonado?
- ¿Cuál es la diferencia entre never-treated y not-yet-treated como control?
- ¿Qué ventajas tendría implementar un Stacked DiD como extensión?

---

---

## Apéndice F — Inventario completo de archivos

Verificación exhaustiva: **todos** los archivos del repositorio están cubiertos en esta guía.

| Categoría | Archivos | Cubierto en |
|-----------|----------|------------|
| Master README | `README.md` | Cap. 1.1 |
| Build tools | `Makefile`, `pyproject.toml`, `requirements.txt` | Cap. 1.1 |
| Git/env config | `.gitignore`, `.env.example` | Cap. 1.1 |
| Docs Markdown | `docs/README.md` – `docs/23_FREEZE_RELEASE.md` (23 archivos numerados + 3 guías) | Caps. 0, 2, 3, 7, 11, 12, 13 |
| Docs PDF | `docs/Análisis de los outputs del EDA…pdf`, `docs/Guía práctica…pdf` | Cap. 2.1b |
| Docs Office | `docs/Construcción del indicador de alcaldesa.docx`, `docs/Diccionario_y_QC_Base_CNBV_alcaldesa_v3.xlsx` | Cap. 2.1c |
| Excel fuente | `docs/Base_de_Datos_de_Inclusion_Financiera_201812.xlsm` | Cap. 2.1 |
| Datos procesados | `data/processed/analytical_panel.parquet`, `analytical_panel_features.parquet` | Cap. 8.3 |
| Utilidades base | `src/db.py`, `src/catalog.py`, `src/plot_style.py` | Cap. 1.2–1.4 |
| Configuración | `src/tesis_alcaldesas/config.py` | Cap. 1.5 |
| EDA script | `src/eda/run_eda.py` | Cap. 3.1 |
| EDA notebooks | `notebooks/tesis_analisis.ipynb`, `notebooks/eda.ipynb` | Cap. 3.2 |
| Transformaciones | `src/transformaciones_{criticas,altas,medias}.py` | Cap. 4.1–4.3 |
| Tests | `src/tests/test_{criticas,altas,medias}.py` | Cap. 5.1 |
| Diagnóstico | `src/tests/context_medias.py` | Cap. 5.1b |
| Ad-hoc | `src/adhoc/{schema_discovery,profile_report,validate_clean,check_balance,context_modelado,_inspect_parquet}.py` | Cap. 6.1 |
| SQL | `sql/00_schema_discovery.sql` | Cap. 6.2 |
| Data pipeline | `src/tesis_alcaldesas/data/{extract_panel,build_features}.py` | Cap. 8.1–8.2 |
| Modelos activos | `src/tesis_alcaldesas/models/{utils,table1_descriptives,twfe,event_study,robustness,heterogeneity,mdes_power,event_study_sensitivity,sample_policy,extensive_margin}.py` | Caps. 9–10 |
| Orchestrador | `src/tesis_alcaldesas/run_all.py` | Cap. 13.1 |
| Outputs EDA | `outputs/eda/` (17 archivos + README.md) | Cap. 3.1 |
| Outputs paper | `outputs/paper/` (35 archivos + README_results.md) | Cap. 12.2 |
| Outputs QC | `outputs/qc/` (3 archivos) | Cap. 6.3 |
| Legacy data | `src/data/{01_extract_panel,02_build_features}.py` + `README_LEGACY.md` | Apéndice E |
| Legacy models | `src/models/{01–05,utils}.py` + `README_LEGACY.md` | Apéndice E |
| Init files | 8 × `__init__.py` (boilerplate vacío) | N/A |

**Total**: ~140 archivos (excluyendo `.venv/`, `.git/`, `__pycache__/`, `.egg-info/`).
Todos cubiertos.

---

*Guía generada el 2 de marzo de 2026. Cubre las ~6,200 líneas de código Python,
21+2 documentos, 2 notebooks, 1 script SQL y 55+ archivos de output de la tesis.*
