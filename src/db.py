"""
src/db.py — Carga de datos desde CSV (exportados de tesis_db).

Nota (2026-03):
  Originalmente este módulo conectaba a PostgreSQL.  La base de datos
  fue exportada a CSV y se almacena en  data/:
    - inclusion_financiera.csv          (175 cols, 41 905 rows)
    - inclusion_financiera_clean.csv    (348 cols, 41 905 rows)
    - inclusion_financiera_v2.csv       (41 cols, 64 126 rows)
    - inclusion_financiera_v2_meta.csv  (2 cols, 8 rows)
  La interfaz pública se mantiene compatible.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# Ruta base — data/ está al lado de src/ en la raíz de Code_V2
_DATA_DIR = Path(__file__).resolve().parent.parent / "data" if \
    (Path(__file__).resolve().parent.parent / "data").exists() else \
    Path(__file__).resolve().parents[1] / "data"

TABLE = "inclusion_financiera"

# Mapa de nombres lógicos --> archivos CSV
_CSV_MAP: dict[str, Path] = {
    "inclusion_financiera":         _DATA_DIR / "inclusion_financiera.csv",
    "inclusion_financiera_clean":   _DATA_DIR / "inclusion_financiera_clean.csv",
    "inclusion_financiera_v2":      _DATA_DIR / "inclusion_financiera_v2.csv",
    "inclusion_financiera_v2_meta": _DATA_DIR / "inclusion_financiera_v2_meta.csv",
}


def load_table(table: str = TABLE, **kwargs) -> pd.DataFrame:
    """Carga una tabla completa desde su CSV correspondiente."""
    path = _CSV_MAP.get(table)
    if path is None:
        raise ValueError(f"Tabla desconocida: {table!r}. Opciones: {list(_CSV_MAP)}")
    if not path.exists():
        raise FileNotFoundError(f"CSV no encontrado: {path}")
    return pd.read_csv(path, low_memory=False, **kwargs)


def check_data(table: str = TABLE) -> dict:
    """Devuelve conteo de filas y columnas del CSV."""
    df = load_table(table)
    return {"table": table, "rows": len(df), "cols": df.shape[1]}


# ---------------------------------------------------------------
# Legacy aliases (compat)
# ---------------------------------------------------------------
def get_engine():
    """Legacy: devuelve None.  Ya no se requiere PostgreSQL."""
    import warnings
    warnings.warn(
        "get_engine() está deprecado — el pipeline usa CSV. "
        "Usa load_table() o tesis_alcaldesas.config.load_csv().",
        DeprecationWarning,
        stacklevel=2,
    )
    return None


def query(sql: str, engine=None) -> pd.DataFrame:
    """Legacy: SQL ya no es soportado.  Usa load_table()."""
    raise NotImplementedError(
        "query(sql) fue deshabilitado tras migrar a CSV.  "
        "Usa load_table(table_name) y filtra con pandas."
    )
