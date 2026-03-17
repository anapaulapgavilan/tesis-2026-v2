# Alcaldesas e Inclusión Financiera de las Mujeres en México

**Tesis de grado** · Ana Paula Pérez Gavilán  
Repositorio de código y datos para la estimación del efecto causal de la representación política femenina municipal sobre la inclusión financiera de las mujeres en México.

---

## 1. Pregunta de investigación

> *¿Cuál es el efecto causal de tener una alcaldesa sobre la inclusión financiera de las mujeres a nivel municipal en México?*

Se emplea un diseño de **diferencias en diferencias (DiD)** con datos de panel municipio-trimestre, explotando la variación temporal en el género de la autoridad municipal. La especificación principal es un modelo **Two-Way Fixed Effects (TWFE)** con efectos fijos de municipio y de periodo, y errores estándar clusterizados a nivel municipio.

---

## 2. Datos

| Característica | Detalle |
|---|---|
| **Unidad de análisis** | Municipio-trimestre |
| **Periodo** | 2018-Q3 a 2022-Q3 (17 trimestres) |
| **Municipios** | 2,471 |
| **Observaciones** | 41,905 (panel balanceado) |
| **Fuente de inclusión financiera** | CNBV (Comisión Nacional Bancaria y de Valores) |
| **Fuente de género de autoridad** | Construcción propia a partir de registros históricos municipales |

### Variable de tratamiento

`alcaldesa_final` ∈ {0,1} — indica si el municipio *i* tiene una alcaldesa en el trimestre *t*.

| Grupo | Municipios | % |
|---|---|---|
| Never-treated (nunca alcaldesa) | 1,476 | 59.7% |
| Switchers (cambian al menos una vez) | 894 | 36.2% |
| Always-treated (alcaldesa todo el panel) | 101 | 4.1% |

De los 894 switchers, **600 tienen periodo pre-tratamiento** y son los que identifican el efecto causal en el event study.

### 5 outcomes primarios (mujeres)

Todas las variables se expresan como **per cápita × 10,000 mujeres adultas** y se transforman con **asinh** (arcoseno hiperbólico) para la estimación.

| Variable | Descripción |
|---|---|
| `ncont_total_m` | Contratos totales de captación |
| `numtar_deb_m` | Tarjetas de débito |
| `numtar_cred_m` | Tarjetas de crédito |
| `numcontcred_hip_m` | Créditos hipotecarios |
| `saldocont_total_m` | Saldo total de captación |

Adicionalmente se construyen 17 outcomes crudos para mujeres y 17 para hombres (estos últimos se usan como placebos de género).

---

## 3. Estructura del repositorio

```
├── data/                          # Datos fuente y procesados
│   ├── inclusion_financiera_clean.csv   # Panel principal exportado (348 cols)
│   ├── inclusion_financiera_v2.csv      # Versión alternativa (41 cols)
│   └── processed/                       # Parquets generados por el pipeline
│       ├── analytical_panel.parquet     # Panel extraído (paso 1)
│       └── analytical_panel_features.parquet  # Panel con features (paso 2)
│
├── src/tesis_alcaldesas/          # Paquete Python principal
│   ├── config.py                  # Configuración centralizada (rutas, constantes)
│   ├── run_all.py                 # Entrypoint: ejecuta el pipeline completo
│   ├── data/                      # Preparación de datos
│   │   ├── extract_panel.py       # Paso 1: extrae columnas del CSV → parquet
│   │   └── build_features.py      # Paso 2: per cápita, asinh, flags, cohortes
│   └── models/                    # Pipeline econométrico
│       ├── utils.py               # Funciones compartidas (PanelOLS wrapper, LaTeX)
│       ├── table1_descriptives.py # Tabla 1: estadísticas descriptivas
│       ├── twfe.py                # Tabla 2: TWFE baseline
│       ├── event_study.py         # Figura 1: event study + pre-trends
│       ├── robustness.py          # Tabla 3: pruebas de robustez
│       ├── heterogeneity.py       # Tabla 4: heterogeneidad
│       ├── mdes_power.py          # Tabla 6: MDES / poder estadístico
│       ├── event_study_sensitivity.py  # Figura 2: sensibilidad del event study
│       ├── sample_policy.py       # Sensibilidad de muestra
│       └── extensive_margin.py    # Tabla 7: margen extensivo y composición
│
├── outputs/paper/                 # Tablas (.csv, .tex) y figuras (.pdf, .png)
├── outputs/qc/                    # Archivos de control de calidad
├── docs/                          # Documentación extendida de la tesis
├── notebooks/                     # Notebooks exploratorios (EDA)
├── Makefile                       # Automatización del pipeline
├── pyproject.toml                 # Metadatos del paquete Python
└── requirements.txt               # Dependencias
```

---

## 4. Pipeline de ejecución

El pipeline tiene dos fases: **preparación de datos** y **modelado econométrico**.

### Fase 1 — Datos

```bash
make data
```

| Paso | Módulo | Descripción |
|---|---|---|
| 1 | `tesis_alcaldesas.data.extract_panel` | Lee `inclusion_financiera_clean.csv`, selecciona las columnas necesarias (IDs, tratamiento, controles, outcomes) y exporta `analytical_panel.parquet` |
| 2 | `tesis_alcaldesas.data.build_features` | Calcula outcomes per cápita (×10,000), transforma con asinh/winsor/log1p, construye ratios de brecha de género M/H, genera flags de calidad, y clasifica cohortes de tratamiento. Exporta `analytical_panel_features.parquet` |

### Fase 2 — Modelos

```bash
make models
```

| Orden | Módulo | Output | Descripción |
|---|---|---|---|
| 1 | `table1_descriptives` | Tabla 1 | Estadísticos descriptivos pre-tratamiento por grupo |
| 2 | `twfe` | Tabla 2 | **Estimación principal**: TWFE con 5 outcomes |
| 3 | `event_study` | Figura 1 | Diagnóstico de tendencias paralelas (leads/lags) |
| 4 | `robustness` | Tabla 3 | 8 pruebas de robustez |
| 5 | `heterogeneity` | Tabla 4 | Heterogeneidad por tipo de municipio y tamaño |
| 6 | `mdes_power` | Tabla 6 | Tamaño mínimo de efecto detectable (MDES) |
| 7 | `event_study_sensitivity` | Figura 2 | Sensibilidad del event study a la definición de bins |
| 8 | `sample_policy` | Comparación | Robustez: muestra completa vs. panel balanceado |
| 9 | `extensive_margin` | Tabla 7 | Margen extensivo (binario) y composición de género |

### Ejecución completa (todo en un comando)

```bash
make all               # Datos + Modelos
# O bien:
python -m tesis_alcaldesas.run_all   # Solo modelos (datos deben existir)
```

---

## 5. Estrategia econométrica

### 5.1 Especificación principal (TWFE)

$$Y_{it} = \alpha_i + \gamma_t + \beta \cdot D_{it} + \delta \cdot \ln(\text{pob}_{it}) + \varepsilon_{it}$$

donde:
- $Y_{it}$ = outcome en escala asinh(per cápita × 10,000 mujeres adultas)
- $\alpha_i$ = efecto fijo de municipio
- $\gamma_t$ = efecto fijo de periodo (trimestre)
- $D_{it}$ = `alcaldesa_final` (tratamiento)
- $\ln(\text{pob}_{it})$ = control de población (pre-determinado/lento)
- $\varepsilon_{it}$ clusterizado a nivel municipio

El coeficiente $\beta$ se interpreta como una semi-elasticidad (≈ cambio porcentual en el outcome).

### 5.2 Event study

$$Y_{it} = \alpha_i + \gamma_t + \sum_{k \neq -1} \delta_k \cdot \mathbf{1}\{\text{event\_time} = k\} + X'\beta + \varepsilon_{it}$$

- Periodo de referencia: $k = -1$ (un trimestre antes del tratamiento)
- Leads: $k = -4, -3, -2$ (con bin extremo en $k \leq -4$)
- Lags: $k = 0, 1, \ldots, 7$ (con bin extremo en $k \geq 8$)
- Test de pre-tendencias: $\chi^2$ conjunto de que todos $\delta_k = 0$ para $k < -1$

### 5.3 Pruebas de robustez (8 tests)

| ID | Descripción |
|---|---|
| R1 | Escala alternativa: log(1+y) en vez de asinh |
| R2 | Winsorización p1-p99 + asinh |
| R3 | Excluir trimestres de transición |
| R4 | Placebo temporal: tratamiento adelantado 4 trimestres (β esperado ≈ 0) |
| R5 | Placebo de género: outcomes de hombres (β esperado ≈ 0) |
| R6 | Per cápita winsorizado sin transformación funcional |
| R7 | Per cápita crudo sin transformación |
| R8 | Solo switchers absorbentes (0→1 permanente) + never-treated |

### 5.4 Heterogeneidad

TWFE por sub-muestra, con corrección de Benjamini-Hochberg (FDR) por múltiples pruebas:
- **Dimensión 1:** Por tipo de municipio (rural, semi-urbano, urbano, metrópoli, etc.)
- **Dimensión 2:** Por terciles de población

### 5.5 MDES (Minimum Detectable Effect Size)

Convierte un resultado nulo en un hallazgo informativo: calcula el efecto mínimo que el diseño podría detectar con 80% de poder estadístico.

$$\text{MDES} = (z_{\alpha/2} + z_\beta) \times SE$$

### 5.6 Extensiones (margen extensivo + composición)

- **Panel A:** Variable binaria $\mathbf{1}\{X_m > 0\}$ (modelo de probabilidad lineal)
- **Panel B:** Share femenino $\frac{y_{m}}{y_{m} + y_{h}}$ (composición de género)

---

## 6. Resultado principal

**No se detecta efecto estadísticamente significativo** de tener una alcaldesa sobre la inclusión financiera de las mujeres.

| Outcome | β | SE | p-valor | IC 95% |
|---|:---:|:---:|:---:|---|
| Contratos totales | 0.007 | 0.022 | 0.747 | [−0.035, 0.049] |
| Tarjetas débito | −0.014 | 0.021 | 0.521 | [−0.055, 0.028] |
| Tarjetas crédito | −0.002 | 0.017 | 0.919 | [−0.036, 0.032] |
| Créditos hipotecarios | 0.018 | 0.021 | 0.400 | [−0.024, 0.060] |
| Saldo total | 0.004 | 0.049 | 0.931 | [−0.092, 0.100] |

- **Pre-tendencias:** 4 de 5 outcomes pasan el test conjunto al 10%. Tarjetas de crédito es borderline (p = 0.083) por el bin extremo k ≤ −4.
- **Robustez:** El resultado nulo es estable en todas las especificaciones alternativas. Los placebos (temporal y de género) confirman ausencia de efecto espurio.
- **Heterogeneidad:** Un efecto nominalmente significativo en metrópolis (β = 0.030, p = 0.024) no sobrevive la corrección por múltiples pruebas (q-value BH = 0.215).

---

## 7. Instalación y reproducción

### Requisitos

- Python ≥ 3.10
- Dependencias: `pandas`, `numpy`, `linearmodels`, `statsmodels`, `matplotlib`, `seaborn` (ver `requirements.txt`)

### Setup

```bash
# Clonar el repositorio
git clone <url> && cd tesis-2026-v2

# Crear entorno virtual e instalar dependencias
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pip install -e .    # Instalar el paquete en modo editable

# Ejecutar pipeline completo (datos + modelos)
make all
```

Los resultados se generan en `outputs/paper/` como archivos `.csv`, `.tex`, `.pdf` y `.png`.

> **Nota:** No se requiere conexión a PostgreSQL. Todos los datos están en CSV en `data/`.

---

## 8. Outputs generados

### Tablas

| Archivo | Contenido |
|---|---|
| `tabla_1_descriptiva.csv/.tex` | Estadísticos descriptivos pre-tratamiento |
| `tabla_2_twfe.csv/.tex` | Estimación TWFE baseline (5 outcomes) |
| `tabla_3_robustez.csv/.tex` | 8 pruebas de robustez |
| `tabla_4_heterogeneidad.csv/.tex` | Heterogeneidad por tipo y tamaño de municipio |
| `tabla_6_mdes.csv/.tex` | MDES y poder estadístico |
| `tabla_7_extensive.csv/.tex` | Margen extensivo y composición de género |

### Figuras

| Archivo | Contenido |
|---|---|
| `figura_1_event_study.pdf/.png` | Event study con 5 outcomes (leads + lags, IC 95%) |
| `figura_2_event_study_sens.pdf/.png` | Sensibilidad del event study (variaciones de bins) |

### Control de calidad

| Archivo | Contenido |
|---|---|
| `outputs/qc/panel_checks.txt` | Validación de PK, balance y distribución |
| `outputs/qc/cohort_summary.csv` | Resumen de cohortes de tratamiento |
| `outputs/paper/pretrends_tests.csv` | Tests χ² de pre-tendencias |
| `outputs/paper/mdes_summary.txt` | Resumen del MDES en lenguaje natural |

---

## 9. Documentación extendida

La carpeta `docs/` contiene documentación detallada de cada etapa de la tesis:

| Documento | Contenido |
|---|---|
| `01_BRIEF.md` | Brief analítico: datos, variables, cobertura |
| `07_DATA_CONTRACT.md` | Contrato de datos y diccionario de variables |
| `09_MODELADO_PROPUESTA.md` | Propuesta completa de modelado econométrico |
| `12_EXPLICACION_EVENT_STUDY.md` | Explicación detallada del event study |
| `13_MODELADO_ECONOMETRICO.md` | Especificaciones econométricas |
| `17_RESULTADOS_EMPIRICOS.md` | Interpretación de resultados |
| `20_BIBLIOGRAFIA.md` | Referencias bibliográficas |

---

## 10. Stack tecnológico

| Componente | Herramienta |
|---|---|
| Lenguaje | Python 3.10+ |
| Econometría | `linearmodels` (PanelOLS), `statsmodels`, `scipy` |
| Datos | `pandas`, `numpy`, `pyarrow` (parquet) |
| Visualización | `matplotlib`, `seaborn` |
| Exportación a LaTeX | `Jinja2` |
| Automatización | `Makefile` |
| Base de datos (legacy) | PostgreSQL + SQLAlchemy (ya no requerida) |
