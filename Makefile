# Makefile — Tesis Alcaldesas × Inclusión Financiera
# Uso: make all   (pipeline completo)
#      make data  (solo datos)
#      make models (solo modelos)

PYTHON = python
PYTHONPATH_CMD = PYTHONPATH=src

.PHONY: all data models mdes sensitivity sample extensive clean

# ── Pipeline completo ──
all: data models

# ── Datos ──
data:
	$(PYTHONPATH_CMD) $(PYTHON) -m tesis_alcaldesas.data.extract_panel
	$(PYTHONPATH_CMD) $(PYTHON) -m tesis_alcaldesas.data.build_features

# ── Modelos (asume datos ya existen) ──
models: twfe event_study robustness heterogeneity mdes sensitivity sample extensive

twfe:
	$(PYTHONPATH_CMD) $(PYTHON) -m tesis_alcaldesas.models.table1_descriptives
	$(PYTHONPATH_CMD) $(PYTHON) -m tesis_alcaldesas.models.twfe

event_study:
	$(PYTHONPATH_CMD) $(PYTHON) -m tesis_alcaldesas.models.event_study

robustness:
	$(PYTHONPATH_CMD) $(PYTHON) -m tesis_alcaldesas.models.robustness

heterogeneity:
	$(PYTHONPATH_CMD) $(PYTHON) -m tesis_alcaldesas.models.heterogeneity

mdes:
	$(PYTHONPATH_CMD) $(PYTHON) -m tesis_alcaldesas.models.mdes_power

sensitivity:
	$(PYTHONPATH_CMD) $(PYTHON) -m tesis_alcaldesas.models.event_study_sensitivity

sample:
	$(PYTHONPATH_CMD) $(PYTHON) -m tesis_alcaldesas.models.sample_policy

extensive:
	$(PYTHONPATH_CMD) $(PYTHON) -m tesis_alcaldesas.models.extensive_margin

# ── Run all via Python entrypoint ──
run_all:
	$(PYTHONPATH_CMD) $(PYTHON) -m tesis_alcaldesas.run_all

# ── Limpieza (solo outputs, no datos) ──
clean:
	rm -f outputs/paper/tabla_5_*.csv outputs/paper/tabla_5_*.tex
	rm -f outputs/paper/tabla_6_*.csv outputs/paper/tabla_6_*.tex
	rm -f outputs/paper/figura_2_*.pdf outputs/paper/figura_2_*.png
	rm -f outputs/paper/mdes_summary.txt
	rm -f outputs/paper/pretrends_tests_sens.csv
	rm -f outputs/paper/sample_sensitivity.txt
	rm -f outputs/paper/tabla_2_twfe_main.* outputs/paper/tabla_2_twfe_full.*
