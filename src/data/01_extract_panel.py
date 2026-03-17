"""
01_extract_panel.py — Extrae columnas necesarias de inclusion_financiera_clean
                      y exporta un parquet listo para feature engineering.

Uso:
    python src/data/01_extract_panel.py

Salida:
    data/processed/analytical_panel.parquet

Nota (2026-03):
    Originalmente leía de PostgreSQL.  Ahora lee del CSV exportado
    inclusion_financiera_clean.csv ubicado en data/.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# 1. Carga desde CSV  (antes: conexión a PostgreSQL)
# ---------------------------------------------------------------------------
from tesis_alcaldesas.config import load_csv  # noqa: E402

# ---------------------------------------------------------------------------
# 2. Definición de columnas a extraer
# ---------------------------------------------------------------------------

# --- Identificadores y panel ---
ID_COLS = [
    "cve_mun",          # PK parte 1  (bigint)
    "periodo_trimestre", # PK parte 2  (text, "2018Q3"–"2022Q3")
    "cvegeo_mun",       # clave INEGI 5 dígitos (text) — merges externos
    "cve_ent",          # entidad (text 2 dígitos)
    "year",             # año calendario
    "quarter",          # trimestre (1–4)
    "t_index",          # índice temporal 0-based (0 = 2018Q3)
]

# --- Tratamiento ---
TREATMENT_COLS = [
    "alcaldesa_final",       # D_it {0,1} — tratamiento principal
    "ever_alcaldesa",        # max_t D_it — invariante; para balance/heterogeneidad
    "alcaldesa_acumulado",   # dosis acumulada; tratamiento alternativo
    # Variantes robustez (excluyen transiciones)
    "alcaldesa_excl_trans",
    "alcaldesa_end_excl_trans",
]

# Leads/lags — SOLO para event study, NUNCA como controles
EVENT_STUDY_COLS = [
    "alcaldesa_final_f1", "alcaldesa_final_f2", "alcaldesa_final_f3",  # leads
    "alcaldesa_final_l1", "alcaldesa_final_l2", "alcaldesa_final_l3",  # lags
]

# --- Controles ---
CONTROL_COLS = [
    "log_pob",           # ln(pob+1); control pre-determinado/lento
    "log_pob_adulta",    # ln(pob_adulta+1)
]

# --- Población (denominadores para per cápita) ---
POP_COLS = [
    "pob_adulta_m",  # denominador principal (mujeres adultas)
    "pob_adulta_h",  # denominador hombres (para ratios)
    "pob_adulta",    # denominador total
]

# --- Categóricas (heterogeneidad) ---
CAT_COLS = [
    "tipo_pob",   # Rural / En Transicion / Semi-urbano / Urbano / Semi-metropoli / Metropoli
    "region",     # 6 regiones
]

# --- Auxiliares ---
AUX_COLS = [
    "ok_panel_completo",   # 1 si tiene los 17 trimestres
    "quarters_in_base",    # trimestres presentes
]

# --- Raw outcomes (mujeres) — 17 variables ---
# Se extraen en crudo para re-calcular per cápita de forma reproducible.
RAW_OUTCOMES_M = [
    # Extensión
    "ncont_total_m",
    "ncont_ahorro_m",
    "ncont_plazo_m",
    "ncont_n1_m",
    "ncont_n2_m",
    "ncont_n3_m",
    "ncont_tradic_m",
    # Profundidad (saldos)
    "saldocont_total_m",
    "saldocont_ahorro_m",
    "saldocont_plazo_m",
    "saldocont_n1_m",
    "saldocont_n2_m",
    "saldocont_n3_m",
    "saldocont_tradic_m",
    # Productos (tarjetas, hipotecarios)
    "numtar_deb_m",
    "numtar_cred_m",
    "numcontcred_hip_m",
]

# --- Raw outcomes (hombres) — para ratios de brecha de género ---
RAW_OUTCOMES_H = [col.replace("_m", "_h") for col in RAW_OUTCOMES_M]
# numcontcred_hip no tiene _pm; _h sí existe (verificado en profile CSV)

ALL_COLS = (
    ID_COLS + TREATMENT_COLS + EVENT_STUDY_COLS + CONTROL_COLS
    + POP_COLS + CAT_COLS + AUX_COLS + RAW_OUTCOMES_M + RAW_OUTCOMES_H
)

# ---------------------------------------------------------------------------
# 3. Validar que todas las columnas existen en el CSV
# ---------------------------------------------------------------------------
def validate_columns(csv_cols: set[str], requested: list[str]) -> list[str]:
    """Retorna lista de columnas faltantes (vacía si todo OK)."""
    return [c for c in requested if c not in csv_cols]


# ---------------------------------------------------------------------------
# 4. Extracción desde CSV
# ---------------------------------------------------------------------------
def extract(columns: list[str], table: str = "inclusion_financiera_clean") -> pd.DataFrame:
    """Lee el CSV exportado de tesis_db y selecciona columnas."""
    df = load_csv(table, usecols=columns)
    df = df.sort_values(["cve_mun", "periodo_trimestre"]).reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# 5. Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("01_extract_panel — Extracción del panel analítico (desde CSV)")
    print("=" * 60)

    # Leer encabezados del CSV para validar columnas
    sample = load_csv("inclusion_financiera_clean")
    csv_cols = set(sample.columns)
    del sample

    # Validar columnas
    missing = validate_columns(csv_cols, ALL_COLS)
    if missing:
        print(f"\n⚠  COLUMNAS FALTANTES ({len(missing)}):")
        for m in missing:
            print(f"   - {m}")
        print("\nSe procede sin ellas.\n")
        cols_to_extract = [c for c in ALL_COLS if c not in set(missing)]
    else:
        print(f"\n✓  Todas las {len(ALL_COLS)} columnas encontradas en el CSV.\n")
        cols_to_extract = ALL_COLS

    # Extraer desde CSV
    print(f"Extrayendo {len(cols_to_extract)} columnas de CSV …")
    df = extract(cols_to_extract)
    print(f"  Filas: {len(df):,}")
    print(f"  Columnas: {df.shape[1]}")

    # Quick sanity
    n_mun = df["cve_mun"].nunique()
    n_per = df["periodo_trimestre"].nunique()
    print(f"  Municipios: {n_mun:,}")
    print(f"  Periodos: {n_per}")
    pk_unique = df.duplicated(subset=["cve_mun", "periodo_trimestre"]).sum() == 0
    print(f"  PK única: {'✓' if pk_unique else '✗ HAY DUPLICADOS'}")

    # Exportar parquet
    out_path = Path("data/processed/analytical_panel.parquet")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False, engine="pyarrow")
    print(f"\n✓  Exportado → {out_path}  ({out_path.stat().st_size / 1e6:.1f} MB)")

    if missing:
        print(f"\n⚠  Recordatorio: {len(missing)} columna(s) faltante(s) — ver arriba.")
        sys.exit(1)

    print("\nDone.")


if __name__ == "__main__":
    main()
