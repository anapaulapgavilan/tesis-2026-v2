"""
build_features.py -- Paso 2 del pipeline: Construye el dataset analitico final.

GUIA PARA EL ASESOR:
  Este script transforma los datos crudos del Paso 1 en variables listas
  para la estimacion econometrica. Es el corazon de la ingenieria de datos.

  Etapas (en orden):
    1. VALIDACION: Verifica PK unica, identifica panel desbalanceado (8 municipios
       con periodos faltantes de 102 obs, 0.24% del panel).
    2. PER CAPITA: Cada outcome se normaliza por poblacion adulta femenina
       (x10,000). Esto permite comparar municipios de distinto tamano.
    3. TRANSFORMACIONES FUNCIONALES:
       - asinh(y_pc): transformacion principal. Similar a log() pero
         definida en cero. Permite interpretar coeficientes como semi-elasticidades.
         (Bellemare & Wichman, 2020)
       - winsor p1-p99: recorta colas para chequear sensibilidad a outliers.
       - log(1+y_pc): alternativa clasica de robustez.
    4. RATIOS DE GENERO: outcome_m / outcome_h para medir brecha relativa.
    5. FLAGS: marca observaciones con denominador cero, panel incompleto,
       o outcomes indefinidos para analisis de sensibilidad.
    6. COHORTE: clasifica municipios en never-treated (1,476), switcher (894),
       y always-treated (101). Calcula event_time = t - first_treat_t.

  El dataset final tiene 41,905 filas x 170 columnas y se exporta como parquet.

Input:   data/processed/analytical_panel.parquet
Outputs: data/processed/analytical_panel_features.parquet
         outputs/qc/panel_checks.txt
         outputs/qc/cohort_summary.csv

Uso:
    python -m tesis_alcaldesas.data.build_features
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from tesis_alcaldesas.config import (
    DATA_DIR, OUTPUT_QC, RAW_OUTCOMES_M, RAW_OUTCOMES_H, PRIMARY_OUTCOMES,
    PARQUET_RAW, PARQUET_FEATURES,
)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
INPUT      = PARQUET_RAW
OUTPUT     = PARQUET_FEATURES
QC_DIR     = OUTPUT_QC

PANEL_LOG  = QC_DIR / "panel_checks.txt"
COHORT_CSV = QC_DIR / "cohort_summary.csv"

# Alias para compatibilidad con código interno
PRIMARY_5 = PRIMARY_OUTCOMES


# ===================================================================
# 1. CARGA Y VALIDACIÓN
# ===================================================================
def load_and_validate(path: Path) -> tuple[pd.DataFrame, list[str]]:
    """Carga parquet, valida PK y balance. Retorna (df, log_lines)."""
    log: list[str] = []
    df = pd.read_parquet(path)
    log.append(f"Archivo: {path}")
    log.append(f"Shape: {df.shape[0]:,} filas × {df.shape[1]} columnas")

    # --- PK ---
    pk_cols = ["cve_mun", "periodo_trimestre"]
    n_dup = df.duplicated(subset=pk_cols).sum()
    log.append(f"\nPK ({', '.join(pk_cols)}): {'OK única' if n_dup == 0 else f'FAIL {n_dup} duplicados'}")

    # --- Panel dimensions ---
    n_mun = df["cve_mun"].nunique()
    n_per = df["periodo_trimestre"].nunique()
    n_expected = n_mun * n_per
    n_actual = len(df)
    balanced = n_actual == n_expected

    log.append(f"\nMunicipios: {n_mun:,}")
    log.append(f"Periodos: {n_per}")
    log.append(f"N esperado (balanceado): {n_expected:,}")
    log.append(f"N actual: {n_actual:,}")
    log.append(f"Celdas faltantes: {n_expected - n_actual:,} ({(n_expected - n_actual) / n_expected * 100:.2f}%)")
    log.append(f"Balanceado: {'OK' if balanced else 'FAIL NO'}")

    # --- Municipios incompletos ---
    if not balanced:
        counts = df.groupby("cve_mun").size()
        incomplete = counts[counts < n_per].sort_values()
        log.append(f"\nMunicipios con panel incompleto ({len(incomplete)}):")
        for mun, ct in incomplete.items():
            log.append(f"  cve_mun={mun}: {ct}/{n_per} periodos ({n_per - ct} faltantes)")
        log.append("\nDecisión de muestra:")
        log.append("  • Se conservan TODOS los municipios (panel no balanceado).")
        log.append("  • Se añade flag `flag_incomplete_panel` para sensibilidad.")
        log.append("  • Robustez: re-estimar excluyendo municipios incompletos.")

    # --- Treatment distribution ---
    if "alcaldesa_final" in df.columns:
        td = df["alcaldesa_final"].value_counts(normalize=True).sort_index()
        log.append(f"\nDistribución tratamiento (alcaldesa_final):")
        for val, pct in td.items():
            log.append(f"  {int(val)}: {pct:.2%}")

    # --- Periodos ---
    periodos = sorted(df["periodo_trimestre"].unique())
    log.append(f"\nPeriodos: {periodos[0]} – {periodos[-1]}")

    return df, log


# ===================================================================
# 2. OUTCOMES PER CAPITA (x10,000)
# ===================================================================
# GUIA: La normalizacion per capita es esencial porque los outcomes
# crudos estan en numeros absolutos. Un municipio grande tiene mas
# contratos simplemente por tener mas poblacion.
# Dividimos por pob_adulta_m y multiplicamos por 10,000 para obtener
# "contratos por cada 10,000 mujeres adultas".
# Si el denominador es 0, el resultado es NaN (no division por cero).
def build_per_capita(df: pd.DataFrame, outcomes: list[str], denom: str) -> pd.DataFrame:
    """Crea columnas _pc = 10000 * raw / denom."""
    for col in outcomes:
        if col not in df.columns:
            print(f"  [!] columna {col} no encontrada — se omite.")
            continue
        pc_col = f"{col}_pc"
        # Usar np.where para manejar denominador=0 --> NaN
        df[pc_col] = np.where(
            df[denom] > 0,
            10_000 * df[col].astype(float) / df[denom].astype(float),
            np.nan,
        )
    return df


# ===================================================================
# 3. TRANSFORMACIONES
# ===================================================================
# GUIA: Se aplican 3 transformaciones funcionales a cada outcome per capita.
#
# a) asinh (arcoseno hiperbolico inverso): Y* = asinh(Y_pc)
#    - Principal escala usada en las regresiones.
#    - Similar a log(Y) para valores grandes, pero definida en Y=0.
#    - Permite interpretar coeficientes como semi-elasticidades aproximadas.
#    - Referencia: Bellemare & Wichman (2020, JASA).
#
# b) winsor p1-p99: Recorta valores extremos al percentil 1 y 99.
#    - Usada en pruebas de robustez (R2) para verificar que los resultados
#      no estan impulsados por outliers.
#
# c) log(1+Y_pc): Transformacion clasica alternativa.
#    - Usada en prueba de robustez (R1) para verificar que la eleccion
#      de asinh vs log no cambia las conclusiones.
def build_asinh(df: pd.DataFrame, outcomes: list[str]) -> pd.DataFrame:
    """asinh(y_pc) — robusta a ceros y valores negativos."""
    for col in outcomes:
        pc_col = f"{col}_pc"
        if pc_col not in df.columns:
            continue
        df[f"{col}_pc_asinh"] = np.arcsinh(df[pc_col])
    return df


def build_winsor(df: pd.DataFrame, outcomes: list[str],
                 lo: float = 0.01, hi: float = 0.99) -> pd.DataFrame:
    """Winsoriza _pc al rango [p1, p99]."""
    for col in outcomes:
        pc_col = f"{col}_pc"
        if pc_col not in df.columns:
            continue
        vals = df[pc_col].dropna()
        if len(vals) == 0:
            continue
        q_lo = vals.quantile(lo)
        q_hi = vals.quantile(hi)
        df[f"{col}_pc_w"] = df[pc_col].clip(lower=q_lo, upper=q_hi)
    return df


def build_log1p(df: pd.DataFrame, outcomes: list[str]) -> pd.DataFrame:
    """log(1 + y_pc) — alternativa de robustez."""
    for col in outcomes:
        pc_col = f"{col}_pc"
        if pc_col not in df.columns:
            continue
        df[f"{col}_pc_log1p"] = np.log1p(df[pc_col].clip(lower=0))
    return df


# ===================================================================
# 4. RATIOS BRECHA DE GENERO
# ===================================================================
# GUIA: Los ratios M/H capturan la brecha de genero relativa.
# Si ratio = 1, hombres y mujeres tienen la misma inclusion.
# Si ratio < 1, las mujeres estan sub-representadas.
# Estos ratios se usan como outcomes adicionales para verificar
# si la alcaldesa cierra la brecha de genero (no solo aumenta
# outcomes femeninos en forma neutral).
def build_ratios(df: pd.DataFrame, outcomes_m: list[str], outcomes_h: list[str]) -> pd.DataFrame:
    """ratio_mh = outcome_m_pc / outcome_h_pc. NaN cuando denominador = 0."""
    for col_m, col_h in zip(outcomes_m, outcomes_h):
        pc_m = f"{col_m}_pc"
        pc_h = f"{col_h}_pc"
        if pc_m not in df.columns or pc_h not in df.columns:
            continue
        # nombre: ratio_mh_ncont_total, ratio_mh_numtar_deb, etc.
        ratio_name = "ratio_mh_" + col_m.replace("_m", "").rstrip("_")
        df[ratio_name] = np.where(
            df[pc_h] > 0,
            df[pc_m] / df[pc_h],
            np.nan,
        )
    return df


# ===================================================================
# 5. FLAGS
# ===================================================================
def build_flags(df: pd.DataFrame, outcomes: list[str], denom: str) -> pd.DataFrame:
    """Flags de calidad de datos."""
    # Flag: denominador = 0
    df["flag_denom_zero"] = (df[denom] == 0).astype(int)

    # Flag: panel incompleto
    n_per = df["periodo_trimestre"].nunique()
    if "quarters_in_base" in df.columns:
        df["flag_incomplete_panel"] = (df["quarters_in_base"] < n_per).astype(int)
    else:
        counts = df.groupby("cve_mun").size().rename("_n")
        df = df.merge(counts.reset_index(), on="cve_mun", how="left")
        df["flag_incomplete_panel"] = (df["_n"] < n_per).astype(int)
        df.drop(columns=["_n"], inplace=True)

    # Flag: outcomes indefinidos (NaN en _pc — causado por denom=0)
    pc_cols = [f"{c}_pc" for c in outcomes if f"{c}_pc" in df.columns]
    df["flag_any_outcome_undef"] = df[pc_cols].isna().any(axis=1).astype(int)

    return df


# ===================================================================
# 6. COHORTE Y EVENT TIME
# ===================================================================
# GUIA: La clasificacion de cohortes es fundamental para el diseno DiD.
#
# Definiciones:
#   - never-treated: municipios que NUNCA tuvieron alcaldesa (D_it = 0 siempre).
#     Son el grupo de control principal (1,476 municipios).
#   - switcher: municipios que transicionaron de D=0 a D=1 en algun punto.
#     Son los tratados de interes (894 municipios).
#   - always-treated: municipios con D_it = 1 en TODOS los periodos.
#     Se excluyen del event study (no tienen pre-periodo) pero se incluyen
#     en el TWFE baseline (101 municipios).
#
# El event_time = t_index - first_treat_t mide la distancia al primer
# trimestre de tratamiento. Negativo = pre-tratamiento, 0 = onset.
def build_cohort(df: pd.DataFrame) -> pd.DataFrame:
    """
    Añade:
      - first_treat_period: primer periodo donde alcaldesa_final==1 (NaN si never-treated)
      - first_treat_t: t_index del primer tratamiento
      - event_time: t_index - first_treat_t
      - cohort_type: never-treated / switcher / always-treated
    """
    treat_col = "alcaldesa_final"
    time_col = "t_index"

    # Para cada municipio, encontrar el primer periodo de tratamiento
    treated_obs = df.loc[df[treat_col] == 1, ["cve_mun", "periodo_trimestre", time_col]]

    if len(treated_obs) > 0:
        first_treat = (
            treated_obs
            .groupby("cve_mun")
            .agg(
                first_treat_period=("periodo_trimestre", "min"),
                first_treat_t=(time_col, "min"),
            )
            .reset_index()
        )
    else:
        first_treat = pd.DataFrame(columns=["cve_mun", "first_treat_period", "first_treat_t"])

    df = df.merge(first_treat, on="cve_mun", how="left")

    # Event time
    df["event_time"] = df[time_col] - df["first_treat_t"]

    # Clasificar municipios
    mun_info = df.groupby("cve_mun").agg(
        ever_treated=(treat_col, "max"),
        always_treated=(treat_col, "min"),
        n_periods=("periodo_trimestre", "count"),
    ).reset_index()

    mun_info["cohort_type"] = "never-treated"
    mun_info.loc[
        (mun_info["ever_treated"] == 1) & (mun_info["always_treated"] == 0),
        "cohort_type",
    ] = "switcher"
    mun_info.loc[
        (mun_info["ever_treated"] == 1) & (mun_info["always_treated"] == 1),
        "cohort_type",
    ] = "always-treated"

    df = df.merge(
        mun_info[["cve_mun", "cohort_type"]],
        on="cve_mun",
        how="left",
    )

    return df


def cohort_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Resumen de cohortes para QC."""
    mun = df.groupby("cve_mun").first()[
        ["cohort_type", "first_treat_period", "first_treat_t"]
    ].reset_index()

    # Resumen por tipo
    by_type = mun.groupby("cohort_type").agg(
        n_municipios=("cve_mun", "count"),
    ).reset_index()

    # Resumen por cohorte (solo switchers y always-treated)
    treated = mun[mun["cohort_type"] != "never-treated"]
    if len(treated) > 0:
        by_cohort = (
            treated
            .groupby(["cohort_type", "first_treat_period"])
            .agg(n_municipios=("cve_mun", "count"))
            .reset_index()
            .sort_values(["cohort_type", "first_treat_period"])
        )
    else:
        by_cohort = pd.DataFrame()

    # Concatenar ambos
    summary = pd.concat([
        by_type.assign(first_treat_period="ALL"),
        by_cohort,
    ], ignore_index=True)

    return summary


# ===================================================================
# 7. MAIN
# ===================================================================
def main():
    print("=" * 60)
    print("02_build_features — Construcción del dataset analítico")
    print("=" * 60)

    # Asegurar que existan los directorios de salida
    QC_DIR.mkdir(parents=True, exist_ok=True)

    # --- 1. Carga y validación ---
    print("\n[1/6] Cargando y validando panel …")
    df, log_lines = load_and_validate(INPUT)
    for line in log_lines:
        print(f"  {line}")

    # Guardar log
    with open(PANEL_LOG, "w") as f:
        f.write("Panel Checks — 02_build_features.py\n")
        f.write("=" * 50 + "\n\n")
        f.write("\n".join(log_lines))
    print(f"\n  --> Log guardado en {PANEL_LOG}")

    # --- 2. Per cápita ---
    print("\n[2/6] Calculando outcomes per cápita (×10,000 mujeres adultas) …")
    df = build_per_capita(df, RAW_OUTCOMES_M, "pob_adulta_m")
    print(f"  Mujeres: {sum(1 for c in RAW_OUTCOMES_M if f'{c}_pc' in df.columns)} outcomes _pc creados")

    # Per cápita hombres (para ratios)
    df = build_per_capita(df, RAW_OUTCOMES_H, "pob_adulta_h")
    print(f"  Hombres: {sum(1 for c in RAW_OUTCOMES_H if f'{c}_pc' in df.columns)} outcomes _pc creados")

    # --- 3. Transformaciones ---
    print("\n[3/6] Transformaciones (asinh, winsor, log1p) …")
    df = build_asinh(df, RAW_OUTCOMES_M)
    df = build_winsor(df, RAW_OUTCOMES_M)
    df = build_log1p(df, RAW_OUTCOMES_M)

    n_asinh = sum(1 for c in df.columns if c.endswith("_pc_asinh"))
    n_w = sum(1 for c in df.columns if c.endswith("_pc_w"))
    n_log1p = sum(1 for c in df.columns if c.endswith("_pc_log1p"))
    print(f"  asinh: {n_asinh} cols | winsor: {n_w} cols | log1p: {n_log1p} cols")

    # Defragment after bulk column additions
    df = df.copy()

    # --- 4. Ratios ---
    print("\n[4/6] Ratios brecha de género (M/H) …")
    df = build_ratios(df, RAW_OUTCOMES_M, RAW_OUTCOMES_H)
    n_ratios = sum(1 for c in df.columns if c.startswith("ratio_mh_"))
    print(f"  {n_ratios} ratios creados")

    # --- 5. Flags ---
    print("\n[5/6] Flags de calidad …")
    df = build_flags(df, RAW_OUTCOMES_M, "pob_adulta_m")
    n_denom0 = df["flag_denom_zero"].sum()
    n_incomp = df["flag_incomplete_panel"].sum()
    n_undef = df["flag_any_outcome_undef"].sum()
    print(f"  flag_denom_zero: {n_denom0:,} obs")
    print(f"  flag_incomplete_panel: {n_incomp:,} obs")
    print(f"  flag_any_outcome_undef: {n_undef:,} obs")

    # --- 6. Cohorte ---
    print("\n[6/6] Cohorte y event_time …")
    df = build_cohort(df)

    summary = cohort_summary(df)
    summary.to_csv(COHORT_CSV, index=False)
    print(f"\n  Resumen de cohortes:")
    # Print type summary
    type_summary = summary[summary["first_treat_period"] == "ALL"]
    for _, row in type_summary.iterrows():
        print(f"    {row['cohort_type']}: {row['n_municipios']:,} municipios")
    print(f"\n  --> Resumen guardado en {COHORT_CSV}")

    # --- Exportar ---
    print(f"\nDataset final: {df.shape[0]:,} filas × {df.shape[1]} columnas")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(OUTPUT, index=False, engine="pyarrow")
    print(f"OK  Exportado --> {OUTPUT}  ({OUTPUT.stat().st_size / 1e6:.1f} MB)")

    # Resumen de escalas por outcome primario
    print("\n" + "=" * 60)
    print("Resumen escalas (5 outcomes primarios, mujeres)")
    print("=" * 60)
    for col in PRIMARY_5:
        pc   = f"{col}_pc"
        asnh = f"{col}_pc_asinh"
        w    = f"{col}_pc_w"
        l1p  = f"{col}_pc_log1p"
        parts = []
        for tag, c in [("pc", pc), ("asinh", asnh), ("w", w), ("log1p", l1p)]:
            if c in df.columns:
                s = df[c].describe()
                parts.append(f"  {tag:>6s}: mean={s['mean']:.2f}  p50={s['50%']:.2f}  p99={df[c].quantile(0.99):.2f}")
        print(f"\n  {col}:")
        for p in parts:
            print(p)

    print("\nDone.")


if __name__ == "__main__":
    main()
