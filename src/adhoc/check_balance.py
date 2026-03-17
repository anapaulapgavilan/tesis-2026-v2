"""Quick check for incomplete panels."""
from sqlalchemy import text
from tesis_alcaldesas.config import get_engine
engine = get_engine()
with engine.connect() as c:
    r = c.execute(text("""
        SELECT cve_mun, COUNT(*) AS n_per
        FROM inclusion_financiera_clean
        GROUP BY cve_mun
        HAVING COUNT(*) < 17
        ORDER BY n_per, cve_mun
    """))
    rows = r.fetchall()
    print(f"Municipios con panel incompleto: {len(rows)}")
    for row in rows[:20]:
        print(f"  cve_mun={row[0]}  periodos={row[1]}")

    # region distinct
    r = c.execute(text("SELECT DISTINCT region, COUNT(*) FROM inclusion_financiera_clean GROUP BY region ORDER BY region"))
    print("\nregion:")
    for row in r: print(f"  {row[0]}: {row[1]}")

    # desc_ent/desc_mun existence
    r = c.execute(text("""SELECT column_name FROM information_schema.columns
        WHERE table_name='inclusion_financiera_clean' AND column_name IN ('desc_ent','desc_mun','estado','municipio')
        ORDER BY column_name"""))
    print("\nColumnas descriptoras geo:")
    for row in r: print(f"  {row[0]}")
