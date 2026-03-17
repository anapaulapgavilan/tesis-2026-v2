"""
Tests de validación para las transformaciones medias 🟢 (Recs 10–12).
"""
from sqlalchemy import text
from tesis_alcaldesas.config import get_engine
import json, math

engine = get_engine()
results = []
data = {}

with engine.connect() as conn:
    # ── General ───────────────────────────────────────────────────────
    n_rows = conn.execute(text("SELECT COUNT(*) FROM inclusion_financiera_clean")).scalar()
    ok = n_rows == 41905
    results.append(ok)
    print(f"T1 - Filas correctas ({n_rows:,}): {'OK' if ok else 'FAIL'}")

    n_cols = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_name='inclusion_financiera_clean'"
    )).scalar()
    ok = n_cols >= 348
    results.append(ok)
    print(f"T2 - Total columnas ({n_cols}): {'OK' if ok else 'FAIL'}")

    # ── Rec 10: alcaldesa_acumulado ───────────────────────────────────
    exists = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_name='inclusion_financiera_clean' AND column_name='alcaldesa_acumulado'"
    )).scalar()
    ok = exists == 1
    results.append(ok)
    print(f"T3 - alcaldesa_acumulado existe: {'OK' if ok else 'FAIL'}")

    # Must be non-negative
    neg = conn.execute(text(
        "SELECT COUNT(*) FROM inclusion_financiera_clean WHERE alcaldesa_acumulado < 0"
    )).scalar()
    ok = neg == 0
    results.append(ok)
    print(f"T4 - Sin negativos ({neg}): {'OK' if ok else 'FAIL'}")

    # Max should be 17 (all trimesters)
    maxval = conn.execute(text(
        "SELECT MAX(alcaldesa_acumulado) FROM inclusion_financiera_clean"
    )).scalar()
    ok = maxval == 17
    results.append(ok)
    print(f"T5 - Max=17 ({maxval}): {'OK' if ok else 'FAIL'}")

    # If alcaldesa_final=0 for all t, acumulado should be 0 on last t
    bad = conn.execute(text("""
        SELECT COUNT(*) FROM (
            SELECT cve_mun, MAX(alcaldesa_acumulado) AS max_acum, SUM(alcaldesa_final) AS sum_alc
            FROM inclusion_financiera_clean GROUP BY cve_mun
            HAVING SUM(alcaldesa_final) = 0 AND MAX(alcaldesa_acumulado) != 0
        ) sub
    """)).scalar()
    ok = bad == 0
    results.append(ok)
    print(f"T6 - never-treated acumulado=0: {'OK' if ok else 'FAIL'}")

    # Monotonic: acumulado should never decrease within a municipality
    bad = conn.execute(text("""
        SELECT COUNT(*) FROM (
            SELECT cve_mun, periodo_trimestre, alcaldesa_acumulado,
                   LAG(alcaldesa_acumulado) OVER (PARTITION BY cve_mun ORDER BY periodo_trimestre) AS prev
            FROM inclusion_financiera_clean
        ) sub WHERE prev IS NOT NULL AND alcaldesa_acumulado < prev
    """)).scalar()
    ok = bad == 0
    results.append(ok)
    print(f"T7 - Monótono creciente ({bad} violaciones): {'OK' if ok else 'FAIL'}")

    data["alcaldesa_acumulado"] = {
        "max": int(maxval),
        "media": float(conn.execute(text("SELECT AVG(alcaldesa_acumulado) FROM inclusion_financiera_clean")).scalar()),
    }

    # ── Rec 11: asinh ─────────────────────────────────────────────────
    n_asinh = conn.execute(text(
        "SELECT COUNT(*) FROM information_schema.columns "
        "WHERE table_name='inclusion_financiera_clean' AND column_name LIKE '%\\_pc\\_asinh' ESCAPE '\\'"
    )).scalar()
    ok = n_asinh == 51
    results.append(ok)
    print(f"T8 - Columnas asinh ({n_asinh}): {'OK' if ok else 'FAIL'}")

    # Verify formula: asinh(x) = ln(x + sqrt(x²+1))
    r = conn.execute(text(
        "SELECT ncont_total_m_pc, ncont_total_m_pc_asinh "
        "FROM inclusion_financiera_clean WHERE ncont_total_m_pc > 0 LIMIT 5"
    )).fetchall()
    ok = all(abs(float(row[1]) - math.asinh(float(row[0]))) < 0.001 for row in r)
    results.append(ok)
    print(f"T9 - Fórmula asinh correcta: {'OK' if ok else 'FAIL'}")

    # asinh(0) should be 0
    n_zero = conn.execute(text(
        "SELECT COUNT(*) FROM inclusion_financiera_clean "
        "WHERE ncont_total_m_pc = 0 AND ABS(ncont_total_m_pc_asinh) > 0.001"
    )).scalar()
    ok = n_zero == 0
    results.append(ok)
    print(f"T10 - asinh(0)=0: {'OK' if ok else 'FAIL'}")

    # ── Rec 12: tipo_pob ──────────────────────────────────────────────
    n_null = conn.execute(text(
        "SELECT COUNT(*) FROM inclusion_financiera_clean WHERE tipo_pob IS NULL"
    )).scalar()
    ok = n_null == 0
    results.append(ok)
    print(f"T11 - tipo_pob sin NULLs ({n_null}): {'OK' if ok else 'FAIL'}")

    # San Felipe and Dzitbalche should be Semi-urbano
    for cve in [2007, 4013]:
        tp = conn.execute(text(
            f"SELECT DISTINCT tipo_pob FROM inclusion_financiera_clean WHERE cve_mun={cve}"
        )).scalar()
        ok = tp == "Semi-urbano"
        results.append(ok)
        print(f"T{12 if cve==2007 else 13} - cve_mun={cve} tipo_pob='{tp}': {'OK' if ok else 'FAIL'}")

    # ── Integrity ─────────────────────────────────────────────────────
    pk = conn.execute(text(
        "SELECT COUNT(*) FROM pg_indexes "
        "WHERE tablename='inclusion_financiera_clean' AND indexname='pk_inclusion_financiera_clean'"
    )).scalar()
    ok = pk >= 1
    results.append(ok)
    print(f"T14 - PK intacta: {'OK' if ok else 'FAIL'}")

    idx = conn.execute(text(
        "SELECT COUNT(*) FROM pg_indexes "
        "WHERE tablename='inclusion_financiera_clean' AND indexname='idx_clean_cvegeo_mun'"
    )).scalar()
    ok = idx >= 1
    results.append(ok)
    print(f"T15 - Índice cvegeo_mun: {'OK' if ok else 'FAIL'}")

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
    print(f"=== OK Todas las {total} pruebas de Recs Medias PASARON ===")
else:
    failed = total - passed
    print(f"=== FAIL {failed}/{total} prueba(s) FALLARON ===")
