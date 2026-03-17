> **Archivos fuente:**
> - `src/models/01_table1_descriptives.py`
> - `src/models/02_twfe.py`
> - `src/models/03_event_study.py`
> - `src/models/04_robustness.py`
> - `src/models/05_heterogeneity.py`

# Resultados empíricos

## 4.1  Estadísticos descriptivos

La Tabla 1 presenta las medias y desviaciones estándar de las variables de interés durante el período pre-tratamiento, desagregadas en tres grupos: municipios *nunca tratados* ($N = 1{,}476$; 25,016 observaciones trimestrales), municipios *conmutadores* (switchers, $N = 600$; 4,036 observaciones pre-tratamiento) y municipios *siempre tratados* ($N = 101$; 1,704 observaciones).  Los indicadores de inclusión financiera se expresan en escala de seno hiperbólico inverso (asinh) de las tasas per cápita por cada 10,000 mujeres adultas, lo que permite interpretar los coeficientes como semi-elasticidades aproximadas.

Los municipios que registran al menos un periodo con alcaldesa (switchers) tienden a ser ligeramente más grandes —con una media de $\ln(\text{Población})$ de 9.95 frente a 9.44 en el grupo de nunca tratados— y exhiben niveles pre-tratamiento algo superiores en todos los indicadores financieros: 7.67 frente a 6.98 en contratos totales (asinh), 7.31 frente a 7.00 en tarjetas de débito, y 6.32 frente a 5.78 en tarjetas de crédito.  Los municipios siempre tratados, por su parte, muestran promedios más cercanos al grupo de nunca tratados y algo inferiores a los switchers, consistente con el hecho de que se trata principalmente de municipios rurales o de menor tamaño donde la alcaldía ha estado ocupada por mujeres de forma continua.

Estas diferencias en niveles motivan la inclusión de efectos fijos municipales, que absorben cualquier heterogeneidad permanente entre unidades, así como efectos fijos de periodo, que capturan choques agregados comunes a todos los municipios en cada trimestre.

## 4.2  Resultados del modelo TWFE de referencia

La Tabla 2 reporta las estimaciones del modelo de diferencias en diferencias con efectos fijos bidireccionales (TWFE).  La especificación toma la forma:

$$y_{it} = \alpha_i + \lambda_t + \beta \cdot D_{it} + \varepsilon_{it}$$

donde $y_{it}$ es el indicador de inclusión financiera del municipio $i$ en el trimestre $t$, medido en escala asinh per cápita; $\alpha_i$ y $\lambda_t$ denotan los efectos fijos de municipio y periodo, respectivamente; $D_{it} = \texttt{alcaldesa\_final}_{it}$ es el indicador de tratamiento; y los errores estándar se agrupan (*cluster*) a nivel municipal para dar cuenta de la correlación serial intra-unidad.

No encontramos evidencia de un efecto estadísticamente significativo de la representación política femenina municipal sobre ninguno de los cinco indicadores primarios de inclusión financiera de las mujeres.  El coeficiente estimado para contratos totales es $\hat{\beta} = 0.007$ (EE = 0.022, $p = 0.747$), con un intervalo de confianza al 95\% de $[-0.035,\; 0.049]$.  En el caso de tarjetas de débito, la estimación puntual es ligeramente negativa ($\hat{\beta} = -0.014$, $p = 0.521$), mientras que para tarjetas de crédito es prácticamente nula ($\hat{\beta} = -0.002$, $p = 0.919$).  Los créditos hipotecarios muestran un coeficiente positivo pero lejos de cualquier umbral convencional de significancia ($\hat{\beta} = 0.018$, $p = 0.400$), y el saldo total registra una estimación cercana a cero ($\hat{\beta} = 0.004$, $p = 0.931$) con el intervalo más amplio de los cinco outcomes: $[-0.092,\; 0.100]$.

En términos sustantivos, un coeficiente de 0.007 en escala asinh equivaldría a un cambio aproximado de 0.7\% en la variable en niveles —una magnitud económicamente irrelevante—, y ninguno de los intervalos de confianza descarta un efecto nulo.  El $R^2$ intra-grupo es prácticamente cero en todos los modelos, lo que confirma que la variación del tratamiento dentro de cada municipio no explica variación adicional en los outcomes una vez absorbidos los efectos fijos.

Las 41,905 observaciones corresponden a 2,471 municipios observados durante 17 trimestres (2018-T3 a 2022-T3), con ocho municipios que presentan paneles incompletos (102 celdas faltantes, 0.24\% del total).

> **📖 Cómo leer la Tabla 2 — TWFE baseline (paso a paso)**
>
> La Tabla 2 (en `outputs/paper/tabla_2_twfe_main.csv`) reporta el efecto
> estimado de `alcaldesa_final` sobre cada outcome financiero.
>
> **Columnas clave:**
> | Columna | Significado |
> |---------|-------------|
> | $\hat{\beta}$ | Coeficiente: cambio en el outcome (asinh) asociado al tratamiento |
> | EE | Error estándar (clustered por municipio) |
> | p | p-valor bilateral |
> | IC 95% | Intervalo de confianza |
> | $R^2$ within | Variación explicada por el tratamiento dentro de cada municipio |
>
> **Paso 1 — ¿Algún coeficiente es significativo?**
> Ninguno. Todos los p-valores están por encima de 0.40 → no hay evidencia
> de efecto bajo TWFE.
>
> **Paso 2 — ¿Son los coeficientes económicamente relevantes?**
> El más grande es $\hat{\beta} = 0.018$ (hipotecarios), que equivale a un
> cambio de ~1.8% → irrelevante en magnitud.
>
> **Paso 3 — ¿Los intervalos de confianza son informativos?**
> Para contratos totales, IC = $[-0.035, 0.049]$. Esto incluye el cero y
> excluye efectos mayores a ~5% → el nulo es razonablemente informativo.
> Para saldo total, IC = $[-0.092, 0.100]$ → más amplio, menos informativo.
>
> **Paso 4 — Lee el $R^2$ within:**
> Cercano a cero en todos los modelos → el tratamiento no explica variación
> adicional una vez absorbidos los efectos fijos. Esto es esperado con un nulo.
>
> **Lectura rápida:** La Tabla 2 es un "nulo limpio": coeficientes cercanos a
> cero, ninguno significativo, intervalos informativos.

## 4.3  Diagnóstico de tendencias paralelas: event study

La identificación causal del estimador TWFE descansa sobre el supuesto de tendencias paralelas: en ausencia del tratamiento, la evolución de los outcomes habría sido similar entre municipios tratados y no tratados.  Para evaluar la plausibilidad de este supuesto, estimamos un modelo de event study con cuatro *leads* ($k = -4, -3, -2$; con $k = -1$ como referencia) y ocho *lags* ($k = 0, 1, \ldots, 7$), agrupando los extremos (*binned endpoints*) para los periodos fuera de la ventana.

La Figura 1 presenta los coeficientes estimados con sus intervalos de confianza al 95\% para cada uno de los cinco outcomes.  El patrón visual es consistente con la validez de tendencias paralelas: los coeficientes pre-tratamiento ($k < 0$) oscilan alrededor de cero sin mostrar una tendencia sistemática de alejamiento, y los coeficientes post-tratamiento permanecen igualmente cercanos a cero, confirmando la ausencia de un efecto dinámico del tratamiento.

Para formalizar el diagnóstico, realizamos un test conjunto de Wald ($\chi^2$) sobre la hipótesis nula de que todos los coeficientes pre-tratamiento ($k = -4, -3, -2$) son simultáneamente iguales a cero.  Los resultados se resumen a continuación:

- **Contratos totales:** $\chi^2 = 5.49$, $p = 0.139$ — no se rechaza al 10\%.
- **Tarjetas de débito:** $\chi^2 = 3.80$, $p = 0.284$ — no se rechaza.
- **Tarjetas de crédito:** $\chi^2 = 6.67$, $p = 0.083$ — rechazo marginal al 10\%.
- **Créditos hipotecarios:** $\chi^2 = 0.75$, $p = 0.861$ — no se rechaza.
- **Saldo total:** $\chi^2 = 3.52$, $p = 0.319$ — no se rechaza.

Cuatro de los cinco outcomes pasan el test de tendencias paralelas a un nivel de significancia del 10\%.  La excepción es tarjetas de crédito, donde el rechazo marginal ($p = 0.083$) se origina en el coeficiente del bin extremo $k \leq -4$ ($\hat{\beta} = -0.078$, $p = 0.043$), que agrega todos los periodos anteriores a cuatro trimestres previos al tratamiento.  Dado que los leads individuales más próximos ($k = -3$ y $k = -2$) no son significativos y que los bins extremos tienden a capturar efectos de composición, esta violación marginal no compromete sustancialmente la credibilidad del diseño.  No obstante, los resultados para tarjetas de crédito deben interpretarse con mayor cautela.

Un patrón similar se observa en contratos totales, donde el bin $k \leq -4$ muestra un coeficiente puntualmente significativo ($\hat{\beta} = -0.087$, $p = 0.031$), pero el test conjunto no rechaza la nula ($p = 0.139$), y los leads $k = -3$ y $k = -2$ no exhiben evidencia de divergencia.

En conjunto, el diagnóstico de tendencias paralelas es razonablemente favorable.  Los coeficientes post-tratamiento no muestran ningún quiebre respecto al patrón pre-tratamiento, lo cual es consistente tanto con la validez del diseño como con la conclusión de un efecto nulo.

> **📖 Cómo leer la Figura 1 y los tests de pre-trends (paso a paso)**
>
> La Figura 1 (en `outputs/paper/figura_1_event_study.pdf`) muestra un gráfico
> por outcome con coeficientes de event-time.
>
> **Ejes del gráfico:**
> - **X:** Event-time $k$ (periodos relativos al tratamiento, $k = -1$ es referencia).
> - **Y:** Coeficiente $\hat{\beta}_k$ (escala asinh). Cero = sin efecto.
>
> **Paso 1 — Verifica pre-trends visualmente:**
> Los puntos para $k < 0$ (izquierda de la línea vertical en $k = -1$) deben
> flotar cerca de cero. Si suben o bajan sistemáticamente → tendencias no paralelas.
>
> **Paso 2 — Lee las barras de error:**
> Cada punto tiene IC 95%. Si el intervalo cruza el cero → no significativo.
> Busca si *algún* lead tiene un intervalo que no cruce el cero → posible
> violación puntual (como el bin $k \leq -4$ en crédito con $p = 0.043$).
>
> **Paso 3 — Evalúa el test conjunto:**
> Los p-valores del test $\chi^2$ formalizan la inspección visual:
> - $p > 0.10$: pre-trends OK ✓
> - $p \in [0.05, 0.10]$: borderline → investigar qué lead lo genera
> - $p < 0.05$: falla → estrategia comprometida para ese outcome
>
> **Paso 4 — Verifica el patrón post-tratamiento:**
> Para un efecto nulo genuino (como en TWFE), los puntos post ($k \geq 0$)
> también deben estar cerca de cero. Si se alejan de cero post-tratamiento,
> hay efecto dinámico.
>
> **Lectura rápida:** 4/5 outcomes pasan limpiamente. Tarjetas de crédito es
> borderline ($p = 0.083$) por el bin extremo — ver sensibilidad en §15.

## 4.4  Análisis de robustez y heterogeneidad

### 4.4.1  Robustez

La Tabla 3 presenta cinco pruebas de robustez aplicadas al outcome focal (contratos totales de mujeres), diseñadas para evaluar la sensibilidad del resultado principal ante elecciones metodológicas alternativas.

**Transformación funcional.**  La estimación bajo la transformación logarítmica $\log(1 + y)$ arroja un coeficiente de 0.005 (EE = 0.020), prácticamente idéntico al de la especificación base (0.007).  Lo mismo ocurre con la winsorización al percentil 1-99 previa a la transformación asinh ($\hat{\beta} = 0.008$, EE = 0.021).  Estas pruebas descartan que el resultado nulo se deba a la influencia de valores extremos o a la elección de escala.

**Exclusión de transiciones.**  Al imponer valores faltantes en los trimestres donde el tratamiento cambia de estado —eliminando posibles efectos transitorios de la alternancia— el coeficiente se reduce a 0.002 (EE = 0.024) con $N = 38{,}303$, lo que confirma que la inclusión de los periodos de transición no sesga la estimación.

**Placebo temporal.**  Al desplazar el indicador de tratamiento cuatro trimestres hacia el futuro, se obtiene un coeficiente de $-0.019$ (EE = 0.020), estadísticamente indistinguible de cero.  La ausencia de un efecto placebo refuerza que no existe anticipación ni tendencias diferenciales pre-tratamiento que contaminen la estimación principal.

**Placebo de género.**  Cuando se estima el mismo modelo TWFE pero utilizando como outcome los contratos de *hombres* en lugar de los de mujeres, el coeficiente es $-0.001$ (EE = 0.025).  La nulidad de este placebo es informativa: si el tratamiento (alcaldesa) generara un efecto sobre toda la actividad financiera municipal —y no específicamente sobre la inclusión de mujeres—, esperaríamos un coeficiente significativo también para hombres.  La ausencia de efecto en ambos géneros apunta a que el resultado nulo es genuino y no producto de un efecto general confundido.

En síntesis, los resultados son robustos a transformaciones funcionales alternativas, a la exclusión de periodos de transición y a dos especificaciones de placebo.  Todas las estimaciones de robustez se encuentran dentro de un rango estrecho ($[-0.019,\; 0.008]$) y ninguna alcanza significancia estadística convencional.

> **📖 Cómo leer la Tabla 3 — Robustez del TWFE (paso a paso)**
>
> La Tabla 3 tiene una fila por test de robustez. Cada fila repite el TWFE
> cambiando **un** supuesto respecto al baseline.
>
> **Interpretación rápida por fila:**
> | Fila | ¿Qué cambia? | Si $\hat{\beta}$ fuera diferente significaría... |
> |------|--------------|----------------------------------------------|
> | R1: log(1+y) | Escala | El resultado depende de la transformación |
> | R2: Winsor + asinh | Outliers | Valores extremos distorsionan el baseline |
> | R3: Excluir transiciones | Definición de tratamiento | Periodos de cambio sesgan |
> | R4: Placebo temporal | Anticipación | Hay tendencias confundentes |
> | R5: Placebo género | Especificidad | El efecto es general, no de género |
>
> Todas las filas muestran $\hat{\beta} \approx 0$ → el nulo no es un artefacto.

### 4.4.2  Heterogeneidad

La Tabla 4 explora la posibilidad de que el efecto promedio nulo oculte efectos heterogéneos en subpoblaciones definidas por dos dimensiones: el tipo de localidad (clasificación CONAPO en seis categorías) y el tercil de población municipal.

Sólo un subgrupo exhibe un coeficiente nominalmente significativo: los municipios clasificados como *metrópoli* ($\hat{\beta} = 0.030$, $p = 0.024$, $N = 220$).  Sin embargo, al ajustar por múltiples pruebas mediante el procedimiento de Benjamini-Hochberg (BH), el $q$-value correspondiente es 0.215, por lo que este resultado **no sobrevive la corrección por comparaciones múltiples** al nivel convencional de 10\%.

Los municipios rurales presentan un coeficiente negativo y de magnitud no despreciable ($\hat{\beta} = -0.104$, $p = 0.109$), pero tampoco alcanza significancia estadística ($q = 0.492$).  Los demás subgrupos —semi-metrópoli, en transición, semi-urbano y urbano— producen estimaciones puntuales cercanas a cero y $p$-valores superiores a 0.77.

La desagregación por terciles de población muestra un gradiente sugerente pero no significativo: los municipios del tercil más pequeño (T1) registran un coeficiente de $-0.069$ ($p = 0.196$), el tercil medio (T2) de $-0.021$ ($p = 0.504$), y el tercil más grande (T3) de $0.003$ ($p = 0.823$).  Ninguno sobrevive la corrección BH.

Estos hallazgos sugieren que no existe evidencia robusta de heterogeneidad en el efecto del tratamiento a lo largo de las dimensiones de urbanización o tamaño municipal.

> **📖 Cómo leer la Tabla 4 — Heterogeneidad (paso a paso)**
>
> La Tabla 4 desglosa el efecto por subgrupo. La trampa principal es confundir
> significancia nominal con significancia real.
>
> **Regla de lectura:**
> 1. Busca filas con $p < 0.05$ → encontrarás solo "Metrópoli" ($p = 0.024$).
> 2. Lee la columna **q-value (BH)** → Metrópoli tiene $q = 0.215$.
> 3. Si $q > 0.10$, la significancia nominal es un probable falso positivo.
> 4. **Conclusión:** Ningún subgrupo sobrevive la corrección FDR → no hay
>    heterogeneidad robusta.
>
> Un $q = 0.215$ significa que si rechazaras esta hipótesis, aceptarías una
> tasa de falsos descubrimientos del ~22%, inaceptable por convención.

## 4.5  Discusión y conclusiones del análisis empírico

Los resultados presentados en esta sección conducen a una conclusión clara.  El modelo TWFE convencional no detecta efectos estadísticamente significativos en ninguno de los cinco indicadores primarios de inclusión financiera femenina.  Los coeficientes son cercanos a cero, económicamente irrelevantes, y robustos a múltiples especificaciones alternativas.

En términos sustantivos, los intervalos de confianza son suficientemente estrechos como para descartar efectos de magnitud económicamente relevante para la mayoría de los outcomes.  Para contratos totales, el IC 95% $[-0.035, 0.049]$ excluye efectos mayores al 5%.  Para saldo total, el IC es más amplio $[-0.092, 0.100]$ pero sigue siendo informativo.

Varias razones teóricas podrían explicar la ausencia de efectos detectables:

**Primer canal: oferta financiera parcialmente exógena y márgenes locales acotados.**  La distribución de sucursales, terminales punto de venta y ciertos productos financieros en México responde principalmente a decisiones de la banca comercial y a la regulación federal (CNBV), más que a la política municipal.  Los márgenes de acción de un gobierno local sobre la inclusión financiera podrían ser limitados.

**Segundo canal: horizonte temporal limitado.**  El panel abarca 17 trimestres (poco más de cuatro años).  Si los mecanismos operan gradualmente (confianza institucional, difusión, programas locales), los efectos podrían requerir un horizonte más largo para manifestarse.

**Tercer canal: heterogeneidad que se cancela en el promedio.**  Los análisis de heterogeneidad muestran signos opuestos entre subgrupos (positivo en metrópolis, negativo en municipios rurales), lo que sugiere que algunos efectos podrían estar presentes en subpoblaciones pero cancelarse en el promedio.  Sin embargo, estos resultados no sobreviven la corrección por múltiples pruebas.

**Cuarto canal: tratamiento difuso.**  La variable `alcaldesa_final` mide la presencia de una mujer en la presidencia municipal, pero no captura orientación programática, capacidad administrativa o intensidad de implementación.

En síntesis, dentro del horizonte temporal y la definición de tratamiento analizados, no encontramos evidencia de un efecto causal de la representación política femenina municipal sobre los indicadores de inclusión financiera de las mujeres.  Esta conclusión es robusta a múltiples especificaciones, y los nulos son informativos dado el poder estadístico razonable del diseño (ver MDES en `docs/16_MDES_PODER.md`).

---

## 4.6  Extensión recomendada: Stacked Difference-in-Differences

Dado que nuestro diseño presenta adopción escalonada —con 15 cohortes de tratamiento que se activan en distintos trimestres—, la literatura reciente de econometría aplicada recomienda complementar el TWFE con estimadores diseñados para evitar el sesgo de atenuación documentado por Goodman-Bacon (2021) y de Chaisemartin & D'Haultfoeuille (2020).

El estimador recomendado como extensión principal es el **Stacked DiD** (Cengiz, Dube, Lindner & Zipperer, 2019), que elimina las comparaciones contaminadas al restringir cada cohorte tratada a un grupo de control limpio de municipios never-treated.  La implementación implicaría:

1. **Construir sub-experimentos** por cada una de las 14 cohortes efectivas (excluyendo la cohorte $g = 0$ de 294 municipios left-censored), cada uno con una ventana de $[-4, +8]$ trimestres alrededor del evento.
2. **Apilar** los sub-datasets e incluir efectos fijos anidados de municipio×stack y periodo×stack.
3. **Estimar** el ATT promedio ponderado por tamaño de cohorte, con errores estándar clustered a nivel municipio original.

Esta extensión permitiría:
- Verificar si los nulos del TWFE persisten o si hay efectos enmascarados por el sesgo de atenuación.
- Realizar un event study dinámico dentro del diseño stacked, libre de comparaciones contaminadas.
- Implementar pruebas de robustez adicionales (ventanas alternativas, muestra absorbing-only).

Adicionalmente, se recomienda como robustez secundaria el estimador de **Callaway & Sant'Anna (2021)**, que ofrece una aproximación alternativa al mismo problema.

> **Nota:** La implementación del Stacked DiD es especialmente relevante para outcomes donde el TWFE reporta coeficientes cercanos a cero, dado que estos son precisamente los casos donde la teoría predice mayor potencial de sesgo de atenuación bajo adopción escalonada con efectos heterogéneos.
