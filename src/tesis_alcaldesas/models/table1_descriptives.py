"""
01_table1_descriptives.py — Tabla 1: Estadísticos descriptivos pre-tratamiento.

Compara promedios en el periodo pre-tratamiento (o todo el panel para never-treated)
por grupo: never-treated, switchers, always-treated.

Outputs:
  outputs/paper/tabla_1_descriptiva.csv
  outputs/paper/tabla_1_descriptiva.tex
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from tesis_alcaldesas.models.utils import load_panel, PRIMARY_5, OUTCOME_DEFS, OUT, export_table_tex


def main():
    print("=" * 60)
    print("01 — Tabla 1: Estadísticos descriptivos")
    print("=" * 60)

    df = load_panel()

    # -------------------------------------------------------------------
    # Pre-treatment sample:
    #   - never-treated: all periods
    #   - switchers: periods before first treatment (event_time < 0)
    #   - always-treated: no pre-periods, use all periods (flagged)
    # -------------------------------------------------------------------
    mask_never = df["cohort_type"] == "never-treated"
    mask_switch_pre = (df["cohort_type"] == "switcher") & (df["event_time"] < 0)
    mask_always = df["cohort_type"] == "always-treated"

    groups = {
        "Never-treated": df.loc[mask_never],
        "Switchers (pre)": df.loc[mask_switch_pre],
        "Always-treated": df.loc[mask_always],
    }

    # Variables to describe
    vars_desc = {
        # Treatment
        "alcaldesa_final": "Alcaldesa (D)",
        # Population
        "log_pob": "ln(Población)",
        "pob_adulta_m": "Pob. adulta mujeres",
    }
    # Add primary 5 outcomes in asinh
    for out in PRIMARY_5:
        vars_desc[f"{out}_pc_asinh"] = f"{OUTCOME_DEFS[out]['label']} (asinh)"
        vars_desc[f"{out}_pc"] = f"{OUTCOME_DEFS[out]['label']} (pc)"

    # -------------------------------------------------------------------
    # Build table
    # -------------------------------------------------------------------
    rows = []
    for var, label in vars_desc.items():
        row = {"Variable": label}
        for gname, gdf in groups.items():
            if var in gdf.columns:
                vals = gdf[var].dropna()
                row[f"{gname} Mean"] = vals.mean()
                row[f"{gname} SD"] = vals.std()
                row[f"{gname} N"] = len(vals)
            else:
                row[f"{gname} Mean"] = np.nan
                row[f"{gname} SD"] = np.nan
                row[f"{gname} N"] = 0
        rows.append(row)

    # Add N municipalities
    mun_row = {"Variable": "N municipios"}
    for gname, gdf in groups.items():
        mun_row[f"{gname} Mean"] = gdf.reset_index()["cve_mun"].nunique()
        mun_row[f"{gname} SD"] = ""
        mun_row[f"{gname} N"] = ""
    rows.append(mun_row)

    tab = pd.DataFrame(rows).set_index("Variable")

    # -------------------------------------------------------------------
    # Print
    # -------------------------------------------------------------------
    print("\n" + tab.to_string())

    # -------------------------------------------------------------------
    # Export CSV
    # -------------------------------------------------------------------
    csv_path = OUT / "tabla_1_descriptiva.csv"
    tab.to_csv(csv_path)
    print(f"\n  → CSV: {csv_path}")

    # -------------------------------------------------------------------
    # Export LaTeX (formatted)
    # -------------------------------------------------------------------
    # Build a nicer version for LaTeX
    tex_rows = []
    for var, label in vars_desc.items():
        row_tex = {"Variable": label}
        for gname, gdf in groups.items():
            if var in gdf.columns:
                vals = gdf[var].dropna()
                mu = vals.mean()
                sd = vals.std()
                # Smart formatting
                if abs(mu) > 1e6:
                    row_tex[gname] = f"{mu:,.0f} ({sd:,.0f})"
                elif abs(mu) > 100:
                    row_tex[gname] = f"{mu:,.1f} ({sd:,.1f})"
                else:
                    row_tex[gname] = f"{mu:.3f} ({sd:.3f})"
            else:
                row_tex[gname] = "---"
        tex_rows.append(row_tex)

    tex_rows.append({
        "Variable": "N municipios",
        **{gname: str(gdf.reset_index()["cve_mun"].nunique()) for gname, gdf in groups.items()},
    })
    tex_rows.append({
        "Variable": "N obs (grupo)",
        **{gname: f"{len(gdf):,}" for gname, gdf in groups.items()},
    })

    tab_tex = pd.DataFrame(tex_rows).set_index("Variable")

    tex_path = OUT / "tabla_1_descriptiva.tex"
    export_table_tex(
        tab_tex, tex_path,
        caption="Estadísticos descriptivos por grupo de tratamiento (pre-tratamiento)",
        label="tab:descriptives",
        note="Media (desv. est.). Switchers evaluados en períodos pre-tratamiento. "
             "Always-treated no tienen pre-período; se reportan todos sus períodos. "
             "Outcomes en escala asinh y per cápita (×10,000 mujeres adultas).",
    )

    print("\nDone.")


if __name__ == "__main__":
    main()
