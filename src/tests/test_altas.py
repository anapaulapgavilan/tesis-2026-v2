"""
Tests de validación para las transformaciones altas 🟡 (Recs 5–9).
Verifica que inclusion_financiera_clean fue actualizada correctamente.
"""
from sqlalchemy import text
from tesis_alcaldesas.config import get_engine
import json

engine = get_engine()
results = []
data = {}  # Para guardar estadísticas para EDA_EXPLICACION_3

with engine.connect() as conn:
    # ── Pruebas generales ─────────────────────────────────────────────
    n_rows = conn.execute(text("SELECT COUNT(*) FROM inclusion_financiera_clean")).scalar()
    ok = n_rows == 41905
    results.append(ok)
    print(f"T1 - Filas correctas ({n_rows:,}): {'OK' if ok else 'FAIL'}")

    n_cols = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_name='inclusion_financiera_clean'"
    )).scalar()
    ok = n_cols >= 295  # 223 base + 4 log + 51 winsor + 17 ratio + 1 ever = 296
    results.append(ok)
    print(f"T2 - Total columnas ({n_cols}): {'OK' if ok else 'FAIL'}")

    # ── Rec 5: log(población) ─────────────────────────────────────────
    log_cols = ["log_pob", "log_pob_adulta", "log_pob_adulta_m", "log_pob_adulta_h"]
    for col in log_cols:
        exists = conn.execute(text(
            f"SELECT COUNT(*) FROM information_schema.columns "
            f"WHERE table_name='inclusion_financiera_clean' AND column_name='{col}'"
        )).scalar()
        ok = exists == 1
        results.append(ok)
    print(f"T3 - 4 log cols existen: {'OK' if all(results[-4:]) else 'FAIL'}")

    # Verificar que log es correcto: log_pob ≈ ln(pob + 1)
    row = conn.execute(text(
        "SELECT pob, log_pob, LN(pob + 1) AS expected "
        "FROM inclusion_financiera_clean WHERE pob > 100 LIMIT 1"
    )).fetchone()
    ok = abs(float(row[1]) - float(row[2])) < 0.001
    results.append(ok)
    print(f"T4 - log_pob = ln(pob+1): {'OK' if ok else 'FAIL'}")

    # Stats for log
    r = conn.execute(text(
        "SELECT AVG(log_pob), MIN(log_pob), MAX(log_pob) FROM inclusion_financiera_clean"
    )).fetchone()
    data["log_pob"] = {"media": round(float(r[0]), 4), "min": round(float(r[1]), 4), "max": round(float(r[2]), 4)}
    print(f"   log_pob: media={data['log_pob']['media']}, rango=[{data['log_pob']['min']}, {data['log_pob']['max']}]")

    # ── Rec 6: Winsorización ──────────────────────────────────────────
    n_w = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_name='inclusion_financiera_clean' AND column_name LIKE '%\\_pc\\_w' ESCAPE '\\'"
    )).scalar()
    ok = n_w == 51
    results.append(ok)
    print(f"T5 - Cols winsorizadas ({n_w}): {'OK' if ok else 'FAIL'}")

    # Verificar que winsorizado ≤ original max y ≥ original min
    r = conn.execute(text(
        "SELECT MAX(ncont_total_m_pc_w), MAX(ncont_total_m_pc) "
        "FROM inclusion_financiera_clean"
    )).fetchone()
    ok = float(r[0]) <= float(r[1])
    results.append(ok)
    print(f"T6 - Winsorizado ≤ original max: {'OK' if ok else 'FAIL'}")
    data["winsor_ejemplo"] = {"max_w": round(float(r[0]), 2), "max_orig": round(float(r[1]), 2)}

    # ── Rec 7: Ratios M/H ────────────────────────────────────────────
    n_ratio = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_name='inclusion_financiera_clean' AND column_name LIKE 'ratio\\_mh\\_%' ESCAPE '\\'"
    )).scalar()
    ok = n_ratio == 17
    results.append(ok)
    print(f"T7 - Ratios M/H ({n_ratio}): {'OK' if ok else 'FAIL'}")

    # Verificar fórmula: ratio = m_pc / h_pc
    r = conn.execute(text(
        "SELECT ncont_total_m_pc, ncont_total_h_pc, ratio_mh_ncont_total, "
        "ROUND((ncont_total_m_pc / NULLIF(ncont_total_h_pc, 0))::numeric, 6) AS expected "
        "FROM inclusion_financiera_clean "
        "WHERE ncont_total_h_pc > 0 LIMIT 5"
    )).fetchall()
    ok = all(abs(float(row[2]) - float(row[3])) < 0.001 for row in r)
    results.append(ok)
    print(f"T8 - Fórmula ratio correcta: {'OK' if ok else 'FAIL'}")

    # Key ratio stats
    r = conn.execute(text(
        "SELECT AVG(ratio_mh_ncont_total), "
        "PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY ratio_mh_ncont_total) "
        "FROM inclusion_financiera_clean WHERE ratio_mh_ncont_total IS NOT NULL"
    )).fetchone()
    data["ratio_ncont_total"] = {"media": round(float(r[0]), 4), "mediana": round(float(r[1]), 4)}
    print(f"   ratio_mh_ncont_total: media={data['ratio_ncont_total']['media']}, mediana={data['ratio_ncont_total']['mediana']}")

    # ── Rec 8: ever_alcaldesa ─────────────────────────────────────────
    exists = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_name='inclusion_financiera_clean' AND column_name='ever_alcaldesa'"
    )).scalar()
    ok = exists == 1
    results.append(ok)
    print(f"T9 - ever_alcaldesa existe: {'OK' if ok else 'FAIL'}")

    # Count
    r = conn.execute(text(
        "SELECT ever_alcaldesa, COUNT(DISTINCT cve_mun) "
        "FROM inclusion_financiera_clean GROUP BY ever_alcaldesa ORDER BY ever_alcaldesa"
    )).fetchall()
    data["ever_alcaldesa"] = {str(row[0]): int(row[1]) for row in r}
    n_ever = data["ever_alcaldesa"].get("1", 0)
    n_never = data["ever_alcaldesa"].get("0", 0)
    ok = n_ever + n_never == 2471
    results.append(ok)
    print(f"T10 - ever_alcaldesa totales ({n_ever + n_never}): {'OK' if ok else 'FAIL'}")
    print(f"    ever=1: {n_ever} mun ({n_ever/(n_ever+n_never)*100:.1f}%)")
    print(f"    ever=0: {n_never} mun ({n_never/(n_ever+n_never)*100:.1f}%)")

    # Verify consistency: if ever=1, at least one trimester has alcaldesa_final=1
    bad = conn.execute(text(
        "SELECT COUNT(DISTINCT cve_mun) FROM inclusion_financiera_clean "
        "WHERE ever_alcaldesa = 1 AND cve_mun NOT IN "
        "(SELECT DISTINCT cve_mun FROM inclusion_financiera_clean WHERE alcaldesa_final = 1)"
    )).scalar()
    ok = bad == 0
    results.append(ok)
    print(f"T11 - ever_alcaldesa consistente: {'OK' if ok else 'FAIL'}")

    # ── Rec 9: cvegeo_mun index ───────────────────────────────────────
    idx = conn.execute(text(
        "SELECT COUNT(*) FROM pg_indexes "
        "WHERE tablename='inclusion_financiera_clean' AND indexname='idx_clean_cvegeo_mun'"
    )).scalar()
    ok = idx >= 1
    results.append(ok)
    print(f"T12 - Índice cvegeo_mun existe: {'OK' if ok else 'FAIL'}")

    # No NULLs in cvegeo_mun
    n_null = conn.execute(text(
        "SELECT COUNT(*) FROM inclusion_financiera_clean WHERE cvegeo_mun IS NULL"
    )).scalar()
    ok = n_null == 0
    results.append(ok)
    print(f"T13 - cvegeo_mun sin NULLs: {'OK' if ok else 'FAIL'}")

    # All 5 digits
    bad_len = conn.execute(text(
        "SELECT COUNT(*) FROM inclusion_financiera_clean WHERE LENGTH(cvegeo_mun) != 5"
    )).scalar()
    ok = bad_len == 0
    results.append(ok)
    print(f"T14 - cvegeo_mun 5 dígitos: {'OK' if ok else 'FAIL'}")

    # ── PK intact ─────────────────────────────────────────────────────
    pk = conn.execute(text(
        "SELECT COUNT(*) FROM pg_indexes "
        "WHERE tablename='inclusion_financiera_clean' AND indexname='pk_inclusion_financiera_clean'"
    )).scalar()
    ok = pk >= 1
    results.append(ok)
    print(f"T15 - PK intacta: {'OK' if ok else 'FAIL'}")

    # ── Original table untouched ──────────────────────────────────────
    n_orig = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.columns WHERE table_name='inclusion_financiera'"
    )).scalar()
    ok = n_orig == 175
    results.append(ok)
    print(f"T16 - Tabla original intacta ({n_orig} cols): {'OK' if ok else 'FAIL'}")

print()
passed = sum(results)
total = len(results)
if all(results):
    print(f"=== OK Todas las {total} pruebas de Recs Altas PASARON ===")
else:
    failed = total - passed
    print(f"=== FAIL {failed}/{total} prueba(s) FALLARON ===")

# Save stats for documentation
print(f"\nEstadísticas recopiladas: {json.dumps(data, indent=2)}")
