"""
Schema discovery + profiling for inclusion_financiera_clean.
READ-ONLY. Outputs a CSV profile and prints grouped column inventory.
"""
import os, csv, sys
import pandas as pd
from sqlalchemy import text

from tesis_alcaldesas.config import get_engine  # noqa: E402
engine = get_engine()

OUT_DIR = "outputs/qc"
os.makedirs(OUT_DIR, exist_ok=True)

with engine.connect() as c:

    # ── 1. Column inventory ──────────────────────────────────────────
    cols_df = pd.read_sql(text("""
        SELECT column_name, data_type, ordinal_position
        FROM information_schema.columns
        WHERE table_name = 'inclusion_financiera_clean'
        ORDER BY ordinal_position
    """), c)
    n_cols = len(cols_df)
    print(f"Columnas: {n_cols}")

    # ── 2. Row count ─────────────────────────────────────────────────
    n_rows = c.execute(text("SELECT COUNT(*) FROM inclusion_financiera_clean")).scalar()
    print(f"Filas:    {n_rows:,}")

    # ── 3. PK uniqueness ─────────────────────────────────────────────
    n_pk = c.execute(text(
        "SELECT COUNT(*) FROM (SELECT DISTINCT cve_mun, periodo_trimestre "
        "FROM inclusion_financiera_clean) sub"
    )).scalar()
    pk_ok = n_pk == n_rows
    print(f"PK única (cve_mun, periodo_trimestre): {n_pk:,} distintos --> {'OK' if pk_ok else 'FAIL DUPLICADOS'}")

    # ── 4. Panel dimensions ──────────────────────────────────────────
    n_mun = c.execute(text("SELECT COUNT(DISTINCT cve_mun) FROM inclusion_financiera_clean")).scalar()
    n_per = c.execute(text("SELECT COUNT(DISTINCT periodo_trimestre) FROM inclusion_financiera_clean")).scalar()
    min_per = c.execute(text("SELECT MIN(periodo_trimestre) FROM inclusion_financiera_clean")).scalar()
    max_per = c.execute(text("SELECT MAX(periodo_trimestre) FROM inclusion_financiera_clean")).scalar()
    balanced = (n_mun * n_per == n_rows)
    print(f"Municipios: {n_mun:,}  |  Periodos: {n_per} ({min_per} – {max_per})  |  Balanceado: {'OK' if balanced else 'FAIL'}")

    # ── 5. Treatment distribution ────────────────────────────────────
    treat = pd.read_sql(text("""
        SELECT alcaldesa_final, COUNT(*) AS n,
               ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER () * 100, 2) AS pct
        FROM inclusion_financiera_clean
        GROUP BY alcaldesa_final ORDER BY alcaldesa_final
    """), c)
    print(f"\nalcaldesa_final distribución:")
    for _, r in treat.iterrows():
        print(f"  {int(r['alcaldesa_final'])}: {int(r['n']):,} ({r['pct']}%)")

    # ── 6. Population columns check ─────────────────────────────────
    pop_candidates = ['pob', 'pob_adulta', 'pob_adulta_m', 'pob_adulta_h',
                      'pob_m', 'pob_h', 'pob_total']
    existing_pop = [col for col in pop_candidates if col in cols_df['column_name'].values]
    print(f"\nColumnas de población encontradas: {existing_pop}")

    # ── 7. Outcome patterns ──────────────────────────────────────────
    prefixes = {
        'ncont_': [], 'numtar_': [], 'numcontcred_': [],
        'saldocont_': [], 'saldoprom_': [],
        'ratio_mh_': [], 'log_': [], 'ever_': [], 'alcaldesa': [],
    }
    suffix_groups = {'_pc': [], '_pc_w': [], '_pc_asinh': []}

    for col in cols_df['column_name']:
        for pfx in prefixes:
            if col.startswith(pfx):
                prefixes[pfx].append(col)
        for sfx in suffix_groups:
            if col.endswith(sfx):
                suffix_groups[sfx].append(col)

    print("\n=== Columnas por prefijo ===")
    for pfx, lst in prefixes.items():
        print(f"  {pfx}*: {len(lst)}")
    print("\n=== Columnas por sufijo ===")
    for sfx, lst in suffix_groups.items():
        print(f"  *{sfx}: {len(lst)}")

    # ── 8. Full profile: null_rate, n_unique, min, p50, max ──────────
    print(f"\nPerfilando {n_cols} columnas (esto tarda ~30s)...")

    profile_rows = []
    col_names = cols_df['column_name'].tolist()
    col_types = dict(zip(cols_df['column_name'], cols_df['data_type']))

    # Batch: null counts
    null_parts = ", ".join(
        f"SUM(CASE WHEN \"{col}\" IS NULL THEN 1 ELSE 0 END) AS \"{col}\""
        for col in col_names
    )
    null_row = c.execute(text(f"SELECT {null_parts} FROM inclusion_financiera_clean")).fetchone()
    null_map = dict(zip(col_names, null_row))

    # Batch: n_distinct for non-text small-cardinality (do per-column for safety)
    for col in col_names:
        dtype = col_types[col]
        null_count = int(null_map[col])
        null_rate = round(null_count / n_rows, 6) if n_rows else 0

        is_numeric = dtype in ('integer', 'bigint', 'smallint', 'numeric',
                               'double precision', 'real')
        is_text = dtype in ('text', 'character varying', 'character')

        # n_unique
        n_unique = c.execute(text(
            f'SELECT COUNT(DISTINCT "{col}") FROM inclusion_financiera_clean'
        )).scalar()

        if is_numeric:
            stats = c.execute(text(f"""
                SELECT MIN("{col}"), PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY "{col}"),
                       MAX("{col}")
                FROM inclusion_financiera_clean
            """)).fetchone()
            mn, p50, mx = stats
        else:
            mn, p50, mx = None, None, None

        profile_rows.append({
            'column': col,
            'dtype': dtype,
            'null_count': null_count,
            'null_rate': null_rate,
            'n_unique': n_unique,
            'min': mn,
            'p50': p50,
            'max': mx,
        })

    # ── 9. Write CSV ─────────────────────────────────────────────────
    csv_path = os.path.join(OUT_DIR, "db_profile_summary.csv")
    profile_df = pd.DataFrame(profile_rows)
    profile_df.to_csv(csv_path, index=False)
    print(f"\nOK Perfil guardado en {csv_path} ({len(profile_rows)} filas)")

    # ── 10. Group columns for data contract ──────────────────────────
    def classify(col):
        if col in ('cve_mun', 'periodo_trimestre', 'cvegeo_mun', 'cve_ent',
                    'cve_mun3', 'desc_ent', 'desc_mun'):
            return 'ID / Geo'
        if col.startswith('alcaldesa') or col in ('ever_alcaldesa',):
            return 'Tratamiento'
        if col.startswith(('pob', 'log_pob')):
            return 'Población'
        if col == 'tipo_pob':
            return 'Categórica'
        if col.startswith('ratio_mh'):
            return 'Ratio M/H'
        if col.startswith('saldoprom') or col.startswith('flag_undef'):
            return 'Saldoprom (excluir)'
        # outcomes by suffix
        if col.endswith('_pc_asinh'):
            return 'Outcome asinh'
        if col.endswith('_pc_w'):
            return 'Outcome winsor'
        if col.endswith('_pc'):
            return 'Outcome pc'
        # raw counts/saldos
        if col.startswith(('ncont_', 'numtar_', 'numcontcred_', 'saldocont_')):
            return 'Outcome raw'
        return 'Otra'

    profile_df['group'] = profile_df['column'].apply(classify)
    print("\n=== Columnas por grupo semántico ===")
    for grp, sub in profile_df.groupby('group'):
        print(f"  {grp}: {len(sub)}")

    # Print leakage candidates
    leakage = [col for col in col_names
               if any(x in col for x in ('_f1', '_f2', '_f3', '_l1', '_l2', '_l3',
                                          'transition', 'excl_trans'))]
    print(f"\n=== Columnas leakage/forward ({len(leakage)}) ===")
    for col in leakage:
        print(f"  [!] {col}")

    print("\nOK Discovery completo.")
