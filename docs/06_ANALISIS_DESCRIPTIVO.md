> **Archivos fuente:**
> - `notebooks/eda.ipynb`
> - `src/eda/run_eda.py`
> - `src/models/01_table1_descriptives.py`
> - `src/tesis_alcaldesas/models/table1_descriptives.py`

# Análisis Descriptivo de los Datos

## A. Descripción de la muestra

### A.1 Fuente de información y estructura del panel

La base de datos empleada en esta investigación proviene de la **Base de Datos de Inclusión Financiera** publicada trimestralmente por la Comisión Nacional Bancaria y de Valores (CNBV), complementada con información electoral sobre la identidad de género de las personas titulares de las presidencias municipales de México. La unidad de observación es el **municipio–trimestre**: cada fila del panel registra los indicadores de inclusión financiera de un municipio en un trimestre específico.

El panel abarca **17 trimestres**, desde el tercer trimestre de 2018 (2018-T3) hasta el tercer trimestre de 2022 (2022-T3), y cubre **2,471 municipios** del país. El número total de observaciones es de **41,905 registros municipio–trimestre**. En un panel perfectamente balanceado se esperarían 42,007 observaciones (2,471 × 17); las 102 observaciones faltantes (0.24% del total) corresponden a **8 municipios con panel incompleto**, es decir, municipios para los cuales no se dispone de información en todos los trimestres del periodo de estudio. Dado que el desbalance es mínimo y no se concentra en el grupo de tratamiento ni de control, se conservan estos municipios en la muestra principal y se verifica en los análisis de robustez que su exclusión no altera los resultados.

La elección del periodo 2018-T3 a 2022-T3 obedece a dos razones. Primero, este intervalo cubre al menos un ciclo electoral municipal completo para la mayoría de los estados, lo que permite observar transiciones de gobiernos masculinos a femeninos (y viceversa) con suficientes trimestres previos y posteriores al cambio de administración. Segundo, el periodo antecede a reformas regulatorias significativas en materia de inclusión financiera digital que podrían confundir la estimación a partir de 2023.

### A.2 Cobertura geográfica

Los 2,471 municipios representan la práctica totalidad de los municipios del país. La muestra abarca las **32 entidades federativas** y presenta heterogeneidad sustancial en términos de tamaño poblacional, grado de urbanización y nivel de desarrollo financiero. La distribución por tipo de población, conforme a la clasificación del INEGI, es la siguiente:

| Tipo de población | Municipios | Porcentaje |
|:---|---:|---:|
| Metrópoli | 218 | 8.8% |
| Urbano | 294 | 11.9% |
| Semi-urbano | 494 | 20.0% |
| En transición | 358 | 14.5% |
| Rural | 775 | 31.4% |
| Semi-rural | 330 | 13.4% |
| *Sin clasificación* | *2* | *0.1%* |

Como se observa, la muestra está compuesta predominantemente por municipios rurales y semi-rurales (44.8% en conjunto), lo cual refleja fielmente la estructura territorial de México, donde la mayor parte de las demarcaciones municipales tienen baja densidad poblacional y, en consecuencia, menor infraestructura financiera. Las metrópolis y municipios urbanos, aunque minoritarios en número (20.7%), concentran la mayor parte de la población y de la actividad financiera del país.

Los dos municipios sin clasificación de tipo de población (San Felipe, Baja California, con 20,320 habitantes, y Dzitbalché, Campeche, con 16,568 habitantes) fueron reclasificados como "Semi-urbano" con base en su tamaño poblacional, siguiendo los umbrales del INEGI.

### A.3 Dimensión temporal y distribución del tratamiento

El periodo de estudio comprende 17 trimestres distribuidos en cinco años:

| Año | Trimestres | Observaciones aprox. |
|:---|:---|---:|
| 2018 | T3–T4 | ~4,942 |
| 2019 | T1–T4 | ~9,884 |
| 2020 | T1–T4 | ~9,884 |
| 2021 | T1–T4 | ~9,884 |
| 2022 | T1–T3 | ~7,311 |

Con respecto al tratamiento, de las 41,905 observaciones municipio–trimestre, **9,331 (22.3%)** corresponden a municipios gobernados por una alcaldesa en ese trimestre (`alcaldesa_final = 1`), mientras que **32,574 (77.7%)** corresponden a municipios con alcalde varón. A nivel de municipios, **995 municipios** (40.3%) tuvieron al menos una mujer como presidenta municipal durante algún trimestre del periodo de estudio (`ever_alcaldesa = 1`; 894 switchers + 101 always-treated), mientras que **1,476 municipios** (59.7%) nunca tuvieron una alcaldesa en el periodo observado y constituyen el grupo de *never-treated* en la estrategia de identificación.

Esta distribución revela dos hechos relevantes. Primero, la participación femenina en las presidencias municipales, aunque creciente, sigue siendo minoritaria: en un trimestre promedio, solo uno de cada cinco municipios es gobernado por una mujer. Segundo, la adopción del tratamiento es **escalonada** (*staggered*) y **no absorbente**: los municipios no transitan simultáneamente a tener una alcaldesa, sino que lo hacen en distintos trimestres a lo largo del panel, y **191 de los 894 switchers experimentan reversiones de tratamiento** (la alcaldesa es reemplazada por un alcalde). Esto genera un ~12.5% de *mismatch* entre la variable de tratamiento basada en el primer episodio (`first_treat_t`) y el estado actual (`alcaldesa_final`), lo que motiva la interpretación de las estimaciones como **ITT** (Intent-to-Treat) y la recomendación de implementar estimadores robustos a la heterogeneidad temporal como extensión futura (ver `docs/17_RESULTADOS_EMPIRICOS.md` §4.6).

### A.4 Demografía municipal: población adulta

La variable de normalización principal es la **población adulta femenina** (`pob_adulta_m`), utilizada como denominador para construir las tasas per cápita de los indicadores financieros. La distribución de esta variable refleja la enorme heterogeneidad entre municipios mexicanos:

| Estadístico | Valor |
|:---|---:|
| Media | 19,698 |
| Desviación estándar | 66,453 |
| Mínimo | 47 |
| Percentil 25 | 1,698 |
| Mediana | 4,629 |
| Percentil 75 | 14,233 |
| Máximo | 1,142,597 |
| Coeficiente de variación | 3.37 |

> **Nota de consistencia:** Estos estadísticos fueron calculados sobre la tabla original
> `inclusion_financiera` (17 trimestres, 41,905 obs). El Data Contract (doc 07) reporta
> valores ligeramente diferentes (min=36, mediana=5,133, max=766,847) porque fue
> calculado sobre `inclusion_financiera_clean` tras transformaciones. La fuente
> autoritativa es el parquet analítico (`analytical_panel_features.parquet`).

El coeficiente de variación de 3.37 indica una dispersión extrema: la población adulta femenina del municipio más grande es más de 24,000 veces la del más pequeño. Esta heterogeneidad justifica dos decisiones metodológicas centrales: (i) la normalización de los indicadores financieros en tasas por cada 10,000 mujeres adultas, y (ii) la inclusión del logaritmo de la población como control en las regresiones.

La población adulta masculina (`pob_adulta_h`) muestra una distribución análoga, con una media de 18,249 y un coeficiente de variación de 3.42, lo que confirma patrones de concentración poblacional similares entre géneros.

---

## B. Definición de variables clave

### B.1 Variable de tratamiento

#### `alcaldesa_final` (variable principal de tratamiento)

Variable binaria que toma el valor de 1 cuando la persona titular de la presidencia municipal del municipio *i* en el trimestre *t* es mujer, y 0 cuando es hombre. Esta variable constituye el tratamiento $D_{it}$ en el diseño de diferencias en diferencias. La construcción de este indicador es no trivial y requiere resolver tres problemas operativos: (i) la conversión de registros históricos de autoridades con fechas irregulares a intervalos diarios, (ii) la agregación de cobertura diaria a frecuencia trimestral, y (iii) el tratamiento de huecos informativos. A continuación se documenta cada etapa de este proceso.

#### Etapa 1: Conversión de registros históricos a intervalos diarios

Para cada municipio se recopiló la información de las personas titulares de la presidencia municipal a partir de registros históricos oficiales (institutos electorales estatales, gacetas de gobierno, portales municipales). Los registros se estandarizaron como intervalos cerrados $[\text{fecha\_inicio}, \text{fecha\_fin}]$ que representan la cobertura diaria de cada autoridad.

**Regla de resolución de traslapes (interinatos).** Cuando dos periodos de autoridad cubren el mismo día —situación frecuente durante interinatos o encargos de despacho que se superponen con el mandato del titular—, se aplica una regla determinística: **se asigna la autoridad cuyo periodo tiene la fecha de inicio más reciente**. Esta regla modela adecuadamente la práctica institucional mexicana en la que un sustituto o encargado desplaza operativamente al titular desde su toma de posesión. La regla es importante por dos razones: (a) evita el doble conteo de autoridad en un mismo día, y (b) hace la asignación diaria completamente determinística, eliminando decisiones discrecionales del investigador.

#### Etapa 2: Agregación a frecuencia trimestral (regla de mayoría de días)

Una vez construida la serie diaria de género de la autoridad para cada municipio, se agregan los datos a nivel trimestral mediante el conteo de cuatro variables:

| Variable diaria | Definición |
|:---|:---|
| `days_total` | Días del trimestre (90–92 según el calendario) |
| `days_female` | Días con una mujer como titular de la presidencia municipal |
| `days_male` | Días con un hombre como titular de la presidencia municipal |
| `days_missing` | Días sin cobertura en el registro histórico |

A partir de estos conteos, se construye la variable de tratamiento algorítmica mediante una **regla de mayoría simple**:

$$
\texttt{alcaldesa}_{it} =
\begin{cases}
1 & \text{si } \texttt{days\_female}_{it} > \texttt{days\_male}_{it} \\
0 & \text{si } \texttt{days\_male}_{it} > \texttt{days\_female}_{it} \\
\text{NA} & \text{si } \texttt{days\_missing}_{it} > 0 \text{ o el municipio no está en el histórico}
\end{cases}
$$

Esta regla asigna el tratamiento al género que gobernó durante la mayor parte del trimestre, lo cual es conceptualmente apropiado para un análisis de efectos que opera a frecuencia trimestral: si una alcaldesa gobernó 60 de 90 días, es razonable atribuir a su administración la gestión predominante del trimestre.

**Variante alternativa: `alcaldesa_end`.** Como definición alternativa, se construye un indicador basado en **quién ocupa la presidencia en el último día del trimestre**. Esta variante se emplea como especificación de robustez, particularmente en trimestres de transición donde la regla de mayoría y la regla de cierre podrían diferir (por ejemplo, cuando un cambio de administración ocurre a mediados del trimestre).

#### Etapa 3: Marcadores de transición

Para identificar trimestres en los que la asignación del tratamiento es potencialmente ruidosa, se construyen dos indicadores de transición:

- **`alcaldesa_transition`**: vale 1 si hubo cambio de autoridad dentro del trimestre (más de un periodo de gobierno cubierto). Estos son trimestres donde la asignación depende de la fecha exacta de toma de posesión.
- **`alcaldesa_transition_gender`**: vale 1 si, adicionalmente, el cambio de autoridad implicó un cambio de género (por ejemplo, hombre → mujer o viceversa). Estos trimestres son los más "ruidosos" para la identificación, pues el outcome refleja parcialmente la administración anterior y la nueva.

Estos marcadores permiten excluir trimestres complicados en las especificaciones de robustez sin perder trazabilidad sobre las razones de exclusión.

#### Etapa 4: Corrección de huecos mediante auditoría manual

La variable algorítmica `alcaldesa` presenta **1,986 valores nulos** (4.7% de las 41,905 observaciones), correspondientes a municipio–trimestres en los que el registro histórico no cubría todos los días del trimestre (`days_missing > 0`) o el municipio no estaba disponible en la fuente histórica. Estas 1,986 observaciones coinciden exactamente con las filas marcadas con `filled_by_manual = 1`, lo que confirma que todos los casos problemáticos fueron identificados sistemáticamente y tratados de forma homogénea.

Para estos casos, se implementó un bloque de auditoría manual con las siguientes variables:

| Variable de auditoría | Contenido |
|:---|:---|
| `alcaldesa_manual` | Codificación manual del género de la autoridad (0/1) |
| `pm_nombre_manual` | Nombre de la persona titular (cuando se documentó) |
| `fuente_manual` | Evidencia utilizada (URL oficial, gaceta, nota periodística) |
| `filled_by_manual` | Indicador binario: 1 si la observación requirió intervención manual |

Este procedimiento sigue las mejores prácticas de transparencia en la construcción de variables: toda corrección manual está documentada con fuente verificable, y las observaciones intervenidas son rastreables mediante un flag explícito.

#### Definición final: `alcaldesa_final`

La variable que se emplea en todas las regresiones combina ambas fuentes de información:

$$
\texttt{alcaldesa\_final}_{it} =
\begin{cases}
\texttt{alcaldesa\_manual}_{it} & \text{si } \texttt{filled\_by\_manual}_{it} = 1 \\
\texttt{alcaldesa}_{it} & \text{en caso contrario}
\end{cases}
$$

El resultado es una variable de tratamiento **sin valores faltantes** (0% de nulls), que cubre la totalidad de las 41,905 observaciones del panel:

| Variable | Obs. con valor 1 | Obs. con valor 0 | Nulls |
|:---|---:|---:|---:|
| `alcaldesa` (algorítmica) | 9,036 | 30,883 | 1,986 |
| `alcaldesa_final` (definitiva) | 9,331 | 32,574 | 0 |

La diferencia entre ambas variables (295 observaciones adicionales con valor 1 y 1,691 con valor 0) corresponde íntegramente a las correcciones manuales. El hecho de que las correcciones amplíen ligeramente el grupo de tratamiento (de 21.6% a 22.3% de las observaciones) descarta la posibilidad de que el proceso manual haya introducido un sesgo sistemático hacia la sub-representación del tratamiento.

#### Variables auxiliares de tratamiento

- **`ever_alcaldesa`**: indicador invariante en el tiempo que vale 1 si el municipio tuvo al menos una alcaldesa en algún trimestre del panel. Su función es clasificar los municipios en *ever-treated* vs. *never-treated*. En las regresiones con efectos fijos de municipio, esta variable es absorbida por el efecto fijo.

- **`alcaldesa_acumulado`**: suma acumulada de `alcaldesa_final` a lo largo del tiempo para cada municipio. Captura la "dosis" de exposición al tratamiento. Por ejemplo, si un municipio tuvo alcaldesa durante 6 trimestres consecutivos, el valor de `alcaldesa_acumulado` crece de 1 a 6 a lo largo de esos trimestres. Esta variable permite explorar efectos dosis-respuesta como especificación alternativa.

- **`female_day_share`** = `days_female` / `days_total`: proporción continua de días con autoridad femenina dentro del trimestre. Acotada en $[0, 1]$, complementa al tratamiento binario permitiendo una especificación dosis-respuesta continua que explota la variación en la exposición parcial durante trimestres de transición.

### B.2 Variables de resultado: indicadores de inclusión financiera

Los indicadores de resultado miden distintas dimensiones de la inclusión financiera de las mujeres a nivel municipal. Todos provienen de registros administrativos de la CNBV y se reportan desagregados por género (mujeres `_m`, hombres `_h`, personas morales `_pm`, y total `_t`). Para esta investigación, las variables de interés primario son las correspondientes al sufijo `_m` (mujeres), aunque las variables masculinas se emplean para construir indicadores de brecha de género.

#### Productos financieros primarios (5 outcomes principales)

Estas cinco variables constituyen el núcleo del análisis econométrico. Fueron seleccionadas por su relevancia para medir distintas dimensiones de la inclusión financiera:

| Variable | Descripción | Dimensión que captura |
|:---|:---|:---|
| **`ncont_total_m`** | Número total de contratos de productos financieros en manos de mujeres | Acceso agregado al sistema financiero formal |
| **`numtar_deb_m`** | Número de tarjetas de débito en manos de mujeres | Acceso a servicios transaccionales básicos |
| **`numtar_cred_m`** | Número de tarjetas de crédito en manos de mujeres | Acceso a crédito de consumo |
| **`numcontcred_hip_m`** | Número de contratos de crédito hipotecario en manos de mujeres | Acceso a crédito de largo plazo / patrimonio |
| **`saldocont_total_m`** | Saldo total de contratos financieros en pesos en manos de mujeres | Profundización financiera (uso intensivo) |

La selección de estos cinco indicadores responde a una lógica de **margen extensivo → margen intensivo**: los contratos totales y las tarjetas de débito capturan el acceso más básico al sistema financiero (¿las mujeres tienen productos?), las tarjetas de crédito y los créditos hipotecarios miden el acceso a productos de mayor sofisticación y riesgo, y los saldos totales capturan el volumen monetario comprometido (¿cuánto usan los productos que tienen?).

#### Productos financieros secundarios (12 outcomes adicionales)

Adicionalmente, la base contiene indicadores para otros productos financieros que se emplean en análisis de extensión:

| Variable | Descripción |
|:---|:---|
| `ncont_ahorro_m` | Contratos de ahorro (cuentas de ahorro) |
| `ncont_plazo_m` | Contratos a plazo fijo |
| `ncont_n1_m` | Contratos nivel 1 (cuentas simplificadas) |
| `ncont_n2_m` | Contratos nivel 2 (cuentas tradicionales) |
| `ncont_n3_m` | Contratos nivel 3 (cuentas avanzadas) |
| `ncont_tradic_m` | Contratos tradicionales |
| `saldocont_ahorro_m` | Saldo en cuentas de ahorro |
| `saldocont_plazo_m` | Saldo en instrumentos a plazo |
| `saldocont_n1_m` | Saldo nivel 1 |
| `saldocont_n2_m` | Saldo nivel 2 |
| `saldocont_n3_m` | Saldo nivel 3 |
| `saldocont_tradic_m` | Saldo en productos tradicionales |

### B.3 Transformaciones de las variables de resultado

Las variables de resultado en su forma cruda (conteos absolutos y saldos en pesos nominales) no son directamente comparables entre municipios de distinto tamaño. Por ello, cada variable se transforma en tres etapas secuenciales:

**Etapa 1: Normalización per cápita.** Para cada variable de resultado Y_it^raw, se construye una tasa por cada 10,000 mujeres adultas:

    Y_it^pc = (Y_it^raw / pob_adulta_m_it) × 10,000

Esta normalización permite interpretar los indicadores como "X contratos (o pesos) por cada 10,000 mujeres adultas", facilitando la comparación entre un municipio metropolitano y uno rural. Las observaciones con denominador igual a cero (`pob_adulta_m = 0`) se codifican como missing y se señalan con un flag de calidad.

**Etapa 2: Transformación asinh (especificación baseline).** Sobre la variable per cápita se aplica la transformación seno hiperbólico inverso:

    Y_it^asinh = asinh(Y_it^pc) = ln(Y_it^pc + √((Y_it^pc)² + 1))

Esta transformación cumple la función del logaritmo natural para comprimir la escala de distribuciones con cola derecha larga, pero con dos ventajas: (i) está definida en cero, lo cual es relevante porque existen municipios sin actividad financiera femenina en ciertos productos y trimestres; y (ii) no requiere la adición de una constante arbitraria *c* como en la transformación ln(Y + c), cuya elección puede alterar las magnitudes estimadas (Bellemare y Wichman, 2020). Para valores moderados y grandes de Y, asinh(Y) ≈ ln(2Y), por lo que los coeficientes se interpretan aproximadamente como semi-elasticidades.

**Etapa 3: Transformaciones alternativas (robustez).** Como verificación de sensibilidad, se construyen dos transformaciones adicionales:

- **Winsorización** (percentiles 1–99): Y_it^w = clip(Y_it^pc, q_0.01, q_0.99). Recorta valores extremos sin eliminar observaciones.
- **log(1 + Y)**: Y_it^log1p = ln(1 + Y_it^pc). Transformación logarítmica convencional con constante unitaria, empleada como punto de comparación.

Los umbrales de winsorización se calculan sobre la distribución conjunta de todos los municipios y trimestres, sin condicionar por estatus de tratamiento, para evitar que la transformación introduzca un sesgo diferencial.

### B.4 Variables de control

| Variable | Construcción | Justificación |
|:---|:---|:---|
| `log_pob` | ln(pob + 1) | Controla el tamaño poblacional total, correlacionado con infraestructura financiera |
| `log_pob_adulta` | ln(pob_adulta + 1) | Alternativa que captura la base de usuarios potenciales del sistema financiero |

Estas variables se incluyen como controles en las especificaciones que no absorben efectos fijos de municipio (para capturar diferencias de nivel), pero en la especificación principal con efectos fijos bidireccionales (municipio + trimestre) capturan variación intra-municipio en el tiempo del tamaño poblacional. En la práctica, dado que la población municipal varía poco en un horizonte de 4 años, estos controles tienen un efecto marginal sobre las estimaciones puntuales.

### B.5 Indicadores de brecha de género

Para contextualizar los resultados, se construyen **ratios de género** para cada producto:

    ratio_mh_it^k = Y_it,m^pc,k / Y_it,h^pc,k

donde *k* indexa el tipo de producto financiero. Un ratio menor a 1 indica que las mujeres tienen menor acceso que los hombres al producto *k* en el municipio *i* y trimestre *t*. Observaciones con denominador cercano a cero se codifican como missing para evitar ratios espurios.

### B.6 Variables para el diseño de event study

El análisis de event study requiere variables adicionales que ubican a cada observación en el "tiempo relativo al evento" (la entrada de una alcaldesa):

| Variable | Definición |
|:---|:---|
| `first_treat_period` | Primer trimestre en que `alcaldesa_final = 1` para el municipio *i* |
| `first_treat_t` | Índice numérico (1–17) correspondiente a `first_treat_period` |
| `event_time` | t_index − first_treat_t: trimestres desde/hasta la primera alcaldesa |
| `cohort_type` | Clasificación: *never-treated* (1,476 muni), *switcher* (894 muni — incluye 294 left-censored con `first_treat_t = 0`), *always-treated* (101 muni, $D=1$ en todos los periodos) |

Los municipios *never-treated* (sin alcaldesa en todo el panel) no tienen `first_treat_period` definido y sirven como grupo de comparación puro en el estimador TWFE. Los municipios *always-treated* (con `alcaldesa_final = 1` en **todos** los periodos del panel) carecen de periodos pre-tratamiento y se excluyen de los event studies por no contribuir a la identificación de efectos dinámicos.

> **Nota sobre left-censored:** De los 894 switchers, 294 tienen `first_treat_t = 0` (ya tenían alcaldesa en 2018Q3) y carecen de periodo pre-tratamiento. Estos se excluyen del event study. Los 600 restantes son los switchers efectivos con periodos pre y post observados. De esos 600, 409 tienen tratamiento absorbente (0→1 permanente) y 191 experimentan reversiones.

### B.7 Flags de calidad de datos

La base incluye indicadores binarios que señalan observaciones potencialmente problemáticas:

| Flag | Condición | Observaciones afectadas |
|:---|:---|:---|
| `flag_denom_zero` | `pob_adulta_m = 0` o `pob_adulta_h = 0` | Muy pocas (~2–5 obs.) |
| `flag_incomplete_panel` | Municipio con menos de 17 trimestres | 102 obs. en 8 municipios |
| `flag_undef_saldoprom_*` | `saldoprom = NULL` porque contratos = 0 | ~28 flags, magnitud variable por producto |

Estos indicadores permiten realizar análisis de sensibilidad excluyendo observaciones comprometidas, sin perder información sobre la razón de la exclusión.

---

*Nota metodológica.* Todas las variables de resultado que se emplean en la estimación econométrica corresponden a la transformación asinh de la tasa per cápita (sufijo `_pc_asinh`). Las transformaciones winsorizada y log(1+Y) se reservan para el análisis de robustez. La tabla de estadísticas descriptivas completas se presenta en la sección de resultados (Tabla 1).
