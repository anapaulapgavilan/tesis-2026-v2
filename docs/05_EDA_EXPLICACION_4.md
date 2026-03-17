> **Archivos fuente:**
> - `src/transformaciones_medias.py`

# EDA — Explicación 4: Resolución de Recomendaciones Medias (🟢)

**Continuación de:** `docs/02_EDA_EXPLICACION.md` (Secciones 1–10), `docs/03_EDA_EXPLICACION_2.md` (Sección 11) y `docs/04_EDA_EXPLICACION_3.md` (Secciones 12–15)  
**Fecha:** Febrero 2026  

---

## 16. Resolución de recomendaciones de prioridad media (🟢)

Las 3 recomendaciones marcadas como **🟢 MEDIA prioridad** en la Sección F del EDA
fueron implementadas sobre la tabla `inclusion_financiera_clean` (que ya contenía las
transformaciones críticas de la Sección 11 y las altas de la Sección 12).

### Tabla resultante

| Propiedad | Valor |
|-----------|-------|
| **Tabla original** | `inclusion_financiera` (175 columnas) — **intacta** |
| **Tabla limpia** | `inclusion_financiera_clean` (348 columnas) |
| **Filas** | 41,905 (sin cambios) |
| **Columnas nuevas (esta fase)** | +52 |
| **Acumulado desde original** | +173 columnas |

| Fase | Columnas añadidas | Total acumulado |
|------|-------------------|-----------------|
| Tabla original | — | 175 |
| + Críticas (Recs 1–4) | +51 per cápita, −3 constantes = +48 | 223 |
| + Altas (Recs 5–9) | +4 log + 51 winsor + 17 ratio + 1 ever = +73 | 296 |
| **+ Medias (Recs 10–12)** | **+1 acumulado + 51 asinh + 0 tipo_pob = +52** | **348** |

---

### Rec 10. Variable de intensidad de tratamiento (`alcaldesa_acumulado`)

#### 10.1 ¿Qué es la "intensidad de tratamiento" en econometría?

En un diseño estándar de diferencias en diferencias (DiD), el tratamiento es
**binario**: un municipio tiene alcaldesa ($D_{it} = 1$) o no ($D_{it} = 0$).
Pero el mundo real es más matizado. Un municipio que lleva 10 trimestres
consecutivos con alcaldesa ha experimentado una "dosis" de tratamiento mucho
mayor que uno que lleva apenas 1 trimestre. El indicador binario no distingue
entre ambos casos.

La **intensidad de tratamiento** generaliza el diseño binario a uno continuo.
Formalmente, definimos:

$$
\text{dose}_{it} = \sum_{s=t_0}^{t} D_{is}
$$

donde $t_0$ es el inicio del panel y $D_{is}$ es el indicador binario de
tratamiento del municipio $i$ en el periodo $s$. Esta variable:
- Vale **0** para municipios never-treated en todos los periodos
- **Crece monótonamente** dentro de cada municipio (la "dosis" solo puede
  acumularse, nunca reducirse)
- Alcanza un **máximo de $T$** (= 17 trimestres en nuestro panel) para
  municipios tratados en todos los periodos

#### 10.2 ¿Por qué usar tratamiento continuo además de binario?

La motivación viene de la literatura de **dosis-respuesta** (dose-response):

| Concepto | Tratamiento binario ($D_{it}$) | Tratamiento continuo ($\text{dose}_{it}$) |
|----------|-------------------------------|------------------------------------------|
| Pregunta que responde | "¿Tener alcaldesa hoy cambia el outcome?" | "¿Cada trimestre adicional con alcaldesa cambia el outcome?" |
| Parámetro estimado | ATT (efecto promedio sobre los tratados) | Efecto marginal de un trimestre adicional |
| Supuesto clave | Tendencias paralelas | Tendencias paralelas + linealidad en la dosis |
| Poder estadístico | Menor (solo usa variación 0/1) | Mayor (usa variación continua 0–17) |

En la práctica, usar ambas especificaciones aporta **robustez**: si el efecto
es real, debería aparecer tanto con el indicador binario como con la variable
de intensidad.

> **Nota para la defensa:** Un sinodal podría preguntar: *"¿Cómo sabemos que
> el efecto no se satura después de cierto número de trimestres?"* La variable
> `alcaldesa_acumulado` permite responder directamente: si la relación es
> cóncava (rendimientos decrecientes), un modelo cuadrático
> $Y_{it} = \beta_1 \cdot \text{dose}_{it} + \beta_2 \cdot \text{dose}_{it}^2 + \ldots$
> mostrará $\beta_2 < 0$.

#### 10.3 Implementación en Python

El código relevante de `src/transformaciones_medias.py` es:

```python
# Ordenar por municipio y tiempo para garantizar la suma acumulada correcta
df = df.sort_values(["cve_mun", "periodo_trimestre"]).reset_index(drop=True)

# Suma acumulada de alcaldesa_final dentro de cada municipio
df["alcaldesa_acumulado"] = df.groupby("cve_mun")["alcaldesa_final"].cumsum()
```

**Desglose línea por línea:**

1. **`sort_values(["cve_mun", "periodo_trimestre"])`** — Ordena el DataFrame
   primero por municipio y luego cronológicamente dentro de cada municipio.
   Esto es **crítico**: `cumsum()` opera sobre el orden de las filas, y si los
   datos no están ordenados cronológicamente, la suma acumulada sería incorrecta.

2. **`.reset_index(drop=True)`** — Resetea el índice para evitar problemas con
   índices duplicados después del ordenamiento. `drop=True` descarta el índice
   viejo en lugar de convertirlo en columna.

3. **`groupby("cve_mun")`** — Agrupa por municipio. Cada grupo contiene las 17
   observaciones trimestrales de un municipio.

4. **`["alcaldesa_final"].cumsum()`** — Dentro de cada grupo, calcula la suma
   acumulada del vector binario `alcaldesa_final`. En un vector
   `[1, 1, 1, 0, 0, 1, 1]`, el resultado es `[1, 2, 3, 3, 3, 4, 5]`.

> **¿Qué es `cumsum()`?** La función *cumulative sum* (suma acumulada) de pandas
> toma un vector $[x_1, x_2, \ldots, x_T]$ y devuelve
> $[x_1,\; x_1+x_2,\; x_1+x_2+x_3,\; \ldots,\; \sum_{s=1}^{T} x_s]$.
> Cuando el vector es binario (0s y 1s), el resultado es simplemente un
> **contador acumulado** de los 1s vistos hasta ese punto.

#### 10.4 Fórmula y estadísticas descriptivas

**Fórmula:**
$$
\text{alcaldesa\_acumulado}_{i,t} = \sum_{s \leq t} \text{alcaldesa\_final}_{i,s}
$$

**Estadísticas descriptivas:**

| Estadístico | Valor |
|-------------|-------|
| Media | 2.82 |
| Mediana | 0 |
| Máximo | 17 (todos los trimestres) |
| Mínimo | 0 |
| % con valor 0 | 69.3% |

La mediana de 0 refleja que la mayoría de las observaciones municipio-trimestre
corresponden a municipios que **nunca** han tenido alcaldesa hasta ese punto
(la distribución está fuertemente concentrada en 0).

#### 10.5 Ejemplo concreto — Municipio 1011 (switcher)

Un municipio *switcher* es aquel que cambia de estado de tratamiento a lo largo
del panel. El municipio 1011 ilustra cómo `alcaldesa_acumulado` captura la
historia completa de exposición:

| Periodo | `alcaldesa_final` | `alcaldesa_acumulado` | Interpretación |
|---------|-------------------|-----------------------|----------------|
| 2018Q3 | 1 | 1 | Primer trimestre con alcaldesa |
| 2018Q4 | 1 | 2 | Segundo consecutivo |
| 2019Q1 | 1 | 3 | Tercero consecutivo |
| 2019Q2 | 1 | 4 | Cuarto consecutivo |
| 2019Q3 | 1 | 5 | Quinto consecutivo |
| 2019Q4 | 0 | **5** | Cambio de gobierno → se queda en 5 |
| 2020Q1 | 0 | **5** | Sigue sin alcaldesa → se queda en 5 |
| … | 0 | **5** | La dosis acumulada no decrece |
| 2021Q4 | 1 | 6 | Nueva alcaldesa → retoma conteo |
| 2022Q1 | 1 | 7 | |
| 2022Q2 | 1 | 8 | |
| 2022Q3 | 1 | 9 | Total: 9 de 17 trimestres |

**Observa** que cuando `alcaldesa_final` vuelve a 0, el acumulado **no decrece**:
se mantiene en 5 durante todo el periodo sin alcaldesa. Esto captura la noción
de que la exposición pasada al tratamiento no se "deshace".

#### 10.6 Propiedades formales verificadas

| Propiedad | Verificación | ¿Por qué importa? |
|-----------|-------------|-------------------|
| **Monótona no-decreciente** | 0 violaciones en 41,905 obs | Garantiza coherencia temporal: la dosis nunca se pierde |
| **Máximo = 17** | Coincide con el total de trimestres en el panel | Validación de rango |
| **Ceros consistentes** | Todo `never_alcaldesa == 0` → `acumulado == 0` siempre | Grupo de control correctamente definido |
| **Sin valores negativos** | Mínimo = 0 | La suma acumulada de un binario no negativo no puede ser negativa |

#### 10.7 Interpretación en regresión

Cuando usamos `alcaldesa_acumulado` como variable de tratamiento en un modelo
de efectos fijos:

$$
Y_{it} = \alpha_i + \gamma_t + \beta \cdot \text{dose}_{it} + X_{it}'\delta + \varepsilon_{it}
$$

El coeficiente $\beta$ se interpreta como:

> **"Un trimestre adicional de exposición a una alcaldesa está asociado con un
> cambio de $\beta$ unidades en el outcome $Y$, controlando por efectos fijos
> de municipio y tiempo."**

Esto es diferente de la interpretación del $\beta$ binario, que dice "tener
alcaldesa *ahora* cambia $Y$ en $\beta$". La variable de intensidad responde
una pregunta más rica: **¿importa cuánto tiempo?**

#### 10.8 ¿Cuándo usar tratamiento binario vs. continuo?

| Situación | Usar binario ($D_{it}$) | Usar continuo ($\text{dose}_{it}$) |
|-----------|------------------------|------------------------------------|
| Especificación principal | ✓ (estándar en DiD) | |
| Robustez | | ✓ |
| Efectos dinámicos | Con event study | ✓ + término cuadrático |
| Rendimientos decrecientes | No puede capturar | ✓ ($\beta_1 > 0$, $\beta_2 < 0$) |
| Comparabilidad con literatura | ✓ | |

**Recomendación para la tesis:** Presentar la especificación binaria como
principal (para comparabilidad con la literatura de DiD) y la continua como
ejercicio de robustez en el apéndice.

---

### Rec 11. Transformación arcoseno hiperbólico inverso (asinh) de outcomes

#### 11.1 El problema: distribuciones extremadamente sesgadas con ceros

Antes de estimar cualquier modelo, necesitamos examinar la distribución de
nuestras variables dependientes. En inclusión financiera, estas distribuciones
tienen dos características problemáticas:

1. **Sesgo extremo (right-skewed):** Unos pocos municipios metropolitanos
   concentran una cantidad desproporcionada de productos financieros.
2. **Ceros genuinos:** Hay municipios (rurales, aislados) donde literalmente
   no hay presencia de ciertos productos. Estos ceros son **datos reales**,
   no valores perdidos.

| Variable | Media | Mediana | Ratio media/mediana | Interpretación |
|----------|-------|---------|---------------------|----------------|
| `ncont_total_m_pc` | 3,429.69 | 575.26 | 6× | Sesgo moderado |
| `saldocont_total_m_pc` | — | — | 390× | Sesgo extremo |

Cuando el ratio media/mediana es muy alto, los valores extremos dominan la
regresión. Un municipio como la CDMX puede tener más peso en el estimador
que cientos de municipios rurales.

#### 11.2 ¿Por qué no usar simplemente $\log(x)$?

La transformación logarítmica es la herramienta clásica para comprimir
distribuciones sesgadas. Pero tiene un problema fatal en nuestro caso:

$$
\log(0) = -\infty \qquad \text{(indefinido)}
$$

Si tenemos municipios con 0 contratos de ahorro para mujeres, el logaritmo
no está definido. Hay tres "parches" comunes, cada uno con problemas:

| Transformación | Problema principal |
|----------------|-------------------|
| $\log(x)$ | Indefinida en $x = 0$; perdemos observaciones |
| $\log(x + 1)$ | El "+1" es arbitrario y distorsiona según la escala |
| $\log(x + c)$ | ¿Qué valor elegimos para $c$? Resultados sensibles a la elección |

El problema de $\log(x + 1)$ merece explicación detallada. Considera dos
variables:
- Variable A con rango $[0,\ 0.01]$: el "+1" domina completamente → $\log(1.01) \approx 0.01$
- Variable B con rango $[0,\ 1{,}000{,}000]$: el "+1" es negligible → $\log(1{,}000{,}001) \approx \log(1{,}000{,}000)$

El "+1" produce una **distorsión que depende de la escala**, lo cual es
inaceptable cuando comparamos variables con rangos muy diferentes (conteos vs.
saldos, por ejemplo).

#### 11.3 La solución: arcoseno hiperbólico inverso ($\text{asinh}$)

La transformación arcoseno hiperbólico inverso se define como:

$$
\text{asinh}(x) = \ln\!\left(x + \sqrt{x^2 + 1}\right)
$$

Esta función tiene propiedades ideales para datos económicos:

| Propiedad | Explicación | Implicación práctica |
|-----------|-------------|---------------------|
| **Definida en todo $\mathbb{R}$** | $\text{asinh}(x)$ existe para cualquier $x$ real | No perdemos observaciones por ceros ni negativos |
| **asinh(0) = 0** | $\ln(0 + \sqrt{0+1}) = \ln(1) = 0$ | Los ceros se preservan exactamente |
| **Impar: asinh(−x) = −asinh(x)** | Simétrica respecto al origen | Funciona con valores negativos (ej. saldos netos) |
| **≈ log(2x) para x grande** | Cuando $x \gg 1$: $\sqrt{x^2+1} \approx x$, entonces $\text{asinh}(x) \approx \ln(2x)$ | Coeficientes se interpretan como semi-elasticidades |
| **≈ x para x ≈ 0** | Serie de Taylor: $\text{asinh}(x) \approx x - \frac{x^3}{6} + \ldots$ | Cerca del cero, se comporta como la función identidad |
| **No depende de escala** | No hay constante arbitraria como el "+1" en log(x+1) | Resultados comparables entre variables con distintos rangos |

> **Gráfico conceptual:**
> ```
> asinh(x)
>    │         ╱ ← se comporta como log(2x) para x grande
>    │       ╱
>    │     ╱
>    │   ╱ ← se comporta como x cerca del origen
>    │ ╱
> ───┼╱──────── x
>   ╱│
> ╱  │
> ```

#### 11.4 Referencia académica: Bellemare & Wichman (2020)

La referencia clave para justificar el uso de asinh en econometría aplicada es:

> Bellemare, M. F. & Wichman, C. J. (2020). "Elasticities and the Inverse
> Hyperbolic Sine Transformation." *Oxford Bulletin of Economics and Statistics*,
> 82(1), 50–61.

**Resultado principal del paper:** Para valores suficientemente grandes de $x$
(digamos $x > 10$), el coeficiente de una regresión con variable dependiente
$\text{asinh}(Y)$ se interpreta **aproximadamente igual** que con $\log(Y)$:
como una **semi-elasticidad** (si el regresor está en niveles) o **elasticidad**
(si el regresor también está en log/asinh).

| Si $Y_{it}$ se transforma con… | $\beta$ de $D_{it}$ se interpreta como… |
|---------------------------------|------------------------------------------|
| Nivel ($Y$) | Un cambio absoluto de $\beta$ unidades |
| $\log(Y)$ | Un cambio porcentual de $\approx 100 \cdot \beta$% |
| $\text{asinh}(Y)$ | Un cambio porcentual de $\approx 100 \cdot \beta$% (para $Y$ grande) |

**Cautela:** Para valores cercanos a 0, la interpretación de semi-elasticidad
**no aplica**. Bellemare & Wichman recomiendan que cuando una proporción grande
de las observaciones toma valores cercanos a 0, se reporten los **efectos
marginales promedio** en lugar de interpretar directamente el coeficiente.

> **Consejo para la tesis:** En el texto principal, reportar los coeficientes
> de la especificación asinh como "cambios porcentuales aproximados". En una
> nota al pie, citar a Bellemare & Wichman y aclarar que para variables con
> muchos ceros, la interpretación es aproximada.

#### 11.5 Comparación práctica: 5 especificaciones de la variable dependiente

A lo largo del EDA hemos construido varias versiones de cada variable
dependiente. Aquí las comparamos:

| Especificación | Sufijo | Ventaja | Desventaja | Uso |
|----------------|--------|---------|------------|-----|
| Nivel per cápita | `_pc` | Coeficiente en unidades naturales | Sensible a outliers | Base para las demás |
| Winsorizada | `_pc_w` | Mitiga outliers extremos (p1–p99) | Pierde variación real en colas | Robustez |
| Log | `log_*` | Interpretación como % | Indefinida en 0; solo 4 variables (población) | Solo para `pob_*` |
| **asinh** | **`_pc_asinh`** | **Maneja ceros + interpretación %** | **Difícil de interpretar cerca de 0** | **Especificación principal** |
| Ratio M/H | `ratio_mh_*` | Mide brecha de género directamente | Indefinida si H = 0 | Análisis descriptivo |

**Recomendación final para la tesis (orden de presentación):**
1. **Especificación principal:** `_pc_asinh` (maneja ceros, comprime distribución, interpretable)
2. **Robustez 1:** `_pc_w` (winsorizada, sin transformación funcional)
3. **Robustez 2:** `_pc` en nivel (sin ninguna transformación)

Si los tres dan la misma dirección y significancia, los resultados son robustos.

#### 11.6 Implementación en Python

El código de `src/transformaciones_medias.py`:

```python
# Identificar columnas per cápita (originales, no winsorizadas)
cols_pc = [c for c in df.columns if c.endswith("_pc") and not c.endswith("_w")]

# Crear transformación asinh
for col in cols_pc:
    col_asinh = f"{col}_asinh"
    df[col_asinh] = np.arcsinh(df[col])
```

**Desglose:**

1. **Selección de columnas:** Se filtran las columnas que terminan en `_pc` pero
   **no** en `_w`, para evitar aplicar asinh a las versiones winsorizadas. La
   transformación se aplica a las variables per cápita originales.

2. **`np.arcsinh()`:** Esta es la función de NumPy que implementa $\text{asinh}(x)$.
   Internamente calcula $\ln(x + \sqrt{x^2 + 1})$, pero de manera numéricamente
   estable para evitar desbordamiento con valores muy grandes.

3. **Convención de nombres:** El sufijo `_asinh` se agrega al nombre completo
   (ej. `ncont_total_m_pc` → `ncont_total_m_pc_asinh`), lo cual permite
   identificar la cadena de transformaciones: conteo → per cápita → asinh.

> **¿Por qué no `np.log1p()` (= $\log(1+x)$)?** Porque `np.arcsinh()` no
> requiere una constante arbitraria. `np.log1p(x)` calcula $\log(1+x)$, que como
> vimos en la sección 11.2, distorsiona según la escala de la variable.

#### 11.7 Compresión de la distribución — ejemplo `ncont_total_m_pc`

| Estadístico | Original (`_pc`) | asinh (`_pc_asinh`) | Factor de compresión |
|-------------|------------------|---------------------|----------------------|
| Media | 3,429.69 | ~8.4 | 408× |
| Mediana | 575.26 | ~7.1 | 81× |
| Máximo | 179,439.41 | ~12.1 | 14,830× |
| Mínimo | 0.00 | 0.00 | — |

Observa cómo el **máximo se comprime 14,830 veces**: de 179,439 a ~12.1.
Esto significa que en la regresión, un municipio metropolitano extremo ya no
tendrá 14,000 veces más "peso" que un municipio mediano. La transformación
reduce la **palanca** (leverage) de los outliers sin eliminarlos.

#### 11.8 Columnas creadas (51 en total)

| Grupo | Ejemplo | # Columnas |
|-------|---------|-----------|
| Conteos (ahorro, a la vista, plazo, total; M/H/T) | `ncont_ahorro_m_pc_asinh` | 21 |
| Saldos (ahorro, a la vista, plazo, total; M/H/T) | `saldocont_ahorro_m_pc_asinh` | 21 |
| Crédito hipotecario (M/H/T) | `numcontcred_hip_m_pc_asinh` | 3 |
| Tarjetas débito (M/H/T) | `numtar_deb_m_pc_asinh` | 3 |
| Tarjetas crédito (M/H/T) | `numtar_cred_m_pc_asinh` | 3 |
| **Total** | | **51** |

#### 11.9 Verificación empírica: ¿las 3 especificaciones dan resultados consistentes?

> **Fecha de verificación:** 5 de marzo de 2026  
> **Script:** `src/tesis_alcaldesas/models/robustness.py` (tests R6 y R7)  
> **Modelo:** PanelOLS con FE de municipio + FE de periodo, cluster SE a nivel
> municipio, control: `log_pob`. Tratamiento: `alcaldesa_final`.

La recomendación de la sección 11.5 propone usar 3 especificaciones. Se
implementaron los tests R6 (`_pc_w` en nivel) y R7 (`_pc` en nivel crudo) en
el script de robustez para verificar la consistencia. Resultados:

**Panel A — Outcome focal: Contratos totales mujeres (`ncont_total_m`)**

| Test | Variable dependiente | $\hat{\beta}$ | SE (cluster) | Sig. |
|------|---------------------|---------------|-------------|------|
| Baseline | `ncont_total_m_pc_asinh` | +0.0070 | (0.0215) | — |
| R6 | `ncont_total_m_pc_w` (nivel) | −71.96 | (41.48) | * |
| R7 | `ncont_total_m_pc` (nivel crudo) | −114.38 | (60.68) | * |

**Panel B — Todos los 5 outcomes primarios (R6: `_pc_w` en nivel)**

| Outcome | $\hat{\beta}$ (R6) | SE | Sig. |
|---------|-------------------|-----|------|
| Contratos totales (M) | −71.96 | (41.48) | * |
| Tarjetas débito (M) | +60.66 | (32.96) | * |
| Tarjetas crédito (M) | +19.63 | (8.64) | ** |
| Créditos hipotecarios (M) | +0.18 | (0.34) | — |
| Saldo total (M) | +1,405,275 | (1,233,219) | — |

**Panel C — Todos los 5 outcomes primarios (R7: `_pc` en nivel crudo)**

| Outcome | $\hat{\beta}$ (R7) | SE | Sig. |
|---------|-------------------|-----|------|
| Contratos totales (M) | −114.38 | (60.68) | * |
| Tarjetas débito (M) | +13.05 | (97.33) | — |
| Tarjetas crédito (M) | +10.90 | (26.51) | — |
| Créditos hipotecarios (M) | +1.58 | (1.06) | — |
| Saldo total (M) | +1,665,613 | (1,463,627) | — |

**Interpretación de los resultados:**

Los resultados revelan por qué la transformación asinh es necesaria:

1. **Inconsistencia de signos en nivel:** Para contratos totales, el baseline
   asinh da $\hat{\beta} = +0.007$ (positivo, no significativo), pero R6 y R7
   dan coeficientes **negativos** y marginalmente significativos. Esto no es una
   contradicción: la especificación en nivel es dominada por outliers (los
   municipios metropolitanos con miles de contratos), que distorsionan el
   estimador.

2. **Magnitudes enormes en saldos:** El coeficiente de "Saldo total" en nivel
   crudo es $\hat{\beta} \approx 1.6$ millones, con un SE de $\approx 1.5$
   millones. Estos números son difíciles de interpretar y reflejan la
   varianza extrema de los saldos en pesos.

3. **La transformación asinh estabiliza los resultados:** En la especificación
   asinh (baseline), todos los coeficientes están en escala comparable
   (~0.01–0.02), son interpretables como semi-elasticidades, y ninguno muestra
   significancia espuria.

4. **Tarjetas crédito (R6) es significativa al 5%:** Este es el único resultado
   que alcanza significancia convencional (**$p < 0.05$) en nivel winsorizado.
   Sin embargo, no aparece en asinh ni en nivel crudo, lo que sugiere que es
   sensible a la especificación y no debe interpretarse como evidencia fuerte.

> **Conclusión para la tesis:** Las especificaciones en nivel (R6 y R7) son
> **sensibles a outliers** y producen resultados inestables entre outcomes y
> entre especificaciones. Esto **refuerza** la elección de `_pc_asinh` como
> especificación principal: comprime la distribución, maneja ceros, y produce
> coeficientes estables e interpretables. Las especificaciones en nivel deben
> presentarse en el apéndice como evidencia de que la transformación es necesaria,
> no como especificaciones alternativas equivalentes.
>
> **Actualización de la recomendación:** A la luz de estos resultados, el orden
> de presentación recomendado es:
> 1. **Principal:** `_pc_asinh`
> 2. **Robustez funcional:** `_pc_w` + asinh encima (test R2 existente: $\hat{\beta} = +0.0081$, mismo signo y magnitud que baseline)
> 3. **Robustez de escala:** `log(1+y)` (test R1: $\hat{\beta} = +0.0054$, consistente)
> 4. **Apéndice:** `_pc_w` en nivel y `_pc` en nivel (para documentar por qué la transformación es necesaria)

---

### Rec 12. Imputación de NULLs en `tipo_pob`

#### 12.1 ¿Qué son los valores faltantes y por qué importan?

En cualquier base de datos, los valores faltantes (NULLs) pueden surgir por
diversas razones. La taxonomía estándar (Rubin, 1976) clasifica los datos
faltantes en tres tipos:

| Tipo | Nombre formal | Significado | Ejemplo |
|------|--------------|-------------|---------|
| **MCAR** | Missing Completely At Random | La probabilidad de ser NULL no depende de nada | Error aleatorio al capturar datos |
| **MAR** | Missing At Random | La probabilidad depende de variables observadas | Municipios pequeños sin oficina censal |
| **MNAR** | Missing Not At Random | La probabilidad depende del valor mismo que falta | Municipios "rurales" no reportan porque son rurales |

**¿Por qué importa la clasificación?** Porque el tipo de dato faltante determina
qué estrategia de imputación es válida:

- **MCAR/MAR:** Se pueden usar métodos de imputación (múltiple, regresión, etc.)
  sin introducir sesgo.
- **MNAR:** La imputación puede generar sesgo; se necesitan modelos de selección.

#### 12.2 Nuestro caso: imputación determinista justificada

En nuestro caso, solo **2 de 2,465 municipios** tienen `tipo_pob = NULL`. No
necesitamos recurrir a técnicas sofisticadas de imputación múltiple. La
situación es mucho más simple:

1. **Conocemos la variable que determina `tipo_pob`:** es la población (`pob`).
2. **Conocemos los rangos de cada categoría** porque los observamos en los demás
   municipios.
3. **Los 2 municipios caen inequívocamente dentro de un rango.**

Esto hace que la imputación sea **determinista** (no hay incertidumbre):
subimos a la tabla de rangos, comparamos la población, y asignamos la categoría.

> **Imputación determinista vs. estocástica:**
>
> | Tipo | Cuándo usarla | Ejemplo |
> |------|--------------|---------|
> | **Determinista** | Cuando la regla de asignación es conocida y exacta | "Si pob ∈ [15k, 50k] → Semi-urbano" |
> | **Estocástica** | Cuando hay incertidumbre sobre el valor verdadero | "Imputar ingreso con regresión + ruido" |
>
> Nuestra imputación es determinista: NO hay ambigüedad sobre la categoría
> correcta.

#### 12.3 Los rangos observados de `tipo_pob`

La variable `tipo_pob` clasifica municipios según su tamaño poblacional. Los
rangos fueron inferidos de los datos existentes (no son una clasificación oficial
publicada, sino que emergen de los umbrales observados en la base):

| Categoría | Rango de población | # Municipios |
|-----------|-------------------|-------------|
| Rural | 81 – 5,000 | 664 |
| En Transición | 5,001 – 14,997 | 624 |
| **Semi-urbano** | **15,009 – 49,920** | **731** |
| Urbano | 42,664 – 299,635 | 361 |
| Semi-metrópoli | 300,295 – 995,129 | 72 |
| Metrópoli | 1,003,530 – 1,922,523 | 13 |

> **Nota:** Los rangos tienen superposición entre Semi-urbano y Urbano (42,664–
> 49,920). Esto sugiere que la clasificación original puede usar criterios
> adicionales más allá de la población. Sin embargo, los 2 municipios que
> necesitamos imputar (20,320 y 16,568) caen **lejos de la zona ambigua**,
> dentro del rango claro de Semi-urbano.

#### 12.4 Los 2 municipios corregidos

| `cve_mun` | Nombre | Estado | Población | Categoría asignada | Justificación |
|-----------|--------|--------|-----------|-------------------|---------------|
| 2007 | San Felipe | Baja California | 20,320 | Semi-urbano | Rango: 15,009–49,920 |
| 4013 | Dzitbalché (Calkiní) | Campeche | 16,568 | Semi-urbano | Rango: 15,009–49,920 |

Ambos municipios tienen poblaciones que caen **cómodamente** dentro del rango
Semi-urbano y lejos de los bordes de la categoría.

#### 12.5 Implementación en Python

El código de `src/transformaciones_medias.py`:

```python
# Rangos observados para asignar categoría
if pob <= 5000:
    cat = "Rural"
elif pob <= 15000:
    cat = "En Transicion"
elif pob <= 50000:
    cat = "Semi-urbano"
elif pob <= 300000:
    cat = "Urbano"
elif pob <= 1000000:
    cat = "Semi-metropoli"
else:
    cat = "Metropoli"

# Asignar a todas las filas de ese municipio
mask = df["cve_mun"] == row["cve_mun"]
df.loc[mask, "tipo_pob"] = cat
```

**Desglose:**

1. **Cadena `if/elif`:** Recorre los rangos de menor a mayor. La lógica es
   mutuamente excluyente: si `pob = 20,320`, entra en `elif pob <= 50000`
   → "Semi-urbano". No hay ambigüedad.

2. **`mask = df["cve_mun"] == row["cve_mun"]`** — Crea un vector booleano que es
   `True` para todas las filas de ese municipio (17 filas, una por trimestre).

3. **`df.loc[mask, "tipo_pob"] = cat`** — Asigna la categoría a **todas** las
   observaciones trimestrales del municipio, no solo a una. Esto es correcto
   porque `tipo_pob` es una característica del municipio que no cambia en el
   tiempo (es *time-invariant*).

> **¿Por qué `df.loc[mask, col]` y no `df[mask][col]`?** En pandas, la
> asignación encadenada (`df[mask]["col"] = valor`) genera un
> `SettingWithCopyWarning` porque puede operar sobre una *copia* y no sobre
> el DataFrame original. `df.loc[mask, "col"]` siempre modifica el original.

#### 12.6 Distribución antes → después

| Categoría | Rango | Antes | Después | Cambio |
|-----------|-------|-------|---------|--------|
| Rural | 81 – 5,000 | 11,288 | 11,288 | — |
| En Transición | 5,001 – 14,997 | 10,613 | 10,613 | — |
| **Semi-urbano** | **15,009 – 49,920** | **12,421** | **12,455** | **+34** |
| Urbano | 42,664 – 299,635 | 6,138 | 6,138 | — |
| Semi-metrópoli | 300,295 – 995,129 | 1,223 | 1,223 | — |
| Metrópoli | 1,003,530 – 1,922,523 | 220 | 220 | — |
| **NULL** | — | **2** | **0** | **−2** |
| **Total** | | **41,905** | **41,905** | |

**¿Por qué +34?** Cada municipio aparece en 17 trimestres. Dos municipios ×
17 trimestres = 34 filas que pasan de NULL a "Semi-urbano".

#### 12.7 ¿Para qué sirve `tipo_pob` en el modelo?

La variable `tipo_pob` tiene dos usos en la estrategia econométrica:

**Uso 1 — Como variable de control categórica:**

En una regresión con variable categórica, statsmodels/pandas crea
**variables indicadoras (dummies)** automáticamente. Con 6 categorías,
se crean 5 dummies (una se omite como categoría de referencia):

```
tipo_pob = Rural        → [1, 0, 0, 0, 0]
tipo_pob = En Transicion → [0, 1, 0, 0, 0]
tipo_pob = Semi-urbano  → [0, 0, 1, 0, 0]
tipo_pob = Urbano       → [0, 0, 0, 1, 0]
tipo_pob = Semi-metropoli → [0, 0, 0, 0, 1]
tipo_pob = Metropoli    → [omitida — categoría de referencia]
```

> **¿Por qué se omite una categoría?** Si incluimos las 6 dummies, tendríamos
> **colinealidad perfecta** (suman 1 para toda observación, que es lo mismo
> que la constante). Omitir una categoría rompe la colinealidad. Los
> coeficientes de las demás se interpretan **relativo a la categoría omitida**.
>
> Ejemplo: si el coeficiente de "Rural" es −0.5, significa que los municipios
> rurales tienen un outcome 0.5 unidades menor que los municipios metrópoli
> (la categoría de referencia), *ceteris paribus*.

**Uso 2 — Para análisis de heterogeneidad:**

¿El efecto de tener una alcaldesa varía según el tamaño del municipio? Para
responder, interactuamos el tratamiento con `tipo_pob`:

$$
Y_{it} = \alpha_i + \gamma_t + \beta \cdot D_{it} + \sum_{k} \theta_k \cdot (D_{it} \times \mathbf{1}[\text{tipo\_pob}_i = k]) + \varepsilon_{it}
$$

Si algún $\theta_k$ es significativo, el efecto de la alcaldesa es
**heterogéneo** por tipo de municipio. Por ejemplo, si $\theta_{\text{Rural}} > 0$,
el efecto es mayor en municipios rurales.

> **Nota:** Para que esta regresión sea estimable, necesitamos que `tipo_pob`
> no tenga NULLs — de ahí la importancia de la Rec 12.

#### 12.8 ¿Cuándo es válida la imputación determinista?

La imputación que hicimos es válida bajo estas condiciones (todas se cumplen):

| Condición | ¿Se cumple? | Evidencia |
|-----------|------------|-----------|
| Pocos valores faltantes | ✅ | 2 de 2,465 municipios (0.08%) |
| Regla de asignación conocida | ✅ | `tipo_pob` se define por rangos de `pob` |
| Sin ambigüedad en la clasificación | ✅ | Ambos municipios lejos de bordes de categoría |
| Variable predictora no faltante | ✅ | `pob` está completa para ambos municipios |
| Bajo impacto en distribución | ✅ | 34 de 41,905 obs (0.08%) |

Si alguna de estas condiciones no se cumpliera (por ejemplo, si faltaran
cientos de municipios o si cayeran en zonas ambiguas), necesitaríamos una
estrategia más sofisticada como **imputación múltiple** (Rubin, 1987).

---

## 17. Validación de transformaciones medias

### 17.1 ¿Por qué automatizar la validación?

En ciencia de datos, un error silencioso en una transformación puede
propagarse por todo el análisis sin ser detectado. Por ejemplo, si la
suma acumulada se calculara sin ordenar los datos cronológicamente, los
valores serían incorrectos pero la columna existiría sin generar ningún
error.

La **suite de tests** automatiza la verificación de que cada transformación
cumple las propiedades esperadas. Se ejecuta después de cada ejecución del
script y falla ruidosamente si algo está mal.

> **Analogía:** Los tests son como un checklist de vuelo. Un piloto no
> despega hasta verificar que *cada* instrumento funciona. Nosotros no
> modelamos hasta verificar que *cada* variable está correctamente construida.

### 17.2 Tests de recomendaciones medias (16/16 ✓)

| # | Test | ¿Qué verifica? | Resultado |
|---|------|----------------|-----------|
| T1 | Filas correctas (41,905) | Que la transformación no creó ni eliminó filas | ✓ |
| T2 | Total columnas (348) | Que el conteo de columnas es exactamente el esperado | ✓ |
| T3 | `alcaldesa_acumulado` existe | Que la Rec 10 se ejecutó | ✓ |
| T4 | Sin valores negativos en acumulado | Propiedad matemática: cumsum de binario ≥ 0 | ✓ |
| T5 | Máximo = 17 (todos los trimestres) | Rango correcto: máx = T periodos en el panel | ✓ |
| T6 | Never-treated → acumulado = 0 | Coherencia: si nunca tratado, dosis = 0 siempre | ✓ |
| T7 | Monótono creciente (0 violaciones) | La dosis acumulada nunca decrece dentro de un municipio | ✓ |
| T8 | 51 columnas asinh existen | Que la Rec 11 creó todas las columnas esperadas | ✓ |
| T9 | Fórmula asinh correcta | Verifica asinh(x) = ln(x + √(x²+1)) numéricamente | ✓ |
| T10 | asinh(0) = 0 | Propiedad clave: los ceros se preservan | ✓ |
| T11 | `tipo_pob` sin NULLs | Que la Rec 12 eliminó todos los valores faltantes | ✓ |
| T12 | San Felipe → Semi-urbano | Verificación puntual del municipio 2007 | ✓ |
| T13 | Dzitbalché → Semi-urbano | Verificación puntual del municipio 4013 | ✓ |
| T14 | PK intacta | La llave primaria (cve_mun, periodo_trimestre) sigue siendo única | ✓ |
| T15 | Índice `cvegeo_mun` intacto | El índice de base de datos no se perdió al reescribir la tabla | ✓ |
| T16 | Tabla original intacta (175 cols) | `inclusion_financiera` no fue modificada accidentalmente | ✓ |

> **Diseño de los tests:**
>
> - **T1–T2** son tests de *forma* (dimensiones del DataFrame).
> - **T3–T7** validan propiedades matemáticas de `alcaldesa_acumulado`.
> - **T8–T10** validan propiedades matemáticas de la transformación asinh.
> - **T11–T13** validan la imputación de `tipo_pob`.
> - **T14–T16** son tests de *integridad* (que nada se rompió en la base de datos).
>
> Esta estructura sigue el patrón **AAA** (Arrange, Act, Assert) de testing:
> se carga la tabla, se verifica una condición, se reporta pass/fail.

### 17.3 Resumen de todas las suites de validación

| Suite | Fase | Cobertura | Tests | Estado |
|-------|------|-----------|-------|--------|
| `src/tests/test_criticas.py` | Recs 1–4 | Per cápita, constantes, PK | 8/8 | ✓ |
| `src/tests/test_altas.py` | Recs 5–9 | Log, winsor, ratio, ever, cvegeo | 19/19 | ✓ |
| `src/tests/test_medias.py` | Recs 10–12 | Acumulado, asinh, tipo_pob | 16/16 | ✓ |
| **Total** | **Recs 1–12** | **Todas las transformaciones** | **43/43** | **✓** |

Los 43 tests pasan al 100%. Esto da confianza de que la tabla
`inclusion_financiera_clean` está correctamente construida y lista para
la fase de modelado.

---

## 18. Scripts creados y pipeline de ejecución

### 18.1 Inventario de scripts

| Script | Propósito | Input | Output |
|--------|-----------|-------|--------|
| `src/transformaciones_criticas.py` | Recs 1–4: per cápita, eliminar constantes | `inclusion_financiera` (175 cols) | `inclusion_financiera_clean` (223 cols) |
| `src/transformaciones_altas.py` | Recs 5–9: log, winsor, ratio, ever, cvegeo | `inclusion_financiera_clean` (223 cols) | `inclusion_financiera_clean` (296 cols) |
| `src/transformaciones_medias.py` | Recs 10–12: acumulado, asinh, tipo_pob | `inclusion_financiera_clean` (296 cols) | `inclusion_financiera_clean` (348 cols) |
| `src/tests/test_criticas.py` | Validación de Recs 1–4 | `inclusion_financiera_clean` | 8 tests |
| `src/tests/test_altas.py` | Validación de Recs 5–9 | `inclusion_financiera_clean` | 19 tests |
| `src/tests/test_medias.py` | Validación de Recs 10–12 | `inclusion_financiera_clean` | 16 tests |

### 18.2 ¿Qué significa "idempotente"?

Un script es **idempotente** si puedes ejecutarlo 1 vez o 100 veces y el resultado
es el mismo. Esto se logra porque cada script:

1. **Verifica si las columnas ya existen** → si sí, las elimina y las recrea.
2. **Usa `DROP TABLE IF EXISTS`** → no falla si la tabla no existe.
3. **Restaura PK e índices** → la base de datos queda en el mismo estado final.

La idempotencia es importante porque permite **re-ejecutar** sin miedo a duplicar
columnas o corromper datos.

### 18.3 Orden de ejecución completo

```bash
cd /Users/anapaulaperezgavilan/Documents/Tesis_DB/Code
source .venv/bin/activate

# 1. Crear tabla limpia con transformaciones críticas (175 → 223 cols)
python src/transformaciones_criticas.py

# 2. Agregar transformaciones de alta prioridad (223 → 296 cols)
python src/transformaciones_altas.py

# 3. Agregar transformaciones de prioridad media (296 → 348 cols)
python src/transformaciones_medias.py

# 4. Validar todo (43 tests)
python src/tests/test_criticas.py    # 8 tests
python src/tests/test_altas.py       # 19 tests
python src/tests/test_medias.py      # 16 tests
```

> **¿Por qué el orden importa?** Cada script depende del output del anterior.
> `transformaciones_altas.py` espera encontrar las columnas `_pc` que creó
> `transformaciones_criticas.py`. Si ejecutas `altas` sin haber corrido `criticas`,
> el script fallará porque las columnas no existen.

---

## 19. Estado final de todas las recomendaciones del EDA

| # | Prioridad | Categoría | Estado | Sección | Script |
|---|-----------|-----------|--------|---------|--------|
| 1 | 🔴 CRÍTICA | Normalización conteos per cápita | ✅ Resuelto | Sección 11 | `transformaciones_criticas.py` |
| 2 | 🔴 CRÍTICA | Normalización saldos per cápita | ✅ Resuelto | Sección 11 | `transformaciones_criticas.py` |
| 3 | 🔴 CRÍTICA | saldoprom NULLs | ✅ Documentado | Sección 11 | `transformaciones_criticas.py` |
| 4 | 🔴 CRÍTICA | Exclusión constantes | ✅ Resuelto | Sección 11 | `transformaciones_criticas.py` |
| 5 | 🟡 Alta | log(pob) controles | ✅ Resuelto | Sección 12 | `transformaciones_altas.py` |
| 6 | 🟡 Alta | Winsorización p1–p99 | ✅ Resuelto | Sección 12 | `transformaciones_altas.py` |
| 7 | 🟡 Alta | Ratio M/H (brecha género) | ✅ Resuelto | Sección 12 | `transformaciones_altas.py` |
| 8 | 🟡 Alta | ever_alcaldesa | ✅ Resuelto | Sección 12 | `transformaciones_altas.py` |
| 9 | 🟡 Alta | IDs estándar (cvegeo_mun) | ✅ Resuelto | Sección 12 | `transformaciones_altas.py` |
| 10 | 🟢 Media | alcaldesa_acumulado | ✅ Resuelto | **Sección 16** | `transformaciones_medias.py` |
| 11 | 🟢 Media | asinh outcomes | ✅ Resuelto | **Sección 16** | `transformaciones_medias.py` |
| 12 | 🟢 Media | tipo_pob NULLs | ✅ Resuelto | **Sección 16** | `transformaciones_medias.py` |

**Progreso: 12/12 recomendaciones resueltas (100%).**

---

## 20. Tabla `inclusion_financiera_clean` — Inventario final de columnas

La tabla final tiene **348 columnas**. A continuación se agrupan por origen:

### 20.1 Columnas heredadas de la tabla original (175)

Variables originales de CNBV/INEGI: periodos, identificadores geográficos,
productos financieros (conteos, saldos, tarjetas, créditos hipotecarios),
población, tipo de población, político (alcaldesa_final), y derivadas.

### 20.2 Columnas añadidas por fase

| Fase | Prefijo/Sufijo | # Cols | Descripción | Sección donde se explica |
|------|---------------|--------|-------------|--------------------------|
| Críticas | `*_pc` | 51 | Variables per cápita (÷ población adulta M/H/T) | Sección 11 |
| Críticas | — | −3 | Constantes eliminadas (`cve_pais`, `desc_pais`, `id_periodo`) | Sección 11 |
| Altas | `log_*` | 4 | Log(población + 1) | Sección 12 |
| Altas | `*_pc_w` | 51 | Per cápita winsorizadas (p1–p99) | Sección 12 |
| Altas | `ratio_mh_*` | 17 | Brecha de género M/H | Sección 12 |
| Altas | `ever_alcaldesa` | 1 | Indicador time-invariant de tratamiento | Sección 12 |
| **Medias** | **`alcaldesa_acumulado`** | **1** | **Dosis acumulada de tratamiento** | **Sección 16 (Rec 10)** |
| **Medias** | **`*_pc_asinh`** | **51** | **Arcoseno hiperbólico inverso de per cápita** | **Sección 16 (Rec 11)** |
| **Medias** | **`tipo_pob` (corregida)** | **0** | **2 NULLs imputados, sin columnas nuevas** | **Sección 16 (Rec 12)** |
| | | **348** | **Total final** | |

### 20.3 Mapa de transformaciones: de variable original a especificaciones disponibles

Para cada variable de conteos/saldos original (ej. `ncont_total_m`), ahora
existen **cuatro versiones** listas para modelar:

```
ncont_total_m  (variable original, nivel absoluto)
    │
    ├── ncont_total_m_pc        (per cápita)
    │       │
    │       ├── ncont_total_m_pc_w       (winsorizada p1–p99)
    │       │
    │       └── ncont_total_m_pc_asinh   (transformación asinh)
    │
    └── ratio_mh_ncont_total    (brecha de género M/H)
```

Este árbol muestra que cada transformación se construye sobre la anterior,
formando una cadena reproducible desde el dato crudo hasta la especificación
final.

---

## 21. Próximos pasos

Con las 12 recomendaciones del EDA resueltas al 100%, la tabla
`inclusion_financiera_clean` (348 columnas, 41,905 filas) está lista para la
fase de modelado econométrico. Los siguientes pasos son:

1. **Construir la muestra analítica**: Seleccionar las variables dependientes
   (`_m_pc` y sus transformaciones), controles (`log_pob_*`, `tipo_pob`) y
   tratamiento (`alcaldesa_final`, `ever_alcaldesa`, `alcaldesa_acumulado`)
   para el modelo principal.

2. **Modelo TWFE (Two-Way Fixed Effects)**: Estimar el efecto causal de
   `alcaldesa_final` sobre los 5 outcomes de inclusión financiera femenina,
   con efectos fijos de municipio ($\alpha_i$) y periodo ($\gamma_t$).

3. **Event Study**: Estimar leads y lags alrededor del cambio de tratamiento
   para verificar tendencias paralelas pre-tratamiento (supuesto clave de DiD).

4. **Estimadores modernos (extensión futura)**: Estimadores robustos a tratamiento escalonado que evitan los
   problemas de comparaciones "prohibidas" del TWFE convencional (Goodman-Bacon,
   2021; Baker et al., 2022).

5. **Robustez**: Comparar resultados bajo las 3 especificaciones de la variable
   dependiente (`_pc`, `_pc_w`, `_pc_asinh`) + especificación alternativa con
   `alcaldesa_acumulado` como tratamiento continuo.

6. **Heterogeneidad**: Análisis por `tipo_pob`, región geográfica, y otras
   características municipales (población, baseline de inclusión financiera).

> **Mapa mental del flujo completo:**
> ```
> Datos crudos (CNBV)           ← Base de Datos/
>     ↓
> PostgreSQL (inclusion_financiera)    ← 175 cols, 41,905 filas
>     ↓
> EDA (12 recomendaciones)             ← 02–05_EDA_EXPLICACION
>     ↓
> inclusion_financiera_clean           ← 348 cols, 41,905 filas
>     ↓
> Muestra analítica (panel)            ← analytical_panel_features.csv
>     ↓
> Modelos (TWFE / Event Study)
>     ↓
> Resultados → Tesis
> ```
