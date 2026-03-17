"""Generate grouped tables for the data contract markdown."""
import pandas as pd

df = pd.read_csv("outputs/qc/db_profile_summary.csv")

def classify(col):
    if col in ('cve_mun','periodo_trimestre','cvegeo_mun','cve_ent','cve_mun3',
               'desc_ent','desc_mun','trim','cve_edo'):
        return '1_ID_Geo'
    if col.startswith('alcaldesa') or col in ('ever_alcaldesa',):
        return '2_Tratamiento'
    if col.startswith(('pob','log_pob')):
        return '3_Poblacion'
    if col in ('tipo_pob','region'):
        return '4_Categorica'
    if col.startswith('ratio_mh'):
        return '5_Ratio_MH'
    if col.startswith('saldoprom') or col.startswith('flag_undef'):
        return '6_Saldoprom'
    if col.endswith('_pc_asinh'):
        return '7_Outcome_asinh'
    if col.endswith('_pc_w'):
        return '8_Outcome_winsor'
    if col.endswith('_pc'):
        return '9_Outcome_pc'
    if col.startswith(('ncont_','numtar_','numcontcred_','saldocont_')):
        return 'A_Outcome_raw'
    return 'B_Otra'

df['group'] = df['column'].apply(classify)

# Print full grouped inventory
for grp in sorted(df['group'].unique()):
    sub = df[df['group'] == grp]
    print(f"\n{'='*80}")
    print(f"GROUP: {grp} ({len(sub)} cols)")
    print(f"{'='*80}")
    for _, r in sub.iterrows():
        null_pct = f"{r['null_rate']*100:.1f}%" if r['null_rate'] > 0 else "0%"
        if pd.notna(r['min']):
            stats = f"min={r['min']:.2f}  p50={r['p50']:.2f}  max={r['max']:.2f}"
        else:
            stats = f"unique={int(r['n_unique'])}"
        print(f"  {r['column']:<50} {r['dtype']:<20} null={null_pct:<8} {stats}")
