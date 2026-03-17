> **Archivos fuente:**
> - `src/transformaciones_criticas.py`
> - `src/transformaciones_altas.py`
> - `src/transformaciones_medias.py`
> - `src/tesis_alcaldesas/config.py`
> - `src/tesis_alcaldesas/data/extract_panel.py`
> - `src/tesis_alcaldesas/data/build_features.py`
> - `src/tesis_alcaldesas/run_all.py`

# Guía de Estudio del Código — Tesis Alcaldesas × Inclusión Financiera

> Esta guía explica, paso a paso, cómo se transformó la base de datos cruda
> hasta llegar al dataset listo para econometría. Léela de arriba a abajo.

---

## Panorama general

```
Excel (32.9 MB)
  → PostgreSQL: inclusion_financiera (175 cols)
    → transformaciones_criticas.py: per cápita, excluir constantes
      → transformaciones_altas.py: log pob, winsor, ratios, ever_alcaldesa
        → transformaciones_medias.py: acumulado, asinh, imputar tipo_pob
          → inclusion_financiera_clean (348 cols en PostgreSQL)
            → 01_extract_panel.py: selecciona 61 cols raw
              → analytical_panel.parquet
                → 02_build_features.py: recalcula todo reproduciblemente
                  → analytical_panel_features.parquet (~200+ cols)
                    → modelos (TWFE, event study, stacked DiD...)
```

---

## Fase 0 — Carga del Excel a PostgreSQL

**Documentación:** `Code/docs/README.md` (sección "Cambios realizados")

1. **Origen:** `Base_20_02_2026.xlsx` (32.9 MB) — datos CNBV × panel municipal.
2. Se cargó a PostgreSQL como tabla `inclusion_financiera` (41,905 filas × 175 cols).
3. **Tipificación:** 62 cols `double → INTEGER`, 15 `double → BIGINT`, `saldoprom_*`
   con `"-"` convertidos a `NULL`.
4. **PK** `(cve_mun, periodo_trimestre)` verificada y creada.
5. **Claves INEGI canónicas:** `cve_ent` (2 dígitos), `cve_mun3` (3 dígitos),
   `cvegeo_mun` (5 dígitos).
6. **28 flags** `flag_undef_saldoprom_*` para marcar NULLs estructurales (÷0 cuando
   no hay contratos).

**Resultado:** tabla `inclusion_financiera` con 175 columnas limpias en PostgreSQL.

### Estructura de la tabla original (175 cols)

| Bloque | Cols | Contenido |
|--------|------|-----------|
| Identificadores | 9 | `cve_mun`, `trim`, `cve_edo`, `cve_ent`, `cve_mun3`, `cvegeo_mun`, `region`, `estado`, `municipio` |
| Demográficas | 5 | `pob`, `pob_adulta`, `pob_adulta_m`, `pob_adulta_h`, `tipo_pob` |
| Inclusión financiera CNBV | 95 | `ncont_*` (28), `saldocont_*` (28), `saldoprom_*` (28), `numtar_*` (8), `numcontcred_hip_*` (3) |
| Temporales/auxiliares | 5 | `cve_mun_int`, `cve_edo_int`, `year`, `quarter`, `periodo_trimestre` |
| Indicador alcaldesa | 33 | `alcaldesa_final`, `alcaldesa`, `alcaldesa_end`, leads/lags, transiciones, days_*, flags panel |
| Flags missingness | 28 | `flag_undef_saldoprom_{producto}_{sexo}` |

---

## Fase 1 — Transformaciones Críticas (Recs 1–4)

**Script:** `Code/src/transformaciones_criticas.py` (~327 líneas)  
**Lee:** `inclusion_financiera` · **Crea:** `inclusion_financiera_clean`

### Rec 1–2: Normalización per cápita

Para cada columna de conteos/saldos (`ncont_*`, `saldocont_*`, `numtar_*`,
`numcontcred_*`), crea una columna `{col}_pc`:

$$
Y_{pc} = \frac{Y_{raw}}{pob\_adulta\_\{m|h|t\}} \times 10{,}000
$$

- El sufijo de la variable determina el denominador:
  - `_m` → `pob_adulta_m` (mujeres adultas)
  - `_h` → `pob_adulta_h` (hombres adultos)
  - `_t` → `pob_adulta` (total)
  - `_pm` → se excluye (persona moral, no tiene denominador poblacional)
- Protección contra ÷0: si denominador = 0, el resultado es `NaN`.
- Unidades resultantes: **outcome por cada 10,000 personas adultas**.

### Rec 3: Documentar saldoprom NULLs

Los `saldoprom_*` con `NULL` son **indefiniciones estructurales** (0 contratos →
saldo promedio = ÷0). NO se imputan. Los flags `flag_undef_saldoprom_*` ya
existentes marcan cuáles son.

| Producto | % undefined (total) |
|----------|-------------------:|
| `ahorro_t` | 92.7% |
| `n1_t` | 90.6% |
| `n3_t` | 82.0% |
| `plazo_t` | 56.9% |
| `tradic_t` | 56.1% |
| `n2_t` | 1.5% |
| `total_t` | 1.4% |

### Rec 4: Excluir columnas constantes

Se eliminan 3 columnas con varianza = 0:

| Columna eliminada | Valor constante |
|-------------------|-----------------|
| `hist_state_available` | Siempre 1 |
| `missing_quarters_alcaldesa` | Siempre 0 |
| `ok_panel_completo_final` | Siempre 1 |

### Validación post-transformación

- ✓ 0 infinitos en columnas `_pc`
- ✓ 0 negativos en columnas `_pc`
- ✓ Constantes eliminadas

**Resultado:** `inclusion_financiera_clean` con ~51 columnas `_pc` nuevas, 3
constantes eliminadas.

---

## Fase 2 — Transformaciones Altas (Recs 5–9)

**Script:** `Code/src/transformaciones_altas.py` (~421 líneas)  
**Lee y actualiza:** `inclusion_financiera_clean` (in-place)

### Rec 5: log(población) como controles

$$
\text{log\_pob} = \ln(\text{pob} + 1)
$$

Crea 4 columnas:
- `log_pob` — población total
- `log_pob_adulta` — población adulta total
- `log_pob_adulta_m` — mujeres adultas
- `log_pob_adulta_h` — hombres adultos

**¿Por qué?** La distribución de población es extremadamente sesgada (CV > 5).
La transformación logarítmica comprime la escala para usarla como control en
regresiones.

### Rec 6: Winsorización p1–p99

Para cada columna `_pc`, crea `_pc_w`:

$$
Y_w = \text{clip}(Y_{pc},\ q_{0.01},\ q_{0.99})
$$

- Recorta valores por debajo del percentil 1 y por encima del percentil 99.
- Los umbrales se calculan sobre **toda la muestra** (no por grupo de
  tratamiento) para evitar sesgo.
- Las columnas originales `_pc` se mantienen intactas.
- Propósito: verificar que los resultados no dependen de outliers en
  municipios muy pequeños.

### Rec 7: Ratio brecha de género (M/H)

$$
\text{ratio\_mh\_X} = \frac{X_{m,pc}}{X_{h,pc}}
$$

- Ratio < 1 → mujeres tienen menos inclusión financiera que hombres.
- Ratio > 1 → mujeres tienen más.
- Si `X_h_pc = 0` → `NaN`.
- ~17 ratios creados (uno por producto financiero).
- **Precaución:** Los ratios de saldos tienen outliers extremos (max > 90,000)
  cuando el denominador masculino es cercano a 0.

### Rec 8: `ever_alcaldesa`

$$
\text{ever\_alcaldesa}_i = \max_t(\text{alcaldesa\_final}_{it})
$$

- Indicador time-invariant: 1 si el municipio tuvo alcaldesa en **cualquier**
  trimestre.
- Se asigna el mismo valor a todos los trimestres de cada municipio.
- Absorbido por efectos fijos de municipio en regresiones → útil solo para
  balance/heterogeneidad.

### Rec 9: Estandarización de IDs

- Verifica consistencia de `cvegeo_mun` (5 dígitos INEGI).
- Crea índice B-tree en PostgreSQL para joins eficientes.
- Verifica que `cvegeo_mun = cve_ent || cve_mun3`.

**Resultado:** `inclusion_financiera_clean` ahora tiene ~296 columnas.

---

## Fase 3 — Transformaciones Medias (Recs 10–12)

**Script:** `Code/src/transformaciones_medias.py` (~332 líneas)  
**Lee y actualiza:** `inclusion_financiera_clean` (in-place)

### Rec 10: `alcaldesa_acumulado` (dosis de exposición)

Suma acumulada de `alcaldesa_final` por municipio a lo largo del tiempo:

```
Ejemplo (municipio 1011):
  t=2018Q3  alcaldesa=1  →  acumulado=1
  t=2018Q4  alcaldesa=1  →  acumulado=2
  t=2019Q3  alcaldesa=1  →  acumulado=5
  t=2019Q4  alcaldesa=0  →  acumulado=5  (no suma)
  t=2021Q4  alcaldesa=1  →  acumulado=6  (retoma)
```

Variable de tratamiento alternativa para evaluar efecto dosis-respuesta.

### Rec 11: asinh (transformación baseline para modelado)

$$
Y_{asinh} = \text{asinh}(Y_{pc}) = \ln\!\left(Y_{pc} + \sqrt{Y_{pc}^2 + 1}\right)
$$

Para cada columna `_pc`, crea `_pc_asinh`. **Esta es la escala que usan todos
los modelos econométricos**.

**¿Por qué asinh y no log?**

| Propiedad | asinh | log(1+Y) | log(Y) |
|-----------|-------|----------|--------|
| Definida en Y = 0 | ✓ | ✓ | ✗ |
| No requiere constante arbitraria | ✓ | ✗ (el "+1" distorsiona) | — |
| Simétrica: f(-x) = -f(x) | ✓ | ✗ | — |
| Interpretación | Semi-elasticidad para Y grande | Depende de escala | Semi-elasticidad |
| Preserva ceros | ✓ (asinh(0) = 0) | ✓ | ✗ |

Para valores grandes: $\text{asinh}(Y) \approx \ln(2Y)$, así que los coeficientes
se interpretan como semi-elasticidades aproximadas (Bellemare & Wichman, 2020).

### Rec 12: Imputar `tipo_pob` NULLs

2 municipios con `tipo_pob = NULL`:

| cve_mun | Municipio | Estado | Población | Asignado |
|---------|-----------|--------|-----------|----------|
| 2007 | San Felipe | BC | 20,320 | Semi-urbano |
| 4013 | Dzitbalché | Campeche | 16,568 | Semi-urbano |

Asignación por rango de población observado en las demás categorías.

**Resultado:** `inclusion_financiera_clean` final con **~348 columnas** en PostgreSQL.

---

## Fase 4 — Extracción del panel analítico

**Script:** `Code/src/tesis_alcaldesas/data/01_extract_panel.py`  
**Lee:** `inclusion_financiera_clean` (348 cols) · **Crea:** `analytical_panel.parquet` (61 cols)

Selecciona **61 de 348 columnas**:

| Grupo | Cols | Qué se lleva |
|-------|------|-------------|
| Identificadores | 7 | `cve_mun`, `periodo_trimestre`, `cvegeo_mun`, `cve_ent`, `year`, `quarter`, `t_index` |
| Tratamiento | 5 | `alcaldesa_final`, `ever_alcaldesa`, `alcaldesa_acumulado`, variantes excl. transiciones |
| Event study | 6 | Leads `f1–f3` y lags `l1–l3` (**NUNCA como controles, solo event study**) |
| Controles | 2 | `log_pob`, `log_pob_adulta` |
| Población | 3 | `pob_adulta_m`, `pob_adulta_h`, `pob_adulta` |
| Categóricas | 2 | `tipo_pob`, `region` |
| Auxiliares | 2 | `ok_panel_completo`, `quarters_in_base` |
| Raw outcomes M | 17 | Los 17 outcomes crudos mujeres |
| Raw outcomes H | 17 | Los 17 outcomes crudos hombres |

**¿Por qué solo 61 y no 348?** Se descartan las columnas `_pc`, `_pc_w`,
`_pc_asinh`, ratios y saldoprom que ya están en la DB. El siguiente script
**recalcula todo desde cero** para garantizar reproducibilidad.

---

## Fase 5 — Feature engineering final

**Script:** `Code/src/tesis_alcaldesas/data/02_build_features.py` (~400 líneas)  
**Lee:** `analytical_panel.parquet` · **Crea:** `analytical_panel_features.parquet`

6 etapas:

### [1/6] Validar panel

- PK `(cve_mun, periodo_trimestre)` única
- 2,471 municipios × 17 periodos = 42,007 esperados
- 41,905 observados → 8 municipios con panel incompleto (102 celdas = 0.24%)
- Decisión: conservar todos, añadir `flag_incomplete_panel`

### [2/6] Per cápita

$$
Y_{pc} = \frac{Y_{raw}}{pob\_adulta\_m} \times 10{,}000
$$

- 17 outcomes mujeres + 17 outcomes hombres = 34 columnas `_pc` nuevas
- Denominador = 0 produce `NaN` (en la práctica: `pob_adulta_m ≥ 36` para
  todos los municipios → 0 ceros)

### [3/6] Tres transformaciones

| Transformación | Sufijo | Fórmula | Uso |
|---------------|--------|---------|-----|
| **asinh** | `_pc_asinh` | $\ln(Y + \sqrt{Y^2+1})$ | **Baseline para todos los modelos** |
| Winsorización | `_pc_w` | $\text{clip}(Y_{pc}, p1, p99)$ | Robustez |
| log(1+Y) | `_pc_log1p` | $\ln(1 + Y_{pc})$ | Robustez / comparabilidad |

### [4/6] Ratios brecha de género

$$
\text{ratio\_mh\_X} = \frac{X_{m,pc}}{X_{h,pc}}
$$

17 ratios. Si denominador = 0 → `NaN`.

### [5/6] Flags de calidad

| Flag | Definición | Uso |
|------|-----------|-----|
| `flag_denom_zero` | `pob_adulta_m = 0` | Marcar obs con _pc = NaN. En la práctica: 0 obs. |
| `flag_incomplete_panel` | `quarters_in_base < 17` | 8 municipios (102 obs). Excluir como sensibilidad. |
| `flag_any_outcome_undef` | Algún `_pc` es NaN | Unión de flags anteriores. |

### [6/6] Cohorte y event_time

| Variable | Definición |
|----------|-----------|
| `first_treat_period` | Primer `periodo_trimestre` donde `alcaldesa_final = 1`. `NaN` si never-treated. |
| `first_treat_t` | `t_index` correspondiente. |
| `event_time` | `t_index - first_treat_t`. Negativo = pre; 0 = primer trimestre tratado; positivo = post. |
| `cohort_type` | `never-treated` / `switcher` / `always-treated` |

**Clasificación de municipios:**

| Tipo | Definición | En el panel |
|------|-----------|-------------|
| **never-treated** | `alcaldesa_final = 0` en todos los periodos | Grupo de control puro |
| **switcher** | Cambia de 0 a 1 al menos una vez | Principal fuente de identificación |
| **always-treated** | `alcaldesa_final = 1` desde el primer periodo | Sin periodos pre → no contribuyen al event study |

**Salida:** `analytical_panel_features.parquet` (~200+ columnas)

---

## Cómo consumen los modelos el dataset

Todos los scripts de modelado hacen lo mismo:

```python
df = pd.read_parquet("data/processed/analytical_panel_features.parquet")
depvar = f"{outcome}_pc_asinh"   # Siempre la columna asinh
```

Los 5 **outcomes primarios** (definidos en `config.py`):

| Variable | Nombre | Familia |
|----------|--------|---------|
| `ncont_total_m` | Contratos totales | Extensión |
| `saldocont_total_m` | Saldo total | Profundidad |
| `numtar_deb_m` | Tarjetas de débito | Productos |
| `numtar_cred_m` | Tarjetas de crédito | Productos |
| `numcontcred_hip_m` | Créditos hipotecarios | Productos |

Cada uno se modela como `{nombre}_pc_asinh` (per cápita × 10k, transformación
asinh). Las variantes winsor y log1p solo aparecen en `robustness.py`.

---

## Variables que NUNCA deben ser controles en regresiones

| Variable | Razón |
|----------|-------|
| `alcaldesa_final_f1/f2/f3` | **Leads**: contienen información futura → leakage |
| `alcaldesa_final_l1/l2/l3` | **Lags**: post-tratamiento → solo event study |
| `alcaldesa_transition`, `_transition_gender` | Endógenas al tratamiento |
| `alcaldesa`, `alcaldesa_end` | Versiones sin imputar (con NULLs) |
| `saldoprom_*` | 60–100% NULLs estructurales |
| Outcomes masculinos como controles | "Bad control" — potencialmente afectados por spillover |
| Outcomes totales (`_t`) | Incluyen al outcome femenino; mecánicamente endógenos |
| `ever_alcaldesa` | Time-invariant → absorbida por FE municipio |

---

## Orden de lectura recomendado

### Para entender los datos (Fases 0–3):

1. `Code/docs/README.md` — Diccionario de las 175 columnas originales
2. `Code/src/transformaciones_criticas.py` — Per cápita + excluir constantes
3. `Code/src/transformaciones_altas.py` — Log pob, winsor, ratios, ever_alcaldesa
4. `Code/src/transformaciones_medias.py` — Acumulado, asinh, tipo_pob
5. `Code/docs/07_DATA_CONTRACT.md` — Contrato de datos (348 cols finales)

### Para entender el pipeline analítico (Fases 4–5):

6. `Code/src/tesis_alcaldesas/config.py` — Rutas, outcomes, constantes centralizadas
7. `Code/src/tesis_alcaldesas/data/01_extract_panel.py` — Qué 61 cols se extraen
8. `Code/docs/08_DATASET_CONSTRUCCION.md` — Fórmulas y decisiones de diseño
9. `Code/src/tesis_alcaldesas/data/02_build_features.py` — Feature engineering

### Para entender los modelos:

10. `Code/src/tesis_alcaldesas/run_all.py` — Pipeline de 11 pasos
11. `Code/docs/13_MODELADO_ECONOMETRICO.md` — Ecuaciones y supuestos
12. `Code/docs/17_RESULTADOS_EMPIRICOS.md` — Resultados y discusión
13. `Code/docs/21_ONE_PAGER_ASESOR.md` — Resumen ejecutivo (1 página)

### Para la defensa:

14. `Code/docs/22_CHECKLIST_DEFENSA.md` — Checklist y preguntas anticipadas
15. `Code/docs/20_BIBLIOGRAFIA.md` — Bibliografía DiD / econometría aplicada

---

## Reproducir todo desde cero

```bash
cd Code/
source .venv/bin/activate

# Fase 1–3 (solo si inclusion_financiera_clean no existe en PostgreSQL):
python src/transformaciones_criticas.py
python src/transformaciones_altas.py
python src/transformaciones_medias.py

# Fase 4–5 + Modelos:
PYTHONPATH=src python -m tesis_alcaldesas.run_all
# Stacked DiD: extensión futura (ver docs/17_RESULTADOS_EMPIRICOS.md §4.6)
```

Todos los outputs quedan en `Code/outputs/paper/`.
