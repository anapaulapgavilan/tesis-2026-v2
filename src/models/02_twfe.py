"""
02_twfe.py — TWFE baseline: FE municipio + FE periodo, cluster SE municipio.

Ecuación:
  Y_{it} = α_i + γ_t + β · D_{it} + X_{it}'δ + ε_{it}

  β = "efecto promedio TWFE" (NO ATT; ver Goodman-Bacon 2021)

Outcomes: 5 primarios en escala asinh.

Outputs:
  outputs/paper/tabla_2_twfe.csv
  outputs/paper/tabla_2_twfe.tex
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.models.utils import (
    load_panel, run_panel_ols,
    PRIMARY_5, OUTCOME_DEFS, OUT,
    coef_str, se_str, stars, export_table_tex,
)


def main():
    print("=" * 60)
    print("02 — TWFE Baseline")
    print("=" * 60)

    df = load_panel()

    treatment = "alcaldesa_final"
    controls = ["log_pob"]
    exog = [treatment] + controls

    results = {}
    raw_results = []

    for out_name in PRIMARY_5:
        depvar = f"{out_name}_pc_asinh"
        label = OUTCOME_DEFS[out_name]["label"]

        print(f"\n  Estimando: {depvar} ← {treatment} + log_pob + FE_mun + FE_t ...")

        res = run_panel_ols(df, depvar=depvar, exog=exog)

        beta = res.params[treatment]
        se = res.std_errors[treatment]
        pval = res.pvalues[treatment]
        ci_lo, ci_hi = res.conf_int().loc[treatment]
        nobs = res.nobs
        r2_within = res.rsquared_within

        print(f"    β = {beta:.4f}{stars(pval)}  SE = {se:.4f}  "
              f"p = {pval:.4f}  N = {nobs:,}  R²w = {r2_within:.4f}")

        results[label] = {
            "Coef": coef_str(beta, pval),
            "SE": se_str(se),
            "p-valor": f"{pval:.4f}",
            "IC 95%": f"[{ci_lo:.4f}, {ci_hi:.4f}]",
            "N": f"{nobs:,}",
            "R² within": f"{r2_within:.4f}",
        }

        raw_results.append({
            "outcome": out_name,
            "depvar": depvar,
            "coef": beta,
            "se": se,
            "pval": pval,
            "ci_lo": ci_lo,
            "ci_hi": ci_hi,
            "nobs": nobs,
            "r2_within": r2_within,
        })

        # Also print log_pob coefficient
        beta_lp = res.params["log_pob"]
        se_lp = res.std_errors["log_pob"]
        pval_lp = res.pvalues["log_pob"]
        print(f"    log_pob: β = {beta_lp:.4f}{stars(pval_lp)}")

    # -------------------------------------------------------------------
    # Build table
    # -------------------------------------------------------------------
    tab = pd.DataFrame(results).T
    tab.index.name = "Outcome"

    print("\n" + "=" * 60)
    print("TABLA 2 — TWFE Baseline (asinh, cluster SE municipio)")
    print("=" * 60)
    print(tab.to_string())

    # CSV
    csv_path = OUT / "tabla_2_twfe.csv"
    tab.to_csv(csv_path)
    print(f"\n  → CSV: {csv_path}")

    # Raw CSV for downstream use
    raw_df = pd.DataFrame(raw_results)
    raw_df.to_csv(OUT / "tabla_2_twfe_raw.csv", index=False)

    # LaTeX
    tex_path = OUT / "tabla_2_twfe.tex"
    export_table_tex(
        tab, tex_path,
        caption="Efecto TWFE de alcaldesa sobre inclusión financiera femenina (asinh)",
        label="tab:twfe",
        note="Errores estándar clusterizados a nivel municipio entre paréntesis. "
             "FE de municipio y período incluidos. Control: ln(población). "
             "Escala: asinh(outcome per cápita ×10,000 mujeres adultas). "
             "*** p<0.01, ** p<0.05, * p<0.10. "
             "El coeficiente se interpreta como efecto promedio TWFE, no como ATT "
             "(ver Goodman-Bacon, 2021).",
    )

    print("\nDone.")


if __name__ == "__main__":
    main()
