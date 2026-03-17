"""Quick inspection of the analytical parquet."""
import pandas as pd

df = pd.read_parquet("data/processed/analytical_panel_features.parquet")
print("Shape:", df.shape)
print("\nAll columns:")
for i, c in enumerate(df.columns):
    print(f"  {i:3d}  {c:45s}  {str(df[c].dtype):20s}  null={df[c].isna().sum()}")

CHECK = [
    "cve_mun", "periodo_trimestre", "t_index", "alcaldesa_final",
    "event_time", "first_treat_period", "first_treat_t", "cohort_type",
    "tipo_pob", "region", "log_pob", "pob_adulta_m",
    "flag_incomplete_panel", "flag_denom_zero",
    "ncont_total_m_pc_asinh", "saldocont_total_m_pc_asinh",
    "numtar_deb_m_pc_asinh", "numtar_cred_m_pc_asinh",
    "numcontcred_hip_m_pc_asinh",
    "ncont_total_m_pc_w", "ncont_total_m_pc_log1p",
    "ncont_total_h", "alcaldesa_excl_trans",
]
print("\nKey column check:")
for c in CHECK:
    if c in df.columns:
        print(f"  OK  {c}")
    else:
        print(f"  *** MISSING  {c}")

# Check for _h outcomes with _pc suffix
h_pc = [c for c in df.columns if "_h_pc" in c]
print(f"\nHombres _pc columns ({len(h_pc)}):", h_pc[:5], "...")

# Columns with _pc_asinh suffix
asinh_cols = [c for c in df.columns if c.endswith("_pc_asinh")]
print(f"\nasinh columns ({len(asinh_cols)}):", asinh_cols[:5], "...")

# cohort_type distribution
print("\ncohort_type:")
print(df.groupby("cohort_type")["cve_mun"].nunique())
