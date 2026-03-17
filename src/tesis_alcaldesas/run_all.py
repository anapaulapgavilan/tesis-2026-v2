"""
run_all.py — Entrypoint que ejecuta el pipeline completo de modelado.

Orden de ejecución:
  1. Tabla 1: descriptivos
  2. Tabla 2: TWFE baseline
  3. Figura 1 + pre-trends: event study
  4. Tabla 3: robustez
  5. Tabla 4: heterogeneidad
  6. Tabla 5: MDES / poder estadístico
  7. Figura 2: sensibilidad event study
  8. Sample policy (main vs full)
  9. Tabla 6: extensión (extensivo + composición)

Uso:
  python -m tesis_alcaldesas.run_all

Nota: Requiere que data/processed/analytical_panel_features.parquet exista.
      Si no existe, correr primero:
        python -m tesis_alcaldesas.data.extract_panel
        python -m tesis_alcaldesas.data.build_features
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[2]  # …/tesis-2026-v2/

# Steps: (label, module)
STEPS = [
    ("Tabla 1 — Descriptivos",                 "tesis_alcaldesas.models.table1_descriptives"),
    ("Tabla 2 — TWFE baseline",                "tesis_alcaldesas.models.twfe"),
    ("Figura 1 — Event study + pre-trends",    "tesis_alcaldesas.models.event_study"),
    ("Tabla 3 — Robustez",                     "tesis_alcaldesas.models.robustness"),
    ("Tabla 4 — Heterogeneidad",               "tesis_alcaldesas.models.heterogeneity"),
    ("Tabla 5 — MDES / poder estadístico",     "tesis_alcaldesas.models.mdes_power"),
    ("Figura 2 — Sensibilidad event study",    "tesis_alcaldesas.models.event_study_sensitivity"),
    ("Sample policy (main vs full)",           "tesis_alcaldesas.models.sample_policy"),
    ("Tabla 6 — Extensión (extensivo + share)","tesis_alcaldesas.models.extensive_margin"),
]


def main():
    print("=" * 70)
    print("  PIPELINE COMPLETO — Tesis Alcaldesas × Inclusión Financiera")
    print("=" * 70)

    src_dir = CODE_DIR / "src"
    env = {**os.environ, "PYTHONPATH": str(src_dir)}

    results = []
    t_total = time.time()

    for i, (label, module) in enumerate(STEPS, 1):
        print(f"\n{'─'*70}")
        print(f"  [{i}/{len(STEPS)}] {label}")
        print(f"  module: {module}")
        print(f"{'─'*70}")

        t0 = time.time()
        try:
            proc = subprocess.run(
                [sys.executable, "-m", module],
                cwd=str(CODE_DIR),
                env=env,
                capture_output=False,
            )
            elapsed = time.time() - t0
            status = "OK" if proc.returncode == 0 else f"FAIL (exit {proc.returncode})"
        except Exception as e:
            elapsed = time.time() - t0
            status = f"FAIL ERROR: {e}"

        results.append((label, status, elapsed))
        print(f"\n  --> {status} ({elapsed:.1f}s)")

    # --- Summary ---
    total_time = time.time() - t_total
    print(f"\n\n{'='*70}")
    print(f"  RESUMEN PIPELINE ({total_time:.0f}s total)")
    print(f"{'='*70}")

    for label, status, elapsed in results:
        print(f"  {status:>5s}  {label:<50s} ({elapsed:.1f}s)")

    n_ok = sum(1 for _, s, _ in results if s == "OK")
    n_fail = len(results) - n_ok
    print(f"\n  {n_ok}/{len(results)} exitosos, {n_fail} fallidos")

    if n_fail > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
