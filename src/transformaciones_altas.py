"""
Transformaciones Altas — Recomendaciones 🟡 del EDA (5–9)
==========================================================

Este script aplica las 5 recomendaciones de ALTA prioridad identificadas en el EDA
sobre la tabla `inclusion_financiera_clean` que ya contiene las transformaciones
críticas (Recs 1–4).

Transformaciones:
  5. log(pob), log(pob_adulta_m), log(pob_adulta_h), log(pob_adulta) como controles
  6. Winsorización de outcomes per cápita al percentil 1–99
  7. Ratio brecha de género = outcome_m_pc / outcome_h_pc
  8. ever_alcaldesa: 1 si el municipio tuvo alcaldesa en cualquier trimestre
  9. Estandarización de IDs — índice sobre cvegeo_mun

La tabla `inclusion_financiera_clean` se actualiza IN PLACE con las nuevas columnas.
La tabla original `inclusion_financiera` NO se toca.

Uso:
    python src/transformaciones_altas.py

Autor: Generado automáticamente como parte del EDA
"""

import os
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

# ── Conexión a la base de datos ──────────────────────────────────────────────
from tesis_alcaldesas.config import get_engine  # noqa: E402
engine = get_engine()


# ═══════════════════════════════════════════════════════════════════════════════
# Rec 5: log(población) como controles para regresiones
# ═══════════════════════════════════════════════════════════════════════════════
def aplicar_log_poblacion(df):
    """
    Crea columnas log-transformadas de las 4 variables de población.
    Se usa log(x + 1) para proteger contra log(0) en municipios con pob = 0.

    Columnas creadas:
      - log_pob          = ln(pob + 1)
      - log_pob_adulta   = ln(pob_adulta + 1)
      - log_pob_adulta_m = ln(pob_adulta_m + 1)
      - log_pob_adulta_h = ln(pob_adulta_h + 1)

    Justificación: La distribución de población es extremadamente sesgada
    (CV > 5). La transformación logarítmica comprime la escala y hace que
    la variable sea apta como control en regresiones lineales.
    """
    print(f"\n{'='*70}")
    print("REC 5: log(población) como controles")
    print(f"{'='*70}")

    mapping = {
        "pob":          "log_pob",
        "pob_adulta":   "log_pob_adulta",
        "pob_adulta_m": "log_pob_adulta_m",
        "pob_adulta_h": "log_pob_adulta_h",
    }

    for col_orig, col_log in mapping.items():
        df[col_log] = np.log1p(df[col_orig]).round(6)
        media = df[col_log].mean()
        print(f"  ✓ {col_log:<25} — media: {media:.4f}  "
              f"(rango: {df[col_log].min():.4f} – {df[col_log].max():.4f})")

    print(f"\n  ✓ 4 columnas log de población creadas")
    return df


# ═══════════════════════════════════════════════════════════════════════════════
# Rec 6: Winsorizar outcomes per cápita al p1–p99
# ═══════════════════════════════════════════════════════════════════════════════
def winsorizar_per_capita(df):
    """
    Crea versiones winsorizadas (sufijo _w) de todas las columnas per cápita (_pc).
    Los valores por debajo del percentil 1 se reemplazan por p1, y los valores
    por encima del percentil 99 se reemplazan por p99.

    Justificación: Los outcomes per cápita tienen distribuciones con colas
    muy pesadas (algunos municipios pequeños generan ratios extremos). La
    winsorización limita la influencia de outliers sin eliminar observaciones,
    lo que es más conservador que truncar.

    Las columnas originales _pc se mantienen intactas — las winsorizadas
    llevan sufijo _w (ej: ncont_total_m_pc_w).
    """
    print(f"\n{'='*70}")
    print("REC 6: Winsorización de outcomes per cápita (p1–p99)")
    print(f"{'='*70}")

    # Identificar todas las columnas per cápita
    cols_pc = [c for c in df.columns if c.endswith("_pc")]
    print(f"  Columnas per cápita encontradas: {len(cols_pc)}")

    stats = []  # Para el reporte

    for col in cols_pc:
        col_w = f"{col}_w"
        # Calcular percentiles (ignorando NaN)
        p1 = df[col].quantile(0.01)
        p99 = df[col].quantile(0.99)

        # Clipear: valores < p1 → p1, valores > p99 → p99
        df[col_w] = df[col].clip(lower=p1, upper=p99)

        # Contar cuántos valores fueron afectados
        n_below = (df[col] < p1).sum()
        n_above = (df[col] > p99).sum()

        stats.append({
            "columna": col_w,
            "p1": p1,
            "p99": p99,
            "n_clip_inferior": int(n_below),
            "n_clip_superior": int(n_above),
        })

    # Mostrar resumen
    print(f"\n  {'Columna':<35} {'p1':>10} {'p99':>12} {'Clip↓':>7} {'Clip↑':>7}")
    print(f"  {'-'*35} {'-'*10} {'-'*12} {'-'*7} {'-'*7}")
    for s in stats[:10]:  # Primeras 10 para no saturar la terminal
        print(f"  {s['columna']:<35} {s['p1']:>10.2f} {s['p99']:>12.2f} "
              f"{s['n_clip_inferior']:>7,} {s['n_clip_superior']:>7,}")
    if len(stats) > 10:
        print(f"  ... ({len(stats) - 10} columnas más)")

    print(f"\n  ✓ {len(cols_pc)} columnas winsorizadas creadas (sufijo _w)")
    return df, stats


# ═══════════════════════════════════════════════════════════════════════════════
# Rec 7: Ratio brecha de género (outcome_m / outcome_h)
# ═══════════════════════════════════════════════════════════════════════════════
def crear_ratio_genero(df):
    """
    Crea columnas de ratio de género = outcome_m_pc / outcome_h_pc para cada
    producto financiero. Un ratio < 1 indica que las mujeres tienen menos
    que los hombres; > 1 significa lo contrario.

    Columnas creadas (prefijo ratio_mh_):
      - ratio_mh_ncont_ahorro, ratio_mh_ncont_plazo, ...
      - ratio_mh_saldocont_ahorro, ratio_mh_saldocont_total, ...
      - ratio_mh_numtar_deb, ratio_mh_numtar_cred
      - ratio_mh_numcontcred_hip

    Protección: Cuando outcome_h_pc = 0, el ratio es NaN (indeterminado).

    Justificación: Este ratio es la variable de interés principal para medir
    si la presencia de una alcaldesa reduce la brecha de género en inclusión
    financiera.
    """
    print(f"\n{'='*70}")
    print("REC 7: Ratio brecha de género (M/H)")
    print(f"{'='*70}")

    # Encontrar pares (m_pc, h_pc) para el mismo producto
    cols_m = [c for c in df.columns if c.endswith("_m_pc") and not c.endswith("_w")]
    pares_ratio = []

    for col_m in cols_m:
        # Construir la columna _h_pc correspondiente
        col_h = col_m.replace("_m_pc", "_h_pc")
        if col_h not in df.columns:
            continue

        # Extraer el nombre del producto (ej: ncont_ahorro → "ncont_ahorro")
        producto = col_m.replace("_m_pc", "")
        col_ratio = f"ratio_mh_{producto}"
        pares_ratio.append((col_m, col_h, col_ratio, producto))

    print(f"  Pares M/H encontrados: {len(pares_ratio)}")

    for col_m, col_h, col_ratio, producto in pares_ratio:
        # Protección ÷0: reemplazar 0 por NaN en el denominador
        denom = df[col_h].replace(0, np.nan)
        df[col_ratio] = (df[col_m] / denom).round(6)

        media = df[col_ratio].mean()
        mediana = df[col_ratio].median()
        n_nan = df[col_ratio].isna().sum()
        print(f"  ✓ {col_ratio:<35} — media: {media:.4f}  "
              f"mediana: {mediana:.4f}  NaN: {n_nan:,}")

    print(f"\n  ✓ {len(pares_ratio)} columnas de ratio M/H creadas")
    return df, pares_ratio


# ═══════════════════════════════════════════════════════════════════════════════
# Rec 8: ever_alcaldesa — indicador a nivel municipio
# ═══════════════════════════════════════════════════════════════════════════════
def crear_ever_alcaldesa(df):
    """
    Crea la variable `ever_alcaldesa` = 1 si el municipio (cve_mun) tuvo
    alcaldesa (alcaldesa_final = 1) en CUALQUIER trimestre del panel.

    Esto captura la variación cross-sectional: separa municipios que en
    algún momento tuvieron una alcaldesa de los que nunca la tuvieron.

    Útil para:
      - Subgrupo de análisis: ¿el efecto es diferente en municipios que
        alguna vez tuvieron alcaldesa vs los que nunca?
      - Balance check previo a DiD

    Se asigna el mismo valor a todos los trimestres de cada municipio.
    """
    print(f"\n{'='*70}")
    print("REC 8: ever_alcaldesa (indicador a nivel municipio)")
    print(f"{'='*70}")

    # Si la columna ya existe (re-ejecución), eliminarla primero
    if "ever_alcaldesa" in df.columns:
        df = df.drop(columns=["ever_alcaldesa"])

    # Calcular max(alcaldesa_final) por municipio
    ever = df.groupby("cve_mun")["alcaldesa_final"].max().reset_index()
    ever.columns = ["cve_mun", "ever_alcaldesa"]

    # Merge de vuelta al panel (cada mun-trimestre recibe el mismo valor)
    n_before = len(df)
    df = df.merge(ever, on="cve_mun", how="left")
    assert len(df) == n_before, "Merge cambió el número de filas!"

    # Estadísticas
    n_ever = (df.groupby("cve_mun")["ever_alcaldesa"].first() == 1).sum()
    n_never = (df.groupby("cve_mun")["ever_alcaldesa"].first() == 0).sum()
    total_mun = n_ever + n_never
    pct_ever = n_ever / total_mun * 100

    print(f"  ✓ ever_alcaldesa creada")
    print(f"    Municipios con alcaldesa alguna vez: {n_ever:,} ({pct_ever:.1f}%)")
    print(f"    Municipios sin alcaldesa nunca:      {n_never:,} ({100 - pct_ever:.1f}%)")
    print(f"    Total municipios:                    {total_mun:,}")

    return df, {"n_ever": int(n_ever), "n_never": int(n_never), "pct_ever": round(pct_ever, 1)}


# ═══════════════════════════════════════════════════════════════════════════════
# Rec 9: Estandarización de IDs — cvegeo_mun como ID canónico
# ═══════════════════════════════════════════════════════════════════════════════
def estandarizar_ids(df, conn):
    """
    Estandariza los identificadores geográficos:
      - Verifica que cvegeo_mun es consistente (5 dígitos, texto, sin NULLs)
      - Crea un índice sobre cvegeo_mun para joins eficientes con catálogos INEGI
      - Verifica consistencia entre cve_mun (int), cve_ent, cve_mun3 y cvegeo_mun

    Justificación: La clave INEGI estándar para municipios es el código de
    5 dígitos (2 de entidad + 3 de municipio). Usar cvegeo_mun como ID
    canónico facilita merges con marcos geoestadísticos, censos, etc.
    """
    print(f"\n{'='*70}")
    print("REC 9: Estandarización de IDs — cvegeo_mun")
    print(f"{'='*70}")

    # 1. Verificar que cvegeo_mun no tiene NULLs
    n_null = df["cvegeo_mun"].isna().sum()
    print(f"  ✓ NULLs en cvegeo_mun: {n_null}")

    # 2. Verificar formato: 5 dígitos texto
    longitudes = df["cvegeo_mun"].str.len().value_counts()
    print(f"  ✓ Longitudes de cvegeo_mun: {dict(longitudes)}")

    # 3. Verificar consistencia con cve_ent y cve_mun3
    # cvegeo_mun debería ser cve_ent || cve_mun3
    df["_check_cvegeo"] = df["cve_ent"].astype(str) + df["cve_mun3"].astype(str)
    inconsistentes = (df["cvegeo_mun"] != df["_check_cvegeo"]).sum()
    df = df.drop(columns=["_check_cvegeo"])
    print(f"  ✓ Inconsistencias cvegeo_mun vs cve_ent+cve_mun3: {inconsistentes}")

    # 4. Verificar unicidad por municipio
    cvegeo_por_mun = df.groupby("cve_mun")["cvegeo_mun"].nunique()
    multi_cvegeo = (cvegeo_por_mun > 1).sum()
    print(f"  ✓ Municipios con múltiples cvegeo_mun: {multi_cvegeo}")

    # 5. Crear índice en PostgreSQL para joins eficientes
    try:
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_clean_cvegeo_mun "
            "ON inclusion_financiera_clean (cvegeo_mun)"
        ))
        print(f"  ✓ Índice idx_clean_cvegeo_mun creado sobre inclusion_financiera_clean")
    except Exception as e:
        print(f"  ⚠ Índice ya existe o error: {e}")

    # 6. Número de municipios únicos por cada ID
    n_cve_mun = df["cve_mun"].nunique()
    n_cvegeo = df["cvegeo_mun"].nunique()
    print(f"\n  Municipios únicos por ID:")
    print(f"    cve_mun (int):    {n_cve_mun:,}")
    print(f"    cvegeo_mun (str): {n_cvegeo:,}")

    stats = {
        "n_null": int(n_null),
        "longitudes": {str(k): int(v) for k, v in longitudes.items()},
        "inconsistentes": int(inconsistentes),
        "multi_cvegeo": int(multi_cvegeo),
        "n_mun_cve_mun": int(n_cve_mun),
        "n_mun_cvegeo": int(n_cvegeo),
    }

    return df, stats


# ═══════════════════════════════════════════════════════════════════════════════
# Pipeline principal
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    """Pipeline de transformaciones de alta prioridad (Recs 5–9)."""
    print("=" * 70)
    print("TRANSFORMACIONES ALTAS — Recomendaciones 🟡 del EDA (5–9)")
    print("=" * 70)

    # ── 1. Cargar datos de la tabla limpia ─────────────────────────────────
    print("\n1. Cargando datos desde inclusion_financiera_clean...")
    df = pd.read_sql("SELECT * FROM inclusion_financiera_clean", engine)
    print(f"   ✓ {df.shape[0]:,} filas × {df.shape[1]} columnas cargadas")

    # Limpiar columnas de ejecuciones anteriores (idempotencia)
    cols_to_drop = [c for c in df.columns
                    if c.startswith("log_pob")
                    or c.endswith("_pc_w")
                    or c.startswith("ratio_mh_")
                    or c == "ever_alcaldesa"]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
        print(f"   ✓ {len(cols_to_drop)} columnas de ejecución anterior eliminadas (idempotencia)")

    n_cols_antes = df.shape[1]
    print(f"   ✓ Columnas base: {n_cols_antes}")

    # ── 2. Rec 5: log(población) ──────────────────────────────────────────
    print("\n2. Aplicando Rec 5: log(población)...")
    df = aplicar_log_poblacion(df)

    # ── 3. Rec 6: Winsorización ───────────────────────────────────────────
    print("\n3. Aplicando Rec 6: Winsorización per cápita (p1–p99)...")
    df, stats_winsor = winsorizar_per_capita(df)

    # ── 4. Rec 7: Ratio M/H ──────────────────────────────────────────────
    print("\n4. Aplicando Rec 7: Ratio brecha de género (M/H)...")
    df, pares_ratio = crear_ratio_genero(df)

    # ── 5. Rec 8: ever_alcaldesa ──────────────────────────────────────────
    print("\n5. Aplicando Rec 8: ever_alcaldesa...")
    df, stats_ever = crear_ever_alcaldesa(df)

    # ── 6. Guardar tabla actualizada en PostgreSQL ────────────────────────
    print(f"\n6. Guardando tabla actualizada en PostgreSQL...")

    # Eliminar y recrear (para mantener idempotencia)
    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS inclusion_financiera_clean"))

    # chunksize bajo porque con 296+ columnas, method='multi' excede el
    # límite de 65535 parámetros de PostgreSQL (296 cols × 200 rows = 59,200)
    df.to_sql(
        "inclusion_financiera_clean",
        engine,
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=200,
    )

    # Agregar PK y índice
    with engine.begin() as conn:
        conn.execute(text("""
            ALTER TABLE inclusion_financiera_clean
            ADD CONSTRAINT pk_inclusion_financiera_clean
            PRIMARY KEY (cve_mun, periodo_trimestre)
        """))

        # ── 7. Rec 9: Estandarización de IDs ─────────────────────────────
        print("\n7. Aplicando Rec 9: Estandarización de IDs...")
        df_check, stats_ids = estandarizar_ids(df, conn)

    print(f"\n   ✓ Tabla 'inclusion_financiera_clean' actualizada")
    print(f"   ✓ PK (cve_mun, periodo_trimestre) restaurada")

    # ── 8. Resumen final ──────────────────────────────────────────────────
    n_cols_despues = df.shape[1]
    n_nuevas = n_cols_despues - n_cols_antes

    print(f"\n{'='*70}")
    print("RESUMEN FINAL")
    print(f"{'='*70}")
    print(f"  Tabla:             inclusion_financiera_clean")
    print(f"  Filas:             {df.shape[0]:,} (sin cambios)")
    print(f"  Columnas antes:    {n_cols_antes}")
    print(f"  Columnas después:  {n_cols_despues}")
    print(f"  Columnas nuevas:   +{n_nuevas}")
    print(f"\n  Desglose de columnas nuevas:")
    print(f"    Rec 5 (log población):   +4")
    print(f"    Rec 6 (winsorización):   +{len(stats_winsor)}")
    print(f"    Rec 7 (ratio M/H):       +{len(pares_ratio)}")
    print(f"    Rec 8 (ever_alcaldesa):  +1")
    print(f"    Rec 9 (índice cvegeo):   +0 (solo índice DB)")
    print(f"    Total:                   +{n_nuevas}")
    print(f"\n  ever_alcaldesa: {stats_ever['n_ever']:,} municipios "
          f"({stats_ever['pct_ever']}%) tuvieron alcaldesa")
    print(f"\n  La tabla original 'inclusion_financiera' NO fue modificada.")

    return df, {
        "stats_winsor": stats_winsor,
        "pares_ratio": pares_ratio,
        "stats_ever": stats_ever,
        "stats_ids": stats_ids,
        "n_cols_antes": n_cols_antes,
        "n_cols_despues": n_cols_despues,
    }


if __name__ == "__main__":
    df_clean, resultados = main()
