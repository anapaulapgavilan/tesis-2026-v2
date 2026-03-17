"""
Tests de validación para las transformaciones críticas (🔴).
Verifica que inclusion_financiera_clean fue creada correctamente.
"""
from sqlalchemy import text
from tesis_alcaldesas.config import get_engine

engine = get_engine()
results = []

with engine.connect() as conn:
    # Test 1: Table exists with correct row count
    n = conn.execute(text("SELECT COUNT(*) FROM inclusion_financiera_clean")).scalar()
    ok = n == 41905
    results.append(ok)
    print(f"Test 1 - Tabla existe ({n:,} filas): {'✓' if ok else '✗'}")

    # Test 2: Constant columns removed
    r = conn.execute(text(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_name='inclusion_financiera_clean' "
        "AND column_name IN ('hist_state_available','missing_quarters_alcaldesa','ok_panel_completo_final')"
    ))
    consts = [row[0] for row in r]
    ok = len(consts) == 0
    results.append(ok)
    print(f"Test 2 - Constantes eliminadas ({len(consts)} restantes): {'✓' if ok else '✗'}")

    # Test 3: 51 per cápita columns
    npc = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_name='inclusion_financiera_clean' AND column_name LIKE '%\\_pc' ESCAPE '\\'"
    )).scalar()
    ok = npc == 51
    results.append(ok)
    print(f"Test 3 - Columnas per cápita ({npc}): {'✓' if ok else '✗'}")

    # Test 4: No infinities
    ninf = conn.execute(text(
        "SELECT COUNT(*) FROM inclusion_financiera_clean "
        "WHERE ncont_total_m_pc = 'Infinity' OR ncont_total_m_pc = '-Infinity'"
    )).scalar()
    ok = ninf == 0
    results.append(ok)
    print(f"Test 4 - Sin infinitos ({ninf}): {'✓' if ok else '✗'}")

    # Test 5: No negatives
    nneg = conn.execute(text(
        "SELECT COUNT(*) FROM inclusion_financiera_clean WHERE ncont_total_m_pc < 0"
    )).scalar()
    ok = nneg == 0
    results.append(ok)
    print(f"Test 5 - Sin negativos ({nneg}): {'✓' if ok else '✗'}")

    # Test 6: Original table untouched
    norig = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='inclusion_financiera'"
    )).scalar()
    ok = norig == 175
    results.append(ok)
    print(f"Test 6 - Tabla original intacta ({norig} cols): {'✓' if ok else '✗'}")

    # Test 7: PK has no duplicates
    ndups = conn.execute(text(
        "SELECT COUNT(*) FROM ("
        "  SELECT cve_mun, periodo_trimestre, COUNT(*) "
        "  FROM inclusion_financiera_clean "
        "  GROUP BY cve_mun, periodo_trimestre HAVING COUNT(*) > 1"
        ") sub"
    )).scalar()
    ok = ndups == 0
    results.append(ok)
    print(f"Test 7 - PK sin duplicados ({ndups}): {'✓' if ok else '✗'}")

    # Test 8: Spot-check per cápita formula
    rows = conn.execute(text(
        "SELECT ncont_total_m, pob_adulta_m, ncont_total_m_pc, "
        "ROUND((ncont_total_m::numeric * 10000 / NULLIF(pob_adulta_m, 0))::numeric, 4) AS expected "
        "FROM inclusion_financiera_clean WHERE pob_adulta_m > 0 LIMIT 5"
    )).fetchall()
    ok = all(abs(float(row[2]) - float(row[3])) < 0.01 for row in rows)
    results.append(ok)
    print(f"Test 8 - Fórmula per cápita correcta: {'✓' if ok else '✗'}")

print()
if all(results):
    print("=== ✓ Todas las pruebas de Recs Críticas PASARON ===")
else:
    failed = sum(1 for r in results if not r)
    print(f"=== ✗ {failed} prueba(s) FALLARON ===")
