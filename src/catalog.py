"""
src/catalog.py — Catálogo programático de variables.
"""

import pandas as pd


def build_catalog(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Genera un catálogo con tipo, NULLs, únicos, min, max para cada columna."""
    records = []
    for col in dataframe.columns:
        s = dataframe[col]
        rec = {
            "columna": col,
            "dtype": str(s.dtype),
            "nulls": s.isna().sum(),
            "pct_null": round(s.isna().mean() * 100, 2),
            "n_unique": s.nunique(),
            "ejemplo": s.dropna().iloc[0] if s.notna().any() else None,
        }
        if pd.api.types.is_numeric_dtype(s):
            rec["min"] = s.min()
            rec["max"] = s.max()
        records.append(rec)
    return pd.DataFrame(records)


def null_summary(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Devuelve solo las columnas con NULLs, ordenadas por porcentaje."""
    cat = build_catalog(dataframe)
    return (
        cat[cat["nulls"] > 0]
        .sort_values("pct_null", ascending=False)
        .reset_index(drop=True)
    )
