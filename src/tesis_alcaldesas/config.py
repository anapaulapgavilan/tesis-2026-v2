"""
tesis_alcaldesas.config — Configuración centralizada del proyecto.

Provee:
  - Rutas canónicas (BASE_DIR, DATA_DIR, OUTPUT_DIR, …)
  - Rutas CSV para datos exportados de tesis_db
  - get_engine() --> SQLAlchemy Engine (legacy, opcional)
  - Listas de outcomes, leakage y constantes reutilizables

Nota (2026-03):
  La base de datos PostgreSQL (tesis_db) fue exportada a CSV y
  almacenada en data/.  El pipeline principal ya no requiere una
  conexión activa a PostgreSQL — lee directamente de los CSV/parquet.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd

# ============================================================
# 1. Rutas
# ============================================================
# BASE_DIR = raíz del repositorio (…/tesis-2026-v2/)
BASE_DIR: Path = Path(__file__).resolve().parents[2]

DATA_DIR: Path = BASE_DIR / "data" / "processed"
CSV_DIR: Path = BASE_DIR / "data"
OUTPUT_DIR: Path = BASE_DIR / "outputs"
OUTPUT_PAPER: Path = OUTPUT_DIR / "paper"
OUTPUT_QC: Path = OUTPUT_DIR / "qc"
SQL_DIR: Path = BASE_DIR / "sql"
DOCS_DIR: Path = BASE_DIR / "docs"

# Archivos clave — panel procesado
PARQUET_RAW: Path = DATA_DIR / "analytical_panel.parquet"
PARQUET_FEATURES: Path = DATA_DIR / "analytical_panel_features.parquet"

# Archivos clave — CSV exportados de tesis_db (2026-03)
CSV_INCLUSION_FINANCIERA: Path = CSV_DIR / "inclusion_financiera.csv"
CSV_INCLUSION_FINANCIERA_CLEAN: Path = CSV_DIR / "inclusion_financiera_clean.csv"
CSV_INCLUSION_FINANCIERA_V2: Path = CSV_DIR / "inclusion_financiera_v2.csv"
CSV_INCLUSION_FINANCIERA_V2_META: Path = CSV_DIR / "inclusion_financiera_v2_meta.csv"


# ============================================================
# 2. Carga de datos desde CSV (fuente principal)
# ============================================================
def load_csv(
    table: str = "inclusion_financiera_clean",
    usecols: list[str] | None = None,
) -> pd.DataFrame:
    """
    Carga una tabla exportada de tesis_db desde su CSV correspondiente.

    Parámetros:
      table    — Nombre lógico de la tabla:
                 'inclusion_financiera'         (175 cols, 41 905 rows)
                 'inclusion_financiera_clean'   (348 cols, 41 905 rows)
                 'inclusion_financiera_v2'      (41 cols, 64 126 rows)
                 'inclusion_financiera_v2_meta' (2 cols, 8 rows)
      usecols  — Lista de columnas a leer (None = todas).

    Retorna: pd.DataFrame
    """
    csv_map = {
        "inclusion_financiera":       CSV_INCLUSION_FINANCIERA,
        "inclusion_financiera_clean": CSV_INCLUSION_FINANCIERA_CLEAN,
        "inclusion_financiera_v2":    CSV_INCLUSION_FINANCIERA_V2,
        "inclusion_financiera_v2_meta": CSV_INCLUSION_FINANCIERA_V2_META,
    }
    path = csv_map.get(table)
    if path is None:
        raise ValueError(f"Tabla desconocida: {table!r}.  Opciones: {list(csv_map)}")
    if not path.exists():
        raise FileNotFoundError(
            f"CSV no encontrado: {path}\n"
            "Exporta la tabla con:  python -c \"from db import ...\"\n"
            "O descárgala del respaldo de tesis_db."
        )
    return pd.read_csv(path, usecols=usecols, low_memory=False)


# ============================================================
# 3. Conexión a PostgreSQL (legacy — solo para scripts adhoc)
# ============================================================
def get_engine():
    """
    Construye un SQLAlchemy Engine a partir de variables de entorno PG*.

    **Legacy:** El pipeline principal ya no necesita PostgreSQL.
    Los datos están en CSV en data/.  Esta función se conserva
    para los scripts adhoc/tests que usan SQL crudo.
    """
    try:
        from sqlalchemy import create_engine
    except ImportError:
        raise RuntimeError(
            "sqlalchemy no está instalado.  La conexión a PostgreSQL es "
            "opcional — el pipeline principal usa CSV.  Si necesitas SQL "
            "crudo, instala: pip install sqlalchemy psycopg2-binary"
        )

    url = os.environ.get("DATABASE_URL")
    if url:
        return create_engine(url)

    host = os.environ.get("PGHOST", "localhost")
    port = os.environ.get("PGPORT", "5432")
    database = os.environ.get("PGDATABASE", "tesis_db")
    user = os.environ.get("PGUSER", os.environ.get("USER", "postgres"))
    password = os.environ.get("PGPASSWORD", "")

    if password:
        url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    else:
        url = f"postgresql://{user}@{host}:{port}/{database}"

    return create_engine(url)


# ============================================================
# 4. Outcomes y variables
# ============================================================

# --- 17 outcomes crudos (mujeres) ---
RAW_OUTCOMES_M: list[str] = [
    # Extensión
    "ncont_total_m", "ncont_ahorro_m", "ncont_plazo_m",
    "ncont_n1_m", "ncont_n2_m", "ncont_n3_m", "ncont_tradic_m",
    # Profundidad (saldos)
    "saldocont_total_m", "saldocont_ahorro_m", "saldocont_plazo_m",
    "saldocont_n1_m", "saldocont_n2_m", "saldocont_n3_m", "saldocont_tradic_m",
    # Productos
    "numtar_deb_m", "numtar_cred_m", "numcontcred_hip_m",
]

# --- 17 outcomes crudos (hombres) — para placebos de género ---
RAW_OUTCOMES_H: list[str] = [col.replace("_m", "_h") for col in RAW_OUTCOMES_M]

# --- 5 outcomes primarios (mujeres) ---
PRIMARY_OUTCOMES: list[str] = [
    "ncont_total_m",
    "numtar_deb_m",
    "numtar_cred_m",
    "numcontcred_hip_m",
    "saldocont_total_m",
]

# --- Etiquetas ---
OUTCOME_LABELS: dict[str, dict[str, str]] = {
    "ncont_total_m":      {"es": "Contratos totales",       "en": "Total contracts"},
    "numtar_deb_m":       {"es": "Tarjetas débito",         "en": "Debit cards"},
    "numtar_cred_m":      {"es": "Tarjetas crédito",        "en": "Credit cards"},
    "numcontcred_hip_m":  {"es": "Créditos hipotecarios",   "en": "Mortgage loans"},
    "saldocont_total_m":  {"es": "Saldo total",             "en": "Total balance"},
}

# --- Columnas de leakage (nunca usar como controles) ---
LEAKAGE_COLS: list[str] = [
    "ever_alcaldesa",
    "alcaldesa_acumulado",
    "alcaldesa_final_f1", "alcaldesa_final_f2", "alcaldesa_final_f3",
    "alcaldesa_final_l1", "alcaldesa_final_l2", "alcaldesa_final_l3",
    "alcaldesa_excl_trans", "alcaldesa_end_excl_trans",
]
