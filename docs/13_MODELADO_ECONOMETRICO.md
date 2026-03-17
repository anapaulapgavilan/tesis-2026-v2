> **Archivos fuente:**
> - `src/models/01_table1_descriptives.py`
> - `src/models/02_twfe.py`
> - `src/models/03_event_study.py`
> - `src/models/04_robustness.py`
> - `src/models/05_heterogeneity.py`
> - `src/models/utils.py`

# Modelado Econométrico — Documentación Técnica

**Pipeline:** `src/models/01_table1_descriptives.py` → `02_twfe.py` → `03_event_study.py` → `04_robustness.py` → `05_heterogeneity.py`  
**Input:** `data/processed/analytical_panel_features.parquet`

---

## 1. Estrategia de identificación

### 1.1 Pregunta

> ¿Cuál es el efecto causal de tener alcaldesa ($D_{it} = 1$) sobre la inclusión
> financiera de las mujeres en municipios mexicanos?

### 1.2 Diseño

**Diferencias en diferencias (DiD)** con datos de panel, explotando variación
within-municipality en `alcaldesa_final` a lo largo de 17 trimestres (2018Q3–2022Q3).

| Componente | Implementación |
|-----------|----------------|
| Tratamiento | `alcaldesa_final` ∈ {0,1} |
| Efectos fijos | Municipio ($\alpha_i$, 2,471) + periodo ($\gamma_t$, 17) |
| Cluster SE | Municipio (2,471 clusters) |
| Control | `log_pob` (predeterminada/lenta) |
| Grupo de control implícito | Never-treated + not-yet-treated (en TWFE) |

### 1.3 Supuesto clave — Tendencias paralelas

En ausencia de tratamiento, los municipios que reciben alcaldesa habrían seguido la
misma trayectoria en inclusión financiera que los municipios que no la reciben.

**Evaluación empírica:** Event study con leads K=4 y lags L=8 (§4).

---

## 2. Modelos y ecuaciones

### 2.1 TWFE baseline

$$
Y_{it} = \alpha_i + \gamma_t + \beta \cdot D_{it} + \delta \cdot \log(\text{pob})_{it} + \varepsilon_{it}
$$

- $Y_{it}$: outcome en escala asinh (ver §3)
- $\beta$: **efecto promedio TWFE** — bajo adopción escalonada con efectos
  heterogéneos, $\hat{\beta}_{\text{TWFE}}$ es un promedio ponderado con pesos
  potencialmente no convexos (Goodman-Bacon, 2021). **No se denomina ATT**; ese
  término se reserva para estimadores que lo recuperan formalmente (Callaway &
  Sant'Anna, Sun & Abraham).

### 2.2 Event study

$$
Y_{it} = \alpha_i + \gamma_t + \sum_{k \neq -1} \delta_k \cdot \mathbf{1}\{K_{it} = k\} + \delta \cdot \log(\text{pob})_{it} + \varepsilon_{it}
$$

- $K_{it}$: event_time = `t_index` − `first_treat_t`
- Referencia: $k = -1$ (trimestre inmediatamente anterior al tratamiento)
- Leads: $k \in \{-4, -3, -2\}$ (diagnostican pre-trends)
- Lags: $k \in \{0, 1, ..., 7\}$ (capturan dinámica post-tratamiento)
- Bins extremos: $k \leq -4$ y $k \geq 8$ agrupados
- Muestra: excluye always-treated (sin pre-período)

**Test conjunto de pre-trends:** estadístico $\chi^2$ Wald que todos los
coeficientes pre-tratamiento ($\delta_{-4}, \delta_{-3}, \delta_{-2}$) = 0.

---

## 3. Escala de la variable dependiente

### 3.1 Per cápita

$$
Y_{pc} = \frac{Y_{\text{raw}}}{\text{pob\_adulta\_m}} \times 10{,}000
$$

Unidades: outcome por cada 10,000 mujeres adultas.

### 3.2 ¿Por qué asinh como baseline?

$$
Y_{\text{asinh}} = \text{asinh}(Y_{pc}) = \ln\!\left(Y_{pc} + \sqrt{Y_{pc}^2 + 1}\right)
$$

1. **Ceros legítimos:** Muchos municipios tienen 0 contratos de ahorro o 0 hipotecas.
   $\ln(Y)$ no está definido en 0.
2. **Sesgo de $\ln(Y+1)$:** Para valores pequeños, $\ln(1+Y) \neq \ln(Y)$, lo que
   introduce sesgo sistemático (Bellemare & Wichman, 2020).
3. **Interpretación:** Para $Y$ grandes, $\text{asinh}(Y) \approx \ln(2Y)$, por lo
   que $\hat{\beta}$ se interpreta como semi-elasticidad aproximada.
4. **Diferenicabilidad:** Monotónica y diferenciable en todo $\mathbb{R}$.

### 3.3 Escalas de robustez

| Escala | Fórmula | Propósito |
|--------|---------|-----------|
| Winsor + asinh | $\text{asinh}(\text{clip}(Y_{pc}, q_{0.01}, q_{0.99}))$ | Controlar outliers |
| $\log(1+Y)$ | $\ln(1 + Y_{pc})$ | Comparabilidad con literatura |

---

## 4. Diagnóstico de pre-trends

### 4.1 Resultados

| Outcome | $\chi^2$ | p-valor | ¿Pasa 10%? |
|---------|------:|--------:|:----------:|
| Contratos totales | 5.49 | 0.139 | ✓ |
| Tarjetas débito | 3.80 | 0.284 | ✓ |
| Tarjetas crédito | 6.67 | 0.083 | ✗ (borderline) |
| Créditos hipotecarios | 0.75 | 0.861 | ✓ |
| Saldo total | 3.52 | 0.319 | ✓ |

### 4.2 Interpretación

> **Cómo leer esta tabla paso a paso:**
>
> 1. **Columna $\chi^2$**: Es el estadístico del test conjunto de Wald. Prueba
>    simultáneamente si los 3 coeficientes pre-tratamiento ($k=-4, -3, -2$) son
>    todos iguales a cero. Un valor más alto indica más evidencia contra tendencias
>    paralelas, pero no tiene escala intuitiva — mira el p-valor.
> 2. **Columna p-valor**: La probabilidad de obtener un $\chi^2$ así de grande si las
>    tendencias fueran realmente paralelas. Si $p > 0.10$, "pasa": no podemos
>    rechazar que las tendencias fueran paralelas. Si $p < 0.10$, hay evidencia de
>    divergencia pre-tratamiento.
> 3. **Columna "¿Pasa 10%?"**: Resumen binario de la columna anterior.
>    ✓ = El supuesto de tendencias paralelas se sostiene para este outcome.
>    ✗ = Hay una violación (al menos marginal). El DiD para este outcome requiere
>    cautela interpretativa.
> 4. **Lectura rápida**: Busca la columna "¿Pasa?" — si la mayoría tiene ✓, el diseño
>    es creíble. Si solo uno falla, se reporta como limitación sin invalidar todo.

- **4 de 5 outcomes** pasan el test conjunto al 10%.
- **Tarjetas de crédito** presenta un lead $k=-4$ significativo ($p=0.043$), pero
  el test conjunto es marginal ($p=0.083$). Esto podría reflejar ruido en el extremo
  del bin (k ≤ -4) más que una violación sistemática.
- **Decisión:** Los pre-trends son razonablemente consistentes con tendencias
  paralelas. Se procede con TWFE como especificación principal.

### 4.3 Mapa de decisiones

```
¿Pre-trends pasan? (χ² test conjunto p > 0.10)
├── 4/5 SÍ → Proceder con TWFE como especificación principal
│   ├── tarjetas crédito borderline → reportar pero no descartar
│   └── Futuro: estimar C&S/Sun-Abraham como robustez
└── Si fallaran:
    ├── Lead -1 significativo → recodificar con anticipación
    ├── Leads -2, -3, -4 significativos → DiD no válido
    │   └── Considerar matching + DiD o tendencias específicas
    └── Solo bin extremo (-4) → probablemente ruido (como en tarjetas crédito)
```

---

## 5. Resultados TWFE

### 5.1 Efecto TWFE (5 outcomes primarios)

| Outcome | $\hat{\beta}$ | SE | p-valor | Significativo |
|---------|----------:|---:|--------:|:-------------:|
| Contratos totales | 0.007 | 0.022 | 0.747 | No |
| Tarjetas débito | -0.014 | 0.021 | 0.521 | No |
| Tarjetas crédito | -0.002 | 0.017 | 0.919 | No |
| Créditos hipotecarios | 0.018 | 0.021 | 0.400 | No |
| Saldo total | 0.004 | 0.049 | 0.931 | No |

### 5.2 Interpretación

> **Cómo leer la Tabla 2 (TWFE) paso a paso:**
>
> Cada fila es un outcome (variable dependiente). Para cada uno, se estimó
> una regresión TWFE separada con la misma especificación, cambiando solo la $Y$.
>
> - **$\hat{\beta}$**: El coeficiente estimado del tratamiento (`alcaldesa_final`).
>   Se interpreta como: "los municipios con alcaldesa tienen $\hat{\beta}$ unidades
>   *más* (en escala asinh) en este outcome, controlando por FE municipio y periodo".
>   Para convertir a porcentaje aproximado: $\Delta\% \approx \hat{\beta} \times 100$
>   cuando $\hat{\beta}$ es pequeño (e.g., 0.007 ≈ 0.7%).
> - **SE**: Error estándar clustered por municipio. Mide la incertidumbre alrededor
>   de $\hat{\beta}$. IC 95% ≈ $\hat{\beta} \pm 1.96 \times SE$.
> - **p-valor**: Probabilidad de obtener un $\hat{\beta}$ así de grande (o más)
>   si el efecto real fuera cero. Convenciones: $p < 0.01$ (***), $p < 0.05$ (**),
>   $p < 0.10$ (*). Aquí todos los p > 0.10 → ninguno es significativo.
> - **"Significativo"**: ¿El p-valor es menor que el umbral? Aquí todos dicen "No".
>
> **Lectura rápida de la tabla**: Los 5 coeficientes son cercanos a cero (entre
> −0.014 y +0.018) con p-valores altos (entre 0.40 y 0.93). Esto significa que
> el estimador TWFE convencional no detecta ningún efecto de tener alcaldesa
> sobre la inclusión financiera femenina. El resultado principal del TWFE es un
> **nulo generalizado** en los 5 indicadores.

Ninguno de los 5 outcomes primarios muestra un efecto estadísticamente significativo
de `alcaldesa_final` sobre la inclusión financiera femenina. Los coeficientes son
cercanos a cero y los intervalos de confianza incluyen el cero con holgura.

**Esto no significa "no hay efecto"** — significa que con la variación disponible en
el panel (894 switchers totales, 600 con pre-periodo efectivo, 17 trimestres), no se detecta un efecto distinguible del
ruido estadístico en la escala asinh.

---

## 6. Robustez

| Test | $\hat{\beta}$ | SE | N | Resultado |
|------|----------:|---:|--:|-----------|
| Baseline asinh | 0.007 | 0.022 | 41,905 | n.s. |
| R1: log(1+y) | 0.005 | 0.020 | 41,905 | Consistente |
| R2: Winsor + asinh | 0.008 | 0.021 | 41,905 | Consistente |
| R3: Excluir transiciones | 0.002 | 0.024 | 38,303 | Consistente |
| R4: Placebo temporal (+4 trim) | -0.019 | 0.020 | 32,027 | ✓ ≈ 0 |
| R5: Placebo género (hombres) | -0.001 | 0.025 | 41,905 | ✓ ≈ 0 |

**Conclusión de robustez:**
- El resultado nulo es robusto a escala, winsorización y definición del tratamiento.
- Los placebos temporal y de género confirman que no hay efecto espurio: el
  tratamiento adelantado 4 trimestres no tiene efecto, y los outcomes masculinos
  tampoco muestran efecto de `alcaldesa_final`.

> **📖 Cómo leer la tabla de robustez (paso a paso)**
>
> Esta tabla evalúa si el resultado nulo del TWFE es genuino o un artefacto de
> decisiones metodológicas. Cada fila repite la estimación cambiando **un** supuesto.
>
> **Columnas:**
> | Columna | Significado |
> |---------|-------------|
> | Test | Nombre del chequeo de robustez |
> | $\hat{\beta}$ | Coeficiente estimado bajo esa variante |
> | SE | Error estándar clusterizado por municipio |
> | N | Tamaño de muestra (puede variar si se excluyen observaciones) |
> | Resultado | Veredicto: ¿consistente con el baseline? |
>
> **Paso 1 — Lee la fila "Baseline asinh":** Es tu punto de referencia
> ($\hat{\beta}=0.007$, no significativo). Todas las demás filas se comparan contra esta.
>
> **Paso 2 — Compara R1 y R2 (transformaciones alternativas):**
> Cambiar de $\text{asinh}(y)$ a $\log(1+y)$ o winsorizar antes de transformar
> produce $\hat{\beta}$ entre 0.005 y 0.008. Son prácticamente idénticos al
> baseline → el resultado **no depende** de la escala elegida.
>
> **Paso 3 — Compara R3 (excluir transiciones):**
> Se eliminan municipios que cambian de alcalde a alcaldesa (o viceversa)
> durante el panel. $N$ baja de 41,905 a 38,303 pero $\hat{\beta}=0.002$
> sigue siendo nulo → las transiciones no generan sesgo.
>
> **Paso 4 — Lee los placebos (R4 y R5):**
> - R4 (placebo temporal): se adelanta el tratamiento 4 trimestres. Si hubiera
>   una tendencia previa confundente, este "tratamiento falso" sería significativo.
>   $\hat{\beta}=-0.019$, no significativo → ✓ sin tendencia espuria.
> - R5 (placebo género): se usa el outcome masculino como variable dependiente.
>   Si la alcaldesa afectara la inclusión financiera general (no solo mujeres),
>   también veríamos efecto en hombres. $\hat{\beta}=-0.001$ → ✓ sin efecto espurio.
>
> **Lectura rápida:** Todos los $\hat{\beta}$ oscilan entre −0.019 y +0.008,
> todos no significativos. El resultado nulo del TWFE es robusto.

---

## 7. Heterogeneidad

Sub-muestras por `tipo_pob` y terciles de `log_pob`:

| Dimensión | Grupo | $\hat{\beta}$ | SE | p-valor | q-value (BH) |
|-----------|-------|----------:|---:|--------:|:----:|
| tipo_pob | Rural | -0.104 | 0.065 | 0.109 | 0.492 |
| | En Transición | -0.007 | 0.035 | 0.839 | 0.928 |
| | Semi-urbano | 0.003 | 0.029 | 0.928 | 0.928 |
| | Urbano | 0.003 | 0.013 | 0.796 | 0.928 |
| | Semi-metrópoli | -0.004 | 0.015 | 0.774 | 0.928 |
| | Metrópoli | 0.030** | 0.013 | 0.024 | 0.215 |
| Tercil pob | T1 (pequeño) | -0.069 | 0.053 | 0.196 | 0.587 |
| | T2 (mediano) | -0.021 | 0.032 | 0.504 | 0.928 |
| | T3 (grande) | 0.003 | 0.014 | 0.823 | 0.928 |

**Notas:**
- Metrópoli muestra significancia nominal ($p=0.024$) pero tiene $q=0.215$ tras
  corrección BH → **no sobrevive múltiples pruebas**.
- El efecto en municipios rurales es negativo y borderline → consistente con
  la hipótesis de que los mecanismos podrían operar diferente en zonas con menor
  infraestructura financiera.
- **Conclusión:** No hay efecto heterogéneo robusto tras corrección FDR.

> **📖 Cómo leer la tabla de heterogeneidad (paso a paso)**
>
> Esta tabla divide la muestra en subgrupos para ver si el efecto de la alcaldesa
> varía por tamaño o tipo de municipio.
>
> **Columnas clave:**
> | Columna | Significado |
> |---------|-------------|
> | Dimensión | Variable de corte (tipo de población o tercil) |
> | Grupo | Categoría específica dentro de la dimensión |
> | $\hat{\beta}$ | Efecto estimado para ese subgrupo |
> | SE | Error estándar clusterizado |
> | p-valor | Significancia individual (sin ajustar) |
> | q-value (BH) | p-valor ajustado por Benjamini-Hochberg para pruebas múltiples |
>
> **Paso 1 — Identifica el grupo "ganador" aparente:**
> Metrópoli tiene $\hat{\beta}=0.030$** con $p=0.024$ → parece significativo al 5%.
>
> **Paso 2 — Aplica la corrección por pruebas múltiples:**
> Estamos probando 9 subgrupos simultáneamente. Sin corregir, esperaríamos
> ~0.45 falsos positivos al 5%. La columna **q-value (BH)** corrige esto:
> Metrópoli pasa de $p=0.024$ a $q=0.215$ → **no significativo** al 10%.
>
> **Paso 3 — Revisa el patrón general:**
> - Rural: $\hat{\beta}=-0.104$ (negativo, grande) pero $p=0.109$ → no significativo.
> - Semi-urbano, Urbano, Semi-metrópoli: $\hat{\beta}$ ≈ 0 → sin efecto.
> - Los terciles de población muestran el mismo patrón: nada sobrevive.
>
> **Paso 4 — Interpreta el q-value:**
> El q-value es la "tasa de falsos descubrimientos" esperada si rechazaras
> esa hipótesis y todas con q menor. Con $q=0.215$, rechazar implicaría
> aceptar un ~22% de falsos positivos — demasiado alto.
>
> **Lectura rápida:** Ningún subgrupo muestra efecto significativo tras
> corrección FDR. El efecto nominal en Metrópoli ($p=0.024$) es un probable
> falso positivo. No hay heterogeneidad robusta.

---

## 8. Stacked Difference-in-Differences (DiD Moderno)

### 8.1 Motivación

Dado que el tratamiento presenta adopción escalonada (15 cohortes entre 2018Q3 y
2022Q3. Se excluyen los 294 municipios con $g=0$ (left-censored)
left-censored sin periodo pre-tratamiento), el $\hat{\beta}_{\text{TWFE}}$ puede
sufrir sesgos por comparaciones contaminadas (Goodman-Bacon 2021). Se recomienda como extensión futura implementar un Stacked DiD (Cengiz, Dube, Lindner & Zipperer
2019) elimina estas comparaciones.

Como hay adopción escalonada y potencial heterogeneidad temporal en el efecto del
tratamiento, el TWFE puede generar ponderaciones no convexas que atenúen o reviertan
el signo del efecto estimado; por eso se recomienda implementar el Stacked DiD como **extensión futura de robustez
principal** del TWFE convencional.

### 8.2 Especificación

Para cada cohorte $g$, se construye un sub-dataset con:
- Municipios tratados de esa cohorte + municipios **never-treated** (1,476)
- Ventana temporal: $[g - 4, g + 8]$ trimestres

Se apilan los 15 sub-datasets y se estima:

$$Y_{i,t,g} = \alpha_{i \times g} + \gamma_{t \times g} + \beta \cdot D_{i,t,g} + \varepsilon_{i,t,g}$$

| Componente | Implementación |
|-----------|----------------|
| Efectos fijos | Municipio×stack ($\alpha_{i \times g}$) + periodo×stack ($\gamma_{t \times g}$) |
| Cluster SE | **Municipio original** (`cve_mun`, ~2,471 clusters), no `mun_stack` |
| Grupo de control | Solo never-treated (1,476 municipios) |
| Ventana | $[-4, +8]$ trimestres alrededor del evento |

**Nota sobre clustering:** Cada municipio aparece en múltiples stacks. Clusterizar
por `mun_stack` (entidad×stack) inflaría artificialmente el número de clusters
($\sim$37,000 vs $\sim$2,471) y subestimaría los errores estándar. Se clusteriza por
el municipio original (`cve_mun`) mediante el argumento `clusters` de `PanelOLS.fit()`.

### 8.3 ATT dinámico

$$Y_{i,t,g} = \alpha_{i \times g} + \gamma_{t \times g} + \sum_{k \neq -1} \delta_k \cdot \mathbf{1}\{\text{event\_time} = k\} + \varepsilon_{i,t,g}$$

Solo los municipios de la cohorte tratada contribuyen a las dummies de event-time;
los never-treated tienen todas las dummies $= 0$.

### 8.4 Pipeline

```bash
# (Stacked DiD: extensión futura — ver docs/17_RESULTADOS_EMPIRICOS.md §4.6)
```

# Outputs del Stacked DiD se generarían tras implementar la extensión.



---

## 9. Variables excluidas por leakage

| Variable | Razón | Aparece en algún modelo |
|----------|-------|:----------------------:|
| `alcaldesa_final_f1`, `f2`, `f3` | Leads — información futura | Solo event study (como dummies diagnósticas) |
| `alcaldesa_final_l1`, `l2`, `l3` | Lags — post-tratamiento | Solo event study (como dummies post) |
| `alcaldesa_transition` | Endógena | No |
| `alcaldesa_transition_gender` | Endógena | No |
| `alcaldesa`, `alcaldesa_end` | Sin imputar (NULLs) | No |
| `ever_alcaldesa` | Absorbida por FE municipio | No (sí en descriptivos) |
| `saldoprom_*` (56 cols) | NULLs estructurales ÷0 | No extraídas |
| Outcomes `_t` (totales) | Endógeno (incluye mujeres) | No extraídos |
| Outcomes `_h` como controles | Bad control | Solo placebo género |

---

## 10. Criterios para interpretar resultados

### Resultado nulo — ¿qué significa?

1. **Poder estadístico:** Con 600 switchers efectivos (de 894 totales) y 17 trimestres, el diseño podría ser
   insuficiente para detectar efectos pequeños. Un cálculo de poder post-hoc ayudaría
   a cuantificar el MDE (Minimum Detectable Effect).

2. **Mecanismo temporal:** El efecto de una alcaldesa sobre inclusión financiera
   podría requerir más de 8 trimestres para materializarse (acción institucional
   es lenta).

3. **Heterogeneidad TWFE:** Bajo efectos heterogéneos, el $\hat{\beta}_{TWFE}$ puede
   ser un promedio mal ponderado (Goodman-Bacon). Recomendación: estimar C&S como
   extensión.

4. **Escala municipal:** Los outcomes financieros están determinados principalmente
   por el sistema bancario (federal), no por gobiernos municipales. El canal causal
   plausible (programas de educación financiera, apoyos locales) podría ser muy
   pequeño relativo a la variación total.

---

## 11. Pipeline de reproducción

```bash
cd <raíz del repo>
source .venv/bin/activate

# 1. Descriptivos
python src/models/01_table1_descriptives.py

# 2. TWFE baseline
python src/models/02_twfe.py

# 3. Event study
python src/models/03_event_study.py

# 4. Robustez
python src/models/04_robustness.py

# 5. Heterogeneidad
python src/models/05_heterogeneity.py

# 6. Stacked DiD (DiD Moderno)
# (Stacked DiD: extensión futura — ver docs/17_RESULTADOS_EMPIRICOS.md §4.6)
```

Dependencias: `pandas`, `numpy`, `linearmodels`, `statsmodels`, `matplotlib`, `scipy`, `pyarrow`, `jinja2`.
