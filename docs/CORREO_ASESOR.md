# Correo al asesor de tesis

---

**Asunto:** Avance de tesis — Resultados completos: alcaldesas e inclusión financiera

---

Hola,

Te escribo para contarte dónde va mi tesis. Te explico todo desde cero: qué hice, por qué tomé cada decisión y qué encontré. Te adjunto el reporte técnico completo (`TESIS_REPORTE_ASESOR.md`), pero aquí te resumo todo de manera narrativa.

---

## La pregunta

Mi tesis investiga si **tener una mujer como presidenta municipal (alcaldesa) tiene un efecto causal sobre la inclusión financiera de las mujeres en ese municipio**. La motivación es directa: si la representación política femenina puede mover indicadores económicos concretos como la tenencia de cuentas bancarias, tarjetas o créditos de las mujeres, eso tendría implicaciones para la política pública en materia de paridad de género.

---

## Los datos

Construí un panel que combina dos fuentes:

1. **Datos de la CNBV** (Comisión Nacional Bancaria y de Valores): indicadores trimestrales de inclusión financiera a nivel municipal, desagregados por género — contratos, saldos, tarjetas de débito, tarjetas de crédito, créditos hipotecarios.

2. **Registros electorales municipales**: compilé la información del género de la autoridad municipal para cada uno de los 2,471 municipios del país, día por día, a partir de institutos electorales estatales, gacetas de gobierno y portales oficiales.

El panel resultante tiene **41,905 observaciones** (2,471 municipios × 17 trimestres, de 2018Q3 a 2022Q3). Es prácticamente balanceado: solo 8 municipios tienen panel incompleto, representando el 0.24% de las celdas.

Elegí este periodo porque cubre al menos un ciclo electoral municipal completo y antecede a reformas regulatorias de inclusión financiera digital que podrían confundir la estimación a partir de 2023.

---

## La variable de tratamiento

Construir la variable de tratamiento (`alcaldesa_final`) fue uno de los retos más grandes del proyecto. El proceso tuvo tres etapas:

**Primero**, convertí los registros históricos de autoridades municipales a intervalos diarios. Cuando había traslapes (por interinatos), apliqué una regla determinística: se asigna la autoridad con fecha de inicio más reciente, que es como funciona institucionalmente.

**Segundo**, agregué de frecuencia diaria a trimestral usando una regla de mayoría: si una mujer gobernó más de la mitad de los días del trimestre, el tratamiento es 1. Esto es conceptualmente apropiado porque el análisis opera a frecuencia trimestral.

**Tercero**, la variable algorítmica tenía un 4.7% de valores faltantes por huecos en los registros históricos. Los corregí mediante auditoría manual, documentando cada corrección con su fuente verificable. La variable final tiene **cero valores faltantes**.

De las 41,905 observaciones, el **22.3% corresponde a municipios con alcaldesa**. A nivel de municipios: 1,476 (59.7%) nunca tuvieron alcaldesa en el periodo (*never-treated*), 894 (36.2%) cambiaron de estatus al menos una vez (*switchers*), y 101 (4.1%) tuvieron alcaldesa todo el periodo (*always-treated*). De los 894 switchers, solo **600 tienen periodo pre-tratamiento observable** y son los que identifican el efecto causal.

Un detalle importante: el tratamiento **no es absorbente** — 191 de los 600 switchers efectivos experimentan reversiones (la alcaldesa es reemplazada por un alcalde). Esto genera un ~12.5% de discrepancia entre la definición de tratamiento basada en el primer episodio y el estado actual, por lo que interpreto las estimaciones como **ITT** (Intent-to-Treat), que es estándar en economía política.

---

## El análisis exploratorio (EDA)

Antes de estimar cualquier modelo, hice un EDA exhaustivo que generó **12 recomendaciones**, todas implementadas y validadas con 43 tests automatizados. Las decisiones más importantes fueron:

**Normalización per cápita.** Los indicadores financieros en bruto miden "tamaño del municipio", no inclusión financiera. La correlación entre conteos brutos de contratos y población es del 67-70%. Normalicé dividiendo entre la población adulta femenina y multiplicando por 10,000 (la convención de la CNBV y el Banco Mundial). Ahora un valor de 3,324 significa "3,324 contratos por cada 10,000 mujeres adultas".

**Transformación asinh.** Las distribuciones per cápita son extremadamente sesgadas (ratio media/mediana de 6x en conteos, 390x en saldos) y contienen ceros legítimos (municipios rurales sin actividad financiera en ciertos productos). Usé la transformación seno hiperbólico inverso, que se comporta como un logaritmo para valores grandes pero está definida en cero y no requiere constantes arbitrarias. Los coeficientes se interpretan como semi-elasticidades aproximadas (Bellemare & Wichman, 2020). Verifiqué empíricamente que las especificaciones en nivel son inestables y dominadas por outliers — esto confirma que la transformación es necesaria, no una elección cosmética.

**Otras transformaciones.** Creé variables winsorizadas (percentil 1-99) para robustez, ratios de brecha de género M/H, la variable `ever_alcaldesa` para clasificar municipios, una variable de intensidad de tratamiento (`alcaldesa_acumulado` = trimestres acumulados con alcaldesa), y corregí 2 municipios sin clasificación de tipo de población.

---

## Los 5 outcomes que estudio

Seleccioné 5 indicadores que cubren un gradiente de acceso financiero:

| Outcome | Qué mide |
|:---|:---|
| Contratos totales (mujeres) | Acceso agregado al sistema formal |
| Tarjetas de débito (mujeres) | Acceso transaccional básico |
| Tarjetas de crédito (mujeres) | Acceso a crédito de consumo |
| Créditos hipotecarios (mujeres) | Acceso a crédito de largo plazo |
| Saldo total (mujeres) | Profundización financiera |

Todos se expresan en escala asinh de la tasa per cápita por 10,000 mujeres adultas.

---

## Estadísticas descriptivas (Tabla 1)

La Tabla 1 compara los tres grupos **antes del tratamiento**:

- Los switchers (municipios que eventualmente tendrán alcaldesa) son ligeramente más grandes y urbanos que los never-treated: ln(Pob) = 9.95 vs. 9.44, lo que equivale a ~21,000 vs. ~12,600 habitantes.
- Los switchers tienen medias ~10% más altas en contratos totales y tarjetas, lo cual es esperable dado que municipios más urbanos tienden a tener mayor participación política femenina Y mayor infraestructura financiera.
- Esto **no es problemático** para el DiD porque los efectos fijos de municipio absorben todas las diferencias permanentes. Lo que importa es que las **tendencias** sean paralelas, no los niveles.
- Los créditos hipotecarios tienen una media muy baja (39 por 10,000 mujeres), reflejando que muchos municipios rurales simplemente no tienen este producto. Esto limita el poder estadístico para ese outcome específico.

**Veredicto:** Datos sensatos, diferencias explicables, N suficiente. Proceder al event study.

---

## Estrategia de identificación

Uso un diseño de **diferencias en diferencias (DiD)** con un modelo de efectos fijos bidireccionales (TWFE):

$$Y_{it} = \alpha_i + \gamma_t + \beta \cdot D_{it} + \delta \cdot \log(\text{pob})_{it} + \varepsilon_{it}$$

- $\alpha_i$: efecto fijo de municipio (2,471 dummies) — absorbe toda heterogeneidad permanente
- $\gamma_t$: efecto fijo de periodo (17 dummies) — absorbe shocks agregados (COVID, regulación)
- $D_{it}$: `alcaldesa_final` (0/1)
- Errores estándar clusterizados a nivel municipio
- Único control adicional: `log_pob` (predeterminada respecto al tratamiento)

No incluyo outcomes masculinos como controles (serían *bad controls* — potencialmente afectados por spillover), ni PIB municipal (no disponible trimestralmente), ni indicadores totales (mecánicamente endógenos porque incluyen el outcome femenino).

El supuesto clave es **tendencias paralelas**: en ausencia de tratamiento, los municipios que reciben alcaldesa habrían seguido la misma trayectoria en inclusión financiera que los que no. Esto se evalúa con el event study.

---

## Event study: ¿se sostienen las tendencias paralelas?

Estimé un event study con 4 leads y 8 lags (K=4, L=8), periodo de referencia k=-1, con endpoint binning. El test conjunto de Wald evalúa si todos los coeficientes pre-tratamiento son simultáneamente cero:

| Outcome | p-valor | ¿Pasa al 10%? |
|:---|---:|:---:|
| Contratos totales | 0.139 | Sí |
| Tarjetas débito | 0.284 | Sí |
| Tarjetas crédito | 0.083 | Borderline |
| Créditos hipotecarios | 0.861 | Sí |
| Saldo total | 0.319 | Sí |

**4 de 5 pasan.** Tarjetas de crédito es borderline ($p = 0.083$), pero al extender la ventana a K=6 leads (más granularidad), pasa con $p = 0.212$. El borderline se origina en el bin extremo ($k \leq -4$) que acumula periodos lejanos con señal heterogénea. Los leads individuales $k = -3$ y $k = -2$ no son significativos.

**Conclusión:** Las tendencias paralelas se sostienen razonablemente para los 5 outcomes. El diseño DiD es creíble.

---

## Resultado principal: TWFE (Tabla 2)

Aquí está el resultado central de la tesis:

| Outcome | Coeficiente | Error estándar | p-valor |
|:---|---:|---:|---:|
| Contratos totales | 0.007 | 0.022 | 0.747 |
| Tarjetas débito | -0.014 | 0.021 | 0.521 |
| Tarjetas crédito | -0.002 | 0.017 | 0.919 |
| Créditos hipotecarios | 0.018 | 0.021 | 0.400 |
| Saldo total | 0.004 | 0.049 | 0.931 |

**No encontré evidencia de un efecto estadísticamente significativo en ninguno de los 5 outcomes.** Los coeficientes son cercanos a cero (entre -0.014 y +0.018 en escala asinh), económicamente irrelevantes (el más grande equivale a un cambio de ~1.8%), y todos los p-valores superan 0.40.

Para ponerlo en contexto: el intervalo de confianza al 95% para contratos totales es [-0.035, 0.049], lo que significa que puedo descartar efectos mayores al ~5% en cualquier dirección.

---

## Robustez

El resultado nulo es **robusto** a cinco pruebas:

1. **Cambiar la transformación** a log(1+y) o winsorizar: mismos coeficientes (~0.005 a 0.008).
2. **Excluir trimestres de transición** (donde cambia la autoridad): coeficiente = 0.002, sigue nulo.
3. **Placebo temporal** (adelantar el tratamiento 4 trimestres): coeficiente = -0.019, no significativo. No hay tendencias confundentes.
4. **Placebo de género** (usar outcomes masculinos): coeficiente = -0.001. Si la alcaldesa afectara la inclusión financiera en general (no solo de mujeres), veríamos efecto también en hombres. No lo hay.

Todas las estimaciones de robustez caen en el rango [-0.019, 0.008]. El nulo no es un artefacto de ninguna decisión metodológica.

---

## Heterogeneidad

Exploré si el efecto promedio nulo esconde efectos heterogéneos por tipo de municipio. Dividí la muestra por la clasificación de tipo de población (Rural, En Transición, Semi-urbano, Urbano, Semi-metrópoli, Metrópoli) y por terciles de población.

Solo un subgrupo muestra significancia nominal: **Metrópoli** ($\hat{\beta} = 0.030$, $p = 0.024$). Sin embargo, al corregir por comparaciones múltiples con Benjamini-Hochberg, el q-value sube a 0.215 — **no sobrevive la corrección FDR**. Con 9 subgrupos evaluados simultáneamente, un falso positivo es esperable por azar.

Los municipios rurales muestran un coeficiente negativo notable ($\hat{\beta} = -0.104$, $p = 0.109$) pero tampoco alcanza significancia.

**Conclusión:** No hay heterogeneidad robusta. El efecto parece homogéneamente nulo a través de todas las dimensiones evaluadas.

---

## Poder estadístico

Dado que el resultado es nulo, es crucial preguntarse: ¿tenía poder suficiente para detectar un efecto si lo hubiera? El Minimum Detectable Effect Size (MDES) responde esto.

Para contratos totales: MDES = 2.80 × 0.022 ≈ 0.062 en escala asinh ≈ **6.4%**. Esto significa que puedo descartar efectos mayores al 6.4% con 80% de poder. Dado que los efectos en la literatura de representación política sobre outcomes económicos suelen ser de un dígito porcentual, **el nulo es razonablemente informativo**: no es que me falte poder para ver algo grande, sino que probablemente no hay un efecto de magnitud relevante para política pública.

---

## ¿Por qué no hay efecto? Cuatro hipótesis

1. **La oferta financiera es mayormente federal.** La banca comercial y la regulación de la CNBV determinan la distribución de productos financieros más que la política municipal. Los márgenes de acción de una alcaldesa son acotados.

2. **El horizonte temporal es corto.** Cuatro años puede ser insuficiente para que mecanismos graduales (confianza institucional, difusión de programas) se materialicen en los indicadores.

3. **Heterogeneidad que se cancela.** Hay indicios de efectos opuestos por tipo de municipio (positivo en metrópolis, negativo en rurales), pero ninguno sobrevive corrección por multiplicidad. Estos podrían cancelarse en el promedio.

4. **Tratamiento difuso.** La variable mide el género de la autoridad, no su agenda, capacidad de gestión o prioridades. Dos alcaldesas pueden tener administraciones radicalmente distintas.

---

## Extensiones pendientes

1. **Stacked DiD** — Es la extensión más importante. El TWFE con adopción escalonada puede sufrir sesgo de atenuación (Goodman-Bacon, 2021). El Stacked DiD elimina las comparaciones contaminadas y podría revelar efectos que el TWFE promedia a cero. Ya tengo el diseño metodológico listo.

2. **Margen extensivo** — Evaluar si la alcaldesa afecta la probabilidad de que un municipio tenga *algún* producto financiero femenino (variable binaria, modelo LPM).

3. **Composición de género** — Evaluar si la proporción de mujeres en el total de productos financieros cambia con la alcaldesa, incluso si el nivel total no se mueve.

---

## Estado del repositorio

Todo el código es reproducible. El pipeline completo se ejecuta con un solo comando (`python -m tesis_alcaldesas.run_all`) y genera todas las tablas (CSV + LaTeX) y figuras (PDF + PNG). La documentación incluye 24 archivos numerados que explican cada decisión desde el EDA hasta los resultados.

---

## Preguntas para la reunión

1. ¿Te parece adecuado presentar el Stacked DiD como extensión o debería ser la especificación principal?
2. Dado el resultado nulo, ¿cómo debería enmarcar la contribución de la tesis?
3. ¿Me sugieres algún análisis adicional de heterogeneidad o algún outcome alternativo?
4. ¿Tengo que correr la extensión del Stacked DiD antes de la defensa o basta con el TWFE?

Quedo atenta a tus comentarios. Te adjunto el reporte técnico completo y te puedo compartir el repositorio si quieres revisar el código.

Saludos,

Ana Paula
