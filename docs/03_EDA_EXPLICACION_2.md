> **Archivos fuente:**
> - `src/transformaciones_criticas.py`

# EDA — Explicación 2: Resolución de Recomendaciones Críticas (🔴)

**Continuación de:** `docs/02_EDA_EXPLICACION.md` (Secciones 1–10)  
**Fecha:** Febrero 2026  

---

## 11. Resolución de recomendaciones críticas (🔴)

Las 4 recomendaciones marcadas como **🔴 CRÍTICAS** en la Sección F del EDA fueron implementadas y aplicadas sobre una **copia** de la tabla original. La tabla original `inclusion_financiera` **NO fue modificada**.

### Tabla resultante

| Propiedad | Valor |
|-----------|-------|
| **Tabla original** | `inclusion_financiera` (175 columnas) — **intacta** |
| **Tabla limpia** | `inclusion_financiera_clean` (223 columnas) |
| **Filas** | 41,905 (sin cambios) |
| **Columnas nuevas (per cápita)** | +51 |
| **Columnas eliminadas (constantes)** | −3 |
| **Diferencia neta** | +48 columnas |

---

### Rec 1. Normalización per cápita de conteos (`ncont_*`, `numtar_*`, `numcontcred_*`)

#### ¿Qué se hizo?

Se crearon 30 columnas nuevas con sufijo `_pc` que dividen cada conteo de contratos/tarjetas entre la población adulta correspondiente y multiplican por 10,000.

#### ¿Por qué es necesaria la normalización per cápita?

Imaginemos dos municipios:

| Municipio | Población adulta mujeres | Contratos totales mujeres (`ncont_total_m`) |
|---|---:|---:|
| A (rural) | 500 | 200 |
| B (metropolitano) | 500,000 | 150,000 |

Si comparamos en **niveles** (números absolutos), el municipio B tiene 750× más contratos que A, y un modelo de regresión le asignaría una "mayor inclusión financiera". Pero esa conclusión es engañosa: B tiene más contratos simplemente porque tiene más personas. En términos de **penetración** (cobertura real del sistema financiero por habitante):

- Municipio A: 200 / 500 = 0.40 → el 40% de las mujeres adultas tienen algún contrato
- Municipio B: 150,000 / 500,000 = 0.30 → solo el 30% tienen contrato

Después de normalizar, **A tiene mayor inclusión financiera que B** — la conclusión se invierte completamente. Sin normalización, nuestro modelo estaría midiendo "tamaño del municipio", no inclusión financiera.

Los datos de nuestro EDA confirman este problema empíricamente: la correlación de Spearman entre `ncont_total_m` (conteo bruto) y `pob_adulta_m` (población) es de **0.67–0.70**. Esto significa que entre el 67% y 70% del ranking de outcomes está explicado simplemente por el tamaño poblacional. Un modelo con efectos fijos de municipio absorbería las diferencias de nivel, pero la normalización sigue siendo necesaria porque:

1. **Interpretabilidad:** Un coeficiente en niveles dice "X contratos más", pero no sabemos si eso es mucho o poco sin contexto poblacional. Un coeficiente per cápita dice "X contratos más por cada 10,000 mujeres", que es directamente interpretable como cambio en la tasa de penetración.
2. **Heterocedasticidad:** Los municipios grandes tienen varianzas absolutas enormes y los pequeños varianzas diminutas. La normalización estabiliza la varianza, mejorando la eficiencia de los estimadores.
3. **Comparabilidad con la literatura:** Los indicadores de inclusión financiera reportados por la CNBV, el Banco Mundial y otros organismos se expresan siempre como tasas por cada 10,000 adultos.

#### ¿Por qué multiplicar por 10,000?

La fórmula es:

$$\text{columna\_pc} = \frac{\text{columna\_original} \times 10{,}000}{\text{pob\_adulta\_*}}$$

El factor de 10,000 es una **convención de escala** con tres justificaciones:

1. **Legibilidad.** Sin el factor, la tasa sería un decimal pequeño. Ejemplo: si un municipio tiene 200 contratos entre 5,000 mujeres adultas, la tasa bruta es 200/5,000 = 0.04. Eso es "0.04 contratos por mujer adulta" — un número difícil de comunicar. Multiplicado por 10,000, se convierte en **400 contratos por cada 10,000 mujeres adultas**, que es intuitivo y fácil de interpretar.

2. **Estándar institucional.** La CNBV publica sus Indicadores Básicos de Inclusión Financiera usando esta misma base de 10,000 adultos. Al usar la misma escala, nuestros resultados son **directamente comparables** con las publicaciones oficiales y con la literatura académica que utiliza datos de la CNBV (e.g., Demirgüç-Kunt et al., 2018; Global Findex).

3. **Precisión numérica.** Coeficientes de regresión del orden de 0.00004 son difíciles de leer, reportar y comparar. Con la escala de 10,000, esos mismos coeficientes se expresan como 0.4, lo cual reduce el riesgo de errores de redondeo y facilita la discusión de significancia económica.

> **Nota para la defensa:** Si el sinodal pregunta "¿por qué 10,000 y no 1,000 o 100,000?", la respuesta es: es la convención de la CNBV y del Banco Mundial para indicadores de inclusión financiera. Usar otra base no cambiaría los resultados estadísticos (los p-valores y los R² son invariantes a reescalamientos lineales), pero haría nuestros números incomparables con la literatura existente.

#### Mapeo de sufijos demográficos

La normalización respeta la desagregación por sexo: los conteos de **mujeres** se dividen entre la población adulta de **mujeres**, no entre la población total. Esto es crucial para evitar distorsiones cuando la composición demográfica por sexo varía entre municipios.

| Sufijo original | Denominador | Significado | ¿Por qué este denominador? |
|:---|:---|:---|:---|
| `_m` | `pob_adulta_m` | Mujeres | Los contratos de mujeres deben normalizarse por el universo de mujeres, no por la población total. Un municipio con 70% de mujeres tendría una tasa artificialmente baja si usáramos el total. |
| `_h` | `pob_adulta_h` | Hombres | Análogo al caso femenino. |
| `_t` | `pob_adulta` | Total (ambos sexos) | Total de conteo ÷ total de población. |
| `_pm` | — (no se normaliza) | Persona moral (empresas) | Las personas morales no tienen un denominador poblacional válido. No tiene sentido dividir contratos de empresas entre personas físicas adultas. |

#### Protección contra ÷0

Hay 8 municipios que se incorporan al panel gradualmente (algunos trimestres con `pob_adulta = 0`). Para estos casos, la fórmula produciría una división por cero. La implementación maneja este caso explícitamente: cuando el denominador es cero, la columna per cápita recibe `NaN` (no se genera infinito ni error). Esto significa que:
- Los 41,897 registros con población > 0 tienen su valor per cápita calculado correctamente.
- Los 8 registros sin población quedan como missing, que los modelos de regresión excluyen automáticamente.

#### Columnas per cápita creadas (conteos)

Se crearon 30 columnas, siguiendo el esquema `{prefijo}_{producto}_{sexo}_pc`:

- `ncont_ahorro_m_pc`, `ncont_ahorro_h_pc`, `ncont_ahorro_t_pc`
- `ncont_plazo_m_pc`, `ncont_plazo_h_pc`, `ncont_plazo_t_pc`
- `ncont_n1_m_pc`, `ncont_n1_h_pc`, `ncont_n1_t_pc`
- `ncont_n2_m_pc`, `ncont_n2_h_pc`, `ncont_n2_t_pc`
- `ncont_n3_m_pc`, `ncont_n3_h_pc`, `ncont_n3_t_pc`
- `ncont_tradic_m_pc`, `ncont_tradic_h_pc`, `ncont_tradic_t_pc`
- `ncont_total_m_pc`, `ncont_total_h_pc`, `ncont_total_t_pc`
- `numtar_deb_m_pc`, `numtar_deb_h_pc`, `numtar_deb_t_pc`
- `numtar_cred_m_pc`, `numtar_cred_h_pc`, `numtar_cred_t_pc`
- `numcontcred_hip_m_pc`, `numcontcred_hip_h_pc`, `numcontcred_hip_t_pc`

#### Estadísticas de validación (columnas clave)

| Columna | Media | Min | Max | NaNs |
|---------|-------|-----|-----|------|
| `ncont_total_m_pc` | 3,429.69 | 0.00 | 179,439.41 | 0 |
| `ncont_ahorro_m_pc` | 6.19 | 0.00 | 3,515.38 | 0 |
| `numtar_deb_m_pc` | 3,515.54 | 0.00 | 2,839,565.83 | 0 |

> **Interpretación de la tabla:** La media de `ncont_total_m_pc` = 3,429 significa que, en promedio, hay 3,429 contratos de captación por cada 10,000 mujeres adultas en un municipio-trimestre. Pero el máximo de 179,439 (casi 18× la base de 10,000) indica que hay municipios donde el número de contratos supera varias veces a la población — esto ocurre cuando la banca comercial de una ciudad metropolitana registra cuentas de personas que no necesariamente residen ahí (efecto sede). El valor extremo de `numtar_deb_m_pc` (2.8 millones) confirma que la **winsorización** (Rec 6) será importante como paso de robustez para manejar estos outliers.

---

### Rec 2. Normalización per cápita de saldos (`saldocont_*`)

#### ¿Qué se hizo?

Se crearon 21 columnas nuevas con sufijo `_pc` para los saldos de captación, usando la misma fórmula y mapeo de denominadores que los conteos.

$$\text{saldocont\_*\_pc} = \frac{\text{saldocont\_*} \times 10{,}000}{\text{pob\_adulta\_*}}$$

#### ¿Por qué normalizar los saldos además de los conteos?

Los conteos (Rec 1) miden la **extensión** del sistema financiero: ¿cuántas personas tienen algún contrato? Los saldos miden la **profundidad**: ¿cuánto dinero hay depositado? Son dimensiones complementarias de la inclusión financiera.

Un municipio puede tener muchos contratos con saldos pequeños (alta extensión, baja profundidad) o pocos contratos con saldos enormes (baja extensión, alta profundidad). Ambas dimensiones son relevantes para la tesis porque el efecto de una alcaldesa podría manifestarse en la apertura de más cuentas (extensión), en mayores depósitos en cuentas existentes (profundidad), o en ambas.

La normalización per cápita de saldos enfrenta exactamente los mismos problemas de escala que los conteos: sin normalizar, los municipios grandes dominan la distribución y los coeficientes miden "tamaño" en vez de "profundidad financiera".

> **Nota:** `saldocont_total_m_pc` es uno de los outcomes primarios de la tesis. La transformación per cápita + asinh es la escala principal del análisis TWFE.

#### Columnas creadas

`saldocont_ahorro_m_pc`, `saldocont_ahorro_h_pc`, ..., `saldocont_total_t_pc` (21 en total; las `_pm` no se normalizan por las mismas razones que en Rec 1).

---

### Rec 3. Documentación de `saldoprom_*` (NULLs estructurales — NO imputar)

#### ¿Qué se hizo?

Se documentó la distribución de NULLs en las 28 columnas `saldoprom_*`. **NO se imputaron** porque los NULLs son el resultado correcto.

#### ¿Por qué NO imputar estos NULLs?

El saldo promedio por contrato se calcula como:

$$\text{saldoprom} = \frac{\text{saldo total de contratos (saldocont)}}{\text{número de contratos (ncont)}}$$

Cuando un municipio tiene **0 contratos** de cierto producto, la operación es $\frac{0}{0}$, que es matemáticamente indefinida. Imputar un valor (como 0, o la media de otros municipios) sería conceptualmente incorrecto:

- **Imputar con 0** diría "el saldo promedio por contrato es $0 pesos" — pero no hay contratos. Cero no es lo mismo que "no aplica". Si un municipio no tiene hipotecas, ¿el saldo promedio por hipoteca es $0? No: la pregunta no tiene sentido.
- **Imputar con la media** diría "suponemos que si este municipio tuviera contratos, tendría el saldo promedio nacional" — pero eso introduce información ficticia y infla artificialmente el tamaño de la muestra.
- **La opción correcta** es mantener el `NULL` y documentarlo con una flag binaria que explique **por qué** falta el dato.

Esta decisión sigue el principio estadístico fundamental de distinguir entre **datos faltantes aleatorios** (MCAR/MAR — que se pueden imputar bajo ciertos supuestos) y **datos faltantes estructurales** (que reflejan una imposibilidad lógica, no una deficiencia en la recolección).

#### Distribución de NULLs en `saldoprom_*`

| Variable | NULLs | % NULL | Interpretación |
|----------|-------|--------|----------------|
| `saldoprom_ahorro_m` | 39,267 | 93.7% | Casi ningún municipio tiene cuentas de ahorro formal |
| `saldoprom_n1_m` | 40,586 | 96.9% | Productos nivel 1 son extremadamente escasos |
| `saldoprom_n2_m` | 1,118 | 2.7% | Productos nivel 2 son los más extendidos |
| `saldoprom_total_m` | 1,102 | 2.6% | Solo 2.6% de observaciones sin ningún contrato |
| `saldoprom_plazo_m` | 24,231 | 57.8% | Más de la mitad sin depósitos a plazo registrados |

#### ¿Cómo se usa en la práctica?

Las flags `flag_undef_saldoprom_*` permiten definir dos muestras analíticas complementarias:

- **Margen extensivo** (usa la muestra completa): "¿Tener alcaldesa aumenta la probabilidad de que el municipio tenga *algún* contrato de ahorro?" → Se usa `ncont_ahorro_m` > 0 como variable dependiente binaria. No necesita `saldoprom_*`.
- **Margen intensivo** (filtra `flag = 0`): "Dado que el municipio ya tiene contratos de ahorro, ¿tener alcaldesa cambia el saldo promedio por contrato?" → Se usa `saldoprom_ahorro_m` como variable dependiente, pero solo para municipios con `flag_undef_saldoprom_ahorro_m = 0`.

Esta distinción extensivo/intensivo es estándar en la literatura de inclusión financiera (Allen et al., 2016; Demirgüç-Kunt et al., 2018) y permite separar el efecto "crear acceso donde no lo hay" del efecto "profundizar el uso donde ya existe".

---

### Rec 4. Exclusión de columnas constantes

#### ¿Qué se hizo?

Se eliminaron 3 columnas que tienen varianza exactamente igual a cero (el mismo valor en las 41,905 observaciones):

| Columna eliminada | Valor constante | Por qué es constante |
|:---|:---|:---|
| `hist_state_available` | 1 | Todos los estados tienen historia municipal disponible |
| `missing_quarters_alcaldesa` | 0 | Ningún municipio tiene trimestres faltantes en `alcaldesa_final` |
| `ok_panel_completo_final` | 1 | Todos los municipios sobreviven el filtro de completitud |

#### ¿Por qué no pueden quedarse en la base?

Una variable constante tiene varianza = 0, lo que significa que **no contiene información alguna** sobre diferencias entre municipios o cambios en el tiempo. En cualquier modelo de regresión:

1. **Colinealidad con el intercepto.** Una columna que siempre vale 1 es algebraicamente idéntica al vector de intercepto $\mathbf{1}$. Incluirla generaría una matriz de diseño $\mathbf{X}$ singular (no invertible), y el estimador OLS $(\mathbf{X}'\mathbf{X})^{-1}\mathbf{X}'\mathbf{y}$ no existiría. Los paquetes estadísticos (linearmodels, statsmodels) detectan esto y eliminan la columna automáticamente, emitiendo una advertencia.

2. **Ruido en la exploración.** Si dejamos 3 columnas que siempre dicen "1, 1, 1, ...", un investigador futuro que explore la base podría perder tiempo preguntándose qué miden, comprobando si son relevantes, o incluyéndolas accidentalmente como controles.

3. **Eficiencia computacional.** Aunque 3 columnas son triviales en tamaño, su eliminación explícita documenta que el equipo de investigación auditó la base, identificó variables inútiles y las removió deliberadamente (no por olvido).

> **Nota para la defensa:** Estas 3 variables se volvieron constantes *como resultado* de nuestro proceso de limpieza. Originalmente, `hist_state_available` variaba entre estados con y sin cobertura histórica, pero al final del proceso todos los estados quedaron cubiertos. El hecho de que sean constantes es, paradójicamente, una buena noticia: sirven como prueba de que nuestra base no tiene huecos.

---

### Script de transformaciones

El script que ejecuta todas las transformaciones se encuentra en:
`src/transformaciones_criticas.py`

**Uso:**
```bash
cd /Users/anapaulaperezgavilan/Documents/Tesis_DB/Code
source .venv/bin/activate
python src/transformaciones_criticas.py
```

El script es **idempotente**: puede re-ejecutarse sin problemas (elimina y recrea la tabla limpia). Esto garantiza reproducibilidad: cualquier miembro del comité de tesis puede regenerar la tabla `inclusion_financiera_clean` ejecutando un solo comando.

---

### Resumen de estado de recomendaciones

| # | Prioridad | Categoría | Estado | Lógica de la recomendación |
|:---|:---|:---|:---|:---|
| 1 | 🔴 CRÍTICA | Normalización conteos | ✅ Resuelto | Sin per cápita, el modelo mide tamaño poblacional, no inclusión financiera |
| 2 | 🔴 CRÍTICA | Normalización saldos | ✅ Resuelto | Complementa Rec 1 midiendo la profundidad (pesos por persona) |
| 3 | 🔴 CRÍTICA | saldoprom NULLs | ✅ Documentado | NULLs son ÷0 estructurales — imputar sería incorrecto |
| 4 | 🔴 CRÍTICA | Exclusión constantes | ✅ Resuelto | Variables sin varianza causan colinealidad y no aportan información |
| 5 | 🟡 Alta | log(pob) | ✅ En modelado | La relación población→outcomes es multiplicativa, no aditiva |
| 6 | 🟡 Alta | Winsorización | ✅ En modelado | Recortar al p1–p99 limita influencia de outliers extremos (efecto sede) |
| 7 | 🟡 Alta | Ratio M/H | Pendiente | Captura brecha de género directamente como outcome alternativo |
| 8 | 🟡 Alta | ever_alcaldesa | ✅ En modelado | Clasifica municipios como ever/never-treated para el análisis DiD |
| 9 | 🟡 Alta | IDs estándar | Pendiente | Facilita merges con INEGI y otros datos administrativos |
| 10 | 🟢 Media | alcaldesa_acumulado | ✅ En modelado | Permite especificaciones dosis-respuesta |
| 11 | 🟢 Media | asinh/log outcomes | ✅ En modelado | Comprime colas y estabiliza varianza en distribuciones asimétricas |
| 12 | 🟢 Media | tipo_pob NULLs | Pendiente | Solo 2 obs — impacto negligible |
