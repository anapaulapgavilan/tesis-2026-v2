"""
04_robustness.py — Tabla 3: Pruebas de robustez mínimas.

Tests:
  R1. Escala alternativa: log1p vs asinh
  R2. Winsor p1–p99
  R3. Excluir transiciones (alcaldesa_excl_trans)
  R4. Placebo temporal (tto adelantado 4 trimestres)
  R5. Placebo de género (outcomes masculinos, misma escala)

Outputs:
  outputs/paper/tabla_3_robustez.csv
  outputs/paper/tabla_3_robustez.tex
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.models.utils import (
    load_panel, run_panel_ols,
    PRIMARY_5, OUTCOME_DEFS, OUT,
    coef_str, se_str, stars, export_table_tex,
)


def run_robustness_twfe(df, depvar, treatment, controls=None):
    """Run a TWFE regression and return key stats."""
    if controls is None:
        controls = ["log_pob"]
    exog = [treatment] + controls
    # Verify columns exist
    for c in [depvar] + exog:
        if c not in df.columns:
            return None
    res = run_panel_ols(df, depvar=depvar, exog=exog)
    beta = res.params[treatment]
    se = res.std_errors[treatment]
    pval = res.pvalues[treatment]
    return {"coef": beta, "se": se, "pval": pval, "nobs": res.nobs}


def main():
    print("=" * 60)
    print("04 — Robustez")
    print("=" * 60)

    df = load_panel()

    # We will run all tests on the first primary outcome (ncont_total_m)
    # plus confirm sign on all 5 for key tests
    focus = "ncont_total_m"
    focus_label = OUTCOME_DEFS[focus]["label"]

    rows = []

    # -------------------------------------------------------------------
    # Baseline (for comparison)
    # -------------------------------------------------------------------
    print("\n[Baseline] asinh, alcaldesa_final")
    bl = run_robustness_twfe(df, f"{focus}_pc_asinh", "alcaldesa_final")
    rows.append({
        "Test": "Baseline (asinh)",
        "Outcome": focus_label,
        "Treatment": "alcaldesa\\_final",
        "Coef": coef_str(bl["coef"], bl["pval"]),
        "SE": se_str(bl["se"]),
        "N": f"{bl['nobs']:,}",
        "Nota": "FE mun + per, cluster mun",
    })
    print(f"  β={bl['coef']:.4f}{stars(bl['pval'])}  SE={bl['se']:.4f}")

    # -------------------------------------------------------------------
    # R1. log1p
    # -------------------------------------------------------------------
    print("\n[R1] Escala alternativa: log1p")
    r1 = run_robustness_twfe(df, f"{focus}_pc_log1p", "alcaldesa_final")
    rows.append({
        "Test": "R1: log(1+y)",
        "Outcome": focus_label,
        "Treatment": "alcaldesa\\_final",
        "Coef": coef_str(r1["coef"], r1["pval"]),
        "SE": se_str(r1["se"]),
        "N": f"{r1['nobs']:,}",
        "Nota": "Escala alternativa",
    })
    print(f"  β={r1['coef']:.4f}{stars(r1['pval'])}  SE={r1['se']:.4f}")

    # -------------------------------------------------------------------
    # R2. Winsor p1-p99
    # -------------------------------------------------------------------
    print("\n[R2] Winsor p1-p99 (asinh)")
    # Winsorized _pc_w → apply asinh on top
    wvar = f"{focus}_pc_w"
    if wvar in df.columns:
        df["_r2_y"] = np.arcsinh(df[wvar])
        r2 = run_robustness_twfe(df, "_r2_y", "alcaldesa_final")
        rows.append({
            "Test": "R2: Winsor p1-p99 + asinh",
            "Outcome": focus_label,
            "Treatment": "alcaldesa\\_final",
            "Coef": coef_str(r2["coef"], r2["pval"]),
            "SE": se_str(r2["se"]),
            "N": f"{r2['nobs']:,}",
            "Nota": "Recorte p1-p99, luego asinh",
        })
        print(f"  β={r2['coef']:.4f}{stars(r2['pval'])}  SE={r2['se']:.4f}")
        df.drop(columns=["_r2_y"], inplace=True)
    else:
        print(f"  ⚠ {wvar} no encontrada — omitido")

    # -------------------------------------------------------------------
    # R3. Excluir transiciones
    # -------------------------------------------------------------------
    print("\n[R3] Excluir transiciones (alcaldesa_excl_trans)")
    excl_col = "alcaldesa_excl_trans"
    if excl_col in df.columns:
        # This variable has NaN in transition periods → they drop naturally
        r3 = run_robustness_twfe(df, f"{focus}_pc_asinh", excl_col)
        rows.append({
            "Test": "R3: Excluir transiciones",
            "Outcome": focus_label,
            "Treatment": "alcaldesa\\_excl\\_trans",
            "Coef": coef_str(r3["coef"], r3["pval"]),
            "SE": se_str(r3["se"]),
            "N": f"{r3['nobs']:,}",
            "Nota": "NaN en trimestres de transición → se excluyen",
        })
        print(f"  β={r3['coef']:.4f}{stars(r3['pval'])}  SE={r3['se']:.4f}  N={r3['nobs']:,}")
    else:
        print(f"  ⚠ {excl_col} no encontrada — omitido")
        rows.append({
            "Test": "R3: Excluir transiciones",
            "Outcome": focus_label,
            "Treatment": "---",
            "Coef": "---",
            "SE": "---",
            "N": "---",
            "Nota": f"Columna {excl_col} no disponible",
        })

    # -------------------------------------------------------------------
    # R4. Placebo temporal — tratamiento adelantado 4 trimestres
    # -------------------------------------------------------------------
    print("\n[R4] Placebo temporal: tto adelantado 4 trimestres")
    # Create fake treatment: shift alcaldesa_final forward by 4 periods
    df_r4 = df.copy()
    # Reset to get flat frame
    df_r4_flat = df_r4.reset_index()
    df_r4_flat = df_r4_flat.sort_values(["cve_mun", "t_index"])
    df_r4_flat["placebo_tto_f4"] = df_r4_flat.groupby("cve_mun")["alcaldesa_final"].shift(-4)
    df_r4_flat = df_r4_flat.dropna(subset=["placebo_tto_f4"])
    df_r4_flat = df_r4_flat.set_index(["cve_mun", "t_index"])

    r4 = run_robustness_twfe(df_r4_flat, f"{focus}_pc_asinh", "placebo_tto_f4")
    rows.append({
        "Test": "R4: Placebo temporal (+4 trim)",
        "Outcome": focus_label,
        "Treatment": "placebo\\_tto\\_f4",
        "Coef": coef_str(r4["coef"], r4["pval"]),
        "SE": se_str(r4["se"]),
        "N": f"{r4['nobs']:,}",
        "Nota": "Efecto esperado ≈ 0 si no hay anticipación",
    })
    print(f"  β={r4['coef']:.4f}{stars(r4['pval'])}  SE={r4['se']:.4f}  N={r4['nobs']:,}")

    # -------------------------------------------------------------------
    # R5. Placebo de género — outcomes masculinos
    # -------------------------------------------------------------------
    print("\n[R5] Placebo de género: outcomes masculinos")
    # Build asinh of male _pc
    h_pc_col = f"{focus.replace('_m', '_h')}_pc"
    if h_pc_col in df.columns:
        df["_r5_y_h_asinh"] = np.arcsinh(df[h_pc_col])
        r5 = run_robustness_twfe(df, "_r5_y_h_asinh", "alcaldesa_final")
        rows.append({
            "Test": "R5: Placebo género (hombres)",
            "Outcome": f"{focus_label} (H)",
            "Treatment": "alcaldesa\\_final",
            "Coef": coef_str(r5["coef"], r5["pval"]),
            "SE": se_str(r5["se"]),
            "N": f"{r5['nobs']:,}",
            "Nota": "Si β≈0, efecto es específico a mujeres. "
                    "Si β≠0, podría reflejar shock general.",
        })
        print(f"  β={r5['coef']:.4f}{stars(r5['pval'])}  SE={r5['se']:.4f}")
        df.drop(columns=["_r5_y_h_asinh"], inplace=True)
    else:
        print(f"  ⚠ {h_pc_col} no encontrada")

    # -------------------------------------------------------------------
    # Repeat baseline for all 5 outcomes (summary row)
    # -------------------------------------------------------------------
    print("\n[All 5 outcomes] Baseline asinh — signo y significancia:")
    for out_name in PRIMARY_5:
        depvar = f"{out_name}_pc_asinh"
        res = run_robustness_twfe(df, depvar, "alcaldesa_final")
        lbl = OUTCOME_DEFS[out_name]["label"]
        sig = stars(res["pval"])
        print(f"  {lbl:25s}: β={res['coef']:+.4f}{sig}")

    # -------------------------------------------------------------------
    # Build table
    # -------------------------------------------------------------------
    tab = pd.DataFrame(rows).set_index("Test")
    print("\n" + "=" * 60)
    print("TABLA 3 — Robustez")
    print("=" * 60)
    print(tab.to_string())

    # CSV
    csv_path = OUT / "tabla_3_robustez.csv"
    tab.to_csv(csv_path)
    print(f"\n  → CSV: {csv_path}")

    # LaTeX
    tex_path = OUT / "tabla_3_robustez.tex"
    export_table_tex(
        tab, tex_path,
        caption="Pruebas de robustez — efecto TWFE sobre contratos totales mujeres",
        label="tab:robustness",
        note="Todas las especificaciones incluyen FE municipio + FE período y "
             "errores estándar clusterizados a nivel municipio. "
             "R1: escala log(1+y) en lugar de asinh. "
             "R2: per cápita winsorizado p1-p99, luego asinh. "
             "R3: tto = alcaldesa\\_excl\\_trans (NaN en trimestres de transición). "
             "R4: tratamiento adelantado 4 trimestres (placebo temporal). "
             "R5: same spec, outcome masculino (placebo de género). "
             "*** p<0.01, ** p<0.05, * p<0.10.",
    )

    print("\nDone.")


if __name__ == "__main__":
    main()
