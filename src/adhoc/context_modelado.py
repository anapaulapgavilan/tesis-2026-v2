"""Quick context query for the modeling proposal."""
from sqlalchemy import text
from tesis_alcaldesas.config import get_engine
engine = get_engine()

with engine.connect() as c:
    # Forward/lag/transition columns
    r = c.execute(text("""SELECT column_name FROM information_schema.columns
        WHERE table_name='inclusion_financiera_clean'
        AND (column_name LIKE '%/_f1%' ESCAPE '/'
             OR column_name LIKE '%/_f2%' ESCAPE '/'
             OR column_name LIKE '%/_f3%' ESCAPE '/'
             OR column_name LIKE '%/_l1%' ESCAPE '/'
             OR column_name LIKE '%/_l2%' ESCAPE '/'
             OR column_name LIKE '%/_l3%' ESCAPE '/'
             OR column_name LIKE '%transition%'
             OR column_name LIKE '%excl/_trans%' ESCAPE '/')
        ORDER BY column_name"""))
    print("=== LEADS / LAGS / TRANSITIONS ===")
    for row in r:
        print(f"  {row[0]}")

    # All alcaldesa columns
    r = c.execute(text("""SELECT column_name FROM information_schema.columns
        WHERE table_name='inclusion_financiera_clean'
        AND column_name LIKE 'alcaldesa%' ORDER BY column_name"""))
    print("\n=== ALCALDESA COLUMNS ===")
    for row in r:
        print(f"  {row[0]}")

    # tipo_pob distinct values
    r = c.execute(text("""SELECT tipo_pob, COUNT(*) FROM inclusion_financiera_clean
        GROUP BY tipo_pob ORDER BY tipo_pob"""))
    print("\n=== TIPO_POB ===")
    for row in r:
        print(f"  {row[0]}: {row[1]}")

    # Panel dimensions
    r = c.execute(text("SELECT COUNT(DISTINCT cve_ent) FROM inclusion_financiera_clean"))
    print(f"\nEntidades: {r.scalar()}")
    r = c.execute(text("SELECT COUNT(DISTINCT cve_mun) FROM inclusion_financiera_clean"))
    print(f"Municipios: {r.scalar()}")
    r = c.execute(text("SELECT COUNT(DISTINCT periodo_trimestre) FROM inclusion_financiera_clean"))
    print(f"Periodos: {r.scalar()}")

    # ever_alcaldesa distribution
    r = c.execute(text("""SELECT ever_alcaldesa, COUNT(DISTINCT cve_mun)
        FROM inclusion_financiera_clean GROUP BY ever_alcaldesa"""))
    print("\n=== EVER_ALCALDESA ===")
    for row in r:
        print(f"  {row[0]}: {row[1]} municipios")

    # Switchers: municipios where alcaldesa_final changes at least once
    r = c.execute(text("""
        WITH changes AS (
            SELECT cve_mun,
                   alcaldesa_final - LAG(alcaldesa_final) OVER (PARTITION BY cve_mun ORDER BY periodo_trimestre) AS delta
            FROM inclusion_financiera_clean
        )
        SELECT COUNT(DISTINCT cve_mun) FROM changes WHERE delta != 0
    """))
    print(f"\nSwitchers (cambian al menos una vez): {r.scalar()}")

    # Treatment timing distribution
    r = c.execute(text("""
        WITH first_treat AS (
            SELECT cve_mun, MIN(periodo_trimestre) AS first_t
            FROM inclusion_financiera_clean
            WHERE alcaldesa_final = 1
            GROUP BY cve_mun
        )
        SELECT first_t, COUNT(*) FROM first_treat GROUP BY first_t ORDER BY first_t
    """))
    print("\n=== FIRST TREATMENT PERIOD ===")
    for row in r:
        print(f"  {row[0]}: {row[1]} municipios")
