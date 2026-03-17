# EDA — Inclusión Financiera y Alcaldesas

**Fecha:** 24/02/2026  
**Pregunta:** ¿Cuál es el efecto de la representación política a nivel municipal en la inclusión financiera de las mujeres en México?

---

## Estructura del EDA

| Sección | Descripción | Output |
|---|---|---|
| **A** | Diccionario observado (perfil de cada variable) | `A_diccionario_observado.csv` |
| **B** | Calidad e integridad (duplicados, balance, consistencia) | `B_calidad_integridad.csv`, `B_completitud_panel.csv` |
| **C** | Distribuciones univariadas (tratamiento, población, outcomes) | `C1_*.png` – `C5_*.png` |
| **D** | Relaciones bivariadas alineadas a la pregunta | `D1_*.png` – `D6_*.png` |
| **E** | Chequeos de sesgo / leakage | `E_sesgo_leakage.csv` |
| **F** | Recomendaciones de limpieza / transformaciones | `F_recomendaciones.csv` |

---

## Hallazgos clave

### 1. Panel limpio y balanceado
- 2,471 municipios × 17 trimestres = 41,905 observaciones
- 100% balanceado, sin duplicados
- PK: `(cve_mun, periodo_trimestre)`

### 2. Tratamiento: `alcaldesa_final`
- ~22% de municipios-trimestre tienen alcaldesa
- **894 municipios son switchers** (cambian de tratamiento): estos identifican el efecto en modelos de efectos fijos
- 101 siempre tratados, 1,476 nunca tratados
- Variación geográfica fuerte: desde ~51% (Baja California) hasta ~10% en otros estados

### 3. Outcomes: inclusión financiera
- 10 variables clave por sexo (contratos, tarjetas, créditos hipotecarios)
- **Normalización per cápita es CRÍTICA**: correlación población-outcomes ~ 0.70
- Brecha de género visible en la mayoría de productos (hombres > mujeres en términos per cápita)

### 4. Calidad de datos
- 47 columnas con NULLs (mayoría estructurales: saldoprom_* por ÷0)
- 3 columnas constantes (excluir de modelos)
- 2 NULLs en tipo_pob (mínimo impacto)
- 0 valores negativos
- 47 municipios con nombre repetido → usar siempre `cve_mun` o `cvegeo_mun`

### 5. Riesgos de sesgo
- Los municipios con alcaldesa tienden a ser más pequeños → sesgo de selección corregible con efectos fijos
- Variables forward (`_f1/f2/f3`) son leakage temporal — solo para pre-trends
- Variables de transición — potencialmente endógenas

---

## Variables para el modelo causal

| Rol | Variables |
|---|---|
| **Y (outcome)** | `ncont_*_m / pob_adulta_m × 10,000` o ratio M/H |
| **T (tratamiento)** | `alcaldesa_final` |
| **FE municipio** | `cve_mun` (absorbe todo lo time-invariant) |
| **FE tiempo** | `periodo_trimestre` (absorbe shocks nacionales) |
| **Controles** | `log(pob_adulta_m)`, `tipo_pob` |
| **Robustez** | `alcaldesa_excl_trans`, winsorización p1–p99, logs |
| **Event study** | `alcaldesa_final_l1/l2/l3` + `alcaldesa_final_f1/f2/f3` |

---

## Próximos pasos

1. ✅ Crear variables per cápita y ratio M/H  
2. Estimar modelo TWFE (Two-Way Fixed Effects) con `linearmodels` o `pyfixest`  
3. Event study con rezagos/adelantos para validar supuesto de tendencias paralelas  
4. Análisis de heterogeneidad por región, tipo_pob, y tamaño de municipio  
5. Robustez: excluir trimestres de transición, winsorizar, transformaciones log  

---

## Cómo reproducir

```bash
# Desde la raíz del proyecto (Code/)
python -m src.eda.run_eda
```

O abrir `notebooks/eda.ipynb` en Jupyter/VS Code y ejecutar celda por celda.

---

## Archivos generados

| Archivo | Tipo | Descripción |
|---|---|---|
| `A_diccionario_observado.csv` | CSV | Perfil de 175 variables: tipo, NA%, cardinalidad, estadísticos |
| `B_calidad_integridad.csv` | CSV | Checklist de validaciones de calidad |
| `B_completitud_panel.csv` | CSV | Municipios y tratamiento por trimestre |
| `C1_tratamiento_por_trimestre.png` | IMG | Proporción de alcaldesas en el tiempo |
| `C2_distribucion_poblacion.png` | IMG | Histogramas de población (log) |
| `C3_boxplot_outcomes_mujeres_pc.png` | IMG | Distribución de outcomes per cápita |
| `C4_categoricas_clave.png` | IMG | Distribución de región, tipo_pob, estados |
| `C5_tipo_pob_tratamiento.png` | IMG | Tipo de población × alcaldesa |
| `D1_outcomes_por_tratamiento.png` | IMG | Outcomes por tratamiento (boxplot) |
| `D2_brecha_genero_temporal.png` | IMG | Mujeres vs hombres en el tiempo |
| `D3_tendencia_por_tratamiento.png` | IMG | **Clave**: ¿tendencias paralelas pre-tratamiento? |
| `D4_ratio_MH_por_tratamiento.png` | IMG | Ratio M/H por tratamiento |
| `D5_correlaciones_spearman.png` | IMG | Heatmap de correlaciones |
| `D6_balance_pre_tratamiento.png` | IMG | Balance baseline de switchers |
| `E_sesgo_leakage.csv` | CSV | Variables con riesgo de sesgo/leakage |
| `F_recomendaciones.csv` | CSV | Transformaciones recomendadas con prioridad |
