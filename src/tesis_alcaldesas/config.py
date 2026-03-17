"""
tesis_alcaldesas.config -- Configuracion centralizada del proyecto.

GUIA PARA EL ASESOR:
  Este archivo es el "centro de control" de toda la tesis.
  Aqui se definen:
    1. RUTAS: donde viven los datos, outputs, y documentacion.
    2. CARGA DE DATOS: funcion load_csv() que abstrae la lectura de CSVs.
    3. CONEXION A BD: funcion legacy get_engine() (ya no se usa en el pipeline).
    4. OUTCOMES: las 17 variables de resultado (mujeres y hombres) y las
       5 primarias que son el foco del analisis econometrico.
    5. LEAKAGE: columnas que NUNCA deben usarse como controles en las
       regresiones (leads/lags, tratamiento acumulado, etc.).

  Cualquier cambio en la definicion de outcomes o rutas se hace aqui
  y se propaga automaticamente a todo el pipeline.

Provee:
  - Rutas canonicas (BASE_DIR, DATA_DIR, OUTPUT_DIR, ...)
  - Rutas CSV para datos exportados de tesis_db
  - get_engine() --> SQLAlchemy Engine (legacy, opcional)
  - Listas de outcomes, leakage y constantes reutilizables

Nota (2026-03):
  La base de datos PostgreSQL (tesis_db) fue exportada a CSV y
  almacenada en data/.  El pipeline principal ya no requiere una
  conexion activa a PostgreSQL -- lee directamente de los CSV/parquet.
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
# GUIA: Estas son las variables de resultado de la CNBV (Comision Nacional
# Bancaria y de Valores) que miden la inclusion financiera de las mujeres.
# Se agrupan en 3 dimensiones:
#   - Extension: numero de contratos (cuentas bancarias)
#   - Profundidad: saldos (cuanto dinero hay en esas cuentas)
#   - Productos: tarjetas de debito/credito e hipotecas
RAW_OUTCOMES_M: list[str] = [
    # Extension (numero de contratos por tipo de cuenta)
    "ncont_total_m", "ncont_ahorro_m", "ncont_plazo_m",
    "ncont_n1_m", "ncont_n2_m", "ncont_n3_m", "ncont_tradic_m",
    # Profundidad (saldos monetarios por tipo de cuenta)
    "saldocont_total_m", "saldocont_ahorro_m", "saldocont_plazo_m",
    "saldocont_n1_m", "saldocont_n2_m", "saldocont_n3_m", "saldocont_tradic_m",
    # Productos financieros (tarjetas e hipotecas)
    "numtar_deb_m", "numtar_cred_m", "numcontcred_hip_m",
]

# --- 17 outcomes crudos (hombres) — para placebos de género ---
RAW_OUTCOMES_H: list[str] = [col.replace("_m", "_h") for col in RAW_OUTCOMES_M]

# --- 5 outcomes primarios (mujeres) ---
# GUIA: Estos 5 outcomes son el foco principal del analisis econometrico.
# Cubren las 3 dimensiones de inclusion financiera:
#   1. Contratos totales   --> extension general
#   2. Tarjetas de debito  --> acceso basico a servicios financieros
#   3. Tarjetas de credito --> acceso a credito al consumo
#   4. Creditos hipotecarios --> acceso a credito de largo plazo
#   5. Saldo total         --> profundidad financiera
# Todos los modelos (TWFE, event study, robustez, heterogeneidad)
# se estiman sobre estos 5 outcomes.
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
# GUIA: Estas variables contienen informacion del futuro o del
# tratamiento en si. Usarlas como controles introduciria sesgo.
# Por ejemplo, ever_alcaldesa resumen post-outcome y los leads
# (f1, f2, f3) solo se usan en el event study, no como controles.
LEAKAGE_COLS: list[str] = [
    "ever_alcaldesa",
    "alcaldesa_acumulado",
    "alcaldesa_final_f1", "alcaldesa_final_f2", "alcaldesa_final_f3",
    "alcaldesa_final_l1", "alcaldesa_final_l2", "alcaldesa_final_l3",
    "alcaldesa_excl_trans", "alcaldesa_end_excl_trans",
]
