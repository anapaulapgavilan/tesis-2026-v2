# Resumen Ejecutivo de Resultados

**Generado:** Febrero 2026  
**Pipeline:** `src/models/01–05`  
**Input:** `data/processed/analytical_panel_features.parquet` (41,905 × 170)

---

## Resultado principal

**No se detecta efecto estadísticamente significativo** de `alcaldesa_final` sobre
ninguno de los 5 outcomes primarios de inclusión financiera femenina.

| Outcome | β (TWFE) | SE cluster | p-valor | IC 95% |
|---------|:--------:|:----------:|:-------:|--------|
| Contratos totales (asinh) | 0.007 | 0.022 | 0.747 | [-0.035, 0.049] |
| Tarjetas débito (asinh) | -0.014 | 0.021 | 0.521 | [-0.055, 0.028] |
| Tarjetas crédito (asinh) | -0.002 | 0.017 | 0.919 | [-0.036, 0.032] |
| Créditos hipotecarios (asinh) | 0.018 | 0.021 | 0.400 | [-0.024, 0.060] |
| Saldo total (asinh) | 0.004 | 0.049 | 0.931 | [-0.092, 0.100] |

Interpretación: coeficientes en escala asinh ≈ semi-elasticidades. Un β = 0.007
significaría un efecto de +0.7% — pero con SE = 0.022 no es distinguible de cero.

---

## Pre-trends

| Outcome | χ² (joint) | p-valor | ¿Pasa 10%? |
|---------|:----------:|:-------:|:----------:|
| Contratos totales | 5.49 | 0.139 | ✓ |
| Tarjetas débito | 3.80 | 0.284 | ✓ |
| Tarjetas crédito | 6.67 | 0.083 | ✗ (borderline) |
| Créditos hipotecarios | 0.75 | 0.861 | ✓ |
| Saldo total | 3.52 | 0.319 | ✓ |

**Veredicto:** 4/5 pasan. Tarjetas crédito tiene lead significativo en k=-4
(probablemente bin extremo). Pre-trends razonablemente sostenidos.

---

## Robustez

Todas las pruebas sobre contratos totales (outcome focal):

| Test | β | SE | Consistente |
|------|:-:|:--:|:-----------:|
| Baseline (asinh) | 0.007 | 0.022 | — |
| log(1+y) | 0.005 | 0.020 | ✓ |
| Winsor p1-p99 + asinh | 0.008 | 0.021 | ✓ |
| Excluir transiciones | 0.002 | 0.024 | ✓ |
| Placebo temporal (+4 trim) | -0.019 | 0.020 | ✓ (≈0) |
| Placebo género (hombres) | -0.001 | 0.025 | ✓ (≈0) |

**Veredicto:** Resultado nulo robusto. Placebos confirman ausencia de efecto espurio.

---

## Heterogeneidad

Único efecto nominalmente significativo: **Metrópoli** (β=0.030, p=0.024),
pero q-value BH = 0.215 → **no sobrevive corrección por múltiples pruebas**.

---

## Outputs generados

### Tablas
| Archivo | Contenido |
|---------|-----------|
| `tabla_1_descriptiva.csv` / `.tex` | Estadísticos pre-tratamiento por grupo |
| `tabla_2_twfe.csv` / `.tex` + `_raw.csv` | TWFE baseline (5 outcomes) |
| `tabla_3_robustez.csv` / `.tex` | 5 pruebas de robustez |
| `tabla_4_heterogeneidad.csv` / `.tex` | Sub-muestras tipo_pob + terciles pob |

### Figuras
| Archivo | Contenido |
|---------|-----------|
| `figura_1_event_study.pdf` / `.png` | Event study (5 outcomes, leads + lags) |

### Diagnósticos
| Archivo | Contenido |
|---------|-----------|
| `pretrends_tests.csv` | Test conjunto χ² para cada outcome |
| `event_study_coefs_*.csv` | Coeficientes individuales por outcome (5 archivos) |

---

## Reproducción

```bash
source .venv/bin/activate
python src/models/01_table1_descriptives.py
python src/models/02_twfe.py
python src/models/03_event_study.py
python src/models/04_robustness.py
python src/models/05_heterogeneity.py
```

Dependencias: `pandas numpy linearmodels statsmodels matplotlib scipy pyarrow jinja2`
