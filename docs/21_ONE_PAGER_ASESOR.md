> **Archivos fuente:**
> - *(Documento de resumen — no referencia scripts directamente)*

# 21 — One-Pager para el Asesor

## Alcaldesas y Bancarización Municipal: Evidencia con Diferencias en Diferencias

**Ana Paula Pérez Gavilán** · ITAM, Tesis de Licenciatura, 2026

---

### Pregunta de investigación

¿Las presidentas municipales (alcaldesas) tienen un efecto causal sobre la
inclusión financiera en sus municipios, medida a través de contratos de
crédito, saldos crediticios y productos bancarios (tarjetas de débito y
crédito, créditos hipotecarios)?

### Datos

- **CNBV — Base de Datos de Inclusión Financiera (BDIF):** panel trimestral
  municipio-periodo, 2018-T3 a 2022-T3 (17 trimestres).
- **2,471 municipios**, 41,905 observaciones.
- **Tratamiento:** `alcaldesa_final = 1` si el municipio tiene alcaldesa;
  varía en el tiempo con el calendario electoral.
- **5 variables dependientes** (per cápita, transformación arcsinh):
  contratos de crédito (`ncont_total`), saldo total (`saldocont_total`),
  tarjetas de débito (`numtar_deb`), tarjetas de crédito (`numtar_cred`),
  créditos hipotecarios (`numcontcred_hip`).

### Estrategia de identificación

1. **TWFE clásico** (two-way fixed effects): efectos fijos municipio + periodo,
   errores estándar clustered por municipio.
2. **Stacked DiD** (Cengiz et al. 2019 / Baker et al. 2022): sub-experimentos
   limpios por cohorte de tratamiento, evitando comparaciones ya-tratado
   vs. ya-tratado. Pre-especificado como robustez ante heterogeneidad
   temporal (Goodman-Bacon 2021).

### Resultados principales

| Estimador | Contratos crédito | Saldo total | Tar. débito | Tar. crédito | Hipotecarios |
|---|---|---|---|---|---|
| **TWFE** | nulo | nulo | nulo | nulo | nulo |
| **Stacked DiD** | **+0.082*** | **+0.274*** | nulo | nulo | nulo |

\* p < 0.01 · Errores clustered por municipio (~2,077 clusters). Estimaciones ITT.
Robustez absorbing-only (409 sw): contratos +0.107***, saldo +0.350***.

- **Event studies** (ambos estimadores): pre-tendencias no significativas.
- **MDES** (diseño mínimo detectable): 0.026–0.088 σ → el diseño tiene poder
  para detectar efectos moderados.
- **Robustez ventana:** coeficientes estables (±5%) en ventanas [-4,+8],
  [-3,+8], [-4,+6]; todos significativos al 1%.

### Interpretación

El TWFE nulo **no implica ausencia de efecto**, sino que la estimación puntual
es estadísticamente indistinguible de cero, posiblemente absorbida por
heterogeneidad temporal en el tratamiento. El Stacked DiD — diseñado para
aislar comparaciones limpias — detecta un efecto positivo y significativo en
**contratos de crédito** (margen extensivo) y **saldo total** (margen
intensivo).

El patrón 3/5 resultados coincidentes entre estimadores sugiere que la
divergencia se concentra donde la teoría lo predice: productos crediticios
agregados son más sensibles a la inclusión financiera que productos
individuales (tarjetas, hipotecas).

### Contribución

- Primera evidencia causal municipio-nivel de un mecanismo de inclusión
  financiera atribuible a género del ejecutivo local en México.
- Implementación rigurosa del Stacked DiD como robustez pre-especificada,
  con análisis de sensibilidad completo (MDES, ventana, heterogeneidad).

### Reproducibilidad

```bash
cd Code
PYTHONPATH=src .venv/bin/python -m tesis_alcaldesas.run_all
PYTHONPATH=src .venv/bin/python -m did_moderno.window_robustness
```

Todos los outputs quedan en `outputs/paper/`. Tag: `v1.0-thesis-results`.
