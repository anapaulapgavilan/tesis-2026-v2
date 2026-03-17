"""
mdes_power.py — Minimum Detectable Effect Size (MDES) y análisis de poder.

Convierte resultados nulos en hallazgos informativos:
  "Con estos datos, descartamos efectos mayores a X% en …"

Para cada outcome primario:
  1. Obtener SE del coeficiente TWFE baseline (tabla_2_twfe_raw.csv)
  2. Calcular MDES = (z_alpha/2 + z_beta) × SE
  3. Traducir asinh → % aproximado en niveles
  4. Reportar al 80% poder (alpha 0.05 y 0.10)

Outputs:
  outputs/paper/tabla_6_mdes.csv
  outputs/paper/tabla_6_mdes.tex
  outputs/paper/mdes_summary.txt

Uso:
  python -m tesis_alcaldesas.models.mdes_power
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as st

from tesis_alcaldesas.config import OUTCOME_LABELS
from tesis_alcaldesas.models.utils import OUT

LABEL_MAP = {k: v["es"] for k, v in OUTCOME_LABELS.items()}


def mdes(se: float, alpha: float = 0.05, power: float = 0.80) -> float:
    """
    MDES = (z_{alpha/2} + z_{power}) × SE

    Para un test bilateral, el efecto mínimo detectable al nivel `alpha`
    con potencia `power`.
    """
    z_alpha = st.norm.ppf(1 - alpha / 2)
    z_beta = st.norm.ppf(power)
    return (z_alpha + z_beta) * se


def asinh_to_pct(delta: float) -> float:
    """
    Aproximación: |Δ asinh| ≈ |Δ ln(y)| para y grande.
    
    Retorna el cambio porcentual aproximado:
      % change ≈ (exp(|delta|) - 1) × 100
    """
    # For small delta, exp(delta)-1 ≈ delta (which is the % approx)
    return (np.exp(abs(delta)) - 1) * 100


def main():
    print("=" * 60)
    print("MDES — Minimum Detectable Effect Size")
    print("=" * 60)

    # --- Load TWFE raw results ---
    twfe_path = OUT / "tabla_2_twfe_raw.csv"
    if not twfe_path.exists():
        print(f"✗ No se encontró {twfe_path}")
        print("  Ejecuta primero: python -m tesis_alcaldesas.models.twfe")
        return

    twfe = pd.read_csv(twfe_path)
    print(f"  TWFE raw: {len(twfe)} outcomes cargados")

    # --- Calculate MDES ---
    rows = []

    for _, tw in twfe.iterrows():
        out_name = tw["outcome"]
        label = LABEL_MAP.get(out_name, out_name)
        se = tw["se"]
        coef = tw["coef"]
        nobs = tw["nobs"]

        # MDES at different alpha/power combos
        mdes_05_80 = mdes(se, alpha=0.05, power=0.80)
        mdes_10_80 = mdes(se, alpha=0.10, power=0.80)
        mdes_05_90 = mdes(se, alpha=0.05, power=0.90)

        # Convert to approximate %
        pct_05_80 = asinh_to_pct(mdes_05_80)
        pct_10_80 = asinh_to_pct(mdes_10_80)
        pct_05_90 = asinh_to_pct(mdes_05_90)

        print(f"\n  {label} ({out_name}):")
        print(f"    SE = {se:.4f}  |  β̂_TWFE = {coef:.4f}")
        print(f"    MDES (α=0.05, 80%): {mdes_05_80:.4f} asinh ≈ {pct_05_80:.1f}%")
        print(f"    MDES (α=0.10, 80%): {mdes_10_80:.4f} asinh ≈ {pct_10_80:.1f}%")
        print(f"    MDES (α=0.05, 90%): {mdes_05_90:.4f} asinh ≈ {pct_05_90:.1f}%")

        rows.append({
            "outcome": out_name,
            "label": label,
            "coef_twfe": coef,
            "se_twfe": se,
            "nobs": nobs,
            "mdes_05_80_asinh": mdes_05_80,
            "mdes_05_80_pct": pct_05_80,
            "mdes_10_80_asinh": mdes_10_80,
            "mdes_10_80_pct": pct_10_80,
            "mdes_05_90_asinh": mdes_05_90,
            "mdes_05_90_pct": pct_05_90,
        })

    df = pd.DataFrame(rows)

    # --- CSV ---
    csv_path = OUT / "tabla_6_mdes.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n  → CSV: {csv_path}")

    # --- TeX table ---
    tex_df = pd.DataFrame({
        "Outcome": df["label"],
        r"$\hat{\beta}_{TWFE}$": df["coef_twfe"].map(lambda x: f"{x:.4f}"),
        "SE": df["se_twfe"].map(lambda x: f"{x:.4f}"),
        "MDES (asinh)": df["mdes_05_80_asinh"].map(lambda x: f"{x:.4f}"),
        r"MDES ($\approx$ \%)": df["mdes_05_80_pct"].map(lambda x: f"{x:.1f}\\%"),
        "N": df["nobs"].map(lambda x: f"{int(x):,}"),
    }).set_index("Outcome")

    tex_path = OUT / "tabla_6_mdes.tex"
    latex = tex_df.to_latex(
        index=True, escape=False,
        column_format="l" + "c" * len(tex_df.columns),
    )

    lines = [
        r"\begin{table}[htbp]",
        r"\centering",
        r"\small",
        r"\caption{Minimum Detectable Effect Size (MDES) — 80\% poder, $\alpha = 0.05$}",
        r"\label{tab:mdes}",
        latex.strip(),
        r"\vspace{2mm}",
        r"\parbox{\textwidth}{\footnotesize \textit{Nota:} MDES = $(z_{\alpha/2} + z_{\beta}) \times SE$. "
        r"SE del coeficiente TWFE baseline (Tabla 2). "
        r"La columna \% es la aproximación $(\exp(|\text{MDES}|) - 1) \times 100$.}",
        r"\end{table}",
    ]
    tex_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"  → TeX: {tex_path}")

    # --- Summary text ---
    summary_lines = [
        "=" * 60,
        "MDES — Resumen (Minimum Detectable Effect Size)",
        "=" * 60,
        "",
        "Interpretación del resultado nulo:",
        "  Con estos datos (panel municipal-trimestral, N ≈ 41,905 obs,",
        "  ~995 municipios tratados), podemos descartar con 80% de poder",
        "  y α = 0.05 los siguientes efectos del tratamiento:",
        "",
    ]

    for _, row in df.iterrows():
        summary_lines.append(
            f"  • {row['label']}: efectos > {row['mdes_05_80_pct']:.1f}% "
            f"(MDES = {row['mdes_05_80_asinh']:.4f} en escala asinh)"
        )

    summary_lines += [
        "",
        "Esto significa que si una alcaldesa produjera un cambio mayor a",
        f"  ~{df['mdes_05_80_pct'].mean():.0f}% en promedio en los outcomes de",
        "  inclusión financiera femenina, lo habríamos detectado.",
        "",
        "Con α = 0.10 (mayor tolerancia a falso positivo):",
    ]

    for _, row in df.iterrows():
        summary_lines.append(
            f"  • {row['label']}: efectos > {row['mdes_10_80_pct']:.1f}%"
        )

    summary_lines += [
        "",
        "Conclusión: los intervalos de confianza del TWFE ya son informativos",
        "  sobre el rango de efectos que los datos pueden descartar. El resultado",
        "  nulo no es un vacío — es la ausencia de efectos de tamaño relevante.",
        "",
        "Fórmula: MDES = (z_{α/2} + z_{β}) × SE_TWFE",
        "  α = 0.05 bilateral → z = 1.96",
        "  poder = 0.80 → z_β = 0.84",
        "  Factor = 2.80",
    ]

    summary_path = OUT / "mdes_summary.txt"
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")
    print(f"  → Summary: {summary_path}")

    print("\n✓ MDES completado.")


if __name__ == "__main__":
    main()
