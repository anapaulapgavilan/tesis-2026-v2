> **Archivos fuente:**
> - `docs/09_MODELADO_PROPUESTA.md` (documento técnico que aquí se explica)
> - `src/models/02_twfe.py`
> - `src/models/03_event_study.py`
> - `src/models/04_robustness.py`
> - `src/models/05_heterogeneity.py`

# Explicación del Modelado Econométrico — De Cero a la Ecuación Final

## Guía tutorial paso a paso para entender la estrategia empírica de la tesis

**Documento explicativo de:** `docs/09_MODELADO_PROPUESTA.md`  
**Continuación de:** `docs/05_EDA_EXPLICACION_4.md` y `docs/07_DATA_CONTRACT.md`  
**Fecha:** Marzo 2026  

---

> **Objetivo de este documento:** Explicar desde cero, como si el lector nunca hubiera
> tomado un curso de econometría, cada concepto que aparece en la propuesta de modelado.
> No se asume conocimiento previo de diferencias en diferencias, datos panel, efectos
> fijos ni event studies. Cada sección construye sobre la anterior, de modo que al
> terminar de leer, el lector pueda entender exactamente qué se está estimando, por
> qué se eligió esta estrategia, y cómo interpretar los resultados.

---

## Tabla de contenido

| # | Sección | Pregunta que responde |
|---|---------|----------------------|
| 1 | ¿Qué son los datos panel? | ¿Qué tipo de datos tenemos y por qué importa? |
| 2 | ¿Qué es un experimento natural? | ¿Por qué no podemos hacer un experimento de laboratorio? |
| 3 | ¿Qué es Diferencias en Diferencias (DiD)? | ¿Cuál es la idea central de nuestra estrategia? |
| 4 | El supuesto de tendencias paralelas | ¿Cuándo funciona el DiD y cuándo no? |
| 5 | ¿Qué son los efectos fijos? | ¿Para qué sirven los $\alpha_i$ y $\gamma_t$ en la ecuación? |
| 6 | El modelo TWFE: nuestra ecuación principal | ¿Qué significa cada símbolo en la fórmula? |
| 7 | Variables de control: ¿por qué solo `log_pob`? | ¿No deberíamos controlar por más cosas? |
| 8 | Leads y lags: el lenguaje del tiempo | ¿Qué son esas variables _f1, _l1, y para qué sirven? |
| 9 | El event study: la prueba diagnóstica | ¿Cómo verificamos que nuestro método funciona? |
| 10 | El problema del tratamiento escalonado | ¿Por qué el TWFE clásico puede fallar? |
| 11 | Trabajo futuro: estimadores modernos | ¿Qué extensiones se recomiendan para fortalecer los resultados? |
| 12 | Robustez: ¿los resultados son creíbles? | ¿Cómo probamos que no estamos viendo espejismos? |
| 13 | Heterogeneidad: ¿el efecto es igual para todos? | ¿Hay municipios donde el efecto es más fuerte? |
| 14 | El modelo final: resumen de la estrategia completa | ¿Qué vamos a estimar exactamente y cómo? |
| 15 | Glosario de términos | Referencia rápida de conceptos |

---

## 1. ¿Qué son los datos panel?

### 1.1 Tres tipos de datos en economía

Antes de hablar de modelos, necesitamos entender qué tipo de datos tenemos. En economía
cuantitativa hay tres estructuras principales:

| Tipo | Descripción | Ejemplo |
|------|------------|---------|
| **Corte transversal** (cross-section) | Muchas unidades observadas en **un solo momento** | Encuesta de 2,471 municipios en un trimestre |
| **Serie de tiempo** (time series) | **Una sola unidad** observada a lo largo de muchos periodos | El PIB de México cada trimestre de 2018 a 2022 |
| **Datos panel** | **Muchas unidades** observadas en **muchos periodos** | 2,471 municipios × 17 trimestres = 41,905 observaciones |

### 1.2 Nuestro panel

Nuestros datos son un **panel balanceado**: cada municipio aparece exactamente en cada
uno de los 17 trimestres (Q3/2018 a Q3/2022). No hay huecos.

```
Municipio    |  2018Q3  |  2018Q4  |  2019Q1  |  ...  |  2022Q3
-------------|----------|----------|----------|-------|----------
Aguascalientes|  obs 1  |  obs 2   |  obs 3   |  ...  |  obs 17
Tijuana       |  obs 1  |  obs 2   |  obs 3   |  ...  |  obs 17
...           |   ...   |   ...    |   ...    |  ...  |   ...
Mérida        |  obs 1  |  obs 2   |  obs 3   |  ...  |  obs 17
```

- **2,471 municipios** (filas): cada uno es una "unidad" de análisis
- **17 trimestres** (columnas temporales): cada uno es un "periodo"
- **41,905 observaciones** = 2,471 × 17

### 1.3 ¿Por qué importa tener un panel?

La ventaja crucial del panel sobre un corte transversal es que podemos observar
**al mismo municipio a lo largo del tiempo**. Esto nos permite:

1. **Ver qué cambia dentro de cada municipio** (variación *within*): si Oaxaca de
   Juárez pasa de no tener alcaldesa a tener alcaldesa, podemos comparar la inclusión
   financiera de Oaxaca *consigo misma* antes y después del cambio.

2. **Controlar por todo lo que no cambia** en el municipio: su geografía, su cultura,
   su nivel histórico de desarrollo. Estos factores son "fijos" en el tiempo y el panel
   nos permite eliminarlos (esto son los **efectos fijos**, que veremos en la Sección 5).

3. **Separar la causa del efecto** (con las herramientas correctas): observar al mismo
   municipio antes y después nos acerca a una inferencia causal, porque estamos
   comparando "manzanas con manzanas" a lo largo del tiempo.

> **Analogía:** Imagina que quieres saber si hacer ejercicio mejora tu salud. Un corte
> transversal compara a muchas personas distintas en un momento (pero las que hacen
> ejercicio pueden ser más sanas de origen). Un panel te sigue *a ti* a lo largo de
> meses: compara tu salud antes y después de empezar a ejercitarte. El segundo diseño
> es mucho más convincente.

---

## 2. ¿Qué es un experimento natural?

### 2.1 El problema fundamental de la inferencia causal

Queremos responder: **¿Tener una alcaldesa causa más inclusión financiera para las
mujeres?**

El estándar de oro para responder preguntas causales es un **experimento aleatorio
controlado** (como en medicina): tomar 2,471 municipios, sortear al azar cuáles tienen
alcaldesa, y comparar los resultados. Pero no podemos hacer eso — las alcaldesas llegan
al poder por elección democrática, no por sorteo.

### 2.2 La solución: explotar la variación "natural"

Un **experimento natural** ocurre cuando un evento del mundo real genera variación en
el tratamiento que *se parece* a un experimento aleatorio, aunque no lo sea.

En nuestro caso, el "experimento natural" es el **ciclo electoral municipal**:
- En ciertos municipios, una mujer ganó la elección y se convirtió en alcaldesa.
- En otros municipios (similares en muchos aspectos), un hombre ganó.

La pregunta clave es: ¿podemos argumentar que la llegada de una alcaldesa es
*suficientemente aleatoria* como para comparar estos dos grupos? No necesitamos
aleatorización perfecta — necesitamos que, **condicional a nuestros controles**,
los municipios tratados y no tratados hubieran seguido la misma trayectoria en
ausencia del tratamiento.

### 2.3 Nuestra variación específica

| Concepto | En nuestros datos |
|----------|------------------|
| **Tratamiento** | `alcaldesa_final = 1` (el municipio tiene alcaldesa en ese trimestre) |
| **Grupo tratado** | 894 municipios "switchers" en total; **600 con periodo pre-tratamiento** (usados en event study y Stacked DiD). Los 294 restantes están left-censored (`first_treat_t = 0`) y se excluyen |
| **Grupo de control** | 1,476 municipios que nunca tienen alcaldesa en el panel |
| **Evento natural** | Elecciones municipales de 2018 y 2021 |
| **Outcome** | Inclusión financiera de las mujeres (cuentas, tarjetas, créditos, saldos) |

> **Clave:** No estamos diciendo que las elecciones son aleatorias. Estamos diciendo
> que, *controlando por las características fijas del municipio* (con efectos fijos),
> la *trayectoria temporal* de la inclusión financiera habría sido similar entre
> municipios que eligen alcaldesa y los que no. Eso es el **supuesto de tendencias
> paralelas**, que explicaremos en la Sección 4.

---

## 3. ¿Qué es Diferencias en Diferencias (DiD)?

### 3.1 La idea en una oración

DiD (Differences-in-Differences) estima el efecto causal de un tratamiento calculando
la **diferencia** en el cambio temporal entre un grupo tratado y un grupo de control.
Son dos diferencias:

1. **Primera diferencia:** El cambio *antes vs. después* del tratamiento en el grupo tratado.
2. **Segunda diferencia:** El cambio *antes vs. después* en el grupo de control (que no recibió tratamiento).
3. **DiD:** Restar la segunda de la primera.

### 3.2 Ejemplo numérico con nuestros datos

Supongamos (números ficticios para ilustrar):

| Grupo | Antes (2018Q3) | Después (2021Q4) | Cambio |
|-------|---------------:|------------------:|-------:|
| Municipios con alcaldesa nueva | 500 cuentas/10k mujeres | 580 cuentas/10k mujeres | +80 |
| Municipios sin alcaldesa | 480 cuentas/10k mujeres | 540 cuentas/10k mujeres | +60 |

- **Cambio en tratados:** +80
- **Cambio en controles:** +60
- **DiD = 80 − 60 = +20** ← Este es el efecto estimado de tener alcaldesa

### 3.3 ¿Por qué necesitamos la segunda diferencia?

Porque muchas cosas cambian con el tiempo que afectan a *todos* los municipios:

- La economía crece → más cuentas bancarias para todos
- La banca digital se expande (COVID‑19) → más inclusión financiera general
- Nuevas regulaciones de la CNBV → cambios en todo el sistema

Sin el grupo de control, diríamos: "Las cuentas subieron 80, ¡es por la alcaldesa!"
Pero 60 de esos 80 habrían ocurrido de todos modos (por la tendencia general). El
efecto *real* de la alcaldesa es solo 20.

### 3.4 Visualización gráfica del DiD

```
Cuentas
por 10k    
mujeres    
  |
600|                        ● Tratados (observado)
   |                      /
580|                    /          ← Efecto DiD = 20
   |                  /
560|              . . . . ○ Tratados (contrafactual)
   |            /       /
540|          /       /      ● Control (observado)
   |        /       /
520|      /       /
   |    /       /
500|  ●       /
   |        /
480|      ●
   |
   |-----|---------|------->
        Antes    Después     Tiempo
         (pre)    (post)

● = observado    ○ = contrafactual (hipotético)
```

La línea punteada (contrafactual) es lo que *habría pasado* en los municipios
tratados si no hubieran tenido alcaldesa. Como no podemos observarla directamente,
la estimamos con la pendiente del grupo de control. **Eso solo funciona si ambos
grupos tenían la misma tendencia antes del tratamiento** (tendencias paralelas).

### 3.5 El DiD en forma de ecuación simple

$$
\hat{\beta}_{\text{DiD}} = \underbrace{(\bar{Y}_{\text{tratados, post}} - \bar{Y}_{\text{tratados, pre}})}_{\text{1ª diferencia: cambio en tratados}} - \underbrace{(\bar{Y}_{\text{control, post}} - \bar{Y}_{\text{control, pre}})}_{\text{2ª diferencia: cambio en controles}}
$$

Este es el DiD en su forma más básica (con 2 grupos y 2 periodos). Nuestro caso es
más complejo porque tenemos 2,471 municipios, 17 periodos, y el tratamiento no empieza
al mismo tiempo para todos. Eso nos lleva al **TWFE** (Sección 6).

---

## 4. El supuesto de tendencias paralelas

### 4.1 ¿Qué es?

El supuesto de **tendencias paralelas** (parallel trends) es la piedra angular del DiD.
Dice:

> *En ausencia del tratamiento, el grupo tratado y el grupo de control habrían seguido
> la misma trayectoria temporal en el outcome.*

No dice que los dos grupos *sean iguales* — los municipios con alcaldesa pueden tener
niveles de inclusión financiera distintos desde siempre. Lo que dice es que el *ritmo
de cambio* habría sido el mismo.

### 4.2 Ejemplo visual

**Tendencias paralelas se cumplen ✅:**
```
Y |
  |     Tratados ────────·····●  ← divergen solo después del tratamiento
  |                    /
  |     Control ──────────────●
  |
  |-----|------------|---------> t
      pre-tto      tto
```

**Tendencias paralelas NO se cumplen ❌:**
```
Y |
  |     Tratados ───────╱─────●  ← ya divergían ANTES del tratamiento
  |                   /
  |     Control ──────────────●
  |
  |-----|------------|---------> t
      pre-tto      tto
```

En el segundo caso, el grupo tratado ya estaba creciendo más rápido *antes* de la
alcaldesa. Si usamos DiD, atribuiríamos erróneamente esa tendencia preexistente al
efecto de la alcaldesa.

### 4.3 ¿Podemos probar el supuesto?

**No directamente**, porque no podemos observar el contrafactual (qué habría pasado
si el grupo tratado no hubiera sido tratado). Pero podemos hacer una prueba
*indirecta*: verificar que las tendencias eran paralelas **antes** del tratamiento.
Si los dos grupos iban a la par durante los periodos previos, es razonable creer que
habrían seguido así sin el tratamiento.

Esta prueba indirecta se hace con el **event study** (Sección 9). Los coeficientes
pre-tratamiento del event study nos dicen si los grupos divergían antes del
tratamiento.

### 4.4 ¿Qué pasa si el supuesto no se cumple?

Si los pre-trends son significativamente distintos de cero, el DiD no es creíble
para ese outcome. Las opciones son:

1. **Si solo falla el lead inmediato (−1):** Puede ser efecto de anticipación; se
   recodifica el timing del tratamiento.
2. **Si fallan varios leads:** La estrategia es débil. Se puede intentar agregar
   tendencias lineales por municipio, pero es una solución parcial.
3. **Si el patrón es sistemático:** Hay que considerar estrategias alternativas
   (matching + DiD, variables instrumentales, etc.).

> **Para nuestra tesis:** El event study se implementa en `src/models/03_event_study.py`.
> Si los pre-trends son planos (cercanos a cero), podemos proceder con confianza.

---

## 5. ¿Qué son los efectos fijos?

### 5.1 El problema que resuelven

Cuando comparamos municipios, hay muchas diferencias entre ellos que podrían confundir
nuestros resultados:

- Monterrey tiene más sucursales bancarias que un municipio rural de Oaxaca
- La CDMX tiene una cultura financiera distinta a un municipio de Guerrero
- Municipios norteños tienen históricamente más actividad económica

Si no controlamos por estas diferencias, nuestro $\hat{\beta}$ podría capturar la
diferencia entre municipios ricos y pobres en vez del efecto de la alcaldesa.

### 5.2 ¿Qué es un efecto fijo?

Un **efecto fijo** es un término en la ecuación de regresión que captura *todo lo que
es específico de una unidad y no cambia en el tiempo*. En la práctica, es como poner
una variable dummy (0/1) para cada municipio.

$$
Y_{it} = \underbrace{\alpha_i}_{\text{efecto fijo de municipio}} + \cdots
$$

- $\alpha_{\text{Monterrey}}$ captura todo lo que hace especial a Monterrey y no
  cambia entre 2018 y 2022: su ubicación, su nivel de desarrollo histórico, su
  infraestructura bancaria base, etc.
- $\alpha_{\text{Tlaxiaco}}$ captura lo mismo para Tlaxiaco.

**Efecto práctico:** Al incluir $\alpha_i$, ya no comparamos Monterrey con Tlaxiaco.
Comparamos *Monterrey consigo mismo* a lo largo del tiempo (variación *within*). Esto
elimina automáticamente toda la heterogeneidad entre municipios que no cambia.

### 5.3 Dos tipos de efectos fijos en nuestro modelo

| Efecto fijo | Notación | Qué absorbe | Ejemplo de lo que controla |
|-------------|----------|------------|---------------------------|
| **De municipio** ($\alpha_i$) | 2,471 dummies | Todo lo que es específico del municipio y constante en el tiempo | Geografía, cultura, infraestructura bancaria histórica, nivel de desarrollo, tamaño |
| **De periodo** ($\gamma_t$) | 17 dummies | Todo lo que afecta a todos los municipios por igual en un periodo dado | COVID-19, cambios regulatorios de la CNBV, política monetaria nacional, expansión de fintech |

### 5.4 Ejemplo concreto

Supongamos que en 2020Q2 la inclusión financiera subió en *todos* los municipios porque
la pandemia aceleró la bancarización digital. Sin $\gamma_t$, podríamos pensar que ese
aumento en los municipios tratados se debe a la alcaldesa. Pero $\gamma_{2020Q2}$ absorbe
ese shock general, dejando solo la variación idiosincrática de cada municipio.

### 5.5 ¿Por qué se llaman "fijos"?

Porque tratamos al $\alpha_i$ como un parámetro *fijo* (no aleatorio) que estimamos.
Hay otra alternativa (efectos *aleatorios*) que trata al $\alpha_i$ como una variable
aleatoria, pero requiere un supuesto muy fuerte: que $\alpha_i$ no esté correlacionado
con las variables explicativas. En DiD, ese supuesto casi nunca se cumple (los
municipios con alcaldesa probablemente difieren sistemáticamente de los que no la
tienen), así que **siempre usamos efectos fijos**.

### 5.6 ¿Qué NO absorben los efectos fijos?

Los efectos fijos no controlan por cosas que **cambian en el tiempo y son específicas
de cada municipio**. Por ejemplo:

- Un boom económico local en un municipio específico durante 2021
- Una sequía que afecta la actividad económica de cierta región
- La apertura de un nuevo centro financiero en un municipio particular

Para eso necesitaríamos controles time-varying adicionales (como `log_pob`). Pero
debemos ser cuidadosos de no incluir "bad controls" (Sección 7).

> **Dato técnico:** En Python, PanelOLS de `linearmodels` implementa los efectos fijos
> con la opción `entity_effects=True` (para $\alpha_i$) y `time_effects=True` (para
> $\gamma_t$). Internamente, hace una transformación *within* que resta la media de
> cada municipio y cada periodo.

---

## 6. El modelo TWFE: nuestra ecuación principal

### 6.1 ¿Qué significa TWFE?

**TWFE** = Two-Way Fixed Effects = Efectos fijos bidireccionales. "Bidireccional" porque
tiene efectos fijos en las dos dimensiones del panel:

1. **Dimensión de unidades** (municipios): $\alpha_i$
2. **Dimensión temporal** (trimestres): $\gamma_t$

### 6.2 La ecuación, símbolo por símbolo

$$
Y_{it} = \alpha_i + \gamma_t + \beta \cdot D_{it} + \delta \cdot \log\_\text{pob}_{it} + \varepsilon_{it}
$$

Vamos pieza por pieza:

| Símbolo | Nombre | Qué representa | En nuestros datos |
|---------|--------|---------------|-------------------|
| $Y_{it}$ | Variable dependiente | Lo que queremos explicar | `ncont_total_m_pc_asinh` (cuentas totales de mujeres per cápita, transformación asinh) |
| $i$ | Subíndice de municipio | Identifica la unidad | $i = 1, 2, \ldots, 2{,}471$ |
| $t$ | Subíndice de tiempo | Identifica el periodo | $t = \text{2018Q3}, \text{2018Q4}, \ldots, \text{2022Q3}$ |
| $\alpha_i$ | Efecto fijo de municipio | Nivel base de cada municipio | Son 2,471 constantes (una por municipio) |
| $\gamma_t$ | Efecto fijo de periodo | Shock común en cada trimestre | Son 17 constantes (una por trimestre) |
| $\beta$ | **Parámetro de interés** | El efecto promedio de tener alcaldesa | Esto es lo que queremos estimar |
| $D_{it}$ | Tratamiento | 1 si el municipio $i$ tiene alcaldesa en $t$; 0 si no | `alcaldesa_final` |
| $\delta$ | Coeficiente del control | Efecto de la población sobre el outcome | Coeficiente de `log_pob` |
| $\log\_\text{pob}_{it}$ | Control | Logaritmo de la población | `log_pob` en nuestro panel |
| $\varepsilon_{it}$ | Error | Todo lo que el modelo no captura | Variación inexplicada, shocks idiosincráticos |

### 6.3 ¿Qué hace cada pieza?

Pensemos en un municipio concreto, digamos **Oaxaca de Juárez**, en el trimestre
**2021Q4** (cuando una alcaldesa asume el cargo):

$$
Y_{\text{Oaxaca, 2021Q4}} = \underbrace{\alpha_{\text{Oaxaca}}}_{\text{nivel base de Oaxaca}} + \underbrace{\gamma_{\text{2021Q4}}}_{\text{shock del trimestre}} + \underbrace{\beta \times 1}_{\text{efecto alcaldesa}} + \underbrace{\delta \times \log(\text{pob}_{\text{Oaxaca, 2021Q4}})}_{\text{ajuste por tamaño}} + \varepsilon
$$

Y para el mismo municipio **un trimestre antes** (2021Q3, antes de la alcaldesa):

$$
Y_{\text{Oaxaca, 2021Q3}} = \alpha_{\text{Oaxaca}} + \gamma_{\text{2021Q3}} + \beta \times 0 + \delta \times \log(\text{pob}_{\text{Oaxaca, 2021Q3}}) + \varepsilon
$$

La diferencia temporal **dentro de Oaxaca** elimina $\alpha_{\text{Oaxaca}}$ (porque
es la misma constante en ambos periodos), y lo que queda es el efecto del tratamiento
$\beta$ más el cambio en el shock temporal ($\gamma_{\text{2021Q4}} - \gamma_{\text{2021Q3}}$).
A su vez, ese shock temporal se identifica con los municipios de control que no tuvieron
cambio de tratamiento en ese periodo. Así es como el TWFE implementa el DiD en un
panel con muchos municipios y periodos.

### 6.4 ¿Cómo se interpreta $\hat{\beta}$?

El símbolo $\hat{\beta}$ (con "sombrero") es la *estimación* de $\beta$ — el número
que sale de correr la regresión con nuestros datos.

La interpretación depende de la escala de $Y$:

| Escala de $Y$ | Interpretación de $\hat{\beta}$ | Ejemplo |
|---------------|-------------------------------|---------|
| **asinh** (nuestra principal) | $\hat{\beta} \approx$ cambio porcentual en el outcome | Si $\hat{\beta} = 0.05$: tener alcaldesa se asocia con ~5% más cuentas |
| **nivel per cápita** | $\hat{\beta}$ = cambio en unidades absolutas por 10k mujeres | Si $\hat{\beta} = 20$: 20 cuentas más por cada 10k mujeres |
| **log(1+Y)** | $\hat{\beta} \approx$ cambio porcentual (similar a asinh) | Similar a asinh para valores grandes |

> **¿Por qué usamos asinh?** Porque las distribuciones per cápita son muy sesgadas
> (hay municipios con 0 cuentas y municipios con miles). La transformación asinh
> comprime los extremos y permite interpretar los coeficientes como cambios
> porcentuales. Se verificó empíricamente (marzo 2026) que las especificaciones en
> nivel son inestables — signos cambian entre outcomes, dominados por outliers
> metropolitanos. Ver `docs/05_EDA_EXPLICACION_4.md` §11.9.

### 6.5 ¿De dónde viene la identificación?

Descomponemos la forma en que $\hat{\beta}$ se estima:

1. $\alpha_i$ absorbe toda diferencia fija entre municipios → no comparamos municipios
   ricos con pobres.
2. $\gamma_t$ absorbe todo shock que afecta a todos igual → no confundimos COVID con
   alcaldesa.
3. Lo que queda es la **variación within**: municipios que cambian de $D_{it} = 0$ a
   $D_{it} = 1$ comparados con municipios que no cambian en el mismo periodo.

Eso es exactamente el DiD, pero implementado en un marco de regresión.

### 6.6 Errores estándar clusterizados

Cuando decimos que $\hat{\beta} = 0.05$, necesitamos saber si es *estadísticamente
significativo* o si podría ser simplemente ruido. Para eso calculamos errores estándar
(SE), que miden la incertidumbre de la estimación.

**¿Por qué "clusterizar" a nivel municipio?** Porque las observaciones de un mismo
municipio a lo largo del tiempo no son independientes: si Monterrey tiene alta
inclusión financiera en 2019Q1, probablemente también la tiene en 2019Q2. Si ignoramos
esta correlación serial, los errores estándar son artificialmente pequeños y declaramos
efectos significativos cuando no lo son.

La solución es **clusterizar** los errores estándar a nivel municipio: permitimos que
las observaciones dentro del mismo municipio estén correlacionadas de forma arbitraria.
Esto da intervalos de confianza más anchos (más honestos).

| Sin clustering | Con clustering a nivel municipio |
|---------------|-------------------------------|
| SE muy pequeños | SE más grandes (más realistas) |
| Muchos falsos positivos | Inferencia honesta |
| Asume independencia entre periodos | Permite correlación serial arbitraria |

> **En Python:** `PanelOLS(..., check_rank=False).fit(cov_type='clustered', cluster_entity=True)`

---

## 7. Variables de control: ¿por qué solo `log_pob`?

### 7.1 ¿Qué es un control y para qué sirve?

Una **variable de control** es una variable que incluimos en la regresión para evitar
que su efecto se confunda con el del tratamiento. La idea es: si dos municipios difieren
en tamaño y eso afecta tanto a la inclusión financiera como a la probabilidad de tener
alcaldesa, necesitamos "controlar" por tamaño.

### 7.2 El principio de los controles en DiD: menos es más

En un diseño DiD con efectos fijos, **la mayoría de las cosas ya están controladas**:

| ¿Qué necesito controlar? | ¿Quién lo controla? | Ejemplo |
|--------------------------|--------------------|---------| 
| Todo lo que no cambia en el municipio | $\alpha_i$ (efecto fijo de municipio) | Geografía, cultura, infraestructura base |
| Todo lo que cambia igual para todos | $\gamma_t$ (efecto fijo de periodo) | COVID, política monetaria, regulación CNBV |
| Lo que cambia distinto por municipio | Controles time-varying necesarios | Población municipal |

Después de incluir $\alpha_i$ y $\gamma_t$, lo único que falta son variables que
(a) cambian en el tiempo, (b) varían entre municipios, y (c) afectan al outcome.

### 7.3 ¿Por qué solo incluimos `log_pob`?

| Control | ¿Predeterminado? | ¿Relevante? | ¿Incluir? |
|---------|-------------------|-------------|-----------|
| `log_pob` | ✅ Sí (proyecciones CONAPO, la alcaldesa no altera la población) | ✅ Sí (municipios más grandes tienen más cuentas) | ✅ **Sí** |
| Outcomes masculinos (`_h`) | ❌ No — podrían ser afectados por la alcaldesa | ✅ Correlacionados | ❌ **No** (bad control) |
| PIB municipal | ❌ No disponible trimestralmente | ✅ Sí | ❌ **No** (no está en los datos) |
| Totales financieros (`_t`) | ❌ Incluyen el outcome femenino mecánicamente | ✅ | ❌ **No** (endógeno) |
| `tipo_pob` (Rural/Urbano) | ✅ (no cambia) | Irrelevante | ❌ **No** (absorbido por $\alpha_i$) |

### 7.4 ¿Qué es un "bad control"?

Un **bad control** (Angrist & Pischke 2009) es una variable que incluimos como control
pero que en realidad está *afectada* por el tratamiento. Incluirla sesga nuestro
estimador.

**Ejemplo:** Si las alcaldesas también aumentan la inclusión financiera de los hombres
(por efecto general de mejor gestión), incluir el outcome masculino como control
*absorbe* parte del efecto que queremos medir. El coeficiente $\hat{\beta}$ se
encogería artificialmente.

**Regla de oro:** Solo incluir controles que sean **predeterminados** (decididos antes
del tratamiento) o **exógenos** (no afectados por el tratamiento). En caso de duda,
mejor no incluirlo.

### 7.5 ¿Por qué log y no nivel?

Usamos $\log(\text{pob})$ en vez de $\text{pob}$ directamente porque:

1. La población tiene una distribución muy sesgada (municipios de 200 personas vs.
   CDMX con millones). El logaritmo comprime esta distribución.
2. En logaritmo, la relación entre población y el outcome es más lineal.
3. Es estándar en la literatura.

---

## 8. Leads y lags: el lenguaje del tiempo

### 8.1 Definiciones

En datos panel, un **lead** y un **lag** son simplemente la versión adelantada o
retrasada de una variable:

| Término | Definición | En nuestros datos | Notación |
|---------|-----------|-------------------|----------|
| **Lag** (retardo) | Valor de la variable en un periodo anterior | Si hoy es 2021Q1, el lag 1 es el valor en 2020Q4 | `alcaldesa_final_l1` |
| **Lead** (adelanto) | Valor de la variable en un periodo futuro | Si hoy es 2021Q1, el lead 1 es el valor en 2021Q2 | `alcaldesa_final_f1` |

En nuestro panel:
- `_l1`, `_l2`, `_l3` = 1, 2 y 3 trimestres antes
- `_f1`, `_f2`, `_f3` = 1, 2 y 3 trimestres después

### 8.2 ¿Para qué sirven?

Los leads y lags del tratamiento son herramientas específicas para el **event study**
(Sección 9):

| Variable | Uso | ¿Incluir como control en TWFE base? |
|----------|-----|-------------------------------------|
| `alcaldesa_final` | Tratamiento principal | ✅ Sí (es $D_{it}$) |
| `alcaldesa_final_l1` a `_l3` | Efectos post-tratamiento en event study | ❌ **Nunca como control** |
| `alcaldesa_final_f1` a `_f3` | Pre-trends en event study | ❌ **Nunca como control** |

### 8.3 ¿Por qué no incluirlos como controles?

Incluir leads del tratamiento como controles sería como "mirar al futuro" — estamos
metiendo información que aún no existía al momento de la observación. Esto sesga el
estimador.

Incluir lags del tratamiento como controles absorbe parte del *efecto acumulado* del
tratamiento, lo cual subestima el impacto verdadero.

> **Regla estricta:** Los leads y lags del tratamiento se usan **única y exclusivamente**
> en la ecuación del event study y en placebos temporales. Nunca en el modelo TWFE base.
> Ver `docs/09_MODELADO_PROPUESTA.md` §2.2.

---

## 9. El event study: la prueba diagnóstica

### 9.1 ¿Qué es un event study?

Un **event study** (estudio de eventos) es una extensión del DiD que, en vez de estimar
un solo coeficiente $\beta$ (efecto promedio), estima un coeficiente **para cada periodo
relativo al tratamiento**. Esto nos permite ver:

1. **Antes del tratamiento:** ¿Ya había diferencias? (validación de tendencias paralelas)
2. **En el momento del tratamiento:** ¿Cuánto cambió inmediatamente?
3. **Después del tratamiento:** ¿El efecto crece, se mantiene o desaparece?

### 9.2 La ecuación del event study

$$
Y_{it} = \alpha_i + \gamma_t + \sum_{\substack{k = -K \\ k \neq -1}}^{L} \mu_k \cdot \mathbf{1}\{t - g_i = k\} + \delta \cdot \log\_\text{pob}_{it} + \varepsilon_{it}
$$

Vamos pieza por pieza:

| Símbolo | Significado | En nuestros datos |
|---------|------------|-------------------|
| $g_i$ | Trimestre en que el municipio $i$ recibe tratamiento por primera vez | El trimestre de la primera alcaldesa |
| $k = t - g_i$ | Tiempo relativo al tratamiento | $k = -3$: tres trimestres antes; $k = 0$: trimestre del tratamiento; $k = +2$: dos trimestres después |
| $\mathbf{1}\{t - g_i = k\}$ | Indicador: vale 1 cuando estamos exactamente $k$ periodos del tratamiento | Dummy para cada "distancia" al evento |
| $\mu_k$ | Efecto del tratamiento $k$ periodos después (o antes) del evento | El coeficiente que estimamos para cada $k$ |
| $k = -1$ | **Periodo de referencia** (omitido, normalizado a 0) | El trimestre justo antes del tratamiento |

### 9.3 ¿Qué es el periodo de referencia y por qué $k = -1$?

Cuando estimamos todos los $\mu_k$, necesitamos un punto de referencia. Normalizamos
$\mu_{-1} = 0$ (el trimestre justo antes del tratamiento). Todos los demás coeficientes
se interpretan *respecto a ese periodo*.

¿Por qué $k = -1$ y no $k = 0$ o $k = -3$? Porque es el último periodo "limpio" antes
del tratamiento. Si ahí ya hubiera un efecto, sería preocupante (significaría
anticipación).

### 9.4 Cómo leer un gráfico de event study

```
   μ_k (coeficiente)
    |
 +0.08|                              ●
    |                         ●        ●
 +0.04|                    ●
    |               ●
    |          .    .    
  0 |----●----●----●----|----|----|----|----|--->
    |                   |
-0.04|                   |
    |                   |
    k:  -4   -3   -2  -1    0    1    2    3
                        ↑
                 periodo de referencia
    
    ←── PRE-tratamiento ──→←── POST-tratamiento ──→
```

**Cómo interpretarlo:**

| Zona del gráfico | ¿Qué esperamos? | ¿Qué significa si se cumple? |
|------------------|-----------------|------------------------------|
| **Pre-tratamiento** ($k < -1$) | Coeficientes ≈ 0 (no significativos) | ✅ Tendencias paralelas se sostienen |
| **$k = -1$** | = 0 por definición (referencia) | Punto de ancla |
| **Post-tratamiento** ($k \geq 0$) | Coeficientes significativos > 0 | ✅ Hay efecto del tratamiento |

**Señales de alerta:**
- Si $\mu_{-3}$ o $\mu_{-4}$ son significativamente distintos de 0 → las tendencias
  no eran paralelas antes del tratamiento → el DiD no es creíble.
- Si los coeficientes post son crecientes ($\mu_0 < \mu_1 < \mu_2 < \cdots$) →
  el efecto se acumula con el tiempo.
- Si los coeficientes post decaen hacia 0 → el efecto es temporal.

### 9.5 Nuestros parámetros

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| $K$ (leads) | 4 | Máximo disponible dado el panel de 17 trimestres |
| $L$ (lags) | 8 | Captura efectos hasta 2 años post-tratamiento |
| Periodo base | $k = -1$ | Estándar en la literatura |
| Endpoint binning | Sí | Se acumulan $k \leq -K$ y $k \geq L$ para no perder observaciones |
| Muestra | Excluyendo always-treated | Los 395 municipios tratados desde 2018Q3 (294 left-censored + 101 always) no tienen periodos pre |

### 9.6 ¿Por qué es la prueba más importante?

Porque si el event study muestra pre-trends planos, tenemos evidencia empírica
de que el supuesto de tendencias paralelas (Sección 4) es razonable. Sin eso, todo
el análisis DiD carece de credibilidad.

> **Analogía:** El event study es como el "placebo pre-tratamiento". Si encontramos
> efectos significativos *antes* de que la alcaldesa llegue al poder, algo anda mal —
> la alcaldesa no puede haber causado un efecto antes de existir.

> **📖 Para un tutorial completo y detallado del event study (ecuación desglosada,
> cómo leer el gráfico, test formal de pre-trends, implementación en Python línea
> por línea, árbol de decisión), ver `docs/12_EXPLICACION_EVENT_STUDY.md`.**

---

## 10. El problema del tratamiento escalonado (staggered treatment)

### 10.1 ¿Cuál es el problema?

En el DiD clásico de libro de texto, hay **un solo momento** en que el tratamiento se
enciende para todos los tratados. En nuestro caso, el tratamiento es **escalonado**
(staggered): distintos municipios reciben su primera alcaldesa en distintos trimestres.

| Cohorte | Primer trimestre con alcaldesa | Municipios |
|---------|--------------------------------|------------|
| 2018Q3 | Inicio del panel | 394 |
| 2018Q4 | 1 trimestre después | 234 |
| 2019Q1–2021Q3 | Entradas esporádicas | 120 |
| 2021Q4 | Ciclo electoral 2021 | 163 |
| 2022Q1–Q3 | Tomas tardías | 84 |
| Nunca | — | 1,476 |

### 10.2 ¿Por qué el TWFE puede dar resultados engañosos?

Goodman-Bacon (2021) demostró que, con tratamiento escalonado, el $\hat{\beta}$ del
TWFE es un **promedio ponderado** de muchas comparaciones 2×2 (DiD de dos grupos en
dos periodos). El problema es que algunas de esas comparaciones usan como "control"
a **municipios que ya fueron tratados antes** (early-treated como control para
late-treated). Si el efecto del tratamiento cambia con el tiempo (es heterogéneo
entre cohortes), estas comparaciones "contaminadas" pueden sesgar el resultado —
incluso pueden producir un $\hat{\beta}$ negativo cuando el efecto verdadero es
positivo para todos.

### 10.3 Ejemplo simplificado

Supongamos dos cohortes:
- **Cohorte temprana (2018Q3):** Efecto grande = +0.10
- **Cohorte tardía (2021Q4):** Efecto pequeño = +0.02

El TWFE clásico podría comparar:
1. Cohorte temprana vs. never-treated → bien, captura +0.10
2. Cohorte tardía vs. never-treated → bien, captura +0.02
3. **Cohorte tardía vs. cohorte temprana (ya tratada)** → problemático: usa como
   "cambio en el control" el cambio en la cohorte temprana, que ya fue tratada y cuyo
   efecto está evolucionando

Si el efecto de la cohorte temprana está creciendo con el tiempo, la comparación (3)
puede subestimar el efecto de la cohorte tardía, o incluso dar signo negativo.

### 10.4 ¿Cómo detectarlo?

El primer paso es correr el TWFE estándar y examinar si los resultados son sensibles a
la inclusión de distintas cohortes. Si se sospecha sesgo, se recomienda implementar
un estimador moderno como el Stacked DiD (ver Sección 11 — Trabajo futuro).

---

## 11. Trabajo futuro: estimadores modernos

El problema del tratamiento escalonado descrito en la Sección 10 motiva el uso de
estimadores modernos diseñados para evitar comparaciones contaminadas. En esta tesis,
el análisis se basa en el **TWFE clásico** como modelo principal. Sin embargo,
se recomienda como extensión futura la implementación de los siguientes estimadores:

### 11.1 Estimadores recomendados

| Estimador | Referencia | Idea central | Recomendación |
|-----------|-----------|-------------|---------------|
| **Stacked DiD** | Cengiz et al. (2019) | Apilar sub-experimentos por cohorte, cada uno contra never-treated | 🟡 Recomendado como extensión principal |
| **Callaway & Sant'Anna** | Callaway & Sant'Anna (2021) | ATT por grupo-periodo, luego agregar | 🟡 Recomendado como robustez |
| **Sun & Abraham** | Sun & Abraham (2021) | Re-ponderar coeficientes del event study | ⬜ Opcional |

### 11.2 ¿Por qué se recomienda el Stacked DiD?

El **Stacked DiD** (Cengiz et al. 2019) resuelve el problema del tratamiento
escalonado separando el panel en sub-experimentos (uno por cohorte de tratamiento),
cada uno con su grupo de control de municipios never-treated. Al apilar estos
sub-experimentos y estimar con efectos fijos anidados (cohorte × municipio,
cohorte × periodo), se eliminan las comparaciones contaminadas que pueden sesgar
el TWFE.

Esta extensión permitiría:
1. Verificar si los resultados del TWFE están atenuados por el sesgo de
   Goodman-Bacon.
2. Obtener estimaciones más precisas del efecto del tratamiento bajo
   adopción escalonada con efectos heterogéneos.
3. Complementar el event study TWFE con un event study dinámico limpio
   de comparaciones contaminadas.

### 11.3 Jerarquía de especificaciones actual

| Prioridad | Especificación | Escala | Rol |
|-----------|---------------|--------|-----|
| 1 (principal) | TWFE clásico | `_pc_asinh` | Resultado principal de la tesis |
| 2 (robustez funcional) | TWFE | `_pc_w` + asinh | Winsorizar primero, luego asinh |
| 3 (robustez funcional) | TWFE | $\log(1+Y_{pc})$ | Alternativa a asinh |
| 4 (recomendado futuro) | Stacked DiD | `_pc_asinh` | Extensión recomendada |
| 5 (recomendado futuro) | Callaway & Sant'Anna | `_pc_asinh` | Estimador alternativo |

---

## 12. Robustez: ¿los resultados son creíbles?

### 12.1 ¿Qué es un análisis de robustez?

Un análisis de robustez consiste en **cambiar algo del modelo** — la muestra, la escala,
el estimador, el control — y verificar que los resultados principales no cambian
dramáticamente. Si lo que encontramos sobrevive a múltiples variaciones, es más
creíble.

> **Analogía:** Es como probar que un puente aguanta cambiando el tipo de vehículo, el
> clima y la velocidad. Si solo funciona bajo condiciones perfectas, no es un buen puente.

### 12.2 Nuestras pruebas de robustez, explicadas una a una

#### R1: Cambio de escala del outcome

**¿Qué cambiamos?** La transformación aplicada a la variable dependiente.

| Versión | Fórmula | Resultado (verificado marzo 2026) |
|---------|---------|----------------------------------|
| **asinh** (principal) | $\text{asinh}(Y_{pc})$ | $\hat{\beta} \approx +0.007$ ✅ |
| **winsor + asinh** | Winsorizar $Y_{pc}$ al percentil 1-99, luego asinh | $\hat{\beta}$ consistente ✅ |
| **log(1+Y)** | $\log(1 + Y_{pc})$ | $\hat{\beta}$ consistente ✅ |
| **winsor nivel** (R6) | Solo winsorizar, sin transformar | Signos inestables ⚠️ |
| **nivel crudo** (R7) | $Y_{pc}$ sin transformar | Signos inestables ⚠️ |

**Conclusión:** Las tres transformaciones funcionales (asinh, winsor+asinh, log1p) dan
resultados consistentes. Las especificaciones en nivel son inestables — dominadas por
outliers metropolitanos. Esto *confirma* que asinh es necesaria, no una elección
arbitraria.

#### R2/R3: Excluir o incluir trimestres de transición

**¿Qué cambiamos?** Los trimestres en que cambia el gobierno municipal son ruidosos
(el nuevo gobierno apenas se instala, hay traspaso de poderes). R2 los excluye usando
`alcaldesa_excl_trans` y R3 los incluye (nuestra especificación base usa `alcaldesa_final`
que los incluye).

**¿Por qué importa?** Si el resultado desaparece al excluir transiciones, podría ser
un artefacto del cambio de gobierno, no de la alcaldesa en sí.

#### R4/R5: Estimadores modernos de DiD

**¿Qué cambiamos?** El estimador. En vez de TWFE, usamos Callaway & Sant'Anna (R4) o
Sun & Abraham (R5), que son robustos al problema del tratamiento escalonado (Sección 10).

**¿Por qué importa?** Si TWFE y estos estimadores difieren mucho, el TWFE está sesgado
por efectos heterogéneos entre cohortes.

#### R6: Placebo temporal

**¿Qué cambiamos?** Asignamos un tratamiento *falso* 4 trimestres antes del real y
re-estimamos el modelo. El "tratamiento placebo" no debería tener efecto.

**¿Por qué importa?** Si encontramos un efecto con el placebo temporal, significa que
había tendencias diferenciales antes del tratamiento real — y por tanto el DiD no
identifica un efecto causal.

#### R7: Placebo de género

**¿Qué cambiamos?** Estimamos el mismo modelo pero usando como outcome las variables
*masculinas* (`ncont_total_h_pc_asinh`).

**¿Por qué importa?** Si la alcaldesa aumenta las cuentas bancarias también de los
hombres en la misma magnitud, el efecto no es específico de género — es un efecto
general de gestión. En ese caso, los outcomes de **brecha de género** (ratio M/H) son
más informativos.

| Resultado placebo género | Interpretación |
|--------------------------|---------------|
| $\hat{\beta}_{\text{hombres}} \approx 0$ | Efecto específico de mujeres ← lo ideal |
| $\hat{\beta}_{\text{hombres}} > 0$ pero $< \hat{\beta}_{\text{mujeres}}$ | Efecto general + diferencial de género ← aún válido |
| $\hat{\beta}_{\text{hombres}} \approx \hat{\beta}_{\text{mujeres}}$ | Efecto de gestión general, no de género ← usar ratios M/H |

#### R8: Excluir always-treated

**¿Qué cambiamos?** Quitamos los municipios que tienen alcaldesa en *todo* el panel
(nunca los vemos sin tratamiento).

**¿Por qué importa?** Estos municipios no aportan variación within (nunca cambian de
estado). Si incluirlos altera el resultado, sugiere que influyen en el promedio de
manera inadecuada.

#### R9: Tratamiento continuo (dosis-respuesta)

**¿Qué cambiamos?** En vez de $D_{it} \in \{0,1\}$, usamos `alcaldesa_acumulado`
(cuántos trimestres lleva con alcaldesa).

**¿Por qué importa?** Permite preguntar: ¿el efecto crece con más tiempo de exposición?
Si $\hat{\beta}_{\text{acum}} > 0$, cada trimestre adicional con alcaldesa añade más
inclusión financiera.

### 12.3 Priorización: ¿cuáles son imprescindibles?

| Nivel | Pruebas | ¿Por qué? |
|-------|---------|-----------|
| **Imprescindibles** | R1, R2/R3, R4, R7 | Responden a las amenazas más directas a la validez |
| **Recomendadas** | R5, R6, R8 | Aportan credibilidad adicional |
| **Opcionales (apéndice)** | R9, R10, R11 | Para completitud |

---

## 13. Heterogeneidad: ¿el efecto es igual para todos?

### 13.1 ¿Qué es el análisis de heterogeneidad?

Hasta ahora, estimamos un **efecto promedio** $\hat{\beta}$. Pero ¿será el mismo
efecto para todos los municipios? El análisis de heterogeneidad pregunta:

> ¿El efecto de la alcaldesa es diferente según el tamaño del municipio, la región,
> la cohorte u otra característica?

### 13.2 ¿Cómo se estima?

Se agrega una **interacción** entre el tratamiento y la variable de heterogeneidad:

$$
Y_{it} = \alpha_i + \gamma_t + \beta_1 D_{it} + \beta_2 (D_{it} \times H_i) + \delta \cdot \log\_\text{pob}_{it} + \varepsilon_{it}
$$

Donde $H_i$ es la variable de heterogeneidad (e.g., tamaño del municipio).

**¿Cómo se interpreta?**
- $\beta_1$ = efecto para el grupo donde $H_i = 0$ (grupo base)
- $\beta_1 + \beta_2$ = efecto para el grupo donde $H_i = 1$
- $\beta_2$ = **diferencia** en el efecto entre los dos grupos

Si $\beta_2$ es significativo, hay heterogeneidad: el efecto es distinto entre grupos.

### 13.3 Dimensiones que probamos

| Dimensión | Variable $H_i$ | Pregunta |
|-----------|----------------|----------|
| Tamaño municipal | `log_pob` (continuo) | ¿El efecto es más fuerte en municipios pequeños? |
| Cohorte de entrada | `early_cohort` (1 si ≤ 2018Q4) | ¿Las alcaldesas tempranas tienen más efecto? |
| Nivel base de IF | `high_baseline` (1 si > mediana pre-tto) | ¿El efecto es mayor donde la IF parte baja? |

### 13.4 Resultados preliminares (marzo 2026)

| Interacción | Resultado |
|-------------|-----------|
| $D \times \log\_\text{pob}$ | 0 de 4 outcomes significativos |
| $D \times \text{early\_cohort}$ | 0 de 4 significativos |
| $D \times \text{high\_baseline}$ | 1 de 4 marginalmente significativo ($p < 0.10$) |

**Conclusión:** El efecto es **homogéneo** — no varía significativamente entre
las dimensiones testadas. Solo 1 de 12 interacciones alcanza significancia marginal,
consistente con un falso positivo por azar ($1/12 \approx 8\%$, cercano al 10% de
significancia nominal).

### 13.5 La trampa de `ever_alcaldesa`

Inicialmente se propuso usar $D_{it} \times \text{ever\_alcaldesa}_i$ como interacción.
Pero hay un problema lógico:

- Si $D_{it} = 1$ (hay alcaldesa ahora), entonces por definición $\text{ever}_i = 1$
  (tuvo alcaldesa alguna vez).
- Por lo tanto: $D_{it} \times \text{ever\_alcaldesa}_i = D_{it} \times 1 = D_{it}$

La interacción es **idéntica** al tratamiento → Python lanza un error de colinealidad
perfecta. No se puede estimar.

**Lección:** No interactuar el tratamiento con variables que son **función lógica**
del propio tratamiento.

---

## 14. El modelo final: resumen de la estrategia completa

### 14.1 Secuencia completa del análisis

Aquí está, paso a paso, todo lo que haremos y en qué orden:

```
PASO 1: Construir la muestra analítica
   └── Cargar panel (41,905 obs), seleccionar variables, crear escalas

PASO 2: Tabla 1 — Estadísticas descriptivas
   └── Medias y SD por grupo (never-treated vs. switchers)
   └── Test de balance entre grupos
   └── Ver tutorial completo: docs/11_TABLA1_ESTADISTICAS_DESCRIPTIVAS.md

PASO 3: Event Study (diagnóstico) ← CRÍTICO
   └── Estimar la ecuación del event study con K=4 leads y L=8 lags
   └── Verificar: ¿los pre-trends son planos (≈ 0)?
       ├── SÍ → Proceder con confianza ✅
       └── NO → Investigar y posiblemente abandonar DiD para ese outcome ❌
   └── Ver tutorial completo: docs/12_EXPLICACION_EVENT_STUDY.md

PASO 4: Modelo principal — TWFE
   └── Ecuación: Y_it = α_i + γ_t + β·D_it + δ·log_pob_it + ε_it
   └── Escala principal: _pc_asinh
   └── Errores estándar clusterizados a nivel municipio
   └── Resultado: β̂ y su significancia para los 5 outcomes primarios

PASO 5: Robustez
   └── R1: Cambiar escala (log1p, winsor+asinh)
   └── R2/R3: Excluir/incluir transiciones
   └── R4: Callaway & Sant'Anna
   └── R6: Placebo temporal
   └── R7: Placebo de género

PASO 6: Heterogeneidad
   └── Interacciones con log_pob, early_cohort, high_baseline
   └── Resultado preliminar: efecto homogéneo

PASO 7: Corrección por comparaciones múltiples
   └── 5 outcomes primarios → familia de hipótesis
   └── Benjamini-Hochberg para controlar falsos descubrimientos

PASO 8: Ensamblar resultados para la tesis
   └── Tablas 1-4, Figuras 1-2
   └── Verificar los 5 criterios de "listo para tesis"
```

#### Archivos por paso

| Paso | Acción | Scripts `.py` | Docs `.md` |
|------|--------|--------------|------------|
| **1** | Construir muestra analítica | `src/data/01_extract_panel.py`, `src/data/02_build_features.py`, `src/tesis_alcaldesas/data/extract_panel.py`, `src/tesis_alcaldesas/data/build_features.py`, `src/tesis_alcaldesas/models/sample_policy.py`, `src/tesis_alcaldesas/models/utils.py` (`load_panel()`), `src/transformaciones_criticas.py`, `src/transformaciones_altas.py`, `src/transformaciones_medias.py` | `08_DATASET_CONSTRUCCION.md` (§1.3 sample policy), `07_DATA_CONTRACT.md`, `09_MODELADO_PROPUESTA.md` §2 |
| **2** | Tabla 1 — Descriptivas | `src/models/01_table1_descriptives.py`, `src/tesis_alcaldesas/models/table1_descriptives.py`, `src/adhoc/check_balance.py` | **`11_TABLA1_ESTADISTICAS_DESCRIPTIVAS.md`** (tutorial), `09_MODELADO_PROPUESTA.md` §8.1, `17_RESULTADOS_EMPIRICOS.md`, `06_ANALISIS_DESCRIPTIVO_TESIS.md` |
| **3** | Event Study (diagnóstico) | `src/models/03_event_study.py`, `src/tesis_alcaldesas/models/event_study.py`, `src/tesis_alcaldesas/models/event_study_sensitivity.py` | **`12_EXPLICACION_EVENT_STUDY.md`** (tutorial), `09_MODELADO_PROPUESTA.md` §4, `10_EXPLICACION_MODELADO.md` §9 (este doc), `15_EVENT_STUDY_SENSIBILIDAD.md` |
| **4** | TWFE (principal) | `src/models/02_twfe.py`, `src/tesis_alcaldesas/models/twfe.py` | `09_MODELADO_PROPUESTA.md` §3, `13_MODELADO_ECONOMETRICO.md`, `10_EXPLICACION_MODELADO.md` §6 (este doc) |
| **5** | Robustez | `src/models/04_robustness.py`, `src/tesis_alcaldesas/models/robustness.py` | `09_MODELADO_PROPUESTA.md` §5, `05_EDA_EXPLICACION_4.md` §11.9 (verificación R6/R7), `10_EXPLICACION_MODELADO.md` §12 (este doc) |
| **6** | Heterogeneidad | `src/models/05_heterogeneity.py`, `src/tesis_alcaldesas/models/heterogeneity.py` | `09_MODELADO_PROPUESTA.md` §6, `04_EDA_EXPLICACION_3.md` §15 (resultados), `10_EXPLICACION_MODELADO.md` §13 (este doc) |
| **7** | Corrección por multiplicidad | (integrado en scripts de Pasos 4-5; sin script dedicado aún) | `09_MODELADO_PROPUESTA.md` §6B (pre-analysis plan BH/Bonferroni), `16_MDES_PODER.md` |
| **8** | Ensamblar resultados | `src/tesis_alcaldesas/run_all.py`, `src/tesis_alcaldesas/models/extensive_margin.py`, `src/tesis_alcaldesas/models/mdes_power.py` | `17_RESULTADOS_EMPIRICOS.md`, `18_EXTENSION_OUTCOMES.md`, `19_APENDICE.md`, `22_CHECKLIST_DEFENSA.md`, `23_FREEZE_RELEASE.md`, `21_ONE_PAGER_ASESOR.md` |

#### Archivos transversales (usados en múltiples pasos)

| Archivo | Rol | Pasos |
|---------|-----|-------|
| `src/tesis_alcaldesas/config.py` | Constantes: `PRIMARY_OUTCOMES`, rutas, parámetros | Todos |
| `src/tesis_alcaldesas/models/utils.py` | `load_panel()`, formateo de resultados | 1–7 |
| `src/db.py` | Conexión a PostgreSQL `tesis_db` | 1 |
| `src/plot_style.py` | Estilo de gráficos matplotlib | 3, 8 |
| `src/catalog.py` | Catálogo de variables y metadatos | 1, 2 |
| `src/tests/test_criticas.py`, `test_altas.py`, `test_medias.py` | Validación de transformaciones | 1 (pre-requisito) |
| `09_MODELADO_PROPUESTA.md` | Diseño de toda la estrategia | Todos |
| `10_EXPLICACION_MODELADO.md` | Tutorial explicativo de cada paso (este doc) | Todos |
| `GUIA_COMPLETA_TESIS.md` / `GUIA_ESTUDIO_CODIGO.md` | Guías de navegación | Todos |
| `20_BIBLIOGRAFIA.md` | Referencias académicas | Todos |

### 14.2 La ecuación que irá en la tesis

**Ecuación principal (TWFE):**

$$
\boxed{Y_{it} = \alpha_i + \gamma_t + \beta \cdot D_{it} + \delta \cdot \log\_\text{pob}_{it} + \varepsilon_{it}}
$$

Donde:
- $\alpha_i$ = efecto fijo de municipio (absorbe heterogeneidad permanente)
- $\gamma_t$ = efecto fijo de periodo (absorbe shocks comunes a todos los municipios)
- $Y_{it}$ = outcome en escala `_pc_asinh`
- $D_{it}$ = `alcaldesa_final` ∈ {0, 1}
- $\hat{\beta}$ = efecto promedio de tener alcaldesa sobre la inclusión financiera
  femenina

**Ecuación del event study:**

$$
\boxed{Y_{it} = \alpha_i + \gamma_t + \sum_{\substack{k=-4 \\ k \neq -1}}^{8} \mu_k \cdot \mathbf{1}\{t - g_i = k\} + \delta \cdot \log\_\text{pob}_{it} + \varepsilon_{it}}
$$

Donde $\mu_k$ para $k < -1$ valida tendencias paralelas, y $\mu_k$ para $k \geq 0$
muestra la dinámica del efecto.

### 14.3 Resultado principal hasta ahora

| Outcome | Estimador | $\hat{\beta}$ | Error estándar | $p$-valor | Significancia |
|---------|-----------|---------------|----------------|-----------|---------------|
| `saldocont_total_m` | TWFE | +0.004 | 0.049 | 0.931 | n.s. |
| `ncont_total_m` | TWFE | +0.007 | 0.022 | 0.747 | n.s. |
| `numtar_deb_m` | TWFE | −0.014 | 0.022 | 0.521 | n.s. |
| `numtar_cred_m` | TWFE | −0.002 | 0.018 | 0.919 | n.s. |
| `numcontcred_hip_m` | TWFE | +0.018 | 0.021 | 0.400 | n.s. |

**Interpretación:** El modelo TWFE no detecta efectos estadísticamente significativos
en ninguno de los cinco indicadores primarios de inclusión financiera femenina.
Los coeficientes son cercanos a cero y económicamente irrelevantes. Los intervalos
de confianza son suficientemente estrechos para descartar efectos grandes.

> **Nota:** Dado que nuestro diseño presenta adopción escalonada (15 cohortes de
> tratamiento), el TWFE clásico podría estar sujeto al sesgo de atenuación
> documentado por Goodman-Bacon (2021). Se recomienda como extensión futura
> implementar un Stacked DiD para verificar si los resultados son robustos
> a este potencial sesgo (ver Sección 11).

### 14.4 Los 5 criterios para que un resultado esté "listo para tesis"

| # | Criterio | ¿Qué verificamos? |
|---|----------|-------------------|
| 1 | **Tendencias paralelas** | Event study no rechaza H₀ de pre-trends = 0 |
| 2 | **Estabilidad** | $\hat{\beta}$ mantiene signo y significancia en ≥3 de 4 pruebas imprescindibles |
| 3 | **Placebo de género** | Efecto en hombres es menor (o nulo) vs. efecto en mujeres |
| 4 | **Reproducibilidad** | Los scripts se ejecutan sin errores y dan los mismos números |
| 5 | **Documentación** | Cada tabla y figura tiene script y descripción asociados |

---

## 15. Glosario de términos

| Término | Definición |
|---------|-----------|
| **ATT** | Average Treatment effect on the Treated — efecto promedio *entre los que recibieron el tratamiento* |
| **Bad control** | Variable que es afectada por el tratamiento y sesga la estimación si se incluye como control |
| **Cluster** | Grupo de observaciones correlacionadas (en nuestro caso, cada municipio a lo largo del tiempo) |
| **Contrafactual** | Lo que habría pasado si el tratamiento no hubiera ocurrido (no observable directamente) |
| **Cohorte** | Grupo de municipios que reciben el tratamiento en el mismo periodo |
| **Correlación serial** | Cuando el valor de una variable en $t$ está correlacionado con su valor en $t-1$ |
| **DiD** | Differences-in-Differences — método que compara cambios en tratados vs. cambios en controles |
| **Efecto fijo** | Constante específica de cada unidad (o periodo) que absorbe heterogeneidad no observada |
| **Endpoint binning** | Acumular los leads/lags más extremos en un solo coeficiente (por limitación muestral) |
| **Error estándar (SE)** | Medida de incertidumbre del estimador; SE pequeño = estimación precisa |
| **Event study** | Extensión del DiD que estima efectos para cada periodo relativo al tratamiento |
| **Exógeno** | Variable no afectada por el tratamiento ni determinada dentro del modelo |
| **Heterocedasticidad** | Cuando la varianza del error varía entre observaciones |
| **Heterogeneidad de efectos** | Cuando el efecto del tratamiento varía entre unidades o cohortes |
| **Interacción** | Término $D \times H$ que permite que el efecto de $D$ varíe según $H$ |
| **Lag** | Valor pasado de una variable ($Y_{t-1}$) |
| **Lead** | Valor futuro de una variable ($Y_{t+1}$) |
| **Never-treated** | Unidades que nunca reciben el tratamiento en el periodo observado |
| **Outcome** | Variable de resultado — lo que medimos como consecuencia del tratamiento |
| **Panel balanceado** | Todas las unidades se observan en todos los periodos (sin huecos) |
| **Pre-trends** | Tendencias previas al tratamiento; si son distintas entre grupos, el DiD no es creíble |
| **Semi-elasticidad** | Cambio porcentual en $Y$ ante un cambio unitario en $X$ |
| **Stacked DiD** | Variante del DiD que apila sub-experimentos por cohorte para evitar sesgo del TWFE (recomendado como extensión futura) |
| **Staggered treatment** | Tratamiento escalonado: distintas unidades se tratan en distintos momentos |
| **SUTVA** | Stable Unit Treatment Value Assumption — no hay spillovers entre unidades |
| **Switcher** | Unidad que cambia de estado de tratamiento al menos una vez durante el panel |
| **Tendencias paralelas** | Supuesto de que tratados y controles habrían seguido la misma trayectoria sin tratamiento |
| **TWFE** | Two-Way Fixed Effects — modelo con efectos fijos de unidad y de periodo |
| **Variación within** | Cambios *dentro de* una misma unidad a lo largo del tiempo (opuesto a *between*) |
| **Winsorización** | Acortar valores extremos al percentil 1-99 (o similar) para limitar influencia de outliers |

---

## 16. Referencias clave

| Referencia | Concepto |
|-----------|---------|
| Angrist & Pischke (2009). *Mostly Harmless Econometrics* | Marco general de inferencia causal; bad controls |
| Bellemare & Wichman (2020). "Elasticities and the Inverse Hyperbolic Sine Transformation" | Justificación de la transformación asinh |
| Bertrand, Duflo & Mullainathan (2004). "How Much Should We Trust DID Estimates?" | Clustering en DiD |
| Callaway & Sant'Anna (2021). "Difference-in-Differences with Multiple Time Periods" | DiD con tratamiento escalonado |
| Cengiz et al. (2019). "The Effect of Minimum Wages on Low-Wage Jobs" | Stacked DiD (recomendado como extensión futura) |
| Goodman-Bacon (2021). "Difference-in-Differences with Variation in Treatment Timing" | Descomposición del TWFE; sesgo por staggered adoption |
| Sun & Abraham (2021). "Estimating Dynamic Treatment Effects in Event Studies with Heterogeneous Treatment Effects" | IW-estimator para event study |

---

> **Siguiente paso:** Con esta base conceptual, el lector debería poder leer y entender
> completamente el documento técnico `docs/09_MODELADO_PROPUESTA.md`, que contiene las
> especificaciones exactas, tablas de robustez, y el checklist reproducible del análisis
> empírico.
