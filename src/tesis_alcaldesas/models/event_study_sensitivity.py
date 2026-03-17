"""
event_study_sensitivity.py -- Sensibilidad del event study al bin extremo y ventana.

GUIA PARA EL ASESOR:
  En el event study principal (04_event_study.py), la variable
  numtar_cred_m (tarjetas de credito mujeres) tiene p=0.083 en el
  chi-cuadrado conjunto de pre-trends. Esto esta justo al borde.

  La sospecha es que ese p viene del "bin extremo": el indicador
  binario que agrupa todos los periodos k <= -4 en una sola dummy.
  Si hay pocos municipios en ese bin, su estimacion es ruidosa y
  puede jalar todo el test.

  Este script testea 3 variantes de ventana para verificar si
  los pre-trends mejoran cuando cambiamos la definicion del bin:

    A) Ventana corta: K=3 leads, L=8 lags (bin en k <= -3)
       --> Comprime mas periodos en el bin, pero lo aleja del tratamiento
    B) Ventana extendida: K=6 leads, L=8 lags (bin en k <= -6)
       --> Usa mas leads individuales, bin solo para muy lejanos
    C) Excluir cohortes tempranas (g=0):
       --> Elimina municipios que cambian de alcaldesa en el primer
           periodo, que son los que dominan el bin extremo

  Si en las 3 variantes p > 0.10, concluimos que los pre-trends
  del baseline son robustos y que el p=0.083 es un artefacto del
  binning, no una violacion del supuesto de tendencias paralelas.

  Interpretacion visual: Se genera un grafico multi-panel donde
  cada columna es una variante (A, B, C) y cada fila un outcome.
  Las bandas de confianza al 95% deben cruzar cero en todos los
  leads pre-tratamiento.

Variantes para los 2 outcomes mas delicados (numtar_cred_m, ncont_total_m):
  A) K=3 leads, L=8 lags (bin en k<=-3)
  B) K=6 leads, L=8 lags (bin en k<=-6)
  C) Excluir cohortes con first_treat muy temprano (g=0)

Outputs:
  outputs/paper/figura_2_event_study_sens.pdf
  outputs/paper/pretrends_tests_sens.csv

Uso:
  python -m tesis_alcaldesas.models.event_study_sensitivity
"""

from __future__ import annotations

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS
from scipy import stats

from tesis_alcaldesas.models.utils import (
    load_panel, PRIMARY_5, OUTCOME_DEFS, OUT, plot_save, stars,
)

# Outcomes to focus on for sensitivity
FOCUS_OUTCOMES = ["numtar_cred_m", "ncont_total_m"]

# Variant configs: (label, K_LEADS, L_LAGS, exclude_cohort_g)
VARIANTS = [
    ("Baseline (K=4, L=8)",        4, 8, None),
    ("A: K=3, L=8 (bin k≤-3)",    3, 8, None),
    ("B: K=6, L=8 (bin k≤-6)",    6, 8, None),
    ("C: Excl. cohorte g=0",       4, 8, 0),
]

REF_K = -1


def build_event_dummies_flex(
    df: pd.DataFrame,
    k_leads: int,
    l_lags: int,
    exclude_cohort_g: int | None = None,
) -> tuple[pd.DataFrame, list[str]]:
    """
    Build event-time dummies with flexible window.
    Mirrors the existing event_study.py logic but parameterized.
    """
    df = df.copy()

    # Exclude always-treated
    df = df[df["cohort_type"] != "always-treated"].copy()

    # Optionally exclude a specific cohort
    if exclude_cohort_g is not None:
        df = df[df["first_treat_t"] != exclude_cohort_g].copy()

    min_k = -k_leads
    max_k = l_lags

    # Bin extremes
    df["evt_binned"] = df["event_time"].copy()
    df.loc[df["evt_binned"] < min_k, "evt_binned"] = min_k
    df.loc[df["evt_binned"] > max_k, "evt_binned"] = max_k

    # Generate dummies
    dummy_cols = []
    for k in range(min_k, max_k + 1):
        if k == REF_K:
            continue
        if k == min_k:
            col = f"evt_k_le{min_k}"
        elif k == max_k:
            col = f"evt_k_ge{max_k}"
        else:
            col = f"evt_k{k:+d}"

        df[col] = ((df["evt_binned"] == k) & df["evt_binned"].notna()).astype(float)
        dummy_cols.append(col)

    return df, dummy_cols


def run_event_study_flex(
    df: pd.DataFrame,
    depvar: str,
    dummy_cols: list[str],
    k_leads: int,
) -> dict:
    """Run event study and return coefficients + pretrend test."""
    exog = dummy_cols + ["log_pob"]
    cols_needed = [depvar] + exog
    mask = df[cols_needed].notna().all(axis=1)
    sub = df.loc[mask].copy()

    # Need panel index
    if sub.index.names != ["cve_mun", "t_index"]:
        if "cve_mun" in sub.columns and "t_index" in sub.columns:
            sub = sub.set_index(["cve_mun", "t_index"])

    y = sub[depvar]
    X = sub[exog]

    mod = PanelOLS(y, X, entity_effects=True, time_effects=True, check_rank=False)
    res = mod.fit(cov_type="clustered", cluster_entity=True)

    # Extract coefs
    coefs = []
    for col in dummy_cols:
        beta = res.params[col]
        se = res.std_errors[col]
        pval = res.pvalues[col]
        ci = res.conf_int().loc[col]

        if "_le" in col:
            k = -k_leads
        elif "_ge" in col:
            # parse the number after "ge"
            k = int(col.split("ge")[1])
        else:
            k = int(col.split("k")[1])

        coefs.append({
            "k": k, "coef": beta, "se": se, "pval": pval,
            "ci_lo": ci.iloc[0], "ci_hi": ci.iloc[1], "col": col,
        })

    # Reference
    coefs.append({
        "k": REF_K, "coef": 0.0, "se": 0.0, "pval": 1.0,
        "ci_lo": 0.0, "ci_hi": 0.0, "col": "reference",
    })

    coefs_df = pd.DataFrame(coefs).sort_values("k")

    # Pre-trends test
    pre_cols = [c for c in dummy_cols if any(
        c.endswith(f"k{kk:+d}") for kk in range(-k_leads, 0) if kk != REF_K
    ) or "_le" in c]

    if pre_cols:
        pre_coefs = np.array([res.params[c] for c in pre_cols])
        vcov = res.cov.loc[pre_cols, pre_cols].values
        try:
            chi2_stat = pre_coefs @ np.linalg.solve(vcov, pre_coefs)
            chi2_pval = 1 - stats.chi2.cdf(chi2_stat, df=len(pre_cols))
        except np.linalg.LinAlgError:
            chi2_stat, chi2_pval = np.nan, np.nan
        n_rest = len(pre_cols)
    else:
        chi2_stat, chi2_pval, n_rest = np.nan, np.nan, 0

    return {
        "coefs": coefs_df,
        "pretrend": {"chi2_stat": chi2_stat, "chi2_pval": chi2_pval, "n_restrictions": n_rest},
        "nobs": res.nobs,
    }


def main():
    print("=" * 60)
    print("Event Study Sensitivity — Bin extremo y ventana")
    print("=" * 60)

    df = load_panel()
    print(f"  Panel: {len(df):,} obs")

    pretrend_rows = []
    all_results = {}   # {(outcome, variant_label): coefs_df}

    for out_name in FOCUS_OUTCOMES:
        depvar = f"{out_name}_pc_asinh"
        label = OUTCOME_DEFS[out_name]["label"]
        print(f"\n{'='*50}")
        print(f"  Outcome: {label} ({out_name})")
        print(f"{'='*50}")

        for var_label, k_leads, l_lags, excl_g in VARIANTS:
            print(f"\n  Variante: {var_label}")

            df_es, dummy_cols = build_event_dummies_flex(
                df, k_leads=k_leads, l_lags=l_lags, exclude_cohort_g=excl_g,
            )

            res = run_event_study_flex(df_es, depvar, dummy_cols, k_leads)

            pt = res["pretrend"]
            print(f"    N = {res['nobs']:,}  "
                  f"Pre-trend χ² = {pt['chi2_stat']:.3f}, p = {pt['chi2_pval']:.4f}")

            key = (out_name, var_label)
            all_results[key] = res["coefs"]

            pretrend_rows.append({
                "outcome": out_name,
                "label": label,
                "variant": var_label,
                "k_leads": k_leads,
                "l_lags": l_lags,
                "excl_cohort": excl_g if excl_g is not None else "",
                "chi2_stat": pt["chi2_stat"],
                "chi2_pval": pt["chi2_pval"],
                "n_restrictions": pt["n_restrictions"],
                "pass_10pct": "Yes" if pt["chi2_pval"] > 0.10 else "No",
                "nobs": res["nobs"],
            })

    # --- Save pretrends ---
    pt_df = pd.DataFrame(pretrend_rows)
    pt_path = OUT / "pretrends_tests_sens.csv"
    pt_df.to_csv(pt_path, index=False)
    print(f"\n  --> Pre-trends sensibilidad: {pt_path}")

    # --- Plot ---
    fig, axes = plt.subplots(len(FOCUS_OUTCOMES), len(VARIANTS),
                              figsize=(5 * len(VARIANTS), 4 * len(FOCUS_OUTCOMES)),
                              squeeze=False)

    colors = ["steelblue", "darkorange", "seagreen", "crimson"]

    for row_i, out_name in enumerate(FOCUS_OUTCOMES):
        label = OUTCOME_DEFS[out_name]["label"]

        for col_j, (var_label, _, _, _) in enumerate(VARIANTS):
            ax = axes[row_i, col_j]
            key = (out_name, var_label)
            cdf = all_results[key]

            color = colors[col_j % len(colors)]
            ax.fill_between(cdf["k"], cdf["ci_lo"], cdf["ci_hi"],
                            alpha=0.15, color=color)
            ax.plot(cdf["k"], cdf["coef"], "o-", color=color,
                    markersize=3, linewidth=1)
            ax.axhline(0, color="black", linewidth=0.5)
            ax.axvline(-0.5, color="red", linewidth=0.8, linestyle="--", alpha=0.7)

            # Pretrend annotation
            pt_row = pt_df[
                (pt_df["outcome"] == out_name) & (pt_df["variant"] == var_label)
            ]
            if len(pt_row) > 0:
                pp = pt_row.iloc[0]["chi2_pval"]
                ax.text(0.02, 0.98, f"p={pp:.3f}",
                        transform=ax.transAxes, fontsize=7, va="top",
                        bbox=dict(boxstyle="round,pad=0.3", facecolor="wheat", alpha=0.5))

            if row_i == 0:
                ax.set_title(var_label, fontsize=9)
            if col_j == 0:
                ax.set_ylabel(f"{label}\nδ_k (asinh)", fontsize=8)
            ax.set_xlabel("Event time (k)", fontsize=8)

    fig.suptitle("Sensibilidad del Event Study al bin extremo y ventana",
                 fontsize=12, y=1.02)
    fig.tight_layout()

    fig_path = OUT / "figura_2_event_study_sens.pdf"
    plot_save(fig, fig_path)

    print("\nOK Sensibilidad event study completada.")


if __name__ == "__main__":
    main()
