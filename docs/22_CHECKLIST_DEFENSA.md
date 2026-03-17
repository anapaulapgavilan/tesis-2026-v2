> **Archivos fuente:**
> - `src/models/01_table1_descriptives.py`
> - `src/models/02_twfe.py`
> - `src/models/03_event_study.py`
> - `src/models/04_robustness.py`
> - `src/models/05_heterogeneity.py`
> - `src/tesis_alcaldesas/models/event_study_sensitivity.py`
> - `src/tesis_alcaldesas/models/extensive_margin.py`
> - `src/tesis_alcaldesas/models/mdes_power.py`
> - `src/tesis_alcaldesas/models/sample_policy.py`

# 22 — Checklist Final para Defensa de Tesis

> Checklist unificado con todos los entregables.

---

## 1. Análisis empírico — Estado

| # | Componente | Estado | Script | Output principal |
|---|---|---|---|---|
| 1 | Descriptivos pre-tratamiento | ✅ | `models/01_table1_descriptives.py` | `tabla_1_descriptiva.*` |
| 2 | TWFE baseline (5 outcomes) | ✅ | `models/02_twfe.py` | `tabla_2_twfe.*` |
| 3 | Event study + pre-trends | ✅ | `models/03_event_study.py` | `figura_1_event_study.pdf` |
| 4 | Robustez (log1p, winsor, excl. trans., placebo) | ✅ | `models/04_robustness.py` | `tabla_3_robustez.*` |
| 5 | Heterogeneidad (tipo_pob, terciles) + BH | ✅ | `models/05_heterogeneity.py` | `tabla_4_heterogeneidad.*` |
| 6 | MDES / poder estadístico | ✅ | `mdes_power.py` | `tabla_5_mdes.*` |
| 7 | Sensibilidad event study (bin extremo) | ✅ | `event_study_sensitivity.py` | `figura_2_*.pdf` |
| 8 | Sample policy (main vs full) | ✅ | `sample_policy.py` | `sample_sensitivity.txt` |
| 9 | Extensivo + composición | ✅ | `extensive_margin.py` | `tabla_6_extensive.*` |

---

## 2. Tablas y figuras — Cuerpo principal

| ID | Contenido | Archivo |
|---|---|---|
| Tabla 1 | Estadísticas descriptivas pre-tratamiento | `tabla_1_descriptiva.tex` |
| Tabla 2 | TWFE baseline (5 outcomes, asinh) | `tabla_2_twfe.tex` |
| Tabla 3 | Pruebas de robustez | `tabla_3_robustez.tex` |
| Tabla 4 | Heterogeneidad + corrección BH | `tabla_4_heterogeneidad.tex` |
| Tabla 5 | MDES — poder estadístico | `tabla_5_mdes.tex` |
| Tabla 6 | Extensivo + share | `tabla_6_extensive.tex` |
| Figura 1 | Event study (5 outcomes, K=4, L=8) | `figura_1_event_study.pdf` |
| Figura 2 | Sensibilidad event study | `figura_2_event_study_sens.pdf` |

## 3. Tablas y figuras — Apéndice

| ID | Contenido | Archivo |
|---|---|---|
| Tabla A1 | MDES (5 outcomes) | `tabla_5_mdes.tex` |
| Tabla A2 | Sensibilidad event study | `pretrends_tests_sens.csv` |
| Figura A1 | Sensibilidad con bins alternativos | `figura_2_event_study_sens.pdf` |

Ver detalle en `docs/19_APENDICE.md`.

---

## 4. Documentación metodológica

| Doc | Tema | Clave |
|---|---|---|
| `13_MODELADO_ECONOMETRICO.md` | Ecuaciones, supuestos, decisiones | Especificación TWFE |
| `17_RESULTADOS_EMPIRICOS.md` | Resultados TWFE + discusión | §4.5 = conclusiones, §4.6 = recomendación Stacked DiD |
| `16_MDES_PODER.md` | MDES + interpretación del nulo | |
| `15_EVENT_STUDY_SENSIBILIDAD.md` | Borderline p=0.083 → sensibilidad | |
| `08_DATASET_CONSTRUCCION.md` §1.3 | Regla de muestra main vs full (integrado) | |
| `18_EXTENSION_OUTCOMES.md` | Margen extensivo y composición | |
| `20_BIBLIOGRAFIA.md` | Bibliografía DiD / econometría aplicada + BibTeX | |
| `19_APENDICE.md` | Índice del apéndice estadístico | |
| `23_FREEZE_RELEASE.md` | Instrucciones de freeze y verif. | |
| `21_ONE_PAGER_ASESOR.md` | Resumen ejecutivo (~1 pág) | |
| **`22_CHECKLIST_DEFENSA.md`** | **Este documento** | |

---

## 5. Verificaciones de coherencia

| Verificación | Pasa |
|---|---|
| Números en Doc 10 coinciden con CSVs | ✅ |
| Ventana `[-4,+8]` consistente en Docs 9/10/11 | ✅ |
| Pre-tendencias no significativas en TWFE | ✅ |
| outputs/paper/ versionados en git | ✅ |
| Tag `v1.0-thesis-results` existente | ✅ |
| README "Resultado principal" matizado | ✅ |

---

## 6. Preguntas anticipadas de defensa

### "¿Por qué no usas Callaway & Sant'Anna u otro estimador robusto?"
El análisis principal se basa en TWFE, que es el estimador estándar. Reconocemos
que con tratamiento escalonado existen estimadores modernos (Cengiz et al. 2019,
Callaway & Sant'Anna 2021) que resuelven sesgos potenciales. Se recomienda
implementar un Stacked DiD como extensión futura (ver Doc 17 §4.6 y Doc 10 §11).

### "¿Cómo sabes que el nulo TWFE no es falta de poder?"
Tabla 5 (MDES): descartamos efectos > 0.026–0.088 σ con 80% de poder.
El nulo TWFE refleja que el efecto, si existe, es muy pequeño o heterogéneo
temporalmente. Un Stacked DiD podría tener mayor poder para detectar señales
en productos crediticios (ver Doc 17 §4.6).

### "¿Cómo manejas el múltiple testing?"
Corrección Benjamini-Hochberg en heterogeneidad (Tabla 4). En el cuerpo
principal, los 5 outcomes son pre-especificados → no es fishing.

### "El pre-trend de tarjetas de crédito no pasa al 10%"
Con K=6 leads (sin binning agresivo), pasa cómodamente (p=0.212).
El borderline se debe al bin extremo k≤−4. Ver Figura 2.

### "¿Hay efecto en el margen extensivo?"
No: ni en acceso binario ni en composición de género. El efecto es
margen intensivo (más crédito donde ya hay). Ver Tabla 6.

---

## 7. Reproducibilidad

```bash
cd Code_V2/
source .venv/bin/activate
pip install -r requirements.txt && pip install -e .

# Pipeline completo:
PYTHONPATH=src python -m tesis_alcaldesas.run_all

# Verificar que outputs no cambiaron:
git diff -- outputs/paper/
```

---

## 8. Antes de entregar — Checklist final

- [ ] `run_all` ejecuta sin errores
- [ ] Todos los CSVs/TEX/PDFs en `outputs/paper/` están presentes
- [ ] Tag `v1.0-thesis-results` (o v1.1) empujado a remoto
- [ ] One-pager (`21_ONE_PAGER_ASESOR.md`) revisado con asesor
- [ ] Slides de defensa creadas y alineadas con Docs 9/10
- [ ] README.md refleja pipeline actualizado
- [ ] Números en slides coinciden con CSVs
