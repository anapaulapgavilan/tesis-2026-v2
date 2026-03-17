"""
03_event_study.py — Event study para diagnóstico de pre-trends.

Construye dummies de leads (K=4) y lags (L=8) con bins extremos,
referencia k = -1.  Excluye always-treated (sin pre-período).

Ecuación:
  Y_{it} = α_i + γ_t + Σ_{k≠-1} δ_k · 1{event_time = k} + X'β + ε_{it}

Outputs:
  outputs/paper/figura_1_event_study.pdf
  outputs/paper/pretrends_tests.csv
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

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
K_LEADS = 4   # pre-treatment leads (k = -4, -3, -2; k=-1 is reference)
L_LAGS  = 8   # post-treatment lags  (k = 0, 1, ..., 7; k=8+ binned)
REF_K   = -1  # reference period


def build_event_dummies(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    """
    Construye dummies de event_time con bins extremos.
    Excluye always-treated y never-treated de las dummies
    (never-treated son el grupo de control implícito --> dummies = 0).
    """
    # Work on a copy
    df = df.copy()

    # Bin extremes
    min_k = -K_LEADS     # -4
    max_k = L_LAGS       #  8

    # Create binned event_time
    df["evt_binned"] = df["event_time"].copy()
    df.loc[df["evt_binned"] < min_k, "evt_binned"] = min_k
    df.loc[df["evt_binned"] > max_k, "evt_binned"] = max_k

    # For never-treated (event_time = NaN), keep as NaN — all dummies will be 0
    # For always-treated, exclude from sample
    df = df[df["cohort_type"] != "always-treated"].copy()

    # Generate dummies for each k (except reference)
    dummy_cols = []
    for k in range(min_k, max_k + 1):
        if k == REF_K:
            continue
        col = f"evt_k{k:+d}" if k != min_k and k != max_k else (
            f"evt_k_le{min_k}" if k == min_k else f"evt_k_ge{max_k}"
        )
        # For never-treated (NaN event_time), dummy = 0
        df[col] = ((df["evt_binned"] == k) & df["evt_binned"].notna()).astype(float)
        dummy_cols.append(col)

    return df, dummy_cols


def run_event_study(df: pd.DataFrame, depvar: str, dummy_cols: list[str]) -> dict:
    """Run event study regression and extract coefficients."""

    exog = dummy_cols + ["log_pob"]
    cols_needed = [depvar] + exog
    mask = df[cols_needed].notna().all(axis=1)
    sub = df.loc[mask].copy()

    y = sub[depvar]
    X = sub[exog]

    mod = PanelOLS(y, X, entity_effects=True, time_effects=True, check_rank=False)
    res = mod.fit(cov_type="clustered", cluster_entity=True)

    # Extract event-time coefficients
    coefs = []
    for col in dummy_cols:
        beta = res.params[col]
        se = res.std_errors[col]
        pval = res.pvalues[col]
        ci_lo, ci_hi = res.conf_int().loc[col]

        # Parse k from column name
        if "_le" in col:
            k = -K_LEADS
        elif "_ge" in col:
            k = L_LAGS
        else:
            k = int(col.split("k")[1])

        coefs.append({
            "k": k,
            "coef": beta,
            "se": se,
            "pval": pval,
            "ci_lo": ci_lo,
            "ci_hi": ci_hi,
            "col": col,
        })

    # Add reference period
    coefs.append({
        "k": REF_K,
        "coef": 0.0,
        "se": 0.0,
        "pval": 1.0,
        "ci_lo": 0.0,
        "ci_hi": 0.0,
        "col": "reference",
    })

    coefs_df = pd.DataFrame(coefs).sort_values("k")

    # -------------------------------------------------------------------
    # Pre-trends test: joint F-test that all pre-treatment coefficients = 0
    # -------------------------------------------------------------------
    pre_cols = [c for c in dummy_cols if any(
        c.endswith(f"k{kk:+d}") for kk in range(-K_LEADS, 0) if kk != REF_K
    ) or "_le" in c]

    if pre_cols:
        pre_coefs = np.array([res.params[c] for c in pre_cols])
        # Variance-covariance of pre-treatment coefficients
        vcov = res.cov.loc[pre_cols, pre_cols].values
        try:
            chi2_stat = pre_coefs @ np.linalg.solve(vcov, pre_coefs)
            n_restrictions = len(pre_cols)
            chi2_pval = 1 - stats.chi2.cdf(chi2_stat, df=n_restrictions)
        except np.linalg.LinAlgError:
            chi2_stat = np.nan
            chi2_pval = np.nan
            n_restrictions = len(pre_cols)
    else:
        chi2_stat = np.nan
        chi2_pval = np.nan
        n_restrictions = 0

    pretrend_test = {
        "chi2_stat": chi2_stat,
        "chi2_pval": chi2_pval,
        "n_restrictions": n_restrictions,
        "pre_cols": pre_cols,
    }

    return {
        "coefs": coefs_df,
        "pretrend": pretrend_test,
        "nobs": res.nobs,
        "r2w": res.rsquared_within,
    }


def plot_event_study(results: dict[str, dict], out_path: Path):
    """Plot event study for all 5 primary outcomes."""
    n = len(results)
    fig, axes = plt.subplots(2, 3, figsize=(14, 8))
    axes = axes.flatten()

    for i, (out_name, res) in enumerate(results.items()):
        ax = axes[i]
        cdf = res["coefs"]

        # Plot CI
        ax.fill_between(cdf["k"], cdf["ci_lo"], cdf["ci_hi"],
                        alpha=0.15, color="steelblue")
        ax.plot(cdf["k"], cdf["coef"], "o-", color="steelblue", markersize=4, linewidth=1.2)

        # Reference line at 0
        ax.axhline(0, color="black", linewidth=0.5, linestyle="-")
        # Treatment onset
        ax.axvline(-0.5, color="red", linewidth=0.8, linestyle="--", alpha=0.7)

        # Pre-trend test annotation
        pt = res["pretrend"]
        pval_str = f"Pre-trend χ²: p={pt['chi2_pval']:.3f}" if not np.isnan(pt["chi2_pval"]) else "Pre-trend: N/A"
        ax.text(0.02, 0.98, pval_str, transform=ax.transAxes,
                fontsize=7, va="top", ha="left",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="wheat", alpha=0.5))

        label = OUTCOME_DEFS.get(out_name, {}).get("label", out_name)
        ax.set_title(label, fontsize=10)
        ax.set_xlabel("Event time (k)")
        ax.set_ylabel("δ_k (asinh)")

    # Hide unused subplot
    if n < len(axes):
        for j in range(n, len(axes)):
            axes[j].set_visible(False)

    fig.suptitle("Event Study — Diagnóstico de Pre-Trends", fontsize=13, y=1.01)
    fig.tight_layout()
    plot_save(fig, out_path)


def main():
    print("=" * 60)
    print("03 — Event Study (Pre-Trends Diagnosis)")
    print("=" * 60)

    df = load_panel()
    df_es, dummy_cols = build_event_dummies(df)

    print(f"  Sample: {len(df_es):,} obs (excl. always-treated)")
    print(f"  Event dummies: {len(dummy_cols)} (ref k={REF_K})")
    print(f"  Dummies: {dummy_cols}")

    all_results = {}
    pretrend_rows = []

    for out_name in PRIMARY_5:
        depvar = f"{out_name}_pc_asinh"
        label = OUTCOME_DEFS[out_name]["label"]
        print(f"\n  [{out_name}] {depvar} ...")

        res = run_event_study(df_es, depvar, dummy_cols)
        all_results[out_name] = res

        pt = res["pretrend"]
        print(f"    N = {res['nobs']:,}  R²w = {res['r2w']:.4f}")
        print(f"    Pre-trend joint test: χ² = {pt['chi2_stat']:.3f}, "
              f"p = {pt['chi2_pval']:.4f}, restrictions = {pt['n_restrictions']}")

        pretrend_rows.append({
            "outcome": out_name,
            "label": label,
            "chi2_stat": pt["chi2_stat"],
            "chi2_pval": pt["chi2_pval"],
            "n_restrictions": pt["n_restrictions"],
            "pass_10pct": "Yes" if pt["chi2_pval"] > 0.10 else "No",
            "nobs": res["nobs"],
        })

        # Print individual pre-trend coefficients
        pre = res["coefs"][res["coefs"]["k"] < 0].sort_values("k")
        for _, row in pre.iterrows():
            k = int(row["k"])
            print(f"      k={k:+d}: β={row['coef']:.4f}{stars(row['pval'])}  "
                  f"SE={row['se']:.4f}  p={row['pval']:.4f}")

    # -------------------------------------------------------------------
    # Save pre-trends tests
    # -------------------------------------------------------------------
    pt_df = pd.DataFrame(pretrend_rows)
    pt_path = OUT / "pretrends_tests.csv"
    pt_df.to_csv(pt_path, index=False)
    print(f"\n  --> Pre-trends tests: {pt_path}")

    # -------------------------------------------------------------------
    # Plot
    # -------------------------------------------------------------------
    fig_path = OUT / "figura_1_event_study.pdf"
    plot_event_study(all_results, fig_path)

    # -------------------------------------------------------------------
    # Save coefficient tables (for appendix)
    # -------------------------------------------------------------------
    for out_name, res in all_results.items():
        coef_path = OUT / f"event_study_coefs_{out_name}.csv"
        res["coefs"].to_csv(coef_path, index=False)

    print("\nDone.")


if __name__ == "__main__":
    main()
