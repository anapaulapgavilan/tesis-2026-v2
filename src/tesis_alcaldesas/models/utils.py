"""
tesis_alcaldesas.models.utils — Funciones compartidas para el pipeline de modelado.

Provee:
  - load_panel()          → carga el parquet analítico
  - OUTCOME_DEFS          → diccionario con los 5 outcomes primarios
  - PRIMARY_5             → lista de 5 outcomes primarios
  - run_panel_ols()       → wrapper de PanelOLS con FE y cluster SE
  - export_table_tex()    → exporta DataFrame a .tex
  - plot_save()           → guarda figura PDF con defaults de paper
  - stars(), coef_str(), se_str() → formateo
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")          # backend no interactivo
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from linearmodels.panel import PanelOLS

from tesis_alcaldesas.config import (
    PARQUET_FEATURES, OUTPUT_PAPER, OUTCOME_LABELS, PRIMARY_OUTCOMES,
)

# ---------------------------------------------------------------------------
# Re-exports (compatibilidad con scripts de modelo)
# ---------------------------------------------------------------------------
OUT = OUTPUT_PAPER
OUT.mkdir(parents=True, exist_ok=True)

PARQUET = PARQUET_FEATURES

# OUTCOME_DEFS: formato legado {"key": {"label": ..., "label_en": ...}}
OUTCOME_DEFS: dict[str, dict[str, str]] = {
    k: {"label": v["es"], "label_en": v["en"]}
    for k, v in OUTCOME_LABELS.items()
}

PRIMARY_5 = PRIMARY_OUTCOMES

# All 17 outcomes (mujeres)
ALL_OUTCOMES_M = [
    "ncont_total_m", "ncont_ahorro_m", "ncont_plazo_m",
    "ncont_n1_m", "ncont_n2_m", "ncont_n3_m", "ncont_tradic_m",
    "saldocont_total_m", "saldocont_ahorro_m", "saldocont_plazo_m",
    "saldocont_n1_m", "saldocont_n2_m", "saldocont_n3_m", "saldocont_tradic_m",
    "numtar_deb_m", "numtar_cred_m", "numcontcred_hip_m",
]


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_panel(path: Path = PARQUET) -> pd.DataFrame:
    """Carga el parquet y setea el MultiIndex (cve_mun, t_index) para PanelOLS."""
    df = pd.read_parquet(path)
    df = df.set_index(["cve_mun", "t_index"])
    df.index.names = ["cve_mun", "t_index"]
    return df


# ---------------------------------------------------------------------------
# Panel regression helper
# ---------------------------------------------------------------------------
def run_panel_ols(
    df: pd.DataFrame,
    depvar: str,
    exog: list[str],
    entity_effects: bool = True,
    time_effects: bool = True,
    cluster_entity: bool = True,
    check_rank: bool = False,
) -> Any:
    """
    Ejecuta PanelOLS con FE y cluster SE.

    Parameters
    ----------
    df : panel DataFrame con MultiIndex (cve_mun, t_index)
    depvar : nombre de la variable dependiente
    exog : lista de regresores (incluye tratamiento y controles)
    entity_effects : absorber FE de municipio
    time_effects : absorber FE de periodo
    cluster_entity : cluster SE a nivel de municipio

    Returns
    -------
    linearmodels PanelEffectsResults
    """
    cols = [depvar] + exog
    mask = df[cols].notna().all(axis=1)
    sub = df.loc[mask].copy()

    y = sub[depvar]
    X = sub[exog]

    mod = PanelOLS(
        y, X,
        entity_effects=entity_effects,
        time_effects=time_effects,
        check_rank=check_rank,
    )

    if cluster_entity:
        res = mod.fit(cov_type="clustered", cluster_entity=True)
    else:
        res = mod.fit(cov_type="robust")

    return res


# ---------------------------------------------------------------------------
# Stars
# ---------------------------------------------------------------------------
def stars(pval: float) -> str:
    if pval < 0.01:
        return "***"
    elif pval < 0.05:
        return "**"
    elif pval < 0.10:
        return "*"
    return ""


def coef_str(coef: float, pval: float, digits: int = 4) -> str:
    """Format coefficient with stars."""
    return f"{coef:.{digits}f}{stars(pval)}"


def se_str(se: float, digits: int = 4) -> str:
    """Format SE in parentheses."""
    return f"({se:.{digits}f})"


# ---------------------------------------------------------------------------
# LaTeX export
# ---------------------------------------------------------------------------
def export_table_tex(
    df: pd.DataFrame,
    path: Path,
    caption: str = "",
    label: str = "",
    note: str = "",
) -> None:
    """Exporta DataFrame a .tex con formato de paper."""
    latex = df.to_latex(
        index=True,
        escape=False,
        column_format="l" + "c" * len(df.columns),
    )

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\small",
    ]
    if caption:
        lines.append(rf"\caption{{{caption}}}")
    if label:
        lines.append(rf"\label{{{label}}}")
    lines.append(latex.strip())
    if note:
        lines.append(r"\vspace{2mm}")
        lines.append(rf"\parbox{{\textwidth}}{{\footnotesize \textit{{Nota:}} {note}}}")
    lines.append(r"\end{table}")

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  → LaTeX: {path}")


# ---------------------------------------------------------------------------
# Plot helper
# ---------------------------------------------------------------------------
def plot_save(fig: plt.Figure, path: Path, dpi: int = 300) -> None:
    """Guarda figura como PDF (paper) y PNG (preview)."""
    fig.savefig(path, bbox_inches="tight", dpi=dpi)
    png_path = path.with_suffix(".png")
    fig.savefig(png_path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  → Figura: {path} + {png_path}")
