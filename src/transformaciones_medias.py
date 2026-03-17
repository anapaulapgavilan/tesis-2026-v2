"""
Transformaciones Medias — Recomendaciones 🟢 del EDA (10–12)
=============================================================

Este script aplica las 3 recomendaciones de MEDIA prioridad identificadas en el EDA
sobre la tabla `inclusion_financiera_clean` que ya contiene las transformaciones
críticas (Recs 1–4) y altas (Recs 5–9).

Transformaciones:
  10. alcaldesa_acumulado: nº trimestres acumulados con alcaldesa hasta t
  11. asinh(outcomes per cápita): transformación para distribuciones asimétricas
  12. tipo_pob NULLs: imputar 2 municipios por rango de población

La tabla `inclusion_financiera_clean` se actualiza IN PLACE.
La tabla original `inclusion_financiera` NO se toca.

Uso:
    python src/transformaciones_medias.py

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
# Rec 10: alcaldesa_acumulado — trimestres acumulados con alcaldesa
# ═══════════════════════════════════════════════════════════════════════════════
def crear_alcaldesa_acumulado(df):
    """
    Crea la variable `alcaldesa_acumulado` = suma acumulada de `alcaldesa_final`
    por municipio a lo largo del tiempo. Captura la "dosis" de exposición al
    tratamiento.

    Ejemplo para municipio 1011:
      t=2018Q3 alcaldesa=1 --> acumulado=1
      t=2018Q4 alcaldesa=1 --> acumulado=2
      t=2019Q3 alcaldesa=1 --> acumulado=5
      t=2019Q4 alcaldesa=0 --> acumulado=5  (no suma)
      t=2021Q4 alcaldesa=1 --> acumulado=6  (retoma)

    Justificación: Complementa al indicador binario `alcaldesa_final` al capturar
    la intensidad acumulada del tratamiento. Permite evaluar si el efecto de tener
    una alcaldesa es creciente con el tiempo de exposición (efecto dosis-respuesta).
    """
    print(f"\n{'='*70}")
    print("REC 10: alcaldesa_acumulado (trimestres acumulados)")
    print(f"{'='*70}")

    # Si ya existe (idempotencia), eliminar
    if "alcaldesa_acumulado" in df.columns:
        df = df.drop(columns=["alcaldesa_acumulado"])

    # Ordenar por municipio y tiempo para garantizar la suma acumulada correcta
    df = df.sort_values(["cve_mun", "periodo_trimestre"]).reset_index(drop=True)

    # Suma acumulada de alcaldesa_final dentro de cada municipio
    df["alcaldesa_acumulado"] = df.groupby("cve_mun")["alcaldesa_final"].cumsum()

    # Estadísticas
    stats = {
        "media": round(float(df["alcaldesa_acumulado"].mean()), 2),
        "mediana": round(float(df["alcaldesa_acumulado"].median()), 2),
        "max": int(df["alcaldesa_acumulado"].max()),
        "pct_cero": round(float((df["alcaldesa_acumulado"] == 0).mean() * 100), 1),
    }

    # Distribución
    dist = df["alcaldesa_acumulado"].value_counts().sort_index()
    print(f"  OK alcaldesa_acumulado creada")
    print(f"    Media:    {stats['media']}")
    print(f"    Mediana:  {stats['mediana']}")
    print(f"    Max:      {stats['max']} (= todos los 17 trimestres con alcaldesa)")
    print(f"    % cero:   {stats['pct_cero']}% de obs nunca han tenido alcaldesa hasta ese t")
    print(f"\n    Distribución (top 5 valores):")
    for val, cnt in dist.head(5).items():
        print(f"      acumulado={val:>2}: {cnt:>6,} obs")

    # Verificar con un ejemplo
    sample = df[df["cve_mun"] == df[df["alcaldesa_final"] == 1]["cve_mun"].iloc[0]]
    sample = sample[["cve_mun", "periodo_trimestre", "alcaldesa_final", "alcaldesa_acumulado"]].head(6)
    print(f"\n    Ejemplo (primer switcher):")
    for _, row in sample.iterrows():
        print(f"      t={row['periodo_trimestre']}  alcaldesa={int(row['alcaldesa_final'])}  "
              f"acumulado={int(row['alcaldesa_acumulado'])}")

    return df, stats


# ═══════════════════════════════════════════════════════════════════════════════
# Rec 11: asinh(outcomes per cápita)
# ═══════════════════════════════════════════════════════════════════════════════
def crear_asinh_outcomes(df):
    """
    Crea versiones asinh-transformadas de las columnas per cápita (_pc).
    La transformación es: asinh(x) = ln(x + sqrt(x² + 1)).

    Columnas creadas: sufijo _asinh (ej: ncont_total_m_pc_asinh).

    Justificación: Las distribuciones per cápita son extremadamente asimétricas
    (mean/median ratio de 6x a 390x). La transformación asinh:
    - Es definida para x = 0 (a diferencia de log)
    - Se comporta como log(2x) para x grandes
    - Es simétrica: asinh(-x) = -asinh(x)
    - Preserva los ceros (asinh(0) = 0)
    - Los coeficientes se interpretan como semi-elasticidades

    Ventaja sobre log(1+x): asinh no depende de la escala de la variable (el "+1"
    en log(1+x) distorsiona si la variable tiene rango [0, 0.01] vs [0, 1000000]).
    """
    print(f"\n{'='*70}")
    print("REC 11: asinh(outcomes per cápita)")
    print(f"{'='*70}")

    # Identificar columnas per cápita (originales, no winsorizadas)
    cols_pc = [c for c in df.columns if c.endswith("_pc") and not c.endswith("_w")]
    print(f"  Columnas per cápita encontradas: {len(cols_pc)}")

    # Eliminar columnas de ejecuciones anteriores (idempotencia)
    old_asinh = [c for c in df.columns if c.endswith("_pc_asinh")]
    if old_asinh:
        df = df.drop(columns=old_asinh)
        print(f"  OK {len(old_asinh)} columnas asinh anteriores eliminadas (idempotencia)")

    stats = []
    for col in cols_pc:
        col_asinh = f"{col}_asinh"
        df[col_asinh] = np.arcsinh(df[col])

        media_orig = df[col].mean()
        media_asinh = df[col_asinh].mean()
        stats.append({
            "columna": col_asinh,
            "media_orig": round(float(media_orig), 2),
            "media_asinh": round(float(media_asinh), 2),
        })

    # Mostrar resumen
    print(f"\n  {'Columna':<35} {'Media orig':>12} {'Media asinh':>12}")
    print(f"  {'-'*35} {'-'*12} {'-'*12}")
    for s in stats[:8]:
        print(f"  {s['columna']:<35} {s['media_orig']:>12,.2f} {s['media_asinh']:>12.4f}")
    if len(stats) > 8:
        print(f"  ... ({len(stats) - 8} columnas más)")

    print(f"\n  OK {len(cols_pc)} columnas asinh creadas (sufijo _asinh)")

    return df, stats


# ═══════════════════════════════════════════════════════════════════════════════
# Rec 12: Imputar tipo_pob NULLs
# ═══════════════════════════════════════════════════════════════════════════════
def imputar_tipo_pob(df):
    """
    Imputa los 2 NULLs de `tipo_pob` asignando la categoría correspondiente
    según el rango de población del municipio.

    Rangos observados:
      Rural:          81 – 5,000
      En Transicion:  5,001 – 14,997
      Semi-urbano:    15,009 – 49,920
      Urbano:         42,664 – 299,635
      Semi-metropoli: 300,295 – 995,129
      Metropoli:      1,003,530 – 1,922,523

    Municipios afectados:
      - cve_mun=2007  San Felipe, BC     pob=20,320 --> Semi-urbano (rango 15k–50k)
      - cve_mun=4013  Dzitbalché, Camp.  pob=16,568 --> Semi-urbano (rango 15k–50k)
    """
    print(f"\n{'='*70}")
    print("REC 12: Imputar tipo_pob NULLs")
    print(f"{'='*70}")

    n_null_antes = df["tipo_pob"].isna().sum()
    print(f"  NULLs antes: {n_null_antes}")

    if n_null_antes == 0:
        print(f"  OK No hay NULLs que imputar (ya resuelto)")
        return df, {"n_imputados": 0, "municipios": []}

    # Mostrar los municipios afectados
    nulls = df[df["tipo_pob"].isna()][["cve_mun", "municipio", "estado", "pob"]].drop_duplicates()

    municipios_imputados = []
    for _, row in nulls.iterrows():
        pob = row["pob"]
        # Asignar categoría según rangos observados
        if pob <= 5000:
            cat = "Rural"
        elif pob <= 15000:
            cat = "En Transicion"
        elif pob <= 50000:
            cat = "Semi-urbano"
        elif pob <= 300000:
            cat = "Urbano"
        elif pob <= 1000000:
            cat = "Semi-metropoli"
        else:
            cat = "Metropoli"

        mask = df["cve_mun"] == row["cve_mun"]
        n_rows = mask.sum()
        df.loc[mask, "tipo_pob"] = cat

        info = {
            "cve_mun": int(row["cve_mun"]),
            "municipio": row["municipio"],
            "estado": row["estado"],
            "pob": int(pob),
            "tipo_pob_asignado": cat,
            "filas_afectadas": int(n_rows),
        }
        municipios_imputados.append(info)
        print(f"  --> cve_mun={row['cve_mun']}  {row['municipio']}, {row['estado']}  "
              f"pob={pob:,} --> {cat} ({n_rows} filas)")

    n_null_despues = df["tipo_pob"].isna().sum()
    print(f"\n  OK NULLs después: {n_null_despues}")
    print(f"  OK {len(municipios_imputados)} municipio(s) imputado(s)")

    return df, {"n_imputados": len(municipios_imputados), "municipios": municipios_imputados}


# ═══════════════════════════════════════════════════════════════════════════════
# Pipeline principal
# ═══════════════════════════════════════════════════════════════════════════════
def main():
    """Pipeline de transformaciones de media prioridad (Recs 10–12)."""
    print("=" * 70)
    print("TRANSFORMACIONES MEDIAS — Recomendaciones 🟢 del EDA (10–12)")
    print("=" * 70)

    # ── 1. Cargar datos ───────────────────────────────────────────────────
    print("\n1. Cargando datos desde inclusion_financiera_clean...")
    df = pd.read_sql("SELECT * FROM inclusion_financiera_clean", engine)
    print(f"   OK {df.shape[0]:,} filas × {df.shape[1]} columnas cargadas")

    # Limpiar columnas de ejecuciones anteriores (idempotencia)
    cols_to_drop = [c for c in df.columns
                    if c == "alcaldesa_acumulado"
                    or c.endswith("_pc_asinh")]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
        print(f"   OK {len(cols_to_drop)} columnas de ejecución anterior eliminadas")

    n_cols_antes = df.shape[1]
    print(f"   OK Columnas base: {n_cols_antes}")

    # ── 2. Rec 10: alcaldesa_acumulado ────────────────────────────────────
    print("\n2. Aplicando Rec 10: alcaldesa_acumulado...")
    df, stats_acum = crear_alcaldesa_acumulado(df)

    # ── 3. Rec 11: asinh(outcomes) ────────────────────────────────────────
    print("\n3. Aplicando Rec 11: asinh(outcomes per cápita)...")
    df, stats_asinh = crear_asinh_outcomes(df)

    # ── 4. Rec 12: tipo_pob NULLs ────────────────────────────────────────
    print("\n4. Aplicando Rec 12: imputar tipo_pob NULLs...")
    df, stats_tipo = imputar_tipo_pob(df)

    # ── 5. Guardar tabla actualizada ──────────────────────────────────────
    print(f"\n5. Guardando tabla actualizada en PostgreSQL...")

    with engine.begin() as conn:
        conn.execute(text("DROP TABLE IF EXISTS inclusion_financiera_clean"))

    # chunksize bajo por el alto nº de columnas (~350)
    df.to_sql(
        "inclusion_financiera_clean",
        engine,
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=150,
    )

    # Restaurar PK e índice
    with engine.begin() as conn:
        conn.execute(text("""
            ALTER TABLE inclusion_financiera_clean
            ADD CONSTRAINT pk_inclusion_financiera_clean
            PRIMARY KEY (cve_mun, periodo_trimestre)
        """))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_clean_cvegeo_mun "
            "ON inclusion_financiera_clean (cvegeo_mun)"
        ))

    print(f"   OK Tabla 'inclusion_financiera_clean' actualizada")
    print(f"   OK PK + índice cvegeo_mun restaurados")

    # ── 6. Resumen final ──────────────────────────────────────────────────
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
    print(f"    Rec 10 (alcaldesa_acumulado):  +1")
    print(f"    Rec 11 (asinh outcomes):        +{len(stats_asinh)}")
    print(f"    Rec 12 (tipo_pob imputado):     +0 (corrección in-place)")
    print(f"    Total:                          +{n_nuevas}")
    print(f"\n  La tabla original 'inclusion_financiera' NO fue modificada.")

    return df, {
        "stats_acum": stats_acum,
        "stats_asinh": stats_asinh,
        "stats_tipo": stats_tipo,
        "n_cols_antes": n_cols_antes,
        "n_cols_despues": n_cols_despues,
    }


if __name__ == "__main__":
    df_clean, resultados = main()
