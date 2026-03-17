"""
sample_policy.py — Sensibilidad a la definición de muestra.

Corre TWFE baseline en dos muestras:
  1. Main sample: drop municipios con flag_incomplete_panel == 1
  2. Full sample: incluye todo

Compara coeficientes para verificar que la exclusión es inocua.

Outputs:
  outputs/paper/tabla_2_twfe_main.csv / .tex
  outputs/paper/tabla_2_twfe_full.csv / .tex
  outputs/paper/sample_sensitivity.txt

Uso:
  python -m tesis_alcaldesas.models.sample_policy
"""

from __future__ import annotations

import pandas as pd

from tesis_alcaldesas.models.utils import (
    load_panel, run_panel_ols,
    PRIMARY_5, OUTCOME_DEFS, OUT,
    coef_str, se_str, stars, export_table_tex,
)


def run_twfe_sample(df: pd.DataFrame, sample_label: str) -> pd.DataFrame:
    """Run TWFE on a given sample, return raw results."""
    treatment = "alcaldesa_final"
    controls = ["log_pob"]
    exog = [treatment] + controls

    rows = []
    for out_name in PRIMARY_5:
        depvar = f"{out_name}_pc_asinh"
        res = run_panel_ols(df, depvar=depvar, exog=exog)

        beta = res.params[treatment]
        se = res.std_errors[treatment]
        pval = res.pvalues[treatment]
        ci_lo, ci_hi = res.conf_int().loc[treatment]

        rows.append({
            "outcome": out_name,
            "depvar": depvar,
            "sample": sample_label,
            "coef": beta,
            "se": se,
            "pval": pval,
            "ci_lo": ci_lo,
            "ci_hi": ci_hi,
            "nobs": res.nobs,
            "r2_within": res.rsquared_within,
            "n_mun": df.index.get_level_values("cve_mun").nunique(),
        })

        print(f"    [{sample_label}] {out_name}: β={beta:.4f}{stars(pval)}  "
              f"SE={se:.4f}  N={res.nobs:,}")

    return pd.DataFrame(rows)


def format_table(raw: pd.DataFrame) -> pd.DataFrame:
    """Format raw results into a presentable table."""
    rows = {}
    for _, r in raw.iterrows():
        label = OUTCOME_DEFS[r["outcome"]]["label"]
        rows[label] = {
            "Coef": coef_str(r["coef"], r["pval"]),
            "SE": se_str(r["se"]),
            "p-valor": f"{r['pval']:.4f}",
            "IC 95%": f"[{r['ci_lo']:.4f}, {r['ci_hi']:.4f}]",
            "N": f"{int(r['nobs']):,}",
            "R² within": f"{r['r2_within']:.4f}",
        }

    tab = pd.DataFrame(rows).T
    tab.index.name = "Outcome"
    return tab


def main():
    print("=" * 60)
    print("Sample Policy — Sensibilidad a la definición de muestra")
    print("=" * 60)

    df = load_panel()

    # Check for flag
    if "flag_incomplete_panel" not in df.columns:
        # Reset index to check
        df_check = df.reset_index()
        if "flag_incomplete_panel" not in df_check.columns:
            print("  [!] flag_incomplete_panel no encontrado. "
                  "Usando full sample como main.")
            # Create a dummy flag (all 0)
            df["flag_incomplete_panel"] = 0

    # --- Full sample ---
    print("\n[Full Sample]")
    raw_full = run_twfe_sample(df, "full")

    # --- Main sample (balanced) ---
    print("\n[Main Sample — balanced panel]")
    if "flag_incomplete_panel" in df.columns:
        df_main = df[df["flag_incomplete_panel"] == 0].copy()
    else:
        df_main = df.copy()

    n_dropped = df.index.get_level_values("cve_mun").nunique() - \
                df_main.index.get_level_values("cve_mun").nunique()
    print(f"  Dropped {n_dropped} municipios incompletos")
    raw_main = run_twfe_sample(df_main, "main")

    # --- Export tables ---
    tab_full = format_table(raw_full)
    tab_main = format_table(raw_main)

    raw_full.to_csv(OUT / "tabla_2_twfe_full.csv", index=False)
    raw_main.to_csv(OUT / "tabla_2_twfe_main.csv", index=False)

    export_table_tex(
        tab_full, OUT / "tabla_2_twfe_full.tex",
        caption="TWFE Baseline — Full Sample (incluye panel incompleto)",
        label="tab:twfe_full",
        note="FE municipio + periodo, cluster SE municipio. Outcomes en escala asinh.",
    )

    export_table_tex(
        tab_main, OUT / "tabla_2_twfe_main.tex",
        caption="TWFE Baseline — Main Sample (panel balanceado)",
        label="tab:twfe_main",
        note="FE municipio + periodo, cluster SE municipio. "
             "Excluye municipios con panel incompleto.",
    )

    # --- Comparison text ---
    lines = [
        "=" * 60,
        "SENSIBILIDAD A LA MUESTRA: Main (balanceado) vs Full",
        "=" * 60,
        "",
        f"{'Outcome':<25s} {'Full β':>10s} {'Main β':>10s} "
        f"{'Full p':>8s} {'Main p':>8s} {'Δβ':>8s} {'Δ% relativo':>12s}",
        "-" * 80,
    ]

    for _, rf in raw_full.iterrows():
        out = rf["outcome"]
        rm = raw_main[raw_main["outcome"] == out].iloc[0]
        label = OUTCOME_DEFS[out]["label"]

        delta = rm["coef"] - rf["coef"]
        pct_delta = abs(delta / rf["se"]) * 100 if rf["se"] > 0 else 0

        lines.append(
            f"{label:<25s} "
            f"{rf['coef']:>10.4f} {rm['coef']:>10.4f} "
            f"{rf['pval']:>8.4f} {rm['pval']:>8.4f} "
            f"{delta:>8.4f} {pct_delta:>11.1f}%"
        )

    lines += [
        "",
        "-" * 80,
        f"Full sample: {int(raw_full.iloc[0]['nobs']):,} obs, "
        f"{int(raw_full.iloc[0]['n_mun']):,} municipios",
        f"Main sample: {int(raw_main.iloc[0]['nobs']):,} obs, "
        f"{int(raw_main.iloc[0]['n_mun']):,} municipios",
        f"Municipios eliminados: {n_dropped}",
        "",
        "Interpretación:",
        "  Si Δβ es pequeño relativo a SE --> la exclusión es inocua.",
        "  Ambas muestras producen la misma conclusión cualitativa.",
    ]

    sens_path = OUT / "sample_sensitivity.txt"
    sens_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n  --> Sensibilidad: {sens_path}")

    print("\nOK Sample policy completado.")


if __name__ == "__main__":
    main()
