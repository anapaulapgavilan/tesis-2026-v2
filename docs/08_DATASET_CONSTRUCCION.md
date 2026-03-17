> **Archivos fuente:**
> - `src/tesis_alcaldesas/data/extract_panel.py`
> - `src/tesis_alcaldesas/data/build_features.py`

# Construcción del Dataset Analítico

**Fuente:** `inclusion_financiera_clean` → `analytical_panel_features.parquet`  
**Pipeline:** `src/data/01_extract_panel.py` → `src/data/02_build_features.py`

---

## 1. Muestra final

| Propiedad | Valor |
|-----------|-------|
| Tabla origen | `inclusion_financiera_clean` (PostgreSQL, `tesis_db`) |
| Filas | 41,905 |
| Municipios | 2,471 |
| Periodos | 17 (2018Q3 – 2022Q3) |
| Balance | **Casi-balanceado** — 8 municipios con panel incompleto (102 celdas faltantes, 0.24%) |

### 1.1 Municipios con panel incompleto

| `cve_mun` | Periodos | Faltantes |
|-----------|:--------:|:---------:|
| 2007 | 1 | 16 |
| 4013 | 1 | 16 |
| 2006 | 4 | 13 |
| 4012 | 4 | 13 |
| 7125 | 4 | 13 |
| 17036 | 4 | 13 |
| 17034 | 8 | 9 |
| 17035 | 8 | 9 |

### 1.2 Decisión de muestra

Se conservan **todos** los municipios (panel no balanceado). Razones:

1. Las celdas faltantes son sólo 0.24% del panel.
2. TWFE y Callaway-Sant'Anna admiten paneles no balanceados.
3. Se añade `flag_incomplete_panel = 1` para estos 8 municipios.
4. **Sensibilidad:** Se re-estimará excluyendo municipios incompletos para verificar
   que los resultados no dependen de estos 102 registros.

### 1.3 Sample policy (regla formal de muestra)

> **Contenido integrado de:** `docs/14_SAMPLE_POLICY.md` (archivo eliminado para consolidar la documentación).  
> **Script:** `src/tesis_alcaldesas/models/sample_policy.py`

**Main sample (muestra principal):**
- Panel balanceado: excluye municipios con `flag_incomplete_panel == 1`.
- Se usa para **todas las tablas y figuras principales** de la tesis.

**Full sample (muestra completa):**
- Incluye todos los municipios, incluso los que no tienen 17 trimestres.
- Se usa como **robustez**: si los resultados no cambian al incluir municipios
  incompletos, la exclusión no sesga.

**¿Son los incompletos diferentes?** La pregunta clave es si el missingness se
correlaciona con el tratamiento. Si los municipios faltantes son más o menos propensos
a tener alcaldesas, excluirlos sesga el estimador. El script `sample_policy.py`
verifica esto corriendo TWFE en ambas muestras.

```bash
python -m tesis_alcaldesas.models.sample_policy
```

**Outputs:**

| Archivo | Contenido |
|---------|-----------|
| `tabla_2_twfe_main.csv` / `.tex` | TWFE solo con panel balanceado |
| `tabla_2_twfe_full.csv` / `.tex` | TWFE con panel completo |
| `sample_sensitivity.txt` | Comparación textual de ambos |

**Regla final:** 8 municipios de ~2,471 = 0.3% del panel. Excluirlos asegura
regularidad para FE. La robustez con full sample confirma que la exclusión no
mueve resultados.

---

## 2. Columnas extraídas (01_extract_panel.py)

| Grupo | N cols | Descripción |
|-------|:------:|-------------|
| Identificadores | 7 | `cve_mun`, `periodo_trimestre`, `cvegeo_mun`, `cve_ent`, `year`, `quarter`, `t_index` |
| Tratamiento | 5 | `alcaldesa_final`, `ever_alcaldesa`, `alcaldesa_acumulado`, `alcaldesa_excl_trans`, `alcaldesa_end_excl_trans` |
| Event study (leads/lags) | 6 | `alcaldesa_final_f1`–`f3`, `alcaldesa_final_l1`–`l3` |
| Controles | 2 | `log_pob`, `log_pob_adulta` |
| Población | 3 | `pob_adulta_m`, `pob_adulta_h`, `pob_adulta` |
| Categóricas | 2 | `tipo_pob`, `region` |
| Auxiliares | 2 | `ok_panel_completo`, `quarters_in_base` |
| Raw outcomes mujeres | 17 | `ncont_*_m`, `saldocont_*_m`, `numtar_*_m`, `numcontcred_hip_m` |
| Raw outcomes hombres | 17 | `ncont_*_h`, `saldocont_*_h`, `numtar_*_h`, `numcontcred_hip_h` |
| **Total** | **61** | |

### Variables EXCLUIDAS por leakage/endogeneidad

| Variable | Razón |
|----------|-------|
| `alcaldesa_final_f1`–`f3` | **Leads**: contienen información futura → **NUNCA como controles**, sólo en event study |
| `alcaldesa_final_l1`–`l3` | **Lags**: post-tratamiento → sólo event study y placebos temporales |
| `alcaldesa_transition`, `_transition_gender` | Endógenas al proceso de tratamiento |
| `alcaldesa`, `alcaldesa_end` | Versiones sin imputar (NULLs) |
| `saldoprom_*` (56 cols) | 60–100% NULLs estructurales (÷0); no aptos como outcomes |
| Outcomes masculinos como controles | "Bad control" — potencialmente afectados por spillover |
| Outcomes totales (`_t`) | Incluyen al outcome femenino; mecánicamente endógenos |

> Los leads y lags se incluyen en la extracción para que el event study pueda usarlos,
> pero nunca entran como covariables en el modelo base TWFE.

---

## 3. Definición de outcomes core

### 3.1 Lista de outcomes

**17 outcomes por género**, organizados en 4 familias:

| Familia | Outcome | Variable raw (mujeres) | Interpretación |
|---------|---------|----------------------|----------------|
| Extensión | Y1 | `ncont_total_m` | Contratos totales |
| | Y2 | `ncont_ahorro_m` | Contratos de ahorro |
| | Y3 | `ncont_plazo_m` | Contratos a plazo |
| | Y4 | `ncont_n1_m` | Contratos nivel 1 |
| | Y5 | `ncont_n2_m` | Contratos nivel 2 |
| | Y6 | `ncont_n3_m` | Contratos nivel 3 |
| | Y7 | `ncont_tradic_m` | Contratos tradicionales |
| Profundidad | Y8 | `saldocont_total_m` | Saldo total |
| | Y9 | `saldocont_ahorro_m` | Saldo ahorro |
| | Y10 | `saldocont_plazo_m` | Saldo a plazo |
| | Y11 | `saldocont_n1_m` | Saldo nivel 1 |
| | Y12 | `saldocont_n2_m` | Saldo nivel 2 |
| | Y13 | `saldocont_n3_m` | Saldo nivel 3 |
| | Y14 | `saldocont_tradic_m` | Saldo tradicional |
| Productos | Y15 | `numtar_deb_m` | Tarjetas de débito |
| | Y16 | `numtar_cred_m` | Tarjetas de crédito |
| | Y17 | `numcontcred_hip_m` | Créditos hipotecarios |

**5 primarios** para la especificación principal: Y1, Y8, Y15, Y16, Y17.

### 3.2 Outcomes secundarios (brecha de género)

Se construyen 17 ratios M/H:

$$
\text{ratio\_mh\_X} = \frac{X_{m,pc}}{X_{h,pc}}
$$

Interpretación: ratio > 1 → más inclusión financiera femenina que masculina.

---

## 4. Fórmulas y unidades

### 4.1 Per cápita

$$
Y_{pc} = \frac{Y_{raw}}{pob\_adulta\_m} \times 10{,}000
$$

- **Denominador:** `pob_adulta_m` (población adulta femenina, CONAPO).
- **Unidades:** outcome por cada 10,000 mujeres adultas.
- **Denominador = 0:** Se produce `NaN`; un flag (`flag_denom_zero`) marca estas
  observaciones. En la práctica, `pob_adulta_m ≥ 36` para todos los municipios
  en el panel, por lo que no hay ceros.

### 4.2 asinh (especificación baseline)

$$
Y_{asinh} = \text{asinh}(Y_{pc}) = \ln\!\left(Y_{pc} + \sqrt{Y_{pc}^2 + 1}\right)
$$

**¿Por qué asinh como baseline?**

1. **Ceros:** Los outcomes per cápita contienen ceros legítimos (municipios sin
   contratos de ahorro, sin hipotecas). El logaritmo natural no está definido en 0;
   `log(Y+1)` introduce sesgo para valores pequeños.
2. **Monotónica y diferenciable:** asinh preserva el orden y permite derivadas en
   todo el dominio real.
3. **Interpretación:** Para $Y$ grandes, $\text{asinh}(Y) \approx \ln(2Y)$, por lo
   que los coeficientes se interpretan como **semi-elasticidades aproximadas**
   (Bellemare & Wichman, 2020).
4. **Simetría:** A diferencia de $\ln(Y+c)$, no requiere elegir una constante
   arbitraria $c$.

### 4.3 Winsorización (robustez `_pc_w`)

$$
Y_{w} = \text{clip}(Y_{pc},\ q_{0.01},\ q_{0.99})
$$

- Recorta al percentil 1 y 99 de la distribución de `Y_pc`.
- Los umbrales se calculan sobre **toda la muestra** (no por grupo de tratamiento)
  para evitar sesgo.
- Propósito: verificar que los resultados no dependen de outliers extremos en
  municipios muy pequeños.

### 4.4 log(1+Y) (robustez `_pc_log1p`)

$$
Y_{log1p} = \ln(1 + Y_{pc})
$$

- Alternativa a asinh usada en la literatura.
- Se reporta como robustez para comparabilidad con estudios previos.
- Valores negativos (imposibles en estos datos) se truncan a 0 antes de aplicar.

---

## 5. Cohorte y event_time

### 5.1 Definiciones

| Variable | Definición |
|----------|-----------|
| `first_treat_period` | Primer `periodo_trimestre` donde `alcaldesa_final = 1`. `NaN` para never-treated. |
| `first_treat_t` | `t_index` correspondiente a `first_treat_period`. |
| `event_time` | `t_index - first_treat_t`. Negativo = pre-tratamiento; 0 = primer periodo tratado; positivo = post. `NaN` para never-treated. |
| `cohort_type` | Clasificación del municipio: |

### 5.2 Clasificación de municipios

| Tipo | Definición | Uso |
|------|-----------|-----|
| `never-treated` | `alcaldesa_final = 0` en **todos** los periodos | Grupo de control puro (para C&S / Sun-Abraham) |
| `switcher` | `alcaldesa_final` cambia al menos una vez (en cualquier dirección) | Principal fuente de identificación (894 total; 600 con pre-periodo, 294 left-censored) |
| `always-treated` | `alcaldesa_final = 1` en **todos** los periodos del panel (nunca la pierde) | Sin periodos pre-tratamiento; excluidos del event study; contribuyen al TWFE |

### 5.3 Notas para el event study

- `event_time` se construye respecto al **primer** episodio de tratamiento.
- Los municipios `always-treated` tienen `event_time ≥ 0` en todos los periodos →
  no contribuyen a estimar coeficientes pre-tratamiento.
- Los municipios `never-treated` tienen `event_time = NaN` → se codifican como
  grupo de control en C&S.

---

## 6. Flags de calidad

| Flag | Definición | Uso |
|------|-----------|-----|
| `flag_denom_zero` | `pob_adulta_m = 0` | Marcar obs donde _pc es NaN por ÷0. En la práctica: 0 obs afectadas. |
| `flag_incomplete_panel` | `quarters_in_base < 17` | 8 municipios (102 obs). Sensibilidad: excluir. |
| `flag_any_outcome_undef` | Algún `_pc` es NaN | Unión de denom_zero y cualquier otro NaN. |

---

## 7. Pipeline reproducible

```bash
# 1. Extracción
export DATABASE_URL="postgresql://user@localhost:5432/tesis_db"
python src/data/01_extract_panel.py
# → data/processed/analytical_panel.parquet

# 2. Feature engineering
python src/data/02_build_features.py
# → data/processed/analytical_panel_features.parquet
# → outputs/qc/panel_checks.txt
# → outputs/qc/cohort_summary.csv
```

---

## 8. Archivos generados

| Archivo | Contenido |
|---------|-----------|
| `data/processed/analytical_panel.parquet` | Panel crudo: 61 columnas extraídas de PostgreSQL |
| `data/processed/analytical_panel_features.parquet` | Dataset final con per cápita, asinh, winsor, log1p, ratios, flags, cohorte |
| `outputs/qc/panel_checks.txt` | Validación de PK, balance, distribución de tratamiento |
| `outputs/qc/cohort_summary.csv` | Conteo de municipios por tipo de cohorte y periodo de primer tratamiento |
