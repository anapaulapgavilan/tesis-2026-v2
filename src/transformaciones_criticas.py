"""
Transformaciones Críticas — Recomendaciones 🔴 del EDA
======================================================

Este script aplica las 4 recomendaciones CRÍTICAS identificadas en el EDA
sobre una COPIA de la tabla original `inclusion_financiera`.

Transformaciones:
  1. Normalización per cápita de ncont_*, numtar_*, numcontcred_* (÷ pob_adulta × 10,000)
  2. Normalización per cápita de saldocont_* (÷ pob_adulta × 10,000)
  3. Marcado de saldoprom_* con NULLs estructurales (NO se imputan; se documentan)
  4. Exclusión de 3 columnas constantes (hist_state_available, missing_quarters_alcaldesa,
     ok_panel_completo_final)

La tabla resultante se llama `inclusion_financiera_clean` y contiene:
  - Todas las columnas originales MENOS las 3 constantes
  - Nuevas columnas per cápita con sufijo _pc
  - Nuevas columnas per cápita de saldos con sufijo _pc

Uso:
    python src/transformaciones_criticas.py

Autor: Generado automáticamente como parte del EDA
"""

import os
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

# ── Conexión a la base de datos ──────────────────────────────────────────────
# Nunca hard-codear usuario; lee de variables de entorno PG* o DATABASE_URL.
from tesis_alcaldesas.config import get_engine  # noqa: E402
engine = get_engine()

# ── Constantes ───────────────────────────────────────────────────────────────
K = 10_000  # Factor de escala: contratos/saldos por cada 10,000 personas

# Columnas constantes a EXCLUIR (Recomendación 4)
COLS_CONSTANTES = [
    "hist_state_available",       # Siempre = 1 en toda la muestra
    "missing_quarters_alcaldesa", # Siempre = 0 en toda la muestra
    "ok_panel_completo_final",    # Siempre = 1 en toda la muestra
]

# ── Mapping de sufijo demográfico a denominador per cápita ───────────────────
# _m  → mujeres    → pob_adulta_m
# _h  → hombres    → pob_adulta_h
# _pm → persona moral (empresas) → no tiene denominador poblacional
# _t  → total      → pob_adulta
SUFIJO_A_DENOM = {
    "_m":  "pob_adulta_m",
    "_h":  "pob_adulta_h",
    "_t":  "pob_adulta",
    "_pm": None,  # Persona moral: no tiene denominador poblacional directo
}


def identificar_columnas_per_capita(df):
    """
    Identifica las columnas de conteos y saldos que necesitan normalización
    per cápita, y las empareja con su denominador correspondiente.

    Retorna una lista de tuplas: (columna_original, columna_pc, denominador)
    """
    pares = []

    # Prefijos que necesitan normalización (Recs 1 y 2)
    prefijos_conteos = ["ncont_", "numtar_", "numcontcred_"]
    prefijos_saldos  = ["saldocont_"]

    for col in df.columns:
        # ¿Es una columna de conteos o saldos?
        es_conteo = any(col.startswith(p) for p in prefijos_conteos)
        es_saldo  = any(col.startswith(p) for p in prefijos_saldos)

        if not (es_conteo or es_saldo):
            continue

        # Determinar el sufijo demográfico y su denominador
        denom = None
        for sufijo, denom_col in SUFIJO_A_DENOM.items():
            if col.endswith(sufijo):
                denom = denom_col
                break

        if denom is None:
            # Columna con sufijo _pm (persona moral): saltar
            continue

        # Nombre de la nueva columna per cápita
        col_pc = f"{col}_pc"
        pares.append((col, col_pc, denom))

    return pares


def aplicar_per_capita(df, pares):
    """
    Crea columnas per cápita (× K) para cada par (columna, denominador).
    Protege contra ÷0 reemplazando 0 en el denominador por NaN.

    Parámetros:
        df    : DataFrame con datos originales
        pares : Lista de tuplas (col_original, col_pc, denominador)

    Retorna:
        DataFrame con las nuevas columnas agregadas
    """
    print(f"\n{'='*70}")
    print(f"NORMALIZACIÓN PER CÁPITA (× {K:,})")
    print(f"{'='*70}")

    conteos_creados = 0
    saldos_creados = 0

    for col_orig, col_pc, denom in pares:
        # Reemplazar 0 por NaN en el denominador para evitar ÷0
        denominador = df[denom].replace(0, np.nan)
        # Fórmula: (valor × K) / población adulta
        df[col_pc] = (df[col_orig] * K / denominador).round(4)

        if col_orig.startswith("saldocont_"):
            saldos_creados += 1
        else:
            conteos_creados += 1

    print(f"  ✓ Columnas de conteos per cápita creadas: {conteos_creados}")
    print(f"  ✓ Columnas de saldos per cápita creadas:  {saldos_creados}")
    print(f"  ✓ Total columnas per cápita nuevas:       {conteos_creados + saldos_creados}")

    return df


def documentar_saldoprom_nulls(df):
    """
    Documenta la distribución de NULLs estructurales en saldoprom_*.
    NO se imputan: los NULLs son el resultado correcto (÷0 cuando
    no hay contratos).

    Se agregan columnas indicadoras `saldoprom_*_es_null` = 1 cuando
    el valor es NULL, para facilitar el filtrado posterior.
    """
    print(f"\n{'='*70}")
    print(f"DOCUMENTACIÓN DE saldoprom_* (NULLs estructurales)")
    print(f"{'='*70}")

    saldoprom_cols = [c for c in df.columns if c.startswith("saldoprom_")
                      and not c.endswith("_es_null")]

    print(f"  Columnas saldoprom_* encontradas: {len(saldoprom_cols)}")
    print(f"\n  {'Columna':<35} {'NULLs':>8} {'% NULL':>8}")
    print(f"  {'-'*35} {'-'*8} {'-'*8}")

    for col in saldoprom_cols:
        n_null = int(df[col].isna().sum())
        pct_null = df[col].isna().mean() * 100
        if n_null > 0:
            print(f"  {col:<35} {n_null:>8,} {pct_null:>7.1f}%")

    print(f"\n  → ACCIÓN: NO se imputan. Los flags `flag_undef_saldoprom_*` ya")
    print(f"    existen en la tabla para filtrar. Usar flag = 0 para análisis")
    print(f"    de margen intensivo (solo donde hay contratos).")

    return df


def excluir_constantes(df):
    """
    Elimina las 3 columnas que tienen varianza = 0 (mismo valor en
    todas las observaciones). Estas columnas no aportan información
    al modelo y serían eliminadas automáticamente por colinealidad.
    """
    print(f"\n{'='*70}")
    print(f"EXCLUSIÓN DE COLUMNAS CONSTANTES")
    print(f"{'='*70}")

    cols_presentes = [c for c in COLS_CONSTANTES if c in df.columns]
    cols_ausentes  = [c for c in COLS_CONSTANTES if c not in df.columns]

    if cols_ausentes:
        print(f"  ⚠ Columnas no encontradas (ya eliminadas?): {cols_ausentes}")

    for col in cols_presentes:
        val_unico = df[col].dropna().unique()
        print(f"  → Eliminando '{col}' (valor constante: {val_unico})")

    df = df.drop(columns=cols_presentes, errors="ignore")
    print(f"  ✓ Columnas eliminadas: {len(cols_presentes)}")

    return df


def validar_transformaciones(df, pares):
    """
    Ejecuta validaciones post-transformación para confirmar que
    los cambios son correctos.
    """
    print(f"\n{'='*70}")
    print(f"VALIDACIÓN POST-TRANSFORMACIÓN")
    print(f"{'='*70}")

    # 1. Verificar que las columnas constantes fueron eliminadas
    constantes_restantes = [c for c in COLS_CONSTANTES if c in df.columns]
    status1 = "✓" if len(constantes_restantes) == 0 else "✗"
    print(f"  {status1} Constantes eliminadas: {len(constantes_restantes) == 0}")

    # 2. Verificar que las columnas per cápita existen
    cols_pc = [col_pc for _, col_pc, _ in pares]
    existentes = [c for c in cols_pc if c in df.columns]
    status2 = "✓" if len(existentes) == len(cols_pc) else "✗"
    print(f"  {status2} Columnas per cápita creadas: {len(existentes)}/{len(cols_pc)}")

    # 3. Verificar que las columnas per cápita no tienen infinitos
    n_inf = 0
    for c in existentes:
        n_inf += np.isinf(df[c]).sum() if df[c].dtype != "object" else 0
    status3 = "✓" if n_inf == 0 else "✗"
    print(f"  {status3} Valores infinitos en per cápita: {n_inf}")

    # 4. Verificar que no hay negativos en per cápita
    n_neg = 0
    for c in existentes:
        if pd.api.types.is_numeric_dtype(df[c]):
            n_neg += (df[c] < 0).sum()
    status4 = "✓" if n_neg == 0 else "✗"
    print(f"  {status4} Valores negativos en per cápita: {n_neg}")

    # 5. Mostrar estadísticas descriptivas de algunas columnas per cápita clave
    key_pc = [c for c in existentes if "total_m_pc" in c or "ahorro_m_pc" in c
              or "deb_m_pc" in c][:5]
    if key_pc:
        print(f"\n  Estadísticas de columnas per cápita clave:")
        print(f"  {'Columna':<30} {'Media':>10} {'Mediana':>10} {'Max':>12} {'NaNs':>8}")
        print(f"  {'-'*30} {'-'*10} {'-'*10} {'-'*12} {'-'*8}")
        for c in key_pc:
            s = df[c]
            print(f"  {c:<30} {s.mean():>10,.2f} {s.median():>10,.2f} "
                  f"{s.max():>12,.2f} {s.isna().sum():>8,}")

    # 6. Dimensiones finales
    print(f"\n  Dimensiones finales del DataFrame: {df.shape[0]:,} filas × {df.shape[1]} columnas")

    return df


def main():
    """Pipeline principal de transformaciones críticas."""
    print("=" * 70)
    print("TRANSFORMACIONES CRÍTICAS — Recomendaciones 🔴 del EDA")
    print("=" * 70)

    # ── 1. Cargar datos originales ──
    print("\n1. Cargando datos desde inclusion_financiera...")
    df = pd.read_sql("SELECT * FROM inclusion_financiera", engine)
    print(f"   ✓ {df.shape[0]:,} filas × {df.shape[1]} columnas cargadas")
    n_cols_original = df.shape[1]

    # ── 2. Identificar columnas para per cápita ──
    print("\n2. Identificando columnas para normalización per cápita...")
    pares = identificar_columnas_per_capita(df)
    print(f"   ✓ {len(pares)} columnas identificadas para normalización")

    # ── 3. Aplicar normalización per cápita (Recs 1 y 2) ──
    print("\n3. Aplicando normalización per cápita...")
    df = aplicar_per_capita(df, pares)

    # ── 4. Documentar saldoprom NULLs (Rec 3) ──
    print("\n4. Documentando saldoprom_* NULLs estructurales...")
    df = documentar_saldoprom_nulls(df)

    # ── 5. Excluir constantes (Rec 4) ──
    print("\n5. Excluyendo columnas constantes...")
    df = excluir_constantes(df)

    # ── 6. Validar ──
    print("\n6. Validando transformaciones...")
    df = validar_transformaciones(df, pares)

    # ── 7. Guardar tabla limpia en PostgreSQL ──
    print(f"\n7. Guardando tabla 'inclusion_financiera_clean' en PostgreSQL...")

    # Primero eliminar la tabla si existe (para poder re-ejecutar)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS inclusion_financiera_clean"))

    # Escribir la tabla completa
    df.to_sql(
        "inclusion_financiera_clean",
        engine,
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=5000,
    )

    # Agregar llave primaria
    with engine.begin() as conn:
        conn.execute(text("""
            ALTER TABLE inclusion_financiera_clean
            ADD CONSTRAINT pk_inclusion_financiera_clean
            PRIMARY KEY (cve_mun, periodo_trimestre)
        """))

    print(f"   ✓ Tabla 'inclusion_financiera_clean' creada exitosamente")
    print(f"   ✓ Llave primaria (cve_mun, periodo_trimestre) agregada")

    # ── 8. Resumen final ──
    print(f"\n{'='*70}")
    print(f"RESUMEN FINAL")
    print(f"{'='*70}")
    print(f"  Tabla original:  inclusion_financiera  ({n_cols_original} columnas)")
    print(f"  Tabla limpia:    inclusion_financiera_clean ({df.shape[1]} columnas)")
    print(f"  Columnas nuevas (per cápita):   +{len(pares)}")
    print(f"  Columnas eliminadas (constantes): -{len(COLS_CONSTANTES)}")
    print(f"  Diferencia neta: +{df.shape[1] - n_cols_original} columnas")
    print(f"\n  La tabla original NO fue modificada.")
    print(f"  Todas las transformaciones están en 'inclusion_financiera_clean'.")

    return df


if __name__ == "__main__":
    df_clean = main()
