> **Archivos fuente:**
> - `src/tesis_alcaldesas/models/extensive_margin.py`

# 18 — Extensión: Outcomes del Margen Extensivo y Composición

## Motivación

Los outcomes principales de la tesis miden **intensidad** (contratos per cápita,
saldos per cápita) en escala asinh. Pero una alcaldesa también podría afectar
el **margen extensivo** (¿hay *algún* acceso?) o la **composición de género**
(¿cambia la proporción de mujeres?).

Esta extensión es **exploratoria**: se declara antes de
ver los resultados como una pregunta complementaria, no como un ejercicio de
búsqueda de significancia.

## Outcomes

### Panel A: Margen extensivo (LPM)

Variable binaria:
$$\text{any\_X\_m} = \mathbf{1}\{X_m > 0\}$$

Se estima con un **Linear Probability Model** (LPM = OLS con Y binaria):
misma estructura TWFE con FE municipio + periodo, cluster SE municipio.

| Variable | Definición |
|---|---|
| `any_ncont_total_m` | ¿Tiene al menos un contrato? |
| `any_numtar_deb_m` | ¿Tiene al menos una tarjeta de débito? |
| `any_numtar_cred_m` | ¿Tiene al menos una tarjeta de crédito? |
| `any_numcontcred_hip_m` | ¿Tiene al menos un crédito hipotecario? |
| `any_saldocont_total_m` | ¿Tiene saldo > 0? |

### Panel B: Composición de género

$$\text{share\_m} = \frac{y_{m,\text{pc}}}{y_{m,\text{pc}} + y_{h,\text{pc}}}$$

con guarda: solo se calcula cuando el denominador > 1 por cada 10,000 adultos.

Un coeficiente positivo significaría que las alcaldesas *redistribuyen* el
acceso financiero hacia las mujeres, incluso si el total no cambia.

## Notas metodológicas

- **LPM vs Logit**: Se usa LPM por consistencia con el diseño de FE de panel.
  Logit con muchos FE puede tener problemas de incidental parameters.
- **Pre-especificación**: Se reporta como extensión exploratoria para evitar
  acusaciones de p-hacking. No forma parte de las hipótesis principales.

## Ejecución

```bash
python -m tesis_alcaldesas.models.extensive_margin
```

## Outputs

| Archivo | Contenido |
|---|---|
| `tabla_7_extensive.csv` | Resultados crudos (ambos paneles) |
| `tabla_7_extensive.tex` | Tabla LaTeX para la tesis |

> **📖 Cómo leer la Tabla 7 — Margen extensivo y composición (paso a paso)**
>
> La Tabla 7 (en `outputs/paper/tabla_7_extensive.csv`) tiene dos paneles:
> A (margen extensivo) y B (composición de género). Cada panel reporta un
> TWFE para cada variable con FE municipio + periodo y cluster SE municipal.
>
> **Panel A — Margen extensivo (LPM):**
>
> | Columna | Significado |
> |---------|-------------|
> | Variable | Indicador binario (1 = tiene al menos un producto) |
> | $\hat{\beta}$ | Cambio en probabilidad (pp) asociado al tratamiento |
> | SE | Error estándar clustered |
> | p | p-valor |
>
> **Paso 1:** Un $\hat{\beta} = 0.02$ significaría que la alcaldesa aumenta
> en 2 puntos porcentuales la probabilidad de que un municipio tenga al menos
> un contrato de mujer. Verifica si alguno es significativo.
>
> **Paso 2:** Si todos son nulos, la alcaldesa no afecta la presencia/ausencia
> de productos — el efecto (si existe) opera en el **margen intensivo** (cantidad).
>
> **Panel B — Composición de género (share):**
>
> | Columna | Significado |
> |---------|-------------|
> | Variable | Proporción de mujeres en el total ($\frac{y_m}{y_m + y_h}$) |
> | $\hat{\beta}$ | Cambio en la proporción de mujeres (en puntos) |
>
> **Paso 1:** Un $\hat{\beta} > 0$ significativo indicaría que la alcaldesa
> redistribuye el acceso financiero **hacia** las mujeres (aunque el total
> no cambie). Si es nulo, la composición se mantiene estable.
>
> **Paso 2:** Compara con los resultados del TWFE (Tabla 2). Si el
> TWFE detecta efecto en algún outcome pero el share no cambia,
> el efecto incrementa el acceso femenino **sin alterar** la proporción total.
>
> **Nota metodológica:** El LPM puede generar predicciones fuera de $[0, 1]$,
> pero en FE de panel es estándar y más robusto que logit con muchos FE
> (problema de parámetros incidentales).
>
> **Lectura rápida:** Esta tabla es exploratoria. Busca si la alcaldesa
> afecta el acceso binario o la proporción de género, complementando los
> resultados intensivos de la Tabla 2.
