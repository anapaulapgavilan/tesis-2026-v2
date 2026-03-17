"""
extensive_margin.py — Margen extensivo y composición de género.

Extensión exploratoria y pre-especificada:
  1. any_X_m = 1{X_m_raw > 0}  — acceso mínimo (margen extensivo LPM)
  2. share_m = y_m_pc / (y_m_pc + y_h_pc) — composición de género

Se estima TWFE (LPM para binarios, OLS para shares) con FE y cluster SE.

Outputs:
  outputs/paper/tabla_7_extensive.csv / .tex

Uso:
  python -m tesis_alcaldesas.models.extensive_margin
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from tesis_alcaldesas.models.utils import (
    load_panel, run_panel_ols,
    OUTCOME_DEFS, OUT,
    coef_str, se_str, stars, export_table_tex,
)

# Outcomes for extensive margin
EXTENSIVE_DEFS = {
    "ncont_total_m":     "Contratos totales (any>0)",
    "numtar_deb_m":      "Tarjetas débito (any>0)",
    "numtar_cred_m":     "Tarjetas crédito (any>0)",
    "numcontcred_hip_m": "Créditos hipotecarios (any>0)",
    "saldocont_total_m": "Saldo total (any>0)",
}

SHARE_DEFS = {
    "ncont_total":     "Share mujeres — contratos totales",
    "numtar_deb":      "Share mujeres — tarjetas débito",
    "numtar_cred":     "Share mujeres — tarjetas crédito",
    "numcontcred_hip": "Share mujeres — créditos hipotecarios",
    "saldocont_total": "Share mujeres — saldo total",
}


def build_extensive_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add any_X_m and share_m features on the fly."""
    df = df.copy()

    for raw_col in EXTENSIVE_DEFS:
        # Binary: any > 0 (use raw counts, not pc)
        if raw_col in df.columns:
            df[f"any_{raw_col}"] = (df[raw_col] > 0).astype(float)
            # Set to NaN where raw is NaN
            df.loc[df[raw_col].isna(), f"any_{raw_col}"] = np.nan

    for base in SHARE_DEFS:
        m_pc = f"{base}_m_pc"
        h_pc = f"{base}_h_pc"
        if m_pc in df.columns and h_pc in df.columns:
            total = df[m_pc] + df[h_pc]
            # Guard: only compute share when total > minimum threshold
            # (avoid division by near-zero denominators)
            threshold = 1.0  # at least 1 per 10,000 adults
            df[f"share_m_{base}"] = np.where(
                total > threshold,
                df[m_pc] / total,
                np.nan,
            )

    return df


def main():
    print("=" * 60)
    print("Extensión: Margen Extensivo y Composición de Género")
    print("=" * 60)

    df = load_panel()
    df = build_extensive_features(df)

    treatment = "alcaldesa_final"
    controls = ["log_pob"]
    exog = [treatment] + controls

    rows = []

    # --- Panel A: Extensive margin (LPM) ---
    print("\n--- Panel A: Margen extensivo (LPM) ---")
    for raw_col, label in EXTENSIVE_DEFS.items():
        depvar = f"any_{raw_col}"
        if depvar not in df.columns:
            print(f"  [!] {depvar} no disponible — omitido.")
            continue

        # Summary stats
        mean_dep = df[depvar].mean()
        print(f"\n  {label} ({depvar}): E[Y] = {mean_dep:.3f}")

        res = run_panel_ols(df, depvar=depvar, exog=exog)
        beta = res.params[treatment]
        se = res.std_errors[treatment]
        pval = res.pvalues[treatment]
        ci_lo, ci_hi = res.conf_int().loc[treatment]

        print(f"    β = {beta:.4f}{stars(pval)}  SE = {se:.4f}  p = {pval:.4f}")

        rows.append({
            "Panel": "A: Extensivo (LPM)",
            "Outcome": label,
            "depvar": depvar,
            "mean_dep": mean_dep,
            "Coef": coef_str(beta, pval),
            "SE": se_str(se),
            "p-valor": f"{pval:.4f}",
            "IC 95%": f"[{ci_lo:.4f}, {ci_hi:.4f}]",
            "N": f"{res.nobs:,}",
            "coef_raw": beta,
            "se_raw": se,
            "pval_raw": pval,
        })

    # --- Panel B: Share mujeres ---
    print("\n--- Panel B: Share mujeres ---")
    for base, label in SHARE_DEFS.items():
        depvar = f"share_m_{base}"
        if depvar not in df.columns:
            print(f"  [!] {depvar} no disponible — omitido.")
            continue

        mean_dep = df[depvar].mean()
        print(f"\n  {label} ({depvar}): E[Y] = {mean_dep:.3f}")

        res = run_panel_ols(df, depvar=depvar, exog=exog)
        beta = res.params[treatment]
        se = res.std_errors[treatment]
        pval = res.pvalues[treatment]
        ci_lo, ci_hi = res.conf_int().loc[treatment]

        print(f"    β = {beta:.6f}{stars(pval)}  SE = {se:.6f}  p = {pval:.4f}")

        rows.append({
            "Panel": "B: Share mujeres",
            "Outcome": label,
            "depvar": depvar,
            "mean_dep": mean_dep,
            "Coef": coef_str(beta, pval, digits=6),
            "SE": se_str(se, digits=6),
            "p-valor": f"{pval:.4f}",
            "IC 95%": f"[{ci_lo:.6f}, {ci_hi:.6f}]",
            "N": f"{res.nobs:,}",
            "coef_raw": beta,
            "se_raw": se,
            "pval_raw": pval,
        })

    # --- Export ---
    result_df = pd.DataFrame(rows)

    csv_path = OUT / "tabla_7_extensive.csv"
    result_df.to_csv(csv_path, index=False)
    print(f"\n  --> CSV: {csv_path}")

    # TeX table
    tex_df = result_df[["Panel", "Outcome", "Coef", "SE", "p-valor", "N"]].copy()
    tex_df = tex_df.set_index(["Panel", "Outcome"])

    export_table_tex(
        tex_df, OUT / "tabla_7_extensive.tex",
        caption="Extensión: Margen extensivo (LPM) y composición de género",
        label="tab:extensive",
        note="Panel A: LPM — Y = 1\\{outcome > 0\\}. "
             "Panel B: Share = $y_m / (y_m + y_h)$. "
             "FE municipio + periodo, cluster SE municipio. "
             "Extensión exploratoria pre-especificada.",
    )

    print("\nOK Extensión outcomes completada.")


if __name__ == "__main__":
    main()
