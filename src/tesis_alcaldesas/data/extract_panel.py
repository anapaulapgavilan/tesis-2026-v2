"""
extract_panel.py -- Paso 1 del pipeline: Extrae columnas del CSV crudo
                    y exporta un parquet limpio para feature engineering.

GUIA PARA EL ASESOR:
  Este script es la PRIMERA etapa del pipeline de datos.
  
  Que hace:
    1. Lee el CSV exportado de la CNBV (inclusion_financiera_clean.csv)
    2. Selecciona las 61 columnas necesarias para el analisis
    3. Valida que todas existan y que la PK (cve_mun, periodo_trimestre) sea unica
    4. Exporta a Parquet para lectura rapida en pasos posteriores
  
  Estructura de las 61 columnas:
    - 7 identificadores (cve_mun, periodo_trimestre, año, etc.)
    - 5 variables de tratamiento (alcaldesa_final y variantes)
    - 6 leads/lags para event study
    - 2 controles (log_pob, log_pob_adulta)
    - 3 poblaciones denominador (pob_adulta_m, pob_adulta_h, pob_adulta)
    - 2 categoricas (tipo_pob, region)
    - 2 auxiliares (ok_panel_completo, quarters_in_base)
    - 17 outcomes mujeres + 17 outcomes hombres (crudos, sin transformar)
  
  El resultado es un panel de 41,905 obs (2,471 municipios x 17 trimestres).

Uso:
    python -m tesis_alcaldesas.data.extract_panel

Salida:
    data/processed/analytical_panel.parquet
"""

from __future__ import annotations

import sys

import pandas as pd

from tesis_alcaldesas.config import load_csv, DATA_DIR

# ---------------------------------------------------------------------------
# 2. Definición de columnas a extraer
# ---------------------------------------------------------------------------

# --- Identificadores y panel ---
# GUIA: Estas columnas identifican cada observacion en el panel.
# La clave primaria es (cve_mun, periodo_trimestre).
# t_index es un indice numerico 0-based (0 = 2018Q3) que facilita
# las operaciones temporales en el event study.
ID_COLS = [
    "cve_mun",          # PK parte 1  (bigint)
    "periodo_trimestre", # PK parte 2  (text, "2018Q3"–"2022Q3")
    "cvegeo_mun",       # clave INEGI 5 dígitos (text) — merges externos
    "cve_ent",          # entidad (text 2 dígitos)
    "year",             # año calendario
    "quarter",          # trimestre (1–4)
    "t_index",          # índice temporal 0-based (0 = 2018Q3)
]

# --- Tratamiento ---
# GUIA: alcaldesa_final es la variable de tratamiento principal D_{it}.
# Vale 1 si el municipio i tiene alcaldesa en el trimestre t.
# Las variantes (excl_trans, end_excl_trans) excluyen periodos de
# transicion para pruebas de robustez (ver 04_robustness.py).
TREATMENT_COLS = [
    "alcaldesa_final",       # D_it {0,1} — tratamiento principal
    "ever_alcaldesa",        # max_t D_it — invariante; para balance/heterogeneidad
    "alcaldesa_acumulado",   # dosis acumulada; tratamiento alternativo
    # Variantes robustez (excluyen transiciones)
    "alcaldesa_excl_trans",
    "alcaldesa_end_excl_trans",
]

# Leads/lags -- SOLO para event study, NUNCA como controles
# GUIA: Los leads (f1-f3) capturan anticipacion del tratamiento.
# Los lags (l1-l3) capturan el efecto rezagado. Se usan solo
# en el event study (03_event_study.py) para diagnosticar
# tendencias pre-tratamiento.
EVENT_STUDY_COLS = [
    "alcaldesa_final_f1", "alcaldesa_final_f2", "alcaldesa_final_f3",  # leads
    "alcaldesa_final_l1", "alcaldesa_final_l2", "alcaldesa_final_l3",  # lags
]

# --- Controles ---
# GUIA: log_pob es el unico control en la especificacion principal.
# Es un control "pre-determinado" (cambia lentamente) que absorbe
# diferencias en tamano entre municipios. No incluimos mas controles
# para evitar el "bad controls problem" (Angrist & Pischke, 2009).
CONTROL_COLS = [
    "log_pob",           # ln(pob+1); control pre-determinado/lento
    "log_pob_adulta",    # ln(pob_adulta+1)
]

# --- Poblacion (denominadores para per capita) ---
# GUIA: Los outcomes crudos estan en numeros absolutos. Para hacer
# comparables municipios de diferente tamano, normalizamos por
# poblacion adulta (por 10,000 habitantes). pob_adulta_m es el
# denominador principal para outcomes femeninos.
POP_COLS = [
    "pob_adulta_m",  # denominador principal (mujeres adultas)
    "pob_adulta_h",  # denominador hombres (para ratios)
    "pob_adulta",    # denominador total
]

# --- Categoricas (heterogeneidad) ---
# GUIA: Estas variables permiten analizar si el efecto del tratamiento
# varia segun el tipo de municipio (rural vs urbano) o la region.
# Se usan en 05_heterogeneity.py para sub-muestras.
CAT_COLS = [
    "tipo_pob",   # Rural / En Transicion / Semi-urbano / Urbano / Semi-metropoli / Metropoli
    "region",     # 6 regiones
]

# --- Auxiliares ---
AUX_COLS = [
    "ok_panel_completo",   # 1 si tiene los 17 trimestres
    "quarters_in_base",    # trimestres presentes
]

# --- Raw outcomes (mujeres) --- 17 variables ---
# GUIA: Se extraen en crudo (numeros absolutos) para luego
# recalcular per capita de forma reproducible en build_features.py.
# El sufijo _m indica "mujeres".
RAW_OUTCOMES_M = [
    # Extensión
    "ncont_total_m",
    "ncont_ahorro_m",
    "ncont_plazo_m",
    "ncont_n1_m",
    "ncont_n2_m",
    "ncont_n3_m",
    "ncont_tradic_m",
    # Profundidad (saldos)
    "saldocont_total_m",
    "saldocont_ahorro_m",
    "saldocont_plazo_m",
    "saldocont_n1_m",
    "saldocont_n2_m",
    "saldocont_n3_m",
    "saldocont_tradic_m",
    # Productos (tarjetas, hipotecarios)
    "numtar_deb_m",
    "numtar_cred_m",
    "numcontcred_hip_m",
]

# --- Raw outcomes (hombres) --- para ratios de brecha de genero ---
# GUIA: Los outcomes masculinos (sufijo _h) se usan para:
#   1. Calcular ratios de brecha de genero: outcome_m / outcome_h
#   2. Placebos de genero: si el tratamiento afecta a hombres, el
#      efecto no seria especifico a mujeres (ver R5 en robustness.py)
RAW_OUTCOMES_H = [col.replace("_m", "_h") for col in RAW_OUTCOMES_M]
# numcontcred_hip no tiene _pm; _h sí existe (verificado en profile CSV)

ALL_COLS = (
    ID_COLS + TREATMENT_COLS + EVENT_STUDY_COLS + CONTROL_COLS
    + POP_COLS + CAT_COLS + AUX_COLS + RAW_OUTCOMES_M + RAW_OUTCOMES_H
)

# ---------------------------------------------------------------------------
# 3. Validar que todas las columnas existen en el CSV
# ---------------------------------------------------------------------------
def validate_columns(available: set[str], requested: list[str]) -> list[str]:
    """Retorna lista de columnas faltantes (vacía si todo OK)."""
    return [c for c in requested if c not in available]


# ---------------------------------------------------------------------------
# 4. Extracción desde CSV
# ---------------------------------------------------------------------------
def extract(columns: list[str], table: str = "inclusion_financiera_clean") -> pd.DataFrame:
    """Lee el CSV exportado de tesis_db y selecciona columnas."""
    df = load_csv(table, usecols=columns)
    df = df.sort_values(["cve_mun", "periodo_trimestre"]).reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# 5. Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("extract_panel — Extracción del panel analítico (desde CSV)")
    print("=" * 60)

    # Leer solo encabezados del CSV para validar columnas (sin cargar datos)
    from tesis_alcaldesas.config import CSV_INCLUSION_FINANCIERA_CLEAN
    csv_cols = set(pd.read_csv(CSV_INCLUSION_FINANCIERA_CLEAN, nrows=0).columns)

    # Validar columnas
    missing = validate_columns(csv_cols, ALL_COLS)
    if missing:
        print(f"\n[!]  COLUMNAS FALTANTES ({len(missing)}):")
        for m in missing:
            print(f"   - {m}")
        print("\nSe procede sin ellas.\n")
        cols_to_extract = [c for c in ALL_COLS if c not in set(missing)]
    else:
        print(f"\nOK  Todas las {len(ALL_COLS)} columnas encontradas en la tabla.\n")
        cols_to_extract = ALL_COLS

    # Extraer desde CSV
    print(f"Extrayendo {len(cols_to_extract)} columnas de CSV …")
    df = extract(cols_to_extract)
    print(f"  Filas: {len(df):,}")
    print(f"  Columnas: {df.shape[1]}")

    # Quick sanity
    n_mun = df["cve_mun"].nunique()
    n_per = df["periodo_trimestre"].nunique()
    print(f"  Municipios: {n_mun:,}")
    print(f"  Periodos: {n_per}")
    pk_unique = df.duplicated(subset=["cve_mun", "periodo_trimestre"]).sum() == 0
    print(f"  PK única: {'OK' if pk_unique else 'FAIL HAY DUPLICADOS'}")

    # Exportar parquet
    out_path = DATA_DIR / "analytical_panel.parquet"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out_path, index=False, engine="pyarrow")
    print(f"\nOK  Exportado --> {out_path}  ({out_path.stat().st_size / 1e6:.1f} MB)")

    if missing:
        print(f"\n[!]  Recordatorio: {len(missing)} columna(s) faltante(s) — ver arriba.")
        sys.exit(1)

    print("\nDone.")


if __name__ == "__main__":
    main()
