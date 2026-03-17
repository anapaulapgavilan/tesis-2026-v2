"""
04_robustness.py -- Tabla 3: Pruebas de robustez.

GUIA PARA EL ASESOR:
  Este script ejecuta 8 pruebas de robustez para verificar que los resultados
  del TWFE baseline no dependen de decisiones metodologicas particulares.
  Cada test cambia UNA dimension y compara con el baseline.

  Tests implementados:
    R1. Escala log1p: usa log(1+y) en vez de asinh. Si los resultados son
        similares, la eleccion de transformacion no importa.
    R2. Winsor + asinh: recorta outliers al p1-p99 antes de asinh.
        Verifica que valores extremos no impulsan los resultados.
    R3. Excluir transiciones: usa alcaldesa_excl_trans (NaN en trimestres de
        cambio de gobierno). Verifica que la medicion del tratamiento es robusta.
    R4. Placebo temporal: adelanta el tratamiento 4 trimestres. Si beta != 0,
        habria "anticipacion" del efecto (amenaza a la identificacion).
    R5. Placebo de genero: estima el efecto sobre outcomes MASCULINOS.
        Si beta != 0 para hombres, el efecto no seria especifico a mujeres.
    R6. Nivel winsorizado: outcome en _pc_w sin transformar (nivel).
        Verifica que la transformacion no oculta efectos en niveles.
    R7. Per capita crudo: outcome en _pc sin ninguna transformacion.
        Analogamente al R6, en escala cruda.
    R8. Absorbing-only: restringe a switchers con tratamiento permanente (0-->1).
        Elimina municipios con tratamientos que se "apagan y prenden".
        Valida la comparacion "limpia" tipo Goodman-Bacon.

Outputs:
  outputs/paper/tabla_3_robustez.csv
  outputs/paper/tabla_3_robustez.tex
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from tesis_alcaldesas.models.utils import (
    load_panel, run_panel_ols,
    PRIMARY_5, OUTCOME_DEFS, OUT,
    coef_str, se_str, stars, export_table_tex,
)


def run_robustness_twfe(df, depvar, treatment, controls=None):
    """Run a TWFE regression and return key stats."""
    if controls is None:
        controls = ["log_pob"]
    exog = [treatment] + controls
    # Verify columns exist
    for c in [depvar] + exog:
        if c not in df.columns:
            return None
    res = run_panel_ols(df, depvar=depvar, exog=exog)
    beta = res.params[treatment]
    se = res.std_errors[treatment]
    pval = res.pvalues[treatment]
    return {"coef": beta, "se": se, "pval": pval, "nobs": res.nobs}


def main():
    print("=" * 60)
    print("04 — Robustez")
    print("=" * 60)

    df = load_panel()

    # We will run all tests on the first primary outcome (ncont_total_m)
    # plus confirm sign on all 5 for key tests
    focus = "ncont_total_m"
    focus_label = OUTCOME_DEFS[focus]["label"]

    rows = []

    # -------------------------------------------------------------------
    # Baseline (for comparison)
    # -------------------------------------------------------------------
    print("\n[Baseline] asinh, alcaldesa_final")
    bl = run_robustness_twfe(df, f"{focus}_pc_asinh", "alcaldesa_final")
    rows.append({
        "Test": "Baseline (asinh)",
        "Outcome": focus_label,
        "Treatment": "alcaldesa\\_final",
        "Coef": coef_str(bl["coef"], bl["pval"]),
        "SE": se_str(bl["se"]),
        "N": f"{bl['nobs']:,}",
        "Nota": "FE mun + per, cluster mun",
    })
    print(f"  β={bl['coef']:.4f}{stars(bl['pval'])}  SE={bl['se']:.4f}")

    # -------------------------------------------------------------------
    # R1. log1p
    # -------------------------------------------------------------------
    print("\n[R1] Escala alternativa: log1p")
    r1 = run_robustness_twfe(df, f"{focus}_pc_log1p", "alcaldesa_final")
    rows.append({
        "Test": "R1: log(1+y)",
        "Outcome": focus_label,
        "Treatment": "alcaldesa\\_final",
        "Coef": coef_str(r1["coef"], r1["pval"]),
        "SE": se_str(r1["se"]),
        "N": f"{r1['nobs']:,}",
        "Nota": "Escala alternativa",
    })
    print(f"  β={r1['coef']:.4f}{stars(r1['pval'])}  SE={r1['se']:.4f}")

    # -------------------------------------------------------------------
    # R2. Winsor p1-p99
    # -------------------------------------------------------------------
    print("\n[R2] Winsor p1-p99 (asinh)")
    # Winsorized _pc_w --> apply asinh on top
    wvar = f"{focus}_pc_w"
    if wvar in df.columns:
        df["_r2_y"] = np.arcsinh(df[wvar])
        r2 = run_robustness_twfe(df, "_r2_y", "alcaldesa_final")
        rows.append({
            "Test": "R2: Winsor p1-p99 + asinh",
            "Outcome": focus_label,
            "Treatment": "alcaldesa\\_final",
            "Coef": coef_str(r2["coef"], r2["pval"]),
            "SE": se_str(r2["se"]),
            "N": f"{r2['nobs']:,}",
            "Nota": "Recorte p1-p99, luego asinh",
        })
        print(f"  β={r2['coef']:.4f}{stars(r2['pval'])}  SE={r2['se']:.4f}")
        df.drop(columns=["_r2_y"], inplace=True)
    else:
        print(f"  [!] {wvar} no encontrada — omitido")

    # -------------------------------------------------------------------
    # R3. Excluir transiciones
    # -------------------------------------------------------------------
    print("\n[R3] Excluir transiciones (alcaldesa_excl_trans)")
    excl_col = "alcaldesa_excl_trans"
    if excl_col in df.columns:
        # This variable has NaN in transition periods --> they drop naturally
        r3 = run_robustness_twfe(df, f"{focus}_pc_asinh", excl_col)
        rows.append({
            "Test": "R3: Excluir transiciones",
            "Outcome": focus_label,
            "Treatment": "alcaldesa\\_excl\\_trans",
            "Coef": coef_str(r3["coef"], r3["pval"]),
            "SE": se_str(r3["se"]),
            "N": f"{r3['nobs']:,}",
            "Nota": "NaN en trimestres de transición --> se excluyen",
        })
        print(f"  β={r3['coef']:.4f}{stars(r3['pval'])}  SE={r3['se']:.4f}  N={r3['nobs']:,}")
    else:
        print(f"  [!] {excl_col} no encontrada — omitido")
        rows.append({
            "Test": "R3: Excluir transiciones",
            "Outcome": focus_label,
            "Treatment": "---",
            "Coef": "---",
            "SE": "---",
            "N": "---",
            "Nota": f"Columna {excl_col} no disponible",
        })

    # -------------------------------------------------------------------
    # R4. Placebo temporal — tratamiento adelantado 4 trimestres
    # -------------------------------------------------------------------
    print("\n[R4] Placebo temporal: tto adelantado 4 trimestres")
    # Create fake treatment: shift alcaldesa_final forward by 4 periods
    df_r4 = df.copy()
    # Reset to get flat frame
    df_r4_flat = df_r4.reset_index()
    df_r4_flat = df_r4_flat.sort_values(["cve_mun", "t_index"])
    df_r4_flat["placebo_tto_f4"] = df_r4_flat.groupby("cve_mun")["alcaldesa_final"].shift(-4)
    df_r4_flat = df_r4_flat.dropna(subset=["placebo_tto_f4"])
    df_r4_flat = df_r4_flat.set_index(["cve_mun", "t_index"])

    r4 = run_robustness_twfe(df_r4_flat, f"{focus}_pc_asinh", "placebo_tto_f4")
    rows.append({
        "Test": "R4: Placebo temporal (+4 trim)",
        "Outcome": focus_label,
        "Treatment": "placebo\\_tto\\_f4",
        "Coef": coef_str(r4["coef"], r4["pval"]),
        "SE": se_str(r4["se"]),
        "N": f"{r4['nobs']:,}",
        "Nota": "Efecto esperado ≈ 0 si no hay anticipación",
    })
    print(f"  β={r4['coef']:.4f}{stars(r4['pval'])}  SE={r4['se']:.4f}  N={r4['nobs']:,}")

    # -------------------------------------------------------------------
    # R5. Placebo de género — outcomes masculinos
    # -------------------------------------------------------------------
    print("\n[R5] Placebo de género: outcomes masculinos")
    # Build asinh of male _pc
    h_pc_col = f"{focus.replace('_m', '_h')}_pc"
    if h_pc_col in df.columns:
        df["_r5_y_h_asinh"] = np.arcsinh(df[h_pc_col])
        r5 = run_robustness_twfe(df, "_r5_y_h_asinh", "alcaldesa_final")
        rows.append({
            "Test": "R5: Placebo género (hombres)",
            "Outcome": f"{focus_label} (H)",
            "Treatment": "alcaldesa\\_final",
            "Coef": coef_str(r5["coef"], r5["pval"]),
            "SE": se_str(r5["se"]),
            "N": f"{r5['nobs']:,}",
            "Nota": "Si β≈0, efecto es específico a mujeres. "
                    "Si β≠0, podría reflejar shock general.",
        })
        print(f"  β={r5['coef']:.4f}{stars(r5['pval'])}  SE={r5['se']:.4f}")
        df.drop(columns=["_r5_y_h_asinh"], inplace=True)
    else:
        print(f"  [!] {h_pc_col} no encontrada")

    # -------------------------------------------------------------------
    # R6. Winsorizada en nivel (sin asinh)
    # -------------------------------------------------------------------
    print("\n[R6] Escala alternativa: _pc_w en nivel (sin transformación)")
    wvar6 = f"{focus}_pc_w"
    if wvar6 in df.columns:
        r6 = run_robustness_twfe(df, wvar6, "alcaldesa_final")
        rows.append({
            "Test": "R6: Winsor p1-p99 (nivel)",
            "Outcome": focus_label,
            "Treatment": "alcaldesa\\_final",
            "Coef": coef_str(r6["coef"], r6["pval"]),
            "SE": se_str(r6["se"]),
            "N": f"{r6['nobs']:,}",
            "Nota": "_pc_w sin transformación funcional",
        })
        print(f"  β={r6['coef']:.4f}{stars(r6['pval'])}  SE={r6['se']:.4f}")
    else:
        print(f"  [!] {wvar6} no encontrada — omitido")

    # -------------------------------------------------------------------
    # R7. Per cápita cruda en nivel (sin ninguna transformación)
    # -------------------------------------------------------------------
    print("\n[R7] Escala alternativa: _pc en nivel crudo")
    pcvar7 = f"{focus}_pc"
    if pcvar7 in df.columns:
        r7 = run_robustness_twfe(df, pcvar7, "alcaldesa_final")
        rows.append({
            "Test": "R7: Per cápita nivel",
            "Outcome": focus_label,
            "Treatment": "alcaldesa\\_final",
            "Coef": coef_str(r7["coef"], r7["pval"]),
            "SE": se_str(r7["se"]),
            "N": f"{r7['nobs']:,}",
            "Nota": "_pc sin ninguna transformación",
        })
        print(f"  β={r7['coef']:.4f}{stars(r7['pval'])}  SE={r7['se']:.4f}")
    else:
        print(f"  [!] {pcvar7} no encontrada — omitido")

    # -------------------------------------------------------------------
    # R6 & R7 for all 5 outcomes (summary)
    # -------------------------------------------------------------------
    print("\n[All 5 outcomes] R6 _pc_w nivel + R7 _pc nivel:")
    for out_name in PRIMARY_5:
        lbl = OUTCOME_DEFS[out_name]["label"]
        # R6
        w_col = f"{out_name}_pc_w"
        if w_col in df.columns:
            r6_i = run_robustness_twfe(df, w_col, "alcaldesa_final")
            if r6_i:
                print(f"  R6 {lbl:25s}: β={r6_i['coef']:+.4f}{stars(r6_i['pval'])}")
        # R7
        pc_col = f"{out_name}_pc"
        if pc_col in df.columns:
            r7_i = run_robustness_twfe(df, pc_col, "alcaldesa_final")
            if r7_i:
                print(f"  R7 {lbl:25s}: β={r7_i['coef']:+.4f}{stars(r7_i['pval'])}")

    # -------------------------------------------------------------------
    # R8. Absorbing-only: restrict to switchers with clean 0-->1 treatment
    # -------------------------------------------------------------------
    print("\n[R8] Absorbing-only: solo switchers 0-->1 permanente + never-treated")
    df_flat = df.reset_index()
    sw = df_flat[df_flat["cohort_type"] == "switcher"]
    absorbing_muns = set()
    for mun, grp in sw.groupby("cve_mun"):
        seq = grp.sort_values("t_index")["alcaldesa_final"].values
        first_t = grp["first_treat_t"].iloc[0]
        if first_t == 0:
            continue  # left-censored
        # Check: once treatment turns on, does it stay on?
        t_indices = grp.sort_values("t_index")["t_index"].values
        post = seq[t_indices >= first_t]
        if len(post) > 0 and all(post == 1):
            absorbing_muns.add(mun)

    # Keep absorbing switchers + never-treated
    keep = df_flat["cve_mun"].isin(
        absorbing_muns | set(df_flat.loc[df_flat["cohort_type"] == "never-treated", "cve_mun"].unique())
    )
    df_r8 = df_flat[keep].set_index(["cve_mun", "t_index"])
    print(f"  Absorbing switchers: {len(absorbing_muns)}")
    print(f"  Panel N: {len(df_r8):,}")

    r8 = run_robustness_twfe(df_r8, f"{focus}_pc_asinh", "alcaldesa_final")
    rows.append({
        "Test": "R8: Absorbing-only (0-->1 perm.)",
        "Outcome": focus_label,
        "Treatment": "alcaldesa\\_final",
        "Coef": coef_str(r8["coef"], r8["pval"]),
        "SE": se_str(r8["se"]),
        "N": f"{r8['nobs']:,}",
        "Nota": f"Solo {len(absorbing_muns)} switchers absorbentes + never-treated",
    })
    print(f"  β={r8['coef']:.4f}{stars(r8['pval'])}  SE={r8['se']:.4f}  N={r8['nobs']:,}")

    # R8 for all 5 outcomes
    print("\n[All 5 outcomes] R8 absorbing-only:")
    for out_name in PRIMARY_5:
        depvar_r8 = f"{out_name}_pc_asinh"
        lbl = OUTCOME_DEFS[out_name]["label"]
        r8_i = run_robustness_twfe(df_r8, depvar_r8, "alcaldesa_final")
        if r8_i:
            print(f"  R8 {lbl:25s}: β={r8_i['coef']:+.4f}{stars(r8_i['pval'])}")

    # -------------------------------------------------------------------
    # Repeat baseline for all 5 outcomes (summary row)
    # -------------------------------------------------------------------
    print("\n[All 5 outcomes] Baseline asinh — signo y significancia:")
    for out_name in PRIMARY_5:
        depvar = f"{out_name}_pc_asinh"
        res = run_robustness_twfe(df, depvar, "alcaldesa_final")
        lbl = OUTCOME_DEFS[out_name]["label"]
        sig = stars(res["pval"])
        print(f"  {lbl:25s}: β={res['coef']:+.4f}{sig}")

    # -------------------------------------------------------------------
    # Build table
    # -------------------------------------------------------------------
    tab = pd.DataFrame(rows).set_index("Test")
    print("\n" + "=" * 60)
    print("TABLA 3 — Robustez")
    print("=" * 60)
    print(tab.to_string())

    # CSV
    csv_path = OUT / "tabla_3_robustez.csv"
    tab.to_csv(csv_path)
    print(f"\n  --> CSV: {csv_path}")

    # LaTeX
    tex_path = OUT / "tabla_3_robustez.tex"
    export_table_tex(
        tab, tex_path,
        caption="Pruebas de robustez — efecto TWFE sobre contratos totales mujeres",
        label="tab:robustness",
        note="Todas las especificaciones incluyen FE municipio + FE período y "
             "errores estándar clusterizados a nivel municipio. "
             "R1: escala log(1+y) en lugar de asinh. "
             "R2: per cápita winsorizado p1-p99, luego asinh. "
             "R3: tto = alcaldesa\\_excl\\_trans (NaN en trimestres de transición). "
             "R4: tratamiento adelantado 4 trimestres (placebo temporal). "
             "R5: same spec, outcome masculino (placebo de género). "
             "R6: per cápita winsorizado p1-p99 en nivel (sin asinh). "
             "R7: per cápita crudo en nivel (sin transformación). "
             "R8: solo switchers absorbentes (0-->1 permanente) + never-treated. "
             "*** p<0.01, ** p<0.05, * p<0.10.",
    )

    print("\nDone.")


if __name__ == "__main__":
    main()
