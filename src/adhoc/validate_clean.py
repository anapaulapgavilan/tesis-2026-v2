"""Quick validation of the clean table."""
from sqlalchemy import text
from tesis_alcaldesas.config import get_engine
engine = get_engine()

with engine.connect() as conn:
    r = conn.execute(text("SELECT COUNT(*) FROM inclusion_financiera_clean"))
    print(f"Filas: {r.scalar():,}")

    r = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_name = 'inclusion_financiera_clean'"
    ))
    print(f"Columnas: {r.scalar()}")

    r = conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'inclusion_financiera_clean' "
        "AND column_name LIKE '%_pc' ORDER BY column_name"
    ))
    pc_cols = [row[0] for row in r]
    print(f"Columnas per cápita: {len(pc_cols)}")
    for c in pc_cols[:8]:
        print(f"  {c}")
    print(f"  ... y {len(pc_cols)-8} más" if len(pc_cols) > 8 else "")

    r = conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name = 'inclusion_financiera_clean' "
        "AND column_name IN ('hist_state_available','missing_quarters_alcaldesa','ok_panel_completo_final')"
    ))
    constantes = [row[0] for row in r]
    print(f"Constantes restantes (debería ser 0): {len(constantes)}")

    r = conn.execute(text(
        "SELECT ROUND(AVG(ncont_total_m_pc)::numeric,2) as media, "
        "ROUND(MIN(ncont_total_m_pc)::numeric,2) as min, "
        "ROUND(MAX(ncont_total_m_pc)::numeric,2) as max "
        "FROM inclusion_financiera_clean"
    ))
    row = r.fetchone()
    print(f"\nncont_total_m_pc: media={row[0]}, min={row[1]}, max={row[2]}")
