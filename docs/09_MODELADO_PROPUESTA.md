> **Archivos fuente:**
> - `src/transformaciones_criticas.py`
> - `src/transformaciones_altas.py`
> - `src/transformaciones_medias.py`
> - `src/models/01_table1_descriptives.py`
> - `src/models/02_twfe.py`
> - `src/models/03_event_study.py`
> - `src/models/04_robustness.py`
> - `src/models/05_heterogeneity.py`

# Propuesta de Modelado Econométrico

**Documento de trabajo — Tesis doctoral**  
**Fecha:** Febrero 2026  
**Fuente de datos:** `inclusion_financiera_clean` (41,905 obs = 2,471 municipios × 17 trimestres, 348 columnas)

---

## 1. Objetivo y estrategia de identificación

### 1.1 Pregunta de investigación

> ¿Cuál es el efecto causal de la representación política femenina a nivel municipal
> (alcaldesas) sobre la inclusión financiera de las mujeres en México?

### 1.2 Contexto empírico

El panel cubre el periodo 2018Q3–2022Q3 y contiene 2,471 municipios mexicanos observados
trimestralmente. El tratamiento es binario: `alcaldesa_final = 1` si la autoridad
municipal es mujer en el trimestre $t$. Existen 894 municipios "switchers" que cambian
de estatus al menos una vez durante el panel. De estos, **600 tienen periodo pre-tratamiento**
(`first_treat_t > 0`) y son los que identifican el efecto causal; los 294 restantes
están left-censored (`first_treat_t = 0`, ya tenían alcaldesa en 2018Q3) y se excluyen
del event study y Stacked DiD. Dos grandes cohortes de entrada están alineadas con
los ciclos electorales municipales (2018Q4 y 2021Q4).

### 1.3 Estrategia de identificación

Se emplea un diseño de **diferencias en diferencias (DiD)** con datos de panel,
explotando la variación within-municipality en el estatus de tratamiento a lo largo
del tiempo. La especificación base es un modelo **Two-Way Fixed Effects (TWFE)** con
efectos fijos de municipio (absorben heterogeneidad no observada time-invariant) y
efectos fijos de periodo (absorben shocks agregados comunes).

La identificación descansa en el **supuesto de tendencias paralelas**: en ausencia de
tratamiento, los municipios que reciben una alcaldesa habrían seguido la misma trayectoria
en inclusión financiera que los municipios que no la reciben. Este supuesto se evalúa
empíricamente mediante un **event study** que estima coeficientes pre-tratamiento
(leads).

### 1.4 Mapa de decisiones

```
¿Tendencias paralelas se sostienen? (event study pre-trends)
├── SÍ → Proceder con TWFE como especificación principal
│   └── ¿Resultados robustos a estimadores modernos (Callaway-Sant'Anna)?
│       ├── SÍ → Reportar TWFE como principal, C&S como robustez
│       └── NO → Investigar heterogeneidad de efectos; reportar C&S como principal
└── NO → Pre-trends significativos
    ├── ¿El patrón sugiere anticipación (sólo lead -1)?
    │   └── SÍ → Recodificar tratamiento con anticipación; re-estimar
    └── ¿Violación sistemática (leads -2, -3 significativos)?
        └── SÍ → La estrategia DiD no es válida; considerar alternativas
            ├── Controles time-varying + tendencias lineales específicas por grupo
            └── Matching + DiD (restringir a municipios comparables)
```

**Por qué importa:** Sin una estrategia de identificación creíble, los resultados no
tienen interpretación causal. El mapa de decisiones garantiza que cada contingencia
tiene un plan de acción explícito.

---

## 2. Construcción de variables (tratamiento, outcomes, escalas)

### 2.1 Variable de tratamiento

| Variable | Definición | Uso |
|----------|-----------|-----|
| `alcaldesa_final` | $D_{it} \in \{0,1\}$; 1 si el municipio $i$ tiene alcaldesa en $t$ | **Tratamiento principal** |
| `alcaldesa_acumulado` | $\sum_{s \leq t} D_{is}$; trimestres acumulados con alcaldesa | Robustez: dosis-respuesta |
| `ever_alcaldesa` | $\max_t D_{it}$; 1 si el municipio tuvo alcaldesa alguna vez | Balance y descriptivos. **No usar como interacción** con $D_{it}$ (ver nota abajo) |

> **Alerta de colinealidad (verificada marzo 2026):** $D_{it} \times \text{ever\_alcaldesa}_i \equiv D_{it}$, porque cuando $D_{it}=1$ necesariamente $\text{ever}_i=1$. PanelOLS lanza `AbsorbingEffectError`. Para heterogeneidad, usar variables independientes del tratamiento: `log_pob`, `early_cohort`, `high_baseline`. Ver `docs/04_EDA_EXPLICACION_3.md` §15.1.

**Distribución del tratamiento:**

| Grupo | Municipios | % |
|-------|-----------|---|
| Never-treated ($D_{it} = 0\ \forall\ t$) | 1,476 | 59.7% |
| Switchers (cambian al menos una vez) | 894 (600 con pre-periodo) | 36.2% |
| Always-treated ($D_{it} = 1$ desde 2018Q3) | 101 | 4.1% |

> **Nota sobre la cohorte 2018Q3 (394 municipios):** De estos, 101 son always-treated
> puros ($D_{it}=1$ todo el panel). Los otros 294 son **switchers left-censored**:
> empezaron con alcaldesa pero la pierden en algún momento. Estos 294 tienen
> `first_treat_t = 0` y **cero periodos pre-tratamiento**, por lo que se excluyen
> del event study y del Stacked DiD. Solo los **600 switchers con `first_treat_t > 0`**
> contribuyen a la identificación causal.

**Cohortes de entrada (periodo de primer tratamiento):**

| Cohorte | Municipios | Notas |
|---------|-----------|----------|
| 2018Q3 (g=0) | 294 switchers + 101 always | **Left-censored — excluidos del DiD** (sin pre-periodo) |
| 2018Q4 | 234 | Tomas de posesión tardías — cohorte más grande |
| 2019Q1–2021Q3 | 120 | Entradas esporádicas (interinos, reelecciones) |
| 2021Q4 | 163 | Ciclo electoral 2021 |
| 2022Q1–Q3 | 84 | Tomas de posesión tardías ciclo 2021 |

### 2.2 Variables a EXCLUIR por leakage o endogeneidad

Las siguientes variables están disponibles en la tabla pero **NO deben incluirse como
controles** en las regresiones porque incorporan información futura o son funciones
directas del tratamiento:

| Variable | Razón de exclusión |
|----------|-------------------|
| `alcaldesa_final_f1`, `_f2`, `_f3` | **Leads del tratamiento** — contienen información del futuro; su inclusión como controles sesga el estimador $\hat{\beta}$ |
| `alcaldesa_final_l1`, `_l2`, `_l3` | **Lags del tratamiento** — son post-tratamiento; no incluir como controles |

> **Regla general para leads y lags:** Las variables `_f1`–`_f3` y `_l1`–`_l3` se usarán
> **exclusivamente** en la especificación de event study (Sección 4) y en placebos
> temporales (R6). Nunca como controles en el modelo base TWFE ni en robustez.
| `alcaldesa_transition` | **Endógena** — es consecuencia del proceso de tratamiento |
| `alcaldesa_transition_gender` | **Endógena** — función del tratamiento |
| `alcaldesa`, `alcaldesa_end` | Variantes sin imputar; contienen NULLs; usar sólo `alcaldesa_final` |
| `alcaldesa_excl_trans`, `*_excl_trans_l*` | Variantes que anulan tratamiento en transiciones; usar como robustez, no como principal |
| `ever_alcaldesa` | Absorbido por el FE de municipio (time-invariant); además $D \times \text{ever} \equiv D$ → colinealidad perfecta si se usa como interacción |
| `alcaldesa_acumulado` | Post-tratamiento si se usa como control (sí como tratamiento alternativo) |
| Variables `saldoprom_*` (28 cols) | 60-100% NULLs estructurales (÷0); no aptos como outcomes ni controles. **Nota:** las variables `saldocont_*` (saldo total de contratos) sí son válidas como outcomes — tienen 0% NULLs. No confundir `saldoprom` (saldo promedio = saldo/contratos, indefinido cuando contratos = 0) con `saldocont` (saldo total, siempre definido) |

### 2.3 Outcomes core

Los outcomes principales capturan la inclusión financiera de las mujeres (`_m`),
normalizados per cápita por población adulta femenina ($\times$ 10,000).

**Outcomes primarios (variable dependiente en especificaciones principales):**

| # | Variable base | Versiones disponibles | Interpretación |
|---|--------------|----------------------|----------------|
| Y1 | `ncont_total_m_pc` | `_pc`, `_pc_w`, `_pc_asinh` | Contratos totales de mujeres (por 10k mujeres adultas) |
| Y2 | `numtar_deb_m_pc` | `_pc`, `_pc_w`, `_pc_asinh` | Tarjetas de débito de mujeres |
| Y3 | `numtar_cred_m_pc` | `_pc`, `_pc_w`, `_pc_asinh` | Tarjetas de crédito de mujeres |
| Y4 | `numcontcred_hip_m_pc` | `_pc`, `_pc_w`, `_pc_asinh` | Créditos hipotecarios de mujeres |
| Y5 | `saldocont_total_m_pc` | `_pc`, `_pc_w`, `_pc_asinh` | Saldo total de contratos de mujeres |

**Outcomes secundarios (análisis complementario):**

| # | Variable base | Interpretación |
|---|--------------|----------------|
| Y6 | `ncont_ahorro_m_pc` | Contratos de ahorro mujeres |
| Y7 | `ratio_mh_ncont_total` | Brecha de género en contratos (M/H); >1 = mujeres > hombres |
| Y8 | `ratio_mh_numtar_deb` | Brecha de género en tarjetas de débito |
| Y9 | `ratio_mh_numtar_cred` | Brecha de género en tarjetas de crédito |

### 2.4 Escalas de la variable dependiente

| Escala | Sufijo | Fórmula | Uso |
|--------|--------|---------|-----|
| **Nivel per cápita** | `_pc` | $Y / \text{pob\_adulta} \times 10{,}000$ | Referencia; difícil de interpretar si hay outliers |
| **Winsorizada** | `_pc_w` | $\text{clip}(Y_{pc},\ p_1,\ p_{99})$ | Robustez: limita influencia de extremos |
| **asinh** | `_pc_asinh` | $\text{asinh}(Y_{pc}) = \ln(Y_{pc} + \sqrt{Y_{pc}^2 + 1})$ | **Especificación principal recomendada**; maneja ceros, coefs ≈ semi-elasticidades |

**Justificación de asinh como escala principal:** Las distribuciones per cápita son
extremadamente sesgadas (ratio media/mediana de 6× en conteos y 390× en saldos).
La transformación asinh (Bellemare & Wichman 2020) comprime la distribución, es monotónica
y diferenciable, y —a diferencia de $\log(Y+1)$— no introduce sesgo cuando los valores
son pequeños. Los coeficientes se interpretan como cambios porcentuales aproximados para
$Y$ grandes.

> **Verificación empírica (marzo 2026):** Se ejecutaron tests R6 (`_pc_w` en nivel) y
> R7 (`_pc` cruda) en `robustness.py`. Resultados: las especificaciones en nivel son
> **inestables** — signos inconsistentes entre outcomes, magnitudes dominadas por outliers
> metropolitanos. En contraste, asinh (baseline), log1p (R1) y winsor+asinh (R2) dan
> coeficientes consistentes en signo y magnitud ($\hat{\beta} \approx +0.005$ a $+0.008$).
> **Conclusión:** asinh confirmado como especificación principal; nivel va al apéndice.
> Detalles en `docs/05_EDA_EXPLICACION_4.md` §11.9.

### 2.5 Controles permitidos (y justificación)

Principio rector: **sólo incluir controles que sean pre-determinados o exógenos al
tratamiento** (Angrist & Pischke 2009, Cap. 3). Evitar "bad controls" que sean outcomes
potenciales del tratamiento.

| Control | Tipo | Justificación |
|---------|------|---------------|
| `log_pob` (o `log_pob_adulta`) | Predeterminada / lenta | Controla escala municipal. La población en el panel proviene de proyecciones intercensales (CONAPO) y cambia lentamente entre trimestres — se trata como predeterminada respecto al tratamiento (la alcaldesa no altera la población municipal en el corto plazo) |
| `tipo_pob` | Time-invariant | Absorbido por FE municipio; útil sólo para interacciones de heterogeneidad |
| FE municipio ($\alpha_i$) | Fijo | Absorbe toda heterogeneidad time-invariant (geografía, cultura, instituciones) |
| FE periodo ($\gamma_t$) | Fijo | Absorbe shocks agregados (política monetaria, COVID-19, regulación CNBV) |

**Controles que NO se incluyen:**

| Variable | Razón |
|----------|-------|
| Outcomes masculinos (`_h`) como controles | Bad control: podrían ser afectados por el tratamiento (spillover intra-hogar) |
| PIB municipal / ingreso | No disponible trimestralmente; además, potencialmente endógeno |
| Indicadores financieros totales (`_t`) | Incluyen el outcome femenino; mecánicamente endógenos |
| `pob_adulta_m` en nivel | Usar la versión log; el nivel tiene distribución muy sesgada |

**Por qué importa:** Incluir bad controls sesga $\hat{\beta}$ y destruye la
interpretación causal. Menos controles correctos es preferible a muchos controles
endógenos.

---

## 3. Modelo base (TWFE): ecuación, interpretación, supuestos

### 3.1 Ecuación

$$
Y_{it} = \alpha_i + \gamma_t + \beta \cdot D_{it} + \mathbf{X}_{it}'\boldsymbol{\delta} + \varepsilon_{it}
$$

donde:
- $Y_{it}$: outcome de inclusión financiera (escala asinh) del municipio $i$ en el trimestre $t$
- $\alpha_i$: efecto fijo de municipio (2,471 dummies)
- $\gamma_t$: efecto fijo de periodo (17 dummies)
- $D_{it}$: `alcaldesa_final` $\in \{0, 1\}$
- $\mathbf{X}_{it}$: vector de controles (inicialmente sólo `log_pob`)
- $\varepsilon_{it}$: término de error idiosincrático
- $\beta$: **parámetro de interés** — efecto promedio TWFE del tratamiento. *Nota:* bajo adopción escalonada con efectos heterogéneos, $\hat{\beta}_{\text{TWFE}}$ es un promedio ponderado de efectos específicos por cohorte con pesos potencialmente no convexos (Goodman-Bacon 2021). Se reserva el término ATT (Average Treatment effect on the Treated) para los estimadores que lo recuperan formalmente: Callaway & Sant'Anna (2021) y Sun & Abraham (2021)

### 3.2 Inferencia

Errores estándar **clusterizados a nivel municipio** para permitir correlación serial
arbitraria dentro de cada unidad:

$$
\widehat{V}(\hat{\beta}) = (X'X)^{-1} \left( \sum_{i=1}^{N} \hat{u}_i' \hat{u}_i \right) (X'X)^{-1}
$$

donde la suma es sobre los $N = 2{,}471$ clusters (municipios).

**Justificación del clustering:** El tratamiento (`alcaldesa_final`) varía a nivel
municipio-periodo, y es altamente persistente dentro de cada municipio (correlación serial
del tratamiento). Bertrand, Duflo & Mullainathan (2004) demuestran que ignorar esta
correlación infla el rechazo del test hasta 45%.

### 3.3 Interpretación de $\hat{\beta}$

- Si $Y_{it}$ está en escala asinh: $\hat{\beta} \approx$ cambio porcentual en el
  outcome asociado a tener una alcaldesa (semi-elasticidad para valores grandes de $Y$).
- Si $Y_{it}$ está en nivel per cápita: $\hat{\beta}$ = cambio en contratos/saldos por
  cada 10,000 mujeres adultas.
- Signo esperado: $\hat{\beta} > 0$ si las alcaldesas incrementan la inclusión financiera
  femenina.

### 3.4 Supuestos de identificación

| # | Supuesto | ¿Testeable? | Prueba |
|---|----------|-------------|--------|
| S1 | **Tendencias paralelas** — En ausencia de tratamiento, $E[Y_{it}(0) \mid D_{it}=1] - E[Y_{it}(0) \mid D_{it}=0]$ es constante en $t$ | Parcialmente | Event study: coeficientes pre-tratamiento ≈ 0 |
| S2 | **No anticipación** — El tratamiento no afecta outcomes antes de su implementación | Parcialmente | Lead $k = -1$ en event study ≈ 0 |
| S3 | **SUTVA** — No hay spillovers entre municipios | No directamente | Placebo geográfico; sensibilidad exploratoria con municipios vecinos si se dispone de shapefile de contigüidad (Marco Geoestadístico INEGI) |
| S4 | **Exogeneidad del tratamiento (condicional)** — La elección de alcaldesa no es causada por la inclusión financiera | Por diseño | El tratamiento es resultado electoral; argumentar que la IF municipal no determina el género del alcalde electo |
| S5 | **Homogeneidad del efecto** (sólo TWFE clásico) — El efecto es constante entre cohortes y periodos | Testeable | Comparar TWFE vs. Callaway-Sant'Anna / Sun-Abraham |

### 3.5 Mapa de decisiones — Violaciones de supuestos

```
S1 violado (pre-trends significativos):
  → Si sólo lead -1: efecto de anticipación → ajustar timing del tratamiento
  → Si leads -2, -3: violación fundamental → abandonar DiD para ese outcome
  → Si patrón pre-trend lineal: agregar trend linear municipio-específico (cautela)

S5 violado (heterogeneidad de efectos entre cohortes):
  → TWFE reporta un promedio ponderado potencialmente negativo (Goodman-Bacon 2021)
  → Solución: usar Callaway & Sant'Anna (2021) como estimador principal
```

**Por qué importa:** El TWFE con adopción escalonada y efectos heterogéneos puede
producir un $\hat{\beta}$ sesgado, incluso de signo contrario al efecto verdadero.
Diagnosticar S5 es tan importante como diagnosticar S1.

---

## 4. Diagnóstico: tendencias paralelas y pre-trends (event study)

### 4.1 Ecuación del event study

$$
Y_{it} = \alpha_i + \gamma_t + \sum_{\substack{k = -K \\ k \neq -1}}^{L} \mu_k \cdot \mathbf{1}\{t - g_i = k\} + \mathbf{X}_{it}'\boldsymbol{\delta} + \varepsilon_{it}
$$

donde:
- $g_i$: periodo de primer tratamiento del municipio $i$ (cohort entry date)
- $k = t - g_i$: tiempo relativo al tratamiento (negativo = pre, positivo = post)
- $\mu_k$: efecto del tratamiento $k$ periodos después (o antes) de la adopción
- $k = -1$: **periodo de referencia** (normalizado a 0)
- $K$: número máximo de leads (pre-tratamiento); $L$: número máximo de lags (post-tratamiento)

### 4.2 Parámetros del event study

| Parámetro | Valor propuesto | Justificación |
|-----------|----------------|---------------|
| $K$ (leads) | 4 | Máximo leads disponibles dado el panel (17 trimestres) |
| $L$ (lags) | 8 | Captura efectos hasta 2 años post-tratamiento |
| Periodo base | $k = -1$ | Estándar; el trimestre inmediatamente anterior al tratamiento |
| Endpoint binning | Sí | Acumular $k \leq -K$ y $k \geq L$ en bins extremos |
| Muestra | Excluir always-treated (sin pre-period) | Los 394 municipios tratados desde 2018Q3 no tienen periodos pre |
| Grupo de control | **TWFE/event study clásico:** not-yet-treated (unidades aún sin tratamiento en $t$) actúan implícitamente como controles junto con los never-treated. **Callaway & Sant'Anna:** control principal = never-treated exclusivamente; robustez con not-yet-treated | Usar never-treated como control es más conservador y evita sesgo por retroalimentación del tratamiento futuro; not-yet-treated aumenta potencia pero introduce riesgo si hay anticipación |

### 4.3 Interpretación

- **Validación de tendencias paralelas:** Si $\hat{\mu}_k \approx 0$ para $k < -1$
  (no significativos individual y conjuntamente), el supuesto S1 se sostiene.
- **Dinámica del efecto:** Los $\hat{\mu}_k$ para $k \geq 0$ muestran cómo evoluciona
  el efecto tras la adopción. Un efecto creciente sugiere acumulación; un efecto
  decreciente sugiere disipación.
- **Test conjunto de pre-trends:** $H_0: \mu_{-K} = \mu_{-K+1} = \cdots = \mu_{-2} = 0$
  (F-test o Wald test).

### 4.4 Decisiones condicionales a resultados

| Resultado del event study | Acción |
|---------------------------|--------|
| Pre-trends ≈ 0 (individual y conjuntamente) | Proceder con TWFE; reportar event study como Figura 1 |
| Un pre-trend marginalmente significativo ($p < 0.10$) | Reportar con nota; verificar robustez a ventana $K$ |
| Pre-trends significativos y crecientes | Explorar covariates + tendencia lineal por municipio; si persiste, la estrategia DiD es débil para ese outcome |
| Efecto post plano ($\mu_0 \approx \mu_1 \approx \cdots$) | Consistente con efecto instantáneo y persistente; TWFE es la especificación correcta |
| Efecto post creciente ($\mu_k$ crece con $k$) | Efecto acumulativo; considerar `alcaldesa_acumulado` como tratamiento |

**Por qué importa:** El event study es la prueba diagnóstica más importante del diseño.
Sin evidencia de tendencias paralelas, el coeficiente $\hat{\beta}$ del TWFE no tiene
interpretación causal.

---

## 5. Robustez y sensibilidad

### 5.1 Lista de pruebas de robustez

| # | Prueba | Especificación | Justificación |
|---|--------|---------------|---------------|
| R1 | **Escala del outcome** | $Y_{pc,\text{asinh}}$ (principal), $Y_{pc,w}$ + asinh (R2 código), $\log(1+Y_{pc})$ (R1 código), $Y_{pc,w}$ nivel (R6 código), $Y_{pc}$ nivel (R7 código) | Verificar que resultados no dependen de la transformación. **Resultado (marzo 2026):** Las 3 transformaciones funcionales (asinh, winsor+asinh, log1p) son consistentes ($\hat{\beta} \approx +0.005$ a $+0.008$). Las especificaciones en nivel son inestables → apéndice |
| R2 | **Excluir transiciones** | Usar `alcaldesa_excl_trans` (NULL en trimestres de transición) | Los trimestres de cambio de gobierno pueden tener efectos mecánicos; excluirlos descarta contaminación |
| R3 | **Incluir transiciones (base)** | Usar `alcaldesa_final` en todos los trimestres | Maximiza potencia; si R2 ≈ R3, las transiciones no distorsionan |
| R4 | **Estimador moderno DiD** | Callaway & Sant'Anna (2021) con never-treated como control | Robusto a efectos heterogéneos entre cohortes; no sufre el sesgo de TWFE bajo staggered adoption |
| R5 | **Sun & Abraham (2021)** | IW-estimator con dummies de cohorte × tiempo relativo | Alternativa a C&S; usa mismos datos pero diferente framework |
| R6 | **Placebo temporal** | Asignar tratamiento falso 4 trimestres antes del real; re-estimar | Si $\hat{\beta}_{\text{placebo}} \neq 0$, hay pre-trends ocultos |
| R7 | **Placebo de género** | Estimar mismo modelo con outcome masculino (`ncont_total_h_pc_asinh`) | Si el "efecto" aparece también en hombres, no es específico a mujeres. Interpretación: un efecto positivo en outcomes masculinos no invalida automáticamente la identificación — puede reflejar un efecto general de gobernanza/gestión municipal sobre la IF, no un sesgo. En ese caso, los outcomes de brecha de género (Y7–Y9: `ratio_mh_*`) son el test más informativo de un efecto *diferencial* sobre mujeres |
| R8 | **Excluir always-treated** | Restringir muestra a switchers + never-treated | Los always-treated contribuyen sólo a la variación between, no within; verificar estabilidad |
| R9 | **Tratamiento continuo** | Reemplazar $D_{it}$ por `alcaldesa_acumulado` | ¿El efecto es proporcional a la duración de exposición? |
| R10 | **Winsorización extrema** | Acotar outcomes al p5–p95 | ¿Los resultados sobreviven a una compresión más agresiva de outliers? |
| R11 | **Wild cluster bootstrap** | Cameron, Gelbach & Miller (2008) | Inferencia válida con pocos clusters tratados en alguna cohorte |

### 5.2 Priorización

- **Imprescindibles (reportar siempre):** R1, R2/R3, R4, R7
- **Recomendadas:** R5, R6, R8
- **Opcionales (apéndice):** R9, R10, R11

### 5.3 Mapa de decisiones — Resultados divergentes

```
TWFE ≈ Callaway-Sant'Anna:
  → Efectos homogéneos; TWFE es eficiente → reportar TWFE como principal

TWFE ≠ Callaway-Sant'Anna:
  → Heterogeneidad de efectos entre cohortes
  → Reportar C&S como principal, TWFE en apéndice
  → Descomponer: ¿qué cohorte impulsa la diferencia?

Placebo de género significativo:
  → El efecto no es exclusivo de mujeres, pero no necesariamente invalida la tesis
  → Distinguir: efecto de gobernanza general vs. efecto diferencial de género
  → Si β_hombres ≈ β_mujeres → efecto general; analizar ratio M/H (Y7–Y9)
  → Si β_hombres < β_mujeres → efecto diferencial a favor de mujeres (hallazgo válido)
  → Si β_hombres > β_mujeres → resultado contrario a la hipótesis; documentar
```

**Por qué importa:** La robustez no es un trámite burocrático. Cada prueba responde a
una amenaza concreta a la validez interna. Si los resultados no sobreviven a R1–R4,
la conclusión principal es frágil.

---

## 6. Heterogeneidad

### 6.1 Dimensiones de heterogeneidad

| # | Dimensión | Variable | Cortes | Justificación |
|---|-----------|----------|--------|---------------|
| H1 | **Tamaño municipal** | `tipo_pob` | Rural vs. Semi-urbano+ | El efecto puede ser mayor en municipios rurales donde la IF femenina parte de niveles más bajos |
| H2 | **Región** | `cve_ent` (agrupada) | Norte / Centro / Sur-Sureste | Diferencias estructurales en instituciones financieras y brechas de género |
| H3 | **Intensidad de exposición** | `alcaldesa_acumulado` | Cuartiles (0, 1–3, 4–8, 9–17) | ¿El efecto es mayor con más trimestres de exposición acumulada? |
| H4 | **Producto financiero** | Outcome específico | Ahorro, débito, crédito, hipotecario | ¿La alcaldesa afecta más los productos de entrada (débito) o los sofisticados (hipotecas)? |

### 6.2 Método

Para cada dimensión, estimar el modelo base TWFE con interacción:

$$
Y_{it} = \alpha_i + \gamma_t + \beta_1 D_{it} + \beta_2 (D_{it} \times H_i) + \mathbf{X}_{it}'\boldsymbol{\delta} + \varepsilon_{it}
$$

donde $H_i$ es la variable de heterogeneidad (o una dummy por grupo). Para variables
time-invariant como `tipo_pob`, el efecto principal de $H_i$ es absorbido por $\alpha_i$.

### 6.3 Precauciones

- **No sobreajustar:** Limitar a máximo 4 dimensiones de heterogeneidad. Reportar
  correcciones por comparaciones múltiples (Bonferroni o Benjamini-Hochberg).
- **Pre-registrar:** Definir las dimensiones de heterogeneidad ex ante (en este
  documento) antes de ver los resultados.
- **Potencia estadística:** Con 600 switchers efectivos (excluyendo 294 left-censored), los subgrupos más pequeños
  (e.g., Metrópoli con 13 municipios) no tendrán potencia. Sólo reportar
  heterogeneidad donde el subgrupo tenga al menos ~100 switchers.
- **Colinealidad con el tratamiento:** No interactuar $D_{it}$ con variables que
  sean función de $D$ (como `ever_alcaldesa`). Si $H_i = f(D_{i\cdot})$, la
  interacción $D \times H$ puede ser colineal con $D$.

**Por qué importa:** Los análisis de heterogeneidad exploratoria sin disciplina
producen falsos positivos. Pre-especificar cortes y corregir por multiplicidad protege
la credibilidad del estudio.

### 6.4 Resultados preliminares de heterogeneidad (marzo 2026)

Se estimó $Y_{it} = \alpha_i + \gamma_t + \beta D_{it} + \theta (D_{it} \times H_i) + \delta \log\_\text{pob}_{it} + \varepsilon_{it}$ para 3 variables de interacción × 4 outcomes (excl. `saldocont_total_m` por ausencia en el panel analítico):

| Interacción ($H_i$) | Definición | Resultado |
|---------------------|------------|----------|
| $D \times \log\_\text{pob}$ | Tamaño municipal (continuo) | 0/4 significativos |
| $D \times \text{early\_cohort}$ | 1 si primer tratamiento ≤ 2018Q4 | 0/4 significativos |
| $D \times \text{high\_baseline}$ | 1 si `ncont_total_m_pc` pre-tto > mediana | 1/4 marginalmente sig. (tarjetas débito, $p < 0.10$) |

**Conclusión:** El efecto del tratamiento es **homogéneo** a lo largo de las dimensiones
testadas. Solo 1 de 12 interacciones alcanza significancia marginal, consistente con
falso positivo por azar ($1/12 \approx 8\%$, cercano al 10% de significancia nominal).
Ver `docs/04_EDA_EXPLICACION_3.md` §15.2 para los resultados completos.

> **Nota sobre $D \times \text{ever\_alcaldesa}$:** Esta interacción no es estimable
> porque $D_{it} = 1 \Rightarrow \text{ever}_i = 1$ por definición, lo que implica
> $D \times \text{ever} \equiv D$ (colinealidad perfecta). Se sustituyó por las 3
> interacciones arriba.

---

## 6B. Pre-analysis plan: outcomes y corrección por multiplicidad

Este mini pre-analysis plan fija, antes de ver los resultados, qué outcomes son
primarios y cómo se ajusta la inferencia por comparaciones múltiples.

### Outcomes primarios (familia 1)

Los 5 outcomes primarios (Y1–Y5) constituyen una **familia de hipótesis**. Se reportan
sin corrección, pero se acompaña de un **test conjunto** y de p-valores ajustados:

| Corrección | Método | Cuándo aplicar |
|------------|--------|----------------|
| Benjamini-Hochberg (FDR) | Controla la tasa de falsos descubrimientos al 5% | **Reporte principal** — balancea potencia y control de error tipo I |
| Bonferroni | $\alpha^* = 0.05 / 5 = 0.01$ por outcome | Robustez conservadora (apéndice) |
| Romano-Wolf (stepdown) | Remuestreo que respeta la correlación entre outcomes | Si los outcomes están muy correlacionados entre sí |

### Outcomes secundarios (familia 2)

Los 4 outcomes secundarios (Y6–Y9) se tratan como **exploratorios**. Se reportan con
p-valores nominales y la nota explícita: "estos resultados son exploratorios y no se
ajustan por comparaciones múltiples".

### Reglas de decisión pre-especificadas

1. Un outcome primario se considera con efecto significativo si $p_{\text{BH}} < 0.05$
   (Benjamini-Hochberg ajustado).
2. La conclusión principal de la tesis se basa en el **patrón conjunto** de Y1–Y5,
   no en un único outcome significativo.
3. Si sólo 1 de 5 outcomes primarios es significativo tras corrección BH, se interpreta
   como evidencia débil — no se declara "efecto causal de las alcaldesas".
4. Si ≥ 3 de 5 son significativos tras corrección BH, se interpreta como evidencia
   robusta.

**Por qué importa:** Sin pre-especificación de la familia de outcomes y la corrección
por multiplicidad, es fácil caer en cherry-picking. Fijar estas reglas antes de estimar
protege la credibilidad y es cada vez más exigido por journals de economía.

---

## 7. Check-list reproducible

Pasos numerados para ejecutar todo el análisis desde cero:

| Paso | Acción | Script / Comando | Output |
|------|--------|-----------------|--------|
| 1 | Regenerar tabla limpia | `python src/transformaciones_criticas.py` | `inclusion_financiera_clean` (223 cols) |
| 2 | Aplicar transformaciones altas | `python src/transformaciones_altas.py` | 296 cols |
| 3 | Aplicar transformaciones medias | `python src/transformaciones_medias.py` | 348 cols |
| 4 | Validar transformaciones | `python src/tests/test_criticas.py && python src/tests/test_altas.py && python src/tests/test_medias.py` | 43/43 tests ✓ |
| 5 | Construir muestra analítica | `python src/models/build_sample.py` | `outputs/paper/analytical_sample.parquet` |
| 6 | Tabla descriptiva (Tabla 1) | `python src/models/descriptives.py` | `outputs/paper/tabla_1_descriptiva.tex` |
| 7 | Modelo TWFE base (Tabla 2) | `python src/models/fit_twfe.py` | `outputs/paper/tabla_2_twfe.tex` |
| 8 | Event study (Figura 1) | `python src/models/event_study.py` | `outputs/paper/figura_1_event_study.pdf` |
| 9 | Tendencias agregadas (Figura 2) | `python src/models/plot_trends.py` | `outputs/paper/figura_2_tendencias.pdf` |
| 10 | Robustez (Tabla 3) | `python src/models/robustez.py` | `outputs/paper/tabla_3_robustez.tex` |
| 11 | Heterogeneidad | `python src/models/heterogeneidad.py` | `outputs/paper/tabla_4_heterogeneidad.tex` |
| 12 | Callaway-Sant'Anna | `python src/models/did_moderno.py` | `outputs/paper/tabla_5_cs.tex`, `outputs/paper/figura_3_cs_event.pdf` |
| 13 | Compilar resultados | `python src/models/compile_results.py` | Resumen en consola |

**Requisitos de entorno:**
```bash
cd <ruta_del_repo>   # raíz del repositorio Code/
source .venv/bin/activate
# Paquetes Python necesarios (además de los existentes):
pip install linearmodels pyfixest did2s csdid stargazer
# Opcional — sólo si se necesita exportar figuras en formato PGF/TikZ para LaTeX:
# pip install matplotlib-backend-pgf
```

**Por qué importa:** La reproducibilidad es un requisito mínimo de rigor científico. Cualquier
persona con acceso a la base de datos y este repositorio debe poder replicar todos los
resultados ejecutando los pasos 1–13.

---

## 8. Entregables y criterios de "listo para tesis"

### 8.1 Tablas principales

| Tabla | Contenido | Criterio de aceptación |
|-------|-----------|----------------------|
| **Tabla 1** — Descriptiva | Medias y desviaciones estándar de outcomes y tratamiento; columnas: (1) Full sample, (2) Never-treated, (3) Switchers, (4) Diferencia (3)−(2) | Balance razonable; diferencias documentadas y coherentes con el diseño |
| **Tabla 2** — TWFE base | 5 outcomes primarios (Y1–Y5) × 3 especificaciones: (a) sólo FE, (b) + `log_pob`, (c) + control adicional. $N$, $R^2$ within, clusters | Coeficientes estables entre especificaciones; SE clusterizados |
| **Tabla 3** — Robustez | Panel A: escalas funcionales (asinh, winsor+asinh, log1p — consistentes). Panel B: excluir transiciones. Panel C: placebos (temporal + género). Panel D (apéndice): escalas en nivel (_pc_w, _pc — inestables, justifican asinh). | Signos y magnitudes consistentes con Tabla 2 para Panels A–C |
| **Tabla 4** — Heterogeneidad | Interacciones con `tipo_pob` y cohorte de entrada | Diferencias económicamente plausibles; corrección por comparaciones múltiples |
| **Tabla 5** — Callaway-Sant'Anna | ATT por grupo y ATT agregado; comparación con TWFE | C&S ≈ TWFE → homogeneidad; C&S ≠ TWFE → reportar C&S como principal |

### 8.2 Figuras principales

| Figura | Contenido | Criterio de aceptación |
|--------|-----------|----------------------|
| **Figura 1** — Event study | Coeficientes $\hat{\mu}_k$ con IC 95%, $k \in [-4, +8]$, línea vertical en $k=0$ | Pre-trends ≈ 0; IC cruzan 0 para $k < 0$ |
| **Figura 2** — Tendencias agregadas | Medias trimestrales de outcome primario (Y1) para tratados vs. control | Tendencias visualmente paralelas pre-tratamiento; divergencia post |
| **Figura 3** — Event study C&S | Misma estructura que Figura 1, estimada con Callaway & Sant'Anna | Comparar con Figura 1; patrón similar refuerza la credibilidad |

### 8.3 Estructura de archivos

```
src/
├── models/
│   ├── build_sample.py       # Paso 5: extrae muestra, excluye leakage cols
│   ├── descriptives.py       # Paso 6: Tabla 1
│   ├── fit_twfe.py           # Paso 7: Tabla 2 (TWFE base)
│   ├── event_study.py        # Paso 8: Figura 1
│   ├── plot_trends.py        # Paso 9: Figura 2
│   ├── robustez.py           # Paso 10: Tabla 3
│   ├── heterogeneidad.py     # Paso 11: Tabla 4
│   ├── did_moderno.py        # Paso 12: Tabla 5 + Figura 3 (C&S / Sun-Abraham)
│   └── compile_results.py    # Paso 13: resumen
├── tests/
│   ├── test_criticas.py
│   ├── test_altas.py
│   └── test_medias.py
├── transformaciones_criticas.py
├── transformaciones_altas.py
└── transformaciones_medias.py

outputs/
└── paper/
    ├── analytical_sample.parquet
    ├── tabla_1_descriptiva.tex
    ├── tabla_2_twfe.tex
    ├── tabla_3_robustez.tex
    ├── tabla_4_heterogeneidad.tex
    ├── tabla_5_cs.tex
    ├── figura_1_event_study.pdf
    ├── figura_2_tendencias.pdf
    └── figura_3_cs_event.pdf

docs/
├── README.md
├── 01_BRIEF.md
├── 02–05_EDA_EXPLICACION*.md
├── 06_ANALISIS_DESCRIPTIVO_TESIS.md
├── 07_DATA_CONTRACT.md
├── 08_DATASET_CONSTRUCCION.md
├── 09_MODELADO_PROPUESTA.md    ← este documento
├── 10_EXPLICACION_MODELADO.md  ← guía tutorial de este documento
├── 11–14 (modelado, DiD, sensibilidad, MDES)
├── 15–16 (resultados, extensiones)
├── 17–18 (apéndice, bibliografía)
├── 21_ONE_PAGER_ASESOR.md
├── 22_CHECKLIST_DEFENSA.md
└── 23_FREEZE_RELEASE.md
```

### 8.4 Criterios de "listo para tesis"

Un resultado está listo para incluirse en el capítulo de resultados si y sólo si:

1. **Tendencias paralelas:** El event study no rechaza $H_0: \mu_{-K} = \cdots = \mu_{-2} = 0$ al 5%.
2. **Estabilidad:** El signo y la significancia de $\hat{\beta}$ se mantienen en al
   menos 3 de las 4 pruebas imprescindibles (R1, R2/R3, R4, R7).
3. **Placebo de género:** El efecto en outcomes masculinos es sustancialmente menor
   (o nulo) respecto al efecto en outcomes femeninos.
4. **Reproducibilidad:** Los scripts 1–13 se ejecutan sin errores y producen los
   mismos resultados.
5. **Documentación:** Cada tabla y figura tiene un archivo `.py` asociado y una
   descripción en este documento o en el capítulo de metodología.

**Por qué importa:** Definir los criterios de aceptación antes de ver los datos
protege contra la tentación de "buscar significancia". Si un resultado no cumple
los 5 criterios, se reporta como nulo o inconcluyente — lo cual es un hallazgo
legítimo.
