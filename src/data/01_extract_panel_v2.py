"""
01_extract_panel_v2.py — Extrae y enriquece el panel v2 (26 trimestres).

Lee de inclusion_financiera_v2 (CSV exportado de tesis_db) y construye
todas las columnas derivadas que el pipeline analítico necesita:
  • periodo_trimestre, year, quarter, t_index
  • cvegeo_mun, cve_ent
  • alcaldesa_final, ever_alcaldesa, alcaldesa_acumulado, etc.
  • log_pob, log_pob_adulta
  • ok_panel_completo, quarters_in_base
  • Leads/lags para event study

Uso:
    cd Code_V2/
    python src/data/01_extract_panel_v2.py

Salida:
    data/processed/analytical_panel.parquet  (mismo path que v1)

Nota (2026-03):
    Originalmente leía de PostgreSQL.  Ahora lee del CSV exportado.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# 1. Carga desde CSV  (antes: conexión a PostgreSQL)
# ---------------------------------------------------------------------------
from tesis_alcaldesas.config import load_csv  # noqa: E402

TABLE = "inclusion_financiera_v2"

# ---------------------------------------------------------------------------
# 2. Trim utilities
# ---------------------------------------------------------------------------
def decode_trim(trim_code: int) -> tuple[int, int, str]:
    """trim (QYY) → (quarter, year, 'YYYYQq')"""
    q = trim_code // 100
    yy = trim_code % 100
    year = 2000 + yy
    return q, year, f"{year}Q{q}"


# Ordered list of ALL trim codes (chronological), used for t_index
ALL_TRIMS_ORDERED = [
    318, 418,                            # 2018 Q3-Q4
    119, 219, 319, 419,                  # 2019
    120, 220, 320, 420,                  # 2020
    121, 221, 321, 421,                  # 2021
    122, 222, 322, 422,                  # 2022
    123, 223, 323, 423,                  # 2023
    124, 224, 324, 424,                  # 2024
]
TRIM_TO_TINDEX = {t: i for i, t in enumerate(ALL_TRIMS_ORDERED)}


# ---------------------------------------------------------------------------
# 3. Extract raw data from CSV
# ---------------------------------------------------------------------------
def extract_raw() -> pd.DataFrame:
    print(f"▸ Leyendo CSV de {TABLE}…")
    df = load_csv(TABLE)
    df = df.sort_values(["cve_mun", "trim"]).reset_index(drop=True)
    print(f"  {len(df):,} filas × {df.shape[1]} cols")
    return df


# ---------------------------------------------------------------------------
# 4. Build identifiers
# ---------------------------------------------------------------------------
def build_identifiers(df: pd.DataFrame) -> pd.DataFrame:
    """Construye columnas derivadas de identificación."""
    # periodo_trimestre: "2022Q4"
    df["periodo_trimestre"] = df["trim"].apply(lambda t: decode_trim(int(t))[2])
    df["year"] = df["trim"].apply(lambda t: decode_trim(int(t))[1])
    df["quarter"] = df["trim"].apply(lambda t: decode_trim(int(t))[0])

    # t_index: 0-based temporal (0 = 2018Q3)
    df["t_index"] = df["trim"].map(TRIM_TO_TINDEX)

    # cvegeo_mun: INEGI 5-digit code (zero-padded)
    df["cvegeo_mun"] = df["cve_mun"].apply(lambda x: f"{int(x):05d}")
    df["cve_ent"] = df["cve_edo"].apply(lambda x: f"{int(x):02d}")

    return df


# ---------------------------------------------------------------------------
# 5. Build treatment variables
# ---------------------------------------------------------------------------
def build_treatment(df: pd.DataFrame) -> pd.DataFrame:
    """
    Construye variables de tratamiento a partir de alcaldesa_final.
    alcaldesa_final ya viene del CSV/DB:
      1=Mujer(alcaldesa), 0=Hombre, NaN=sin match.
    """
    # alcaldesa_final ya llega del DB (1, 0, NaN)
    # Asegurar tipo float (NaN para sin match genuino)
    df["alcaldesa_final"] = pd.to_numeric(df["alcaldesa_final"], errors="coerce")

    # ever_alcaldesa: 1 si alguna vez tuvo alcaldesa
    ever = df.groupby("cve_mun")["alcaldesa_final"].transform("max")
    df["ever_alcaldesa"] = ever

    # alcaldesa_acumulado: dosis acumulada (requiere orden temporal)
    df = df.sort_values(["cve_mun", "t_index"])
    df["alcaldesa_acumulado"] = df.groupby("cve_mun")["alcaldesa_final"].cumsum()

    # Variantes de robustez: excluir transiciones
    # Una "transición" = primer trimestre en que cambia el valor de alcaldesa_final
    df["_prev"] = df.groupby("cve_mun")["alcaldesa_final"].shift(1)
    df["_is_transition"] = (df["alcaldesa_final"] != df["_prev"]) & df["_prev"].notna()
    df["alcaldesa_excl_trans"] = df["alcaldesa_final"].copy()
    df.loc[df["_is_transition"], "alcaldesa_excl_trans"] = np.nan

    # alcaldesa_end_excl_trans: exclusión bilateral (transición → NaN, + 1 trimestre después)
    df["_next_trans"] = df.groupby("cve_mun")["_is_transition"].shift(-1).fillna(False)
    df["alcaldesa_end_excl_trans"] = df["alcaldesa_final"].copy()
    df.loc[df["_is_transition"] | df["_next_trans"], "alcaldesa_end_excl_trans"] = np.nan

    df.drop(columns=["_prev", "_is_transition", "_next_trans"], inplace=True)

    return df


# ---------------------------------------------------------------------------
# 6. Build event study leads/lags
# ---------------------------------------------------------------------------
def build_event_study(df: pd.DataFrame, max_leads: int = 3, max_lags: int = 3) -> pd.DataFrame:
    """Construye leads F1-F3 y lags L1-L3 de alcaldesa_final."""
    df = df.sort_values(["cve_mun", "t_index"])
    for k in range(1, max_leads + 1):
        col = f"alcaldesa_final_f{k}"
        df[col] = df.groupby("cve_mun")["alcaldesa_final"].shift(-k)
    for k in range(1, max_lags + 1):
        col = f"alcaldesa_final_l{k}"
        df[col] = df.groupby("cve_mun")["alcaldesa_final"].shift(k)
    return df


# ---------------------------------------------------------------------------
# 7. Build controls
# ---------------------------------------------------------------------------
def build_controls(df: pd.DataFrame) -> pd.DataFrame:
    df["log_pob"] = np.log1p(df["pob"].astype(float))
    df["log_pob_adulta"] = np.log1p(df["pob_adulta"].astype(float))
    return df


# ---------------------------------------------------------------------------
# 8. Build panel quality flags
# ---------------------------------------------------------------------------
def build_panel_flags(df: pd.DataFrame) -> pd.DataFrame:
    n_per = df["periodo_trimestre"].nunique()
    counts = df.groupby("cve_mun").size().rename("quarters_in_base")
    df = df.merge(counts.reset_index(), on="cve_mun", how="left")
    df["ok_panel_completo"] = (df["quarters_in_base"] == n_per).astype(int)
    return df


# ---------------------------------------------------------------------------
# 9. Column ordering (match v1 output format)
# ---------------------------------------------------------------------------
ID_COLS = [
    "cve_mun", "periodo_trimestre", "cvegeo_mun", "cve_ent",
    "year", "quarter", "t_index",
]
TREATMENT_COLS = [
    "alcaldesa_final", "ever_alcaldesa", "alcaldesa_acumulado",
    "alcaldesa_excl_trans", "alcaldesa_end_excl_trans",
]
EVENT_STUDY_COLS = [
    "alcaldesa_final_f1", "alcaldesa_final_f2", "alcaldesa_final_f3",
    "alcaldesa_final_l1", "alcaldesa_final_l2", "alcaldesa_final_l3",
]
CONTROL_COLS = ["log_pob", "log_pob_adulta"]
POP_COLS = ["pob_adulta_m", "pob_adulta_h", "pob_adulta"]
CAT_COLS = ["tipo_pob", "region"]
AUX_COLS = ["ok_panel_completo", "quarters_in_base"]

RAW_OUTCOMES_M = [
    "ncont_total_m", "ncont_ahorro_m", "ncont_plazo_m",
    "ncont_n1_m", "ncont_n2_m", "ncont_n3_m",
    "numtar_deb_m", "numtar_cred_m", "numcontcred_hip_m",
]
RAW_OUTCOMES_H = [c.replace("_m", "_h") for c in RAW_OUTCOMES_M]
RAW_OUTCOMES_T = [c.replace("_m", "_t") for c in RAW_OUTCOMES_M]

ALL_COLS = (
    ID_COLS + TREATMENT_COLS + EVENT_STUDY_COLS + CONTROL_COLS
    + POP_COLS + CAT_COLS + AUX_COLS + RAW_OUTCOMES_M + RAW_OUTCOMES_H
    + RAW_OUTCOMES_T
)


# ---------------------------------------------------------------------------
# 10. Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("01_extract_panel_v2 — Panel ampliado 2018Q3–2024Q4")
    print("=" * 60)

    df = extract_raw()

    print("\n▸ Construyendo identificadores…")
    df = build_identifiers(df)

    print("▸ Construyendo tratamiento (alcaldesa)…")
    df = build_treatment(df)

    print("▸ Construyendo leads/lags event study…")
    df = build_event_study(df)

    print("▸ Construyendo controles…")
    df = build_controls(df)

    print("▸ Construyendo flags de panel…")
    df = build_panel_flags(df)

    # Select and order columns
    available = [c for c in ALL_COLS if c in df.columns]
    missing = [c for c in ALL_COLS if c not in df.columns]
    if missing:
        print(f"\n  ⚠ Columnas no disponibles: {missing}")

    df = df[available].copy()

    # --- Sanity checks ---
    print(f"\n▸ Validación:")
    n_mun = df["cve_mun"].nunique()
    n_per = df["periodo_trimestre"].nunique()
    pk_ok = df.duplicated(subset=["cve_mun", "periodo_trimestre"]).sum() == 0
    print(f"  Municipios: {n_mun:,}")
    print(f"  Periodos:   {n_per}")
    print(f"  PK única:   {'✓' if pk_ok else '✗ DUPLICADOS'}")

    # Treatment distribution
    td = df["alcaldesa_final"].value_counts(normalize=True, dropna=False).sort_index()
    print(f"\n  Distribución alcaldesa_final:")
    for val, pct in td.items():
        label = "NaN (sin match)" if pd.isna(val) else str(int(val))
        print(f"    {label}: {pct:.2%}")

    # --- Export ---
    out_path = Path("data/processed/analytical_panel.parquet")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False, engine="pyarrow")
    print(f"\n✓ Exportado → {out_path}  ({out_path.stat().st_size / 1e6:.1f} MB)")
    print(f"  {df.shape[0]:,} filas × {df.shape[1]} cols")
    print(f"  Rango: {sorted(df['periodo_trimestre'].unique())[0]} → {sorted(df['periodo_trimestre'].unique())[-1]}")
    print("\nDone.")


if __name__ == "__main__":
    main()
