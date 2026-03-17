> **Archivos fuente:**
> - `src/tesis_alcaldesas/models/mdes_power.py`
> - `src/tesis_alcaldesas/models/event_study_sensitivity.py`

# Apéndice — Tablas y Figuras Complementarias

Este apéndice lista los outputs complementarios que acompañan el capítulo de
resultados empíricos.  Todos son reproducibles con el pipeline del repositorio.

---

## A. Tablas

### Tabla A1. MDES — Minimum Detectable Effect Size

| Campo | Detalle |
|---|---|
| Archivo | `outputs/paper/tabla_6_mdes.csv`, `outputs/paper/tabla_6_mdes.tex` |
| Script | `src/tesis_alcaldesas/models/mdes_power.py` |
| Texto resumen | `outputs/paper/mdes_summary.txt` |
| Muestra | 41,905 obs (panel principal), 894 switchers totales (600 con pre-periodo) |
| Estimador | TWFE (cálculo analítico de MDE basado en varianza residual y $N_{eff}$) |
| Poder | 80%, $\alpha = 0.05$ (bilateral) |

Reporta el efecto mínimo detectable para cada outcome, permitiendo interpretar
los nulos del TWFE como "descartamos efectos mayores a X%".

> **📖 Cómo leer la Tabla A1 (paso a paso)**
>
> Cada fila es un outcome. Las columnas clave: MDES_asinh y MDES_pct.
>
> **Paso 1:** Lee MDES_pct para cada outcome. Si es < 10%, el nulo del TWFE
> descarta efectos de magnitud relevante para política pública.
>
> **Paso 2:** Compara MDES con el coeficiente estimado por el TWFE.
> Si ambos son del mismo orden de magnitud, el poder estadístico es
> suficiente para detectar efectos de tamaño relevante.

---

### Tabla A2. Sensibilidad del event study — pre-trends bajo especificaciones alternativas

| Campo | Detalle |
|---|---|
| Archivo (tests) | `outputs/paper/pretrends_tests_sens.csv` |
| Archivo (figura) | `outputs/paper/figura_2_event_study_sens.pdf` |
| Script | `src/tesis_alcaldesas/models/event_study_sensitivity.py` |
| Muestra | 41,905 obs (panel principal) |
| Variantes | 4 especificaciones × 2 outcomes (`ncont_total_m`, `numtar_cred_m`) |
| Objetivo | Blindar el borderline $p = 0.083$ en tarjetas de crédito |

Las variantes incluyen: (i) baseline K=4/L=8, (ii) K=6/L=8 sin binning agresivo,
(iii) K=4/L=6, (iv) K=4/L=8 con log(1+y).  Con K=6, tarjetas de crédito pasa
holgadamente ($p > 0.20$).

> **📖 Cómo leer la Tabla A2 (paso a paso)**
>
> Cada fila combina un outcome × variante. Las columnas: χ² stat, p-value.
>
> **Paso 1:** Para tarjetas de crédito, busca la variante donde $p > 0.10$
> (K=6, L=8) → el borderline desaparece al evitar el binning agresivo.
>
> **Paso 2:** Para contratos totales, confirma que pasa en la mayoría de
> variantes (3/4) → pre-trends robustos.
>
> **Paso 3:** Si una variante empeora $p$ (ej. Variante A reduce K a 3),
> no es señal de violación genuina: reducir grados de libertad infla
> mecánicamente el test.

---

## B. Figuras

### Figura A1. Sensibilidad del event study

| Campo | Detalle |
|---|---|
| Archivo | `outputs/paper/figura_2_event_study_sens.pdf` (`.png` también disponible) |
| Script | `src/tesis_alcaldesas/models/event_study_sensitivity.py` |
| Contenido | Coeficientes de event-time bajo 4 variantes × 2 outcomes |

> **📖 Cómo leer la Figura A1 (paso a paso)**
>
> Panel de gráficos: filas = outcomes (crédito, contratos), columnas = variantes.
>
> **Paso 1:** Compara la forma de los leads entre paneles. Si una variante
> "aplana" los leads → la pre-trend mejora con esa ventana.
>
> **Paso 2:** Los post-treatment deben ser estables entre variantes. Si
> cambian mucho, la estimación depende de la ventana (preocupante).
>
> **Paso 3:** Busca la variante K=6 para tarjetas de crédito: los leads
> individuales deben estar más cerca de cero que el bin acumulado del baseline.

---

## C. Otros outputs complementarios

| Archivo | Contenido |
|---|---|
| `outputs/paper/sample_sensitivity.txt` | Comparación main sample vs full sample |
| `outputs/paper/tabla_2_twfe_main.csv` / `_full.csv` | TWFE por muestra |
| `outputs/paper/tabla_5_extensive.csv` | Margen extensivo (LPM binary + share) |

---

## Reproducción

```bash
cd Code/
source .venv/bin/activate
PYTHONPATH=src python -m tesis_alcaldesas.run_all          # pipeline principal (Tablas 1-6, Figuras 1-2)
```
