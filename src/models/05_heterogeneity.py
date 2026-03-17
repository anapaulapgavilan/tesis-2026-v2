"""
05_heterogeneity.py — Tabla 4: Heterogeneidad del efecto TWFE.

Dimensiones:
  H1. tipo_pob  (Rural / En Transicion / Semi-urbano / Urbano / Semi-metropoli / Metropoli)
  H2. Cuantiles de población (terciles de log_pob)

Corrección por múltiples pruebas: Benjamini-Hochberg (FDR), q-values.

Se ejecuta solo si pre-trends son razonables (check automático o pass-through).

Outputs:
  outputs/paper/tabla_4_heterogeneidad.csv
  outputs/paper/tabla_4_heterogeneidad.tex
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.stats.multitest import multipletests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from src.models.utils import (
    load_panel, run_panel_ols,
    PRIMARY_5, OUTCOME_DEFS, OUT,
    coef_str, se_str, stars, export_table_tex,
)


def bh_correction(pvals: list[float]) -> list[float]:
    """Benjamini-Hochberg FDR correction. Returns q-values."""
    pvals_arr = np.array(pvals)
    # Handle NaN
    valid = ~np.isnan(pvals_arr)
    q = np.full_like(pvals_arr, np.nan)
    if valid.sum() > 0:
        _, q_valid, _, _ = multipletests(pvals_arr[valid], method="fdr_bh")
        q[valid] = q_valid
    return q.tolist()


def run_heterogeneity_interaction(df, depvar, treatment, interact_var, interact_vals):
    """
    Run TWFE with interaction: D × group dummies.
    Returns coefficients for each group.
    """
    df = df.copy()

    # Create interaction dummies (omit first category as reference)
    ref_val = interact_vals[0]
    interaction_cols = []

    for val in interact_vals[1:]:
        col_name = f"D_x_{interact_var}_{val}".replace(" ", "_")
        df[col_name] = (
            (df[treatment] * (df[interact_var] == val)).astype(float)
        )
        interaction_cols.append((col_name, val))

    exog = [treatment, "log_pob"] + [c for c, _ in interaction_cols]

    # Drop NaN
    cols_needed = [depvar] + exog
    mask = df[cols_needed].notna().all(axis=1)
    sub = df.loc[mask]

    from linearmodels.panel import PanelOLS

    y = sub[depvar]
    X = sub[exog]

    mod = PanelOLS(y, X, entity_effects=True, time_effects=True, check_rank=False)
    res = mod.fit(cov_type="clustered", cluster_entity=True)

    results = []
    # Base group effect (treatment coefficient = effect for reference group)
    results.append({
        "group": ref_val,
        "coef": res.params[treatment],
        "se": res.std_errors[treatment],
        "pval": res.pvalues[treatment],
        "type": "base",
    })

    # Interaction effects (incremental)
    for col_name, val in interaction_cols:
        results.append({
            "group": val,
            "coef_incr": res.params[col_name],
            "se_incr": res.std_errors[col_name],
            "pval_incr": res.pvalues[col_name],
            "coef": res.params[treatment] + res.params[col_name],  # total effect
            "se": np.nan,  # total SE requires delta method — approximate
            "pval": np.nan,
            "type": "interaction",
        })

    return results, res.nobs


def run_subsample_heterogeneity(df, depvar, treatment, group_var, group_vals):
    """Run separate TWFE for each subgroup. More interpretable than interaction."""
    results = []
    for val in group_vals:
        sub = df[df[group_var] == val].copy()
        if len(sub) < 100:
            results.append({
                "group": val,
                "coef": np.nan, "se": np.nan, "pval": np.nan,
                "nobs": len(sub),
            })
            continue

        try:
            res = run_panel_ols(sub, depvar=depvar, exog=[treatment, "log_pob"])
            results.append({
                "group": val,
                "coef": res.params[treatment],
                "se": res.std_errors[treatment],
                "pval": res.pvalues[treatment],
                "nobs": res.nobs,
            })
        except Exception as e:
            print(f"    [!] {group_var}={val}: {e}")
            results.append({
                "group": val,
                "coef": np.nan, "se": np.nan, "pval": np.nan,
                "nobs": len(sub),
            })

    return results


def main():
    print("=" * 60)
    print("05 — Heterogeneidad")
    print("=" * 60)

    # -------------------------------------------------------------------
    # Check pre-trends before proceeding
    # -------------------------------------------------------------------
    pt_path = OUT / "pretrends_tests.csv"
    if pt_path.exists():
        pt = pd.read_csv(pt_path)
        n_pass = (pt["pass_10pct"] == "Yes").sum()
        n_total = len(pt)
        print(f"\n  Pre-trends check: {n_pass}/{n_total} outcomes pasan (p > 0.10)")
        if n_pass == 0:
            print("  [!] NINGÚN outcome pasa pre-trends --> heterogeneidad no confiable.")
            print("    Se procede de todos modos para documentación, pero los resultados")
            print("    deben interpretarse con extrema cautela.")
    else:
        print("  [!] pretrends_tests.csv no encontrado — se procede sin verificación.")

    df = load_panel()
    treatment = "alcaldesa_final"
    focus = "ncont_total_m"
    depvar = f"{focus}_pc_asinh"

    all_rows = []

    # -------------------------------------------------------------------
    # H1. Por tipo_pob (sub-sample)
    # -------------------------------------------------------------------
    print("\n[H1] Heterogeneidad por tipo_pob (sub-sample)")
    tipo_vals = sorted(df["tipo_pob"].dropna().unique())
    h1 = run_subsample_heterogeneity(df, depvar, treatment, "tipo_pob", tipo_vals)

    for r in h1:
        print(f"  {r['group']:20s}: β={r['coef']:+.4f}{stars(r['pval']) if not np.isnan(r['pval']) else ''}  "
              f"SE={r['se']:.4f}  N={r['nobs']:,}" if not np.isnan(r.get('coef', np.nan)) else
              f"  {r['group']:20s}: N insuficiente")
        all_rows.append({
            "Dimension": "tipo\\_pob",
            "Group": r["group"],
            "Coef": coef_str(r["coef"], r["pval"]) if not np.isnan(r.get("coef", np.nan)) else "---",
            "SE": se_str(r["se"]) if not np.isnan(r.get("se", np.nan)) else "---",
            "p-valor": f"{r['pval']:.4f}" if not np.isnan(r.get("pval", np.nan)) else "---",
            "N": f"{r.get('nobs', 0):,}",
            "raw_pval": r.get("pval", np.nan),
        })

    # -------------------------------------------------------------------
    # H2. Por terciles de log_pob
    # -------------------------------------------------------------------
    print("\n[H2] Heterogeneidad por terciles de población")
    # Compute terciles based on municipality-level mean log_pob
    mun_pop = df.groupby(level="cve_mun")["log_pob"].mean()
    tercile_cuts = pd.qcut(mun_pop, 3, labels=["T1 (pequeño)", "T2 (mediano)", "T3 (grande)"])
    tercile_map = tercile_cuts.to_dict()
    df["pop_tercile"] = df.index.get_level_values("cve_mun").map(tercile_map)

    terc_vals = ["T1 (pequeño)", "T2 (mediano)", "T3 (grande)"]
    h2 = run_subsample_heterogeneity(df, depvar, treatment, "pop_tercile", terc_vals)

    for r in h2:
        if not np.isnan(r.get("coef", np.nan)):
            print(f"  {r['group']:20s}: β={r['coef']:+.4f}{stars(r['pval'])}  "
                  f"SE={r['se']:.4f}  N={r['nobs']:,}")
        else:
            print(f"  {r['group']:20s}: N insuficiente")
        all_rows.append({
            "Dimension": "Tercil población",
            "Group": r["group"],
            "Coef": coef_str(r["coef"], r["pval"]) if not np.isnan(r.get("coef", np.nan)) else "---",
            "SE": se_str(r["se"]) if not np.isnan(r.get("se", np.nan)) else "---",
            "p-valor": f"{r['pval']:.4f}" if not np.isnan(r.get("pval", np.nan)) else "---",
            "N": f"{r.get('nobs', 0):,}",
            "raw_pval": r.get("pval", np.nan),
        })

    df.drop(columns=["pop_tercile"], inplace=True)

    # -------------------------------------------------------------------
    # BH FDR correction
    # -------------------------------------------------------------------
    print("\n[BH] Corrección por múltiples pruebas (Benjamini-Hochberg FDR)")
    raw_pvals = [r["raw_pval"] for r in all_rows]
    q_values = bh_correction(raw_pvals)

    for i, q in enumerate(q_values):
        all_rows[i]["q-value (BH)"] = f"{q:.4f}" if not np.isnan(q) else "---"

    # Remove raw_pval from output
    for r in all_rows:
        del r["raw_pval"]

    # -------------------------------------------------------------------
    # Build table
    # -------------------------------------------------------------------
    tab = pd.DataFrame(all_rows)
    tab = tab.set_index(["Dimension", "Group"])

    print("\n" + "=" * 60)
    print("TABLA 4 — Heterogeneidad")
    print("=" * 60)
    print(tab.to_string())

    # CSV
    csv_path = OUT / "tabla_4_heterogeneidad.csv"
    tab.to_csv(csv_path)
    print(f"\n  --> CSV: {csv_path}")

    # LaTeX
    tex_path = OUT / "tabla_4_heterogeneidad.tex"
    export_table_tex(
        tab.reset_index().set_index("Dimension"), tex_path,
        caption="Heterogeneidad del efecto TWFE por tipo de población y tamaño municipal",
        label="tab:heterogeneity",
        note="Sub-muestras independientes. FE municipio + período, cluster SE municipio. "
             "Outcome: asinh(contratos totales mujeres per cápita ×10k). "
             "q-value: corrección Benjamini-Hochberg (FDR). "
             "*** p<0.01, ** p<0.05, * p<0.10.",
    )

    print("\nDone.")


if __name__ == "__main__":
    main()
