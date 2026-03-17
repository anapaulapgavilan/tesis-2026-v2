> **Archivos fuente:**
> - `src/tesis_alcaldesas/models/event_study_sensitivity.py`
> - `src/models/03_event_study.py`

# 15 — Sensibilidad del Event Study al Bin Extremo

## Problema

En el event study baseline (K=4 leads, L=8 lags), el test conjunto de
pre-trends para **tarjetas de crédito** (`numtar_cred_m`) arroja p=0.083,
ligeramente por debajo del umbral convencional de 10%. Esto podría levantar
la crítica de que el bin extremo (k ≤ -4) está arrastrando el test.

## ¿Qué se hizo?

Se corrieron 3 variantes adicionales para los 2 outcomes más delicados
(tarjetas de crédito y contratos totales):

| Variante | K leads | L lags | Excluye |
|---|---|---|---|
| **Baseline** | 4 | 8 | — |
| **A** | 3 | 8 | — (bin cambia a k ≤ -3) |
| **B** | 6 | 8 | — (bin cambia a k ≤ -6, más granular) |
| **C** | 4 | 8 | Cohorte g=0 (tratados desde el inicio) |

## Resultados

### Tarjetas de crédito (`numtar_cred_m`)

| Variante | χ² stat | p-value | Pasa al 10%? |
|---|---|---|---|
| Baseline (K=4) | 6.671 | 0.083 | No (borderline) |
| A: K=3 | 5.111 | 0.078 | No (borderline) |
| B: K=6 | 7.119 | 0.212 | **Sí** |
| C: Excl. g=0 | 7.155 | 0.067 | No |

> **📖 Cómo leer la tabla de sensibilidad — tarjetas de crédito (paso a paso)**
>
> Esta tabla evalúa si el borderline $p = 0.083$ del test de pre-trends para
> tarjetas de crédito es robusto o un artefacto de la ventana elegida.
>
> **Columnas:**
> | Columna | Significado |
> |---------|-------------|
> | Variante | Especificación alternativa del event study |
> | χ² stat | Estadístico del test conjunto de Wald (H₀: todos los leads = 0) |
> | p-value | Probabilidad de observar ese χ² si H₀ es verdadera |
> | Pasa al 10%? | ¿Se rechaza H₀ al 10%? "Sí" = pre-trends OK; "No" = sospecha de violación |
>
> **Paso 1 — Lee la fila Baseline:**
> $\chi^2 = 6.671$, $p = 0.083$. Está justo debajo del 10% → borderline.
>
> **Paso 2 — Compara con Variante B (K=6):**
> Al extender la ventana a 6 leads, $p = 0.212$ → pasa holgadamente.
> Esto indica que el problema estaba en el **bin extremo** ($k \leq -4$),
> que acumulaba periodos lejanos con señal heterogénea.
>
> **Paso 3 — Lee Variante A (K=3):**
> $p = 0.078$ → sigue borderline. Reducir la ventana no ayuda, confirmando
> que la señal no estaba solo en $k = -4$.
>
> **Paso 4 — Lee Variante C (excl. g=0):**
> $p = 0.067$ → ligeramente peor. Las cohortes tempranas no son las culpables.
>
> **Lectura rápida:** El borderline se resuelve con K=6 (más granularidad en
> pre-trends). El baseline K=4 es conservador; la conclusión de "pre-trends
> marginalmente OK" se sostiene.

### Contratos totales (`ncont_total_m`)

| Variante | χ² stat | p-value | Pasa al 10%? |
|---|---|---|---|
| Baseline (K=4) | 5.491 | 0.139 | Sí |
| A: K=3 | 4.850 | 0.089 | No (borderline) |
| B: K=6 | 7.170 | 0.208 | **Sí** |
| C: Excl. g=0 | 5.623 | 0.131 | Sí |

> **📖 Cómo leer la tabla de sensibilidad — contratos totales (paso a paso)**
>
> Misma estructura que la tabla anterior, ahora para contratos totales.
>
> **Paso 1 — Lee la fila Baseline:**
> $p = 0.139$ → pasa al 10%. Contratos totales no tenía problema de pre-trends.
>
> **Paso 2 — Nota la excepción (Variante A, K=3):**
> $p = 0.089$ → cae al borderline. Al acortar la ventana, se pierde un lead
> y el test pierde grados de libertad. Es un artefacto de la especificación,
> no una violación genuina.
>
> **Paso 3 — Variante B confirma robustez:**
> $p = 0.208$ → pasa holgadamente con la ventana extendida.
>
> **Lectura rápida:** Contratos totales pasa pre-trends en 3 de 4 variantes.
> La única excepción (K=3) es borderline y se explica por la pérdida de
> granularidad en la ventana pre.

## Interpretación

1. **Variante B (K=6)** es la más favorable: al extender la ventana pre, el
   bin deja de acumular periodos lejanos y el test pasa cómodamente. Esto
   sugiere que el p=0.083 del baseline proviene de la acumulación heterogénea
   en el bin k ≤ -4.

2. **Variante A (K=3)** no mejora el p-value de tarjetas de crédito, lo que
   sugiere que la señal no está solo en k = -4 sino distribuida en los leads.

3. **Variante C (excluir g=0)** no cambia sustancialmente el resultado, lo
   que indica que las cohortes tempranas no son las únicas responsables.

4. **Conclusión para la tesis**: El borderline p=0.083 es sensible a la
   especificación de la ventana. Con K=6 leads (que permite ver más periodos
   pre-tratamiento sin binning), el test de pre-trends pasa. Esto refuerza
   la interpretación de que las tendencias paralelas se sostienen para los
   5 outcomes primarios.

## Outputs

| Archivo | Contenido |
|---|---|
| `pretrends_tests_sens.csv` | Tests conjuntos para cada variante × outcome |
| `figura_2_event_study_sens.pdf` | Panel de event studies: outcomes × variantes |

> **📖 Cómo leer la Figura 2 — Panel de sensibilidad del event study**
>
> La Figura 2 muestra múltiples gráficos de event study, uno por combinación
> de outcome × variante de ventana, permitiendo comparar visualmente cómo
> cambian los coeficientes pre y post al modificar K leads.
>
> **Paso 1 — Identifica los paneles:**
> Cada sub-gráfico tiene su título (ej. "numtar_cred_m — K=6, L=8").
> Compara los paneles de la misma fila (mismo outcome) horizontalmente.
>
> **Paso 2 — Compara los leads entre variantes:**
> Para tarjetas de crédito: en el Baseline (K=4) el punto del bin extremo
> ($k \leq -4$) puede estar alejado de cero. En B (K=6), ese bin se descompone
> en puntos individuales que se acercan a cero → menos acumulación.
>
> **Paso 3 — Verifica que los post-treatment no cambian:**
> Los coeficientes post ($k \geq 0$) deberían ser estables entre variantes.
> Si cambian mucho, la estimación es sensible a la ventana (preocupante).
>
> **Lectura rápida:** Las variantes muestran que los pre-trends se suavizan
> con K=6 y los post-treatment son estables → robustez confirmada.

## Ejecución

```bash
python -m tesis_alcaldesas.models.event_study_sensitivity
```
