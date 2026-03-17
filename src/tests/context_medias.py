"""Gather context for medium-priority recommendations (10-12)."""
from sqlalchemy import text
from tesis_alcaldesas.config import get_engine

e = get_engine()
with e.connect() as c:
    # --- Rec 12: tipo_pob NULLs ---
    r = c.execute(text(
        "SELECT tipo_pob, COUNT(*) AS n FROM inclusion_financiera_clean "
        "GROUP BY tipo_pob ORDER BY tipo_pob"
    ))
    print("=== tipo_pob distribution ===")
    for row in r:
        print(f"  {str(row[0]):20s}  {row[1]:>6,}")

    r = c.execute(text(
        "SELECT DISTINCT cve_mun, municipio, estado, pob, cvegeo_mun "
        "FROM inclusion_financiera_clean WHERE tipo_pob IS NULL"
    ))
    print("\n=== Municipios con tipo_pob NULL ===")
    for row in r:
        print(f"  cve_mun={row[0]}  {row[1]}, {row[2]}  pob={row[3]:,}  cvegeo={row[4]}")

    # Population ranges by tipo_pob
    r = c.execute(text(
        "SELECT tipo_pob, MIN(pob) AS minp, MAX(pob) AS maxp, "
        "ROUND(AVG(pob))::int AS avgp, COUNT(DISTINCT cve_mun) AS n_mun "
        "FROM inclusion_financiera_clean WHERE tipo_pob IS NOT NULL "
        "GROUP BY tipo_pob ORDER BY MIN(pob)"
    ))
    print("\n=== tipo_pob population ranges ===")
    print(f"  {'tipo_pob':20s} {'min':>8} {'max':>10} {'avg':>8} {'n_mun':>6}")
    for row in r:
        print(f"  {str(row[0]):20s} {row[1]:>8,} {row[2]:>10,} {row[3]:>8,} {row[4]:>6}")

    # --- Rec 10: alcaldesa_acumulado ---
    r = c.execute(text(
        "SELECT cve_mun, periodo_trimestre, alcaldesa_final "
        "FROM inclusion_financiera_clean "
        "WHERE cve_mun = (SELECT cve_mun FROM inclusion_financiera_clean "
        "                 WHERE alcaldesa_final = 1 "
        "                 GROUP BY cve_mun HAVING COUNT(*) BETWEEN 5 AND 12 LIMIT 1) "
        "ORDER BY periodo_trimestre"
    ))
    print("\n=== Sample switcher (alcaldesa_final over time) ===")
    for row in r:
        print(f"  mun={row[0]}  t={row[1]}  alcaldesa={row[2]}")

    # --- Rec 11: asinh outcomes ---
    r = c.execute(text("""
        SELECT
            ROUND(AVG(ncont_total_m_pc)::numeric, 2) AS mean_ncont,
            ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ncont_total_m_pc))::numeric, 2) AS med_ncont,
            ROUND(STDDEV(ncont_total_m_pc)::numeric, 2) AS sd_ncont,
            ROUND(MAX(ncont_total_m_pc)::numeric, 2) AS max_ncont,
            ROUND(AVG(saldocont_total_m_pc)::numeric, 2) AS mean_saldo,
            ROUND((PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY saldocont_total_m_pc))::numeric, 2) AS med_saldo,
            ROUND(MAX(saldocont_total_m_pc)::numeric, 2) AS max_saldo
        FROM inclusion_financiera_clean
    """))
    row = r.fetchone()
    print(f"\n=== Per capita skewness check ===")
    print(f"  ncont_total_m_pc:     mean={row[0]}  median={row[1]}  sd={row[2]}  max={row[3]}")
    print(f"  saldocont_total_m_pc: mean={row[4]}  median={row[5]}  max={row[6]}")

    n = c.execute(text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_name='inclusion_financiera_clean'"
    )).scalar()
    print(f"\n=== Current state: {n} columns ===")
