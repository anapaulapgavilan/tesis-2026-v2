#!/usr/bin/env python3
"""
src/eda/run_eda.py — Pipeline completo de Análisis Exploratorio de Datos
=======================================================================
Tesis: Efecto de la representación política municipal (alcaldesas) sobre
       la inclusión financiera de las mujeres en México.

Uso:
    python -m src.eda.run_eda          # desde la raíz del proyecto
    python src/eda/run_eda.py          # directo

Outputs --> outputs/eda/
    ├── A_diccionario_observado.csv
    ├── B_calidad_integridad.csv
    ├── B_completitud_panel.csv
    ├── C_dist_*.png                   (univariados)
    ├── D_biv_*.png                    (bivariados)
    ├── E_sesgo_leakage.csv
    ├── F_recomendaciones.csv
    └── README.md
"""

# ── Imports ──────────────────────────────────────────────────────────────────
import warnings
warnings.filterwarnings("ignore")

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns

# ── Configuración ────────────────────────────────────────────────────────────
SEED = 42
np.random.seed(SEED)

ROOT = Path(__file__).resolve().parents[2]          # …/Code
OUT  = ROOT / "outputs" / "eda"
OUT.mkdir(parents=True, exist_ok=True)

# Carga de datos desde CSV (antes: PostgreSQL).
from tesis_alcaldesas.config import load_csv  # noqa: E402
TABLE = "inclusion_financiera"

# ── Estilo de gráficos ──────────────────────────────────────────────────────
sns.set_theme(style="whitegrid", context="notebook", font_scale=1.1)
plt.rcParams.update({
    "figure.figsize": (10, 5),
    "figure.dpi": 140,
    "axes.titlesize": 14,
    "axes.labelsize": 12,
    "savefig.bbox": "tight",
    "savefig.dpi": 200,
})
PAL = sns.color_palette("Set2")

# ── Variables de interés (constantes del análisis) ───────────────────────────
# Tratamiento
TREATMENT = "alcaldesa_final"

# Outcomes clave — contratos por 10K mujeres adultas
OUTCOME_COLS_M = [
    "ncont_ahorro_m", "ncont_plazo_m", "ncont_n1_m", "ncont_n2_m",
    "ncont_n3_m", "ncont_tradic_m", "ncont_total_m",
    "numtar_deb_m", "numtar_cred_m", "numcontcred_hip_m",
]
OUTCOME_COLS_H = [c.replace("_m", "_h") for c in OUTCOME_COLS_M]

# Controles
CONTROL_COLS = ["pob", "pob_adulta", "pob_adulta_m", "pob_adulta_h", "tipo_pob"]

# Panel keys
PK = ["cve_mun", "periodo_trimestre"]

# ═════════════════════════════════════════════════════════════════════════════
# HELPERS
# ═════════════════════════════════════════════════════════════════════════════

def _save_fig(fig, name: str) -> Path:
    """Guarda figura en outputs/eda/ y cierra."""
    path = OUT / f"{name}.png"
    fig.savefig(path, facecolor="white")
    plt.close(fig)
    print(f"  📊 {path.name}")
    return path


def _save_csv(df: pd.DataFrame, name: str) -> Path:
    """Guarda CSV en outputs/eda/."""
    path = OUT / f"{name}.csv"
    df.to_csv(path, index=False)
    print(f"  📄 {path.name}")
    return path


def _per_capita(df: pd.DataFrame, cols: list, denom: str, k: int = 10_000):
    """Tasa per cápita (×k) con protección de ÷0."""
    out = pd.DataFrame(index=df.index)
    for c in cols:
        short = c.replace("ncont_", "").replace("numtar_", "t_").replace("numcontcred_", "cr_")
        out[f"{short}_pc"] = df[c] * k / df[denom].replace(0, np.nan)
    return out


# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN A — DICCIONARIO OBSERVADO
# ═════════════════════════════════════════════════════════════════════════════

def seccion_a(df: pd.DataFrame) -> pd.DataFrame:
    """Genera tabla resumen por variable: tipo, NA%, n_unique, min/p50/max."""
    print("\n══ A. Diccionario observado ══")
    records = []
    for col in df.columns:
        s = df[col]
        rec = {
            "variable": col,
            "dtype": str(s.dtype),
            "na_n": int(s.isna().sum()),
            "na_pct": round(s.isna().mean() * 100, 2),
            "n_unique": int(s.nunique()),
        }
        if pd.api.types.is_numeric_dtype(s):
            desc = s.describe()
            rec["min"]  = desc.get("min")
            rec["p25"]  = desc.get("25%")
            rec["p50"]  = desc.get("50%")
            rec["p75"]  = desc.get("75%")
            rec["max"]  = desc.get("max")
            rec["mean"] = round(s.mean(), 4) if s.notna().any() else None
            rec["std"]  = round(s.std(), 4)  if s.notna().any() else None
            rec["cv"]   = round(s.std() / s.mean(), 2) if s.mean() != 0 and s.notna().any() else None
        else:
            rec["top"]   = s.mode().iloc[0] if not s.mode().empty else None
            rec["top_n"] = int((s == rec.get("top")).sum()) if rec.get("top") is not None else None
        records.append(rec)

    cat = pd.DataFrame(records)

    # Agregar comentarios automáticos
    comments = []
    for _, r in cat.iterrows():
        c = []
        if r["na_pct"] > 60:
            c.append("[!] >60% NA")
        if r["n_unique"] <= 1:
            c.append("constante")
        if r.get("cv") is not None and r["cv"] > 5:
            c.append("alta dispersión")
        if r.get("min") is not None and r["min"] < 0:
            c.append("valores negativos")
        comments.append("; ".join(c) if c else "")
    cat["comentario"] = comments

    _save_csv(cat, "A_diccionario_observado")
    print(f"  --> {len(cat)} variables perfiladas")
    return cat


# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN B — CALIDAD E INTEGRIDAD
# ═════════════════════════════════════════════════════════════════════════════

def seccion_b(df: pd.DataFrame) -> dict:
    """Validación de duplicados, integridad referencial, completitud."""
    print("\n══ B. Calidad e integridad ══")
    results = {}

    # B1. Duplicados en llave primaria
    dup = df.duplicated(PK).sum()
    print(f"  Duplicados en PK {PK}: {dup}")
    results["duplicados_pk"] = dup

    # B2. Completitud del panel (cada municipio debe tener 17 trimestres)
    panel = df.groupby("cve_mun")["periodo_trimestre"].nunique().reset_index()
    panel.columns = ["cve_mun", "n_trimestres"]
    panel["completo"] = panel["n_trimestres"] == 17
    results["panel_balance"] = panel["completo"].all()
    print(f"  Panel balanceado: {panel['completo'].all()} "
          f"({panel['completo'].sum()}/{len(panel)} municipios con 17 trimestres)")

    # B3. Completitud por periodo (filas por trimestre)
    by_period = df.groupby("periodo_trimestre").agg(
        n_mun=("cve_mun", "nunique"),
        n_rows=("cve_mun", "size"),
        pct_alcaldesa=(TREATMENT, "mean"),
    ).reset_index()
    by_period["pct_alcaldesa"] = (by_period["pct_alcaldesa"] * 100).round(1)
    _save_csv(by_period, "B_completitud_panel")

    # B4. Consistencia geográfica (municipio no cambia de estado)
    mun_estado = df.groupby("cve_mun")["estado"].nunique()
    inconsist_geo = (mun_estado > 1).sum()
    print(f"  Municipios que cambian de estado: {inconsist_geo}")
    results["inconsistencia_geo"] = inconsist_geo

    # B5. Tipo_pob NULLs
    tipo_na = df["tipo_pob"].isna().sum()
    print(f"  NULLs en tipo_pob: {tipo_na}")
    results["tipo_pob_na"] = tipo_na

    # B6. Rangos temporales
    periodos = sorted(df["periodo_trimestre"].unique())
    print(f"  Periodos: {periodos[0]} — {periodos[-1]} ({len(periodos)} trimestres)")
    results["periodo_min"] = periodos[0]
    results["periodo_max"] = periodos[-1]
    results["n_periodos"] = len(periodos)

    # B7. Conteos negativos (no debería haber)
    num_cols = df.select_dtypes("number").columns
    neg_cols = [(c, int((df[c] < 0).sum())) for c in num_cols if (df[c] < 0).any()]
    print(f"  Columnas con valores negativos: {len(neg_cols)}")
    results["cols_negativos"] = neg_cols

    # Tabla resumen de calidad
    quality = pd.DataFrame([
        {"check": "Duplicados PK", "resultado": dup, "status": "OK" if dup == 0 else "FAIL"},
        {"check": "Panel 100% balanceado", "resultado": str(panel["completo"].all()), "status": "OK" if panel["completo"].all() else "FAIL"},
        {"check": "Municipios cambian estado", "resultado": inconsist_geo, "status": "OK" if inconsist_geo == 0 else "FAIL"},
        {"check": "NULLs en tipo_pob", "resultado": tipo_na, "status": "[!]" if tipo_na > 0 else "OK"},
        {"check": "Columnas con negativos", "resultado": len(neg_cols), "status": "OK" if len(neg_cols) == 0 else "FAIL"},
        {"check": "Periodos cubiertos", "resultado": f"{periodos[0]}–{periodos[-1]} ({len(periodos)})", "status": "OK"},
    ])
    _save_csv(quality, "B_calidad_integridad")

    return results


# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN C — DISTRIBUCIONES UNIVARIADAS
# ═════════════════════════════════════════════════════════════════════════════

def seccion_c(df: pd.DataFrame):
    """Histogramas/boxplots para numéricas clave, barras para categóricas."""
    print("\n══ C. Distribuciones univariadas ══")

    # ── C1. Distribución del tratamiento por trimestre ────────────────────────
    fig, ax = plt.subplots(figsize=(12, 5))
    treat_ts = df.groupby("periodo_trimestre")[TREATMENT].mean() * 100
    treat_ts = treat_ts.reindex(sorted(treat_ts.index))
    ax.plot(range(len(treat_ts)), treat_ts.values, "o-", color=PAL[0], lw=2)
    ax.set_xticks(range(len(treat_ts)))
    ax.set_xticklabels(treat_ts.index, rotation=45, ha="right")
    ax.set_ylabel("% municipios con alcaldesa")
    ax.set_title("C1. Proporción de alcaldesas por trimestre")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter())
    _save_fig(fig, "C1_tratamiento_por_trimestre")

    # ── C2. Distribución de población (log scale) ────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    for ax, col, title in zip(axes, ["pob", "pob_adulta_m"],
                               ["Población total", "Pob. adulta mujeres"]):
        data = df[col].dropna()
        ax.hist(np.log1p(data), bins=60, color=PAL[1], edgecolor="white", alpha=0.8)
        ax.set_xlabel(f"log(1 + {col})")
        ax.set_title(f"C2. {title} (log)")
    fig.tight_layout()
    _save_fig(fig, "C2_distribucion_poblacion")

    # ── C3. Boxplot de outcomes per cápita (mujeres) ─────────────────────────
    pc = _per_capita(df, OUTCOME_COLS_M, "pob_adulta_m")
    fig, ax = plt.subplots(figsize=(14, 6))
    pc_melt = pc.melt(var_name="variable", value_name="per_10k")
    sns.boxplot(data=pc_melt, x="variable", y="per_10k", palette=PAL, ax=ax,
                showfliers=False)
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right")
    ax.set_title("C3. Outcomes inclusión financiera mujeres (por 10K adultas)")
    ax.set_ylabel("Contratos / 10K mujeres adultas")
    _save_fig(fig, "C3_boxplot_outcomes_mujeres_pc")

    # ── C4. Barras de categóricas clave ──────────────────────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))

    # Región
    order_r = df["region"].value_counts().index
    sns.countplot(data=df.drop_duplicates("cve_mun"), y="region",
                  order=order_r, palette=PAL, ax=axes[0])
    axes[0].set_title("C4a. Municipios por región")
    axes[0].set_xlabel("Nº municipios")

    # Tipo población
    order_t = df["tipo_pob"].value_counts().index
    sns.countplot(data=df.drop_duplicates("cve_mun"), y="tipo_pob",
                  order=order_t, palette=PAL, ax=axes[1])
    axes[1].set_title("C4b. Municipios por tipo de población")
    axes[1].set_xlabel("Nº municipios")

    # Top 10 estados por nº municipios
    top_est = df.drop_duplicates("cve_mun")["estado"].value_counts().head(10).index
    sns.countplot(data=df.drop_duplicates("cve_mun").query("estado in @top_est"),
                  y="estado", order=top_est, palette=PAL, ax=axes[2])
    axes[2].set_title("C4c. Top 10 estados (nº municipios)")
    axes[2].set_xlabel("Nº municipios")

    fig.tight_layout()
    _save_fig(fig, "C4_categoricas_clave")

    # ── C5. Histograma de tipo de municipio por tratamiento ──────────────────
    fig, ax = plt.subplots(figsize=(10, 5))
    treat_labels = {0: "Sin alcaldesa", 1: "Con alcaldesa"}
    mun_data = df.drop_duplicates("cve_mun")
    ct = pd.crosstab(mun_data["tipo_pob"],
                     mun_data.groupby("cve_mun")[TREATMENT].transform("max"),
                     normalize="index") * 100
    ct.plot(kind="barh", stacked=True, color=[PAL[3], PAL[0]], ax=ax)
    ax.set_xlabel("% municipios")
    ax.set_title("C5. Tipo de población × alguna vez con alcaldesa")
    ax.legend(["Nunca alcaldesa", "Al menos 1 trim con alcaldesa"])
    _save_fig(fig, "C5_tipo_pob_tratamiento")


# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN D — RELACIONES BIVARIADAS (alineadas a la pregunta)
# ═════════════════════════════════════════════════════════════════════════════

def seccion_d(df: pd.DataFrame):
    """Comparaciones clave por tratamiento, correlaciones, tendencias."""
    print("\n══ D. Relaciones bivariadas ══")

    # ── D1. Outcomes per cápita: alcaldesa vs no alcaldesa (boxplot) ──────────
    pc_m = _per_capita(df, OUTCOME_COLS_M, "pob_adulta_m")
    pc_m[TREATMENT] = df[TREATMENT].values

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    key_outcomes = ["ahorro_m_pc", "total_m_pc", "t_deb_m_pc",
                    "t_cred_m_pc", "cr_hip_m_pc", "plazo_m_pc"]
    for ax, col in zip(axes.flat, key_outcomes):
        if col in pc_m.columns:
            sns.boxplot(data=pc_m, x=TREATMENT, y=col, palette=[PAL[3], PAL[0]],
                        showfliers=False, ax=ax)
            ax.set_title(col)
            ax.set_xticklabels(["Sin alcaldesa", "Con alcaldesa"])
    fig.suptitle("D1. Distribución de outcomes (per cápita) por tratamiento",
                 fontsize=15, y=1.02)
    fig.tight_layout()
    _save_fig(fig, "D1_outcomes_por_tratamiento")

    # ── D2. Tendencia temporal: outcomes mujeres vs hombres ──────────────────
    df_ts = df.copy()
    for c in OUTCOME_COLS_M:
        short = c.replace("ncont_", "").replace("numtar_", "t_").replace("numcontcred_", "cr_")
        df_ts[f"{short}_pc"] = df_ts[c] * 10_000 / df_ts["pob_adulta_m"].replace(0, np.nan)
    for c in OUTCOME_COLS_H:
        short = c.replace("ncont_", "").replace("numtar_", "t_").replace("numcontcred_", "cr_")
        df_ts[f"{short}_pc"] = df_ts[c] * 10_000 / df_ts["pob_adulta_h"].replace(0, np.nan)

    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    pairs = [
        ("total_m_pc", "total_h_pc", "Contratos totales"),
        ("ahorro_m_pc", "ahorro_h_pc", "Contratos ahorro"),
        ("t_deb_m_pc", "t_deb_h_pc", "Tarjetas débito"),
        ("t_cred_m_pc", "t_cred_h_pc", "Tarjetas crédito"),
        ("cr_hip_m_pc", "cr_hip_h_pc", "Créditos hipotecarios"),
        ("plazo_m_pc", "plazo_h_pc", "Depósitos a plazo"),
    ]
    for ax, (cm, ch, title) in zip(axes.flat, pairs):
        if cm in df_ts.columns and ch in df_ts.columns:
            ts_m = df_ts.groupby("periodo_trimestre")[cm].mean()
            ts_h = df_ts.groupby("periodo_trimestre")[ch].mean()
            ts_m = ts_m.reindex(sorted(ts_m.index))
            ts_h = ts_h.reindex(sorted(ts_h.index))
            ax.plot(range(len(ts_m)), ts_m.values, "o-", color=PAL[0], label="Mujeres", lw=2)
            ax.plot(range(len(ts_h)), ts_h.values, "s--", color=PAL[1], label="Hombres", lw=2)
            ax.set_xticks(range(0, len(ts_m), 4))
            ax.set_xticklabels([ts_m.index[i] for i in range(0, len(ts_m), 4)], rotation=45)
            ax.set_title(title)
            ax.legend(fontsize=8)
    fig.suptitle("D2. Brecha de género en inclusión financiera (per cápita, ×10K)",
                 fontsize=15, y=1.02)
    fig.tight_layout()
    _save_fig(fig, "D2_brecha_genero_temporal")

    # ── D3. Tendencia por tratamiento: pre/post alcaldesa ────────────────────
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    key_pc = ["total_m_pc", "t_deb_m_pc", "ahorro_m_pc"]
    titles = ["Contratos totales (M)", "Tarjetas débito (M)", "Ahorro (M)"]
    for ax, col, title in zip(axes, key_pc, titles):
        if col in df_ts.columns:
            for treat_val, label, color, ls in [(0, "Sin alcaldesa", PAL[3], "--"),
                                                  (1, "Con alcaldesa", PAL[0], "-")]:
                sub = df_ts[df_ts[TREATMENT] == treat_val]
                ts = sub.groupby("periodo_trimestre")[col].mean()
                ts = ts.reindex(sorted(ts.index))
                ax.plot(range(len(ts)), ts.values, f"o{ls}", color=color,
                        label=label, lw=2, markersize=4)
            ax.set_xticks(range(0, len(ts), 4))
            ax.set_xticklabels([ts.index[i] for i in range(0, len(ts), 4)], rotation=45)
            ax.set_title(title)
            ax.legend(fontsize=8)
    fig.suptitle("D3. Tendencia de outcomes por tratamiento (per cápita, ×10K)",
                 fontsize=15, y=1.02)
    fig.tight_layout()
    _save_fig(fig, "D3_tendencia_por_tratamiento")

    # ── D4. Brecha de género (ratio M/H) por tratamiento ────────────────────
    for c in OUTCOME_COLS_M:
        short = c.replace("ncont_", "").replace("numtar_", "t_").replace("numcontcred_", "cr_")
        h_col = c.replace("_m", "_h")
        df_ts[f"ratio_mh_{short}"] = df_ts[c] / df_ts[h_col].replace(0, np.nan)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    ratios = ["ratio_mh_total_m", "ratio_mh_t_deb_m", "ratio_mh_ahorro_m"]
    titles = ["Contratos totales M/H", "Tarjetas débito M/H", "Ahorro M/H"]
    for ax, col, title in zip(axes, ratios, titles):
        if col in df_ts.columns:
            for treat_val, label, color, ls in [(0, "Sin alcaldesa", PAL[3], "--"),
                                                  (1, "Con alcaldesa", PAL[0], "-")]:
                sub = df_ts[df_ts[TREATMENT] == treat_val]
                ts = sub.groupby("periodo_trimestre")[col].median()
                ts = ts.reindex(sorted(ts.index))
                ax.plot(range(len(ts)), ts.values, f"o{ls}", color=color,
                        label=label, lw=2, markersize=4)
            ax.axhline(1, color="grey", ls=":", alpha=0.5)
            ax.set_xticks(range(0, len(ts), 4))
            ax.set_xticklabels([ts.index[i] for i in range(0, len(ts), 4)], rotation=45)
            ax.set_title(title)
            ax.set_ylabel("Ratio Mujer / Hombre")
            ax.legend(fontsize=8)
    fig.suptitle("D4. Ratio M/H de inclusión financiera por tratamiento",
                 fontsize=15, y=1.02)
    fig.tight_layout()
    _save_fig(fig, "D4_ratio_MH_por_tratamiento")

    # ── D5. Correlación entre outcomes, controles y tratamiento ──────────────
    corr_cols = [TREATMENT, "pob", "pob_adulta_m"] + OUTCOME_COLS_M[:7]
    corr = df[corr_cols].corr(method="spearman")
    fig, ax = plt.subplots(figsize=(10, 8))
    mask = np.triu(np.ones_like(corr, dtype=bool))
    sns.heatmap(corr, mask=mask, annot=True, fmt=".2f", cmap="RdBu_r",
                center=0, ax=ax, square=True, linewidths=0.5)
    ax.set_title("D5. Correlaciones de Spearman (tratamiento + outcomes + controles)")
    _save_fig(fig, "D5_correlaciones_spearman")

    # ── D6. Switchers: balance pre-tratamiento ──────────────────────────────
    # Identificar municipios que cambian de tratamiento (switchers)
    switcher_status = df.groupby("cve_mun")[TREATMENT].agg(["min", "max"])
    switcher_status["tipo"] = np.where(
        switcher_status["min"] == switcher_status["max"],
        np.where(switcher_status["min"] == 0, "Nunca", "Siempre"),
        "Switcher"
    )
    df_bal = df.merge(switcher_status[["tipo"]], left_on="cve_mun", right_index=True)

    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    bal_vars = ["pob", "pob_adulta_m", "ncont_total_m"]
    bal_titles = ["Población total", "Pob. adulta mujeres", "Contratos totales (M)"]
    # Solo primer periodo para balance baseline
    baseline = df_bal[df_bal["periodo_trimestre"] == df_bal["periodo_trimestre"].min()]
    for ax, var, title in zip(axes, bal_vars, bal_titles):
        sns.boxplot(data=baseline, x="tipo", y=var, palette=PAL,
                    order=["Nunca", "Switcher", "Siempre"], showfliers=False, ax=ax)
        ax.set_title(f"D6. {title} (baseline)")
        ax.set_ylabel(var)
    fig.suptitle("D6. Balance pre-tratamiento: Nunca vs Switcher vs Siempre alcaldesa",
                 fontsize=15, y=1.02)
    fig.tight_layout()
    _save_fig(fig, "D6_balance_pre_tratamiento")


# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN E — CHEQUEOS DE SESGO / LEAKAGE
# ═════════════════════════════════════════════════════════════════════════════

def seccion_e(df: pd.DataFrame) -> pd.DataFrame:
    """Identifica variables que podrían ser leakage o definidas post-hoc."""
    print("\n══ E. Chequeos de sesgo / leakage ══")

    checks = []

    # E1. Adelantos (forwards) --> usan información futura
    forward_cols = [c for c in df.columns if "_f1" in c or "_f2" in c or "_f3" in c]
    for c in forward_cols:
        checks.append({
            "variable": c,
            "tipo_riesgo": "leakage_temporal",
            "razon": f"Adelanto (forward) de tratamiento — usa información de t+k. "
                     "NO usar como control; solo para test de pre-trends (event study).",
            "accion": "EXCLUIR de regresiones causales como regresor"
        })

    # E2. Transiciones — potencialmente endógenas
    trans_cols = [c for c in df.columns if "transition" in c]
    for c in trans_cols:
        checks.append({
            "variable": c,
            "tipo_riesgo": "endogeneidad",
            "razon": "Transición de gobierno puede estar correlacionada con outcomes. "
                     "Contemporánea al tratamiento.",
            "accion": "Usar variantes *_excl_trans como robustez, no como control principal"
        })

    # E3. Variables de calidad del panel — artefactos de construcción
    quality_cols = ["hist_mun_available", "hist_state_available",
                    "ok_panel_completo", "ok_panel_completo_final",
                    "missing_quarters_alcaldesa", "filled_by_manual",
                    "quarters_in_base"]
    for c in quality_cols:
        if c in df.columns:
            checks.append({
                "variable": c,
                "tipo_riesgo": "artefacto_construccion",
                "razon": "Variable de calidad/proceso de construcción, no confusor causal.",
                "accion": "NO usar como control (no existía antes del tratamiento)"
            })

    # E4. Columnas constantes
    const_cols = [c for c in df.select_dtypes("number").columns if df[c].std() == 0]
    for c in const_cols:
        checks.append({
            "variable": c,
            "tipo_riesgo": "constante",
            "razon": "Varianza = 0 --> no aporta información.",
            "accion": "EXCLUIR de regresiones"
        })

    # E5. Flags de missingness — no confusores
    flag_cols = [c for c in df.columns if c.startswith("flag_undef_")]
    for c in flag_cols:
        checks.append({
            "variable": c,
            "tipo_riesgo": "flag_proceso",
            "razon": "Flag de missingness estructural (÷0). Útil para filtrar, no como control.",
            "accion": "Usar solo para filtrar muestras, no como regresor"
        })

    # E6. Rezagos del tratamiento — válidos para event study pero cuidado
    lag_cols = [c for c in df.columns if "_l1" in c or "_l2" in c or "_l3" in c]
    lag_cols = [c for c in lag_cols if "alcaldesa" in c]
    for c in lag_cols:
        checks.append({
            "variable": c,
            "tipo_riesgo": "lag_tratamiento",
            "razon": "Rezago del tratamiento — válido para event study / efectos dinámicos. "
                     "No usar como control independiente.",
            "accion": "Usar SOLO en especificación de event study"
        })

    leakage_df = pd.DataFrame(checks)
    _save_csv(leakage_df, "E_sesgo_leakage")
    print(f"  --> {len(checks)} variables con riesgo de sesgo/leakage identificadas")

    # Resumen por tipo
    if len(leakage_df) > 0:
        print(leakage_df.groupby("tipo_riesgo").size().to_string())

    return leakage_df


# ═════════════════════════════════════════════════════════════════════════════
# SECCIÓN F — RECOMENDACIONES DE LIMPIEZA / TRANSFORMACIONES
# ═════════════════════════════════════════════════════════════════════════════

def seccion_f(df: pd.DataFrame) -> pd.DataFrame:
    """Recomendaciones de transformaciones orientadas a inferencia causal."""
    print("\n══ F. Recomendaciones de limpieza / transformaciones ══")

    recs = [
        # ── Normalización ──
        {
            "categoria": "Normalización",
            "variable(s)": "ncont_*, numtar_*, numcontcred_*",
            "transformacion": "Per cápita: dividir entre pob_adulta_m (mujeres) o pob_adulta_h (hombres) × 10,000",
            "razon": "La inclusión financiera en niveles está altamente correlacionada con población (r=0.67–0.70). "
                     "Comparar municipios de distinto tamaño requiere normalización.",
            "prioridad": "CRÍTICA"
        },
        {
            "categoria": "Normalización",
            "variable(s)": "saldocont_*",
            "transformacion": "Per cápita: dividir entre pob_adulta_* × 10,000",
            "razon": "Saldos monetarios escalan con población. Alternativamente, saldo promedio (saldoprom_*) "
                     "ya está normalizado pero tiene NULLs estructurales.",
            "prioridad": "CRÍTICA"
        },
        # ── Transformaciones de escala ──
        {
            "categoria": "Escala",
            "variable(s)": "pob, pob_adulta, pob_adulta_m, pob_adulta_h",
            "transformacion": "log(x) para controlar en regresiones; dejar en niveles para per cápita",
            "razon": "Distribución log-normal típica de población. CV = 5.74 indica cola fuerte a la derecha.",
            "prioridad": "Alta"
        },
        {
            "categoria": "Escala",
            "variable(s)": "outcomes per cápita (todos)",
            "transformacion": "Evaluar log(1+x) si distribución es muy asimétrica; "
                     "alternativamente, asinh(x) que acepta ceros",
            "razon": "Estabiliza varianza y facilita interpretación en coeficientes como semi-elasticidades.",
            "prioridad": "Media"
        },
        # ── Winsorization ──
        {
            "categoria": "Outliers",
            "variable(s)": "outcomes per cápita",
            "transformacion": "Winsorizar al p1–p99 como análisis de robustez",
            "razon": "Los outcomes muestran alta dispersión (CV > 5). Winsorización controla "
                     "influencia de extremos sin perder observaciones.",
            "prioridad": "Alta (robustez)"
        },
        # ── Imputación ──
        {
            "categoria": "Imputación",
            "variable(s)": "tipo_pob (2 NULLs)",
            "transformacion": "Asignar categoría basándose en rango de población del municipio, "
                     "o excluir las 2 obs problemáticas",
            "razon": "Solo 2 observaciones: impacto mínimo pero evita perder filas en regresiones con FE.",
            "prioridad": "Baja"
        },
        {
            "categoria": "Imputación",
            "variable(s)": "saldoprom_* (NULLs estructurales)",
            "transformacion": "NO imputar. Filtrar con flag_undef_saldoprom_* = 0 para margen intensivo. "
                     "Para margen extensivo, usar ncont_* > 0 como binaria.",
            "razon": "Los NULLs son el resultado correcto (÷0), no datos faltantes.",
            "prioridad": "CRÍTICA"
        },
        # ── Feature engineering ──
        {
            "categoria": "Feature engineering",
            "variable(s)": "brecha_genero_* (nuevas)",
            "transformacion": "Crear ratio = outcome_m / outcome_h o diferencia = outcome_m − outcome_h",
            "razon": "La pregunta es sobre inclusión financiera DE MUJERES. "
                     "La brecha M/H captura directamente la disparidad.",
            "prioridad": "Alta"
        },
        {
            "categoria": "Feature engineering",
            "variable(s)": "alcaldesa_acumulado (nueva)",
            "transformacion": "Variable 'dosis': nº trimestres acumulados con alcaldesa hasta t",
            "razon": "Permite evaluar si el efecto se acumula con el tiempo de exposición.",
            "prioridad": "Media"
        },
        {
            "categoria": "Feature engineering",
            "variable(s)": "ever_alcaldesa (nueva)",
            "transformacion": "1 si el municipio tiene alcaldesa en cualquier trimestre del panel",
            "razon": "Clasifica municipios para análisis de balance y heterogeneidad.",
            "prioridad": "Alta"
        },
        # ── IDs ──
        {
            "categoria": "Estandarización IDs",
            "variable(s)": "cve_mun, cve_ent, cve_mun3, cvegeo_mun",
            "transformacion": "Usar cvegeo_mun (5 dígitos, texto) como ID canónico para merges con INEGI/CONAPO/etc.",
            "razon": "Formato estándar INEGI de 5 dígitos evita errores de zero-padding.",
            "prioridad": "Alta"
        },
        # ── Columnas a excluir ──
        {
            "categoria": "Limpieza",
            "variable(s)": "hist_state_available, missing_quarters_alcaldesa, ok_panel_completo_final",
            "transformacion": "EXCLUIR — son constantes (std = 0)",
            "razon": "No aportan variación: hist_state_available = 1, missing_quarters = 0, "
                     "ok_panel_completo_final = 1 para toda la muestra.",
            "prioridad": "CRÍTICA"
        },
    ]

    rec_df = pd.DataFrame(recs)
    _save_csv(rec_df, "F_recomendaciones")
    print(f"  --> {len(recs)} recomendaciones documentadas")

    return rec_df


# ═════════════════════════════════════════════════════════════════════════════
# MAIN — PIPELINE COMPLETO
# ═════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 70)
    print("EDA — Inclusión financiera y alcaldesas")
    print(f"Outputs --> {OUT}")
    print("=" * 70)

    # ── Carga desde CSV ──────────────────────────────────────────────────────────
    print(f"\n⏳ Cargando CSV {TABLE}...")
    df = load_csv(TABLE)
    print(f"OK {df.shape[0]:,} filas × {df.shape[1]} columnas ({df.memory_usage(deep=True).sum()/1e6:.1f} MB)")

    # ── Ejecutar secciones ───────────────────────────────────────────────────
    catalogo   = seccion_a(df)
    calidad    = seccion_b(df)
    seccion_c(df)
    seccion_d(df)
    leakage    = seccion_e(df)
    recomend   = seccion_f(df)

    print("\n" + "=" * 70)
    print("OK EDA completado")
    print(f"  Outputs en: {OUT}")
    print(f"  Archivos generados: {len(list(OUT.glob('*')))}")
    print("=" * 70)


if __name__ == "__main__":
    main()
