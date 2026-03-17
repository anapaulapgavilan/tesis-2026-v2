> **Archivos fuente:**
> - `src/tesis_alcaldesas/models/mdes_power.py`

# 16 — MDES y Análisis de Poder Estadístico

## ¿Qué es el MDES?

El **Minimum Detectable Effect Size** (MDES) es el efecto más pequeño que un
diseño de investigación puede detectar con una probabilidad determinada (poder
estadístico). Se calcula como:

$$\text{MDES} = (z_{\alpha/2} + z_{\beta}) \times SE$$

donde:
- $z_{\alpha/2}$ = cuantil normal bilateral para el nivel de significancia
  (1.96 para $\alpha = 0.05$)
- $z_{\beta}$ = cuantil normal para el poder deseado
  (0.84 para poder = 80%)
- $SE$ = error estándar del coeficiente de tratamiento

## ¿Por qué importa para esta tesis?

El resultado principal de la tesis es un **efecto nulo**: no se detecta un
impacto estadísticamente significativo de las alcaldesas sobre la inclusión
financiera femenina. Sin embargo, un nulo puede significar dos cosas:

1. **No hay efecto** (verdadero nulo)
2. **Hay efecto pero el estudio no tiene poder para detectarlo** (falso nulo)

El MDES permite distinguir entre ambos: reporta el efecto más pequeño que
*sí podríamos haber detectado*. Si ese umbral es razonablemente pequeño,
el nulo es informativo ("descartamos efectos mayores a X%").

## Resultados

Los resultados están en:
- `outputs/paper/tabla_6_mdes.csv` — tabla completa
- `outputs/paper/tabla_6_mdes.tex` — formato LaTeX para la tesis
- `outputs/paper/mdes_summary.txt` — interpretación en lenguaje natural

### Interpretación

La SE del tratamiento TWFE viene de la Tabla 2 baseline. Los MDES se reportan
en dos escalas:

1. **Escala asinh** — directamente comparable con los coeficientes reportados
2. **Escala porcentual aproximada** — usando $(\exp(|\text{MDES}|) - 1) \times 100$

Esta aproximación es válida porque para $y$ grande, $\text{asinh}(y) \approx \ln(2y)$,
y cambios en log son cambios porcentuales.

> **📖 Cómo leer la Tabla 6 — MDES (paso a paso)**
>
> La Tabla 6 (en `outputs/paper/tabla_6_mdes.csv`) reporta el efecto mínimo
> detectable para cada outcome. Aquí se explica cómo interpretarla.
>
> **Columnas esperadas:**
> | Columna | Significado |
> |---------|-------------|
> | outcome | Variable dependiente |
> | SE | Error estándar del coeficiente TWFE (de Tabla 2) |
> | MDES_asinh | Efecto mínimo detectable en escala asinh: $(z_{0.025} + z_{0.80}) \times SE = 2.80 \times SE$ |
> | MDES_pct | Aproximación porcentual: $(\exp(|\text{MDES}|) - 1) \times 100$ |
>
> **Paso 1 — Lee la columna MDES_pct para cada outcome:**
> Este número dice: "con nuestro diseño, podemos descartar efectos mayores
> a X%". Por ejemplo, si MDES_pct = 6.2% para contratos totales, entonces
> el nulo del TWFE es informativo: descartamos incrementos mayores al 6.2%.
>
> **Paso 2 — Compara MDES con los efectos del Stacked DiD:**
> Si el Stacked DiD detecta $\hat{\beta} = 0.082$ (~8.5%) pero el MDES del
> TWFE era ~6%, eso explica por qué el TWFE podría haberlo detectado si no
> tuviera sesgo de atenuación. La divergencia refuerza la hipótesis de sesgo.
>
> **Paso 3 — Evalúa la "informatividad" del nulo:**
> Para outcomes donde ambos estimadores coinciden en nulo (tarjetas, hipotecarios):
> - Si MDES_pct es pequeño (< 10%): el nulo es informativo → "no hay efectos
>   de magnitud relevante para política pública".
> - Si MDES_pct es grande (> 30%): el nulo **no** es informativo → el estudio
>   simplemente no tenía poder para detectar efectos plausibles.
>
> **Paso 4 — Contextualiza con la literatura:**
> ¿Qué efectos son realistas? En la literatura de representación política
> femenina, los efectos sobre outcomes financieros suelen ser de un dígito
> porcentual. Si el MDES es del mismo orden, el estudio tiene relevancia.
>
> **Lectura rápida:** El MDES traduce "no encontramos efecto" en "podemos
> descartar efectos mayores a X%". Cuanto menor sea X, más informativo
> es el resultado nulo.

### Cómo citar en la tesis

> "Con el diseño actual (N ≈ 41,905 observaciones municipio-trimestre, errores
> estándar agrupados a nivel municipal), podemos descartar con 80% de poder
> estadístico ($\alpha = 0.05$) efectos del tratamiento mayores a [X]% en
> [outcome]. El resultado nulo es informativo: efectos de la magnitud que la
> política pública podría esperar (mejoras de un dígito porcentual en indicadores
> de inclusión financiera) no están en nuestro intervalo de confianza."

## Ejecución

```bash
python -m tesis_alcaldesas.models.mdes_power
```

## Referencias

- Bloom, H. S. (1995). *Minimum Detectable Effects: A Simple Way to Report the
  Statistical Power of Experimental Designs*. Evaluation Review, 19(5), 547–556.
- Ioannidis, J. P. A., Stanley, T. D. & Doucouliagos, H. (2017). *The Power of
  Bias in Economics Research*. Economic Journal, 127, F236–F265.
