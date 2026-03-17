"""
src/plot_style.py — Configuración centralizada de estilo de gráficos.
"""

import matplotlib.pyplot as plt
import seaborn as sns

SEED = 42
PALETTE = sns.color_palette("Set2")


def apply_style():
    """Aplica el estilo estándar del proyecto."""
    sns.set_theme(style="whitegrid", context="notebook", font_scale=1.1)
    plt.rcParams.update({
        "figure.figsize": (10, 5),
        "figure.dpi": 120,
        "axes.titlesize": 14,
        "axes.labelsize": 12,
        "savefig.bbox": "tight",
        "savefig.dpi": 200,
    })
    return PALETTE
