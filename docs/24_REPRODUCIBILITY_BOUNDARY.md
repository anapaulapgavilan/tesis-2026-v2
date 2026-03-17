# 24 — Reproducibility Boundary: Full Pipeline Map

> **Propósito:** Documentar —con exactitud de nombres de archivo, ubicaciones y orden
> de ejecución— cada paso del pipeline desde los datos crudos hasta las tablas y
> figuras del paper. Esto hace al proyecto defendible, replicable y auditable.

---

## 1. Problema que resuelve este documento

Los scripts de estimación causal (`Code/src/`) trabajan sobre un parquet analítico
(`analytical_panel_features.parquet`) que es el producto final de una cadena ETL
más larga. Esa cadena anterior —scraping, consolidación, gender matching, carga a
PostgreSQL— vive en un directorio hermano (`Base de Datos/`). Sin mapear
explícitamente ambos tramos, un replicador no podría reconstruir los datos desde cero,
y un lector de la tesis no sabría dónde se toman las decisiones más
consequenciales (imputación de género, armonización de IDs municipales, alineación
de ciclos electorales).

---

## 2. Diagrama del pipeline completo

```
 ┌─────────────────────────────────────────────────────────────────────┐
 │  TRAMO 1: ETL "upstream"  (Base de Datos/)                        │
 │  ─────────────────────────────────────────                         │
 │                                                                     │
 │  ① Web scraping de presidentes municipales                         │
 │     historico_municipios.py → Historico/*.txt                      │
 │                                                                     │
 │  ② Parseo + detección de género                                    │
 │     busca_genero.py → generos.csv                                  │
 │                                                                     │
 │  ③ Consolidación CNBV (base vieja + archivos nuevos)               │
 │     build_panel_v2.py                                               │
 │       ├─ Lee: Base_FINAL_FINAL.csv (17 trim, 2018Q3–2022Q3)       │
 │       ├─ Lee: CNBV_nuevos/*.xlsx  (9 trim, 2022Q4–2024Q4)         │
 │       ├─ Lee: Historico/*_filtrado.csv (matching de género)        │
 │       └─ Genera: panel_unificado_v2.csv (≈26 trimestres)          │
 │                                                                     │
 │  ④ Correcciones manuales de género (7 municipios)                  │
 │     fill_manual_gender.py → panel_unificado_v2.csv (actualizado)   │
 │                                                                     │
 │  ⑤ Carga a PostgreSQL                                              │
 │     load_panel_v2.py → tabla 'inclusion_financiera_v2'             │
 │                                                                     │
 └────────────────────────────┬────────────────────────────────────────┘
                              │
                    PostgreSQL tesis_db
                              │
 ┌────────────────────────────┴────────────────────────────────────────┐
 │  TRAMO 2: Pipeline analítico  (Code/src/)                          │
 │  ────────────────────────────────────────                           │
 │                                                                     │
 │  ⑥ Extracción + feature engineering                                │
 │     src/data/01_extract_panel_v2.py                                │
 │       └─ Genera: data/processed/analytical_panel.parquet           │
 │                                                                     │
 │  ⑦ Feature engineering adicional                                    │
 │     src/data/02_build_features.py                                  │
 │       ├─ cohort_type, event_time, first_treat_t                    │
 │       ├─ per cápita + asinh + winsorizado + log(1+y)               │
 │       └─ Genera: data/processed/analytical_panel_features.parquet  │
 │                                                                     │
 │  ⑧ Modelos y outputs                                               │
 │     src/models/01_table1_descriptives.py  → Tabla 1                │
 │     src/models/02_twfe.py                 → Tabla 2                │
 │     src/models/03_event_study.py          → Figura 1 + pre-trends  │
 │     src/models/04_robustness.py           → Tabla 3                │
 │     src/models/05_heterogeneity.py        → Tabla 4                │
 │     src/tesis_alcaldesas/models/mdes_power.py        → Tabla 5     │
 │     src/tesis_alcaldesas/models/extensive_margin.py  → Tabla 6     │
 │     src/tesis_alcaldesas/models/event_study_sensitivity.py → A2    │
 │                                                                     │
 └─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Inventario detallado — Tramo 1 (ETL upstream)

Todos los archivos listados viven en `Base de Datos/`.

### ① Web scraping: `historico_municipios.py`

| Campo | Detalle |
|---|---|
| **Qué hace** | Usa Selenium + Firefox para navegar el SNIM (snim.rami.gob.mx) y descargar la lista histórica de presidentes municipales por estado/municipio |
| **Input** | Sitio web en vivo (requiere Firefox + Geckodriver) |
| **Output** | `Historico/*.txt` — un archivo de texto por municipio con nombre, género y años de gobierno |
| **Decisiones clave** | Depende de que el sitio web siga activo; los archivos `.txt` generados son la versión congelada |
| **Riesgo de reproducibilidad** | Alto si el sitio cambia o desaparece. **Mitigación:** los archivos `.txt` están preservados en `Historico/` |

### ② Detección de género: `busca_genero.py`

| Campo | Detalle |
|---|---|
| **Qué hace** | Parsea los archivos `.txt` del scraping, extrae nombre, género (H/M) y años de gobierno usando regex |
| **Input** | `Historico/*.txt` |
| **Output** | `generos.csv` |
| **Decisiones clave** | La regex `r'((?P<nombre>.+)(?P<gen>[H|M]del?\s).*(?P<inicio>\d{4}).*(?P<fin>\d{4}))'` decide cómo extraer género; se filtran por `inicio >= 2018` |
| **Riesgo** | Medio — depende del formato de los `.txt`; si varía entre estados, puede fallar |

### ③ Consolidación de panel: `build_panel_v2.py` (631 líneas)

| Campo | Detalle |
|---|---|
| **Qué hace** | Unifica la base vieja (2018Q3–2022Q3) con los archivos nuevos de CNBV (2022Q4–2024Q4) en un panel longitudinal. Realiza matching multinivel de género (exacto → artículo → substring → temporal). Genera `alcaldesa_final`. |
| **Inputs** | `Base_FINAL_FINAL.csv` + `CNBV_nuevos/*.xlsx` + `Historico/*_filtrado.csv` |
| **Output** | `panel_unificado_v2.csv` (~26 trimestres, ~41 columnas) |
| **Decisiones clave** | (1) **Eliminación de variables:** saldocont_*, saldoprom_*, ncont_tradic_*, sufijos _pm. (2) **Generación de _t = _m + _h.** (3) **Matching de género multinivel** — esta es la decisión más consequencial del pipeline. (4) **Regla de asignación por trimestre:** cuando la transición ocurre a mitad del trimestre, se asigna según quién gobernó la MAYORÍA del trimestre. |
| **Riesgo** | Medio — el matching de género puede fallar para nombres ambiguos; el orden de fallback importa |

### ④ Correcciones manuales: `fill_manual_gender.py`

| Campo | Detalle |
|---|---|
| **Qué hace** | Corrige manualmente `alcaldesa_final` para 7 municipios donde el matching automatizado falló, usando investigación en portales oficiales (IEPC, IEEPCO, periódicos oficiales, DOF) |
| **Input** | `panel_unificado_v2.csv` |
| **Output** | `panel_unificado_v2.csv` (actualizado in-place) |
| **Municipios corregidos** | 12038 (Zihuatanejo), 20017 (La Compañía), 20566 (San Mateo Yucutindó — irrecuperable → NaN), 29004 (Atltzayanca), 29037 (Zitlaltepec), 29043 (Yauhquemehcan), 30189 (Tuxpan) |
| **Decisiones clave** | Dos municipios quedan con NaN persistentes por ser irrecuperables |

### ⑤ Carga a DB: `load_panel_v2.py`

| Campo | Detalle |
|---|---|
| **Qué hace** | Lee el CSV consolidado y lo carga a PostgreSQL como tabla `inclusion_financiera_v2` |
| **Output** | Tabla `inclusion_financiera_v2` con PK (trim, cve_mun) |
| **⚠️ Credential issue** | Hard-codea `DB_URL` con usuario local. Seguir las instrucciones de la sección 5 para corregir. |

---

## 4. Inventario detallado — Tramo 2 (Pipeline analítico)

Todos los archivos viven en `Code/src/`. La conexión a DB ahora se centraliza
a través de `tesis_alcaldesas.config.get_engine()` (lee variables PG* del entorno).

### ⑥ Extracción: `src/data/01_extract_panel_v2.py`

Lee de `inclusion_financiera_v2`, construye `periodo_trimestre`, `year`, `quarter`,
`t_index`, variables de tratamiento (leads, lags, transiciones), controles (`log_pob`),
y exporta `analytical_panel.parquet`.

### ⑦ Features: `src/data/02_build_features.py`

Agrega: `cohort_type`, `event_time`, `first_treat_t`, transformaciones
per-cápita (÷ pob_adulta × 10,000), asinh, log(1+y), winsorización. Exporta
`analytical_panel_features.parquet` — el input de toda la estimación.

### ⑧ Modelos

Ver `Makefile` y `docs/README.md` para la lista completa de scripts y su orden.

---

## 5. Configuración para replicación

### 5.1 Base de datos

```bash
# Crear la DB (una vez)
createdb tesis_db

# Variables de entorno (añadir a .zshrc o .env)
export PGHOST=localhost
export PGPORT=5432
export PGDATABASE=tesis_db
export PGUSER=$(whoami)    # ← adaptar a tu usuario local
export PGPASSWORD=""        # ← vacío si usas peer auth
```

### 5.2 Ejecución del Tramo 1

```bash
cd "Base de Datos/"

# ① y ② — Solo si necesitas re-scraping (normalmente NO)
# python historico_municipios.py
# python busca_genero.py

# ③ Consolidar panel
python build_panel_v2.py

# ④ Correcciones manuales
python fill_manual_gender.py

# ⑤ Cargar a DB
python load_panel_v2.py
```

### 5.3 Ejecución del Tramo 2

```bash
cd Code/
source .venv/bin/activate

# ⑥-⑦ Extraer y construir features
PYTHONPATH=src python src/data/01_extract_panel_v2.py
PYTHONPATH=src python src/data/02_build_features.py

# ⑧ Estimar todo
PYTHONPATH=src python -m tesis_alcaldesas.run_all

```

---

## 6. Decisiones más consequenciales (para la defensa)

Estas son las decisiones enterradas en el Tramo 1 que un sinodal podría cuestionar:

| # | Decisión | Archivo | Riesgo | Mitigación |
|---|----------|---------|--------|------------|
| 1 | **Matching de género multinivel** | `build_panel_v2.py` | Falsos positivos/negativos en asignación de género | Revisión manual (fill_manual_gender.py) + tasa de NaN reportada como 0% tras correcciones |
| 2 | **Regla de mayoría para transiciones intra-trimestre** | `build_panel_v2.py`, `fill_manual_gender.py` | Asignación discrecional cuando el cambio ocurre a mitad de trimestre | Documentado explícitamente; robustez excluye trimestres de transición (R3) |
| 3 | **Eliminación de saldocont_*, saldoprom_*** | `build_panel_v2.py` | Pierde outcomes de profundidad financiera en el panel v2 (26 trims) | Panel analítico (17 trims) los conserva; la extensión a 26 trims es exploratoria |
| 4 | **Municipios con NaN irrecuperable** | `fill_manual_gender.py` | 20566 (todos), 20017 (2020–2022) quedan without treatment | Se excluyen automáticamente; son 2 de 2,471 municipios |
| 5 | **Armonización de IDs municipales (`cve_mun`)** | `build_panel_v2.py` | Cambios de clave INEGI entre censos | Se usa cve_mun del catálogo CNBV, consistente dentro del periodo |

---

## 7. Archivos que faltan del repositorio pero existen localmente

| Archivo | Ubicación | Status |
|---------|-----------|--------|
| `Base_FINAL_FINAL.csv` | `Base de Datos/` | ✅ Presente (input crudo) |
| `CNBV_nuevos/*.xlsx` | `Base de Datos/CNBV_nuevos/` | ✅ Presente (inputs crudos) |
| `Historico/*.txt` | `Base de Datos/Historico/` | ✅ Presente (scraped) |
| `Historico/*_filtrado.csv` | `Base de Datos/Historico/` | ✅ Presente (processed) |
| `generos.csv` | `Base de Datos/` | ✅ Presente |
| `panel_unificado_v2.csv` | `Base de Datos/` | ✅ Presente |

> **Recomendación:** Estos archivos deberían estar bajo control de versiones (o al
> menos archivados en un repositorio de datos como Zenodo/Figshare con un DOI) para
> garantizar reproducibilidad completa. Si el tamaño impide commit a Git, usar
> Git LFS o un `.dvc` (Data Version Control) con un remote de almacenamiento.

---

## 8. Nota sobre el `load_panel_v2.py` en Base de Datos/

Este script aún hard-codea `DB_URL`. A diferencia de los scripts en `Code/src/` (que
ahora usan `tesis_alcaldesas.config.get_engine()`), los scripts del Tramo 1 no
tienen acceso al paquete `tesis_alcaldesas`. La mitigación recomendada es usar el
mismo patrón de variables de entorno directamente:

```python
import os
user = os.environ.get("PGUSER", os.environ.get("USER", "postgres"))
DB_URL = f"postgresql://{user}@localhost:5432/tesis_db"
```
