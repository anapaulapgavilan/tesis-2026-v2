> **Archivos fuente:**
> - `src/tesis_alcaldesas/run_all.py`

# 23 — Freeze & Release: Instrucciones para congelar resultados

## Versión actual

| Campo | Valor |
|---|---|
| Tag | `v1.0-thesis-results` |
| Commit | `3c3b51a` (freeze original) |
| HEAD actual | `e15573e` (post-freeze: tonal fix + ventana robustez) |
| Fecha | 2026-02-26 |

---

## 1. Crear tag anotado (ya hecho)

```bash
git tag -a v1.0-thesis-results -m "Resultados finales congelados — NO TOCAR salvo bugs"
```

Para crear un nuevo tag tras correcciones menores:

```bash
git tag -a v1.1-thesis-final -m "Versión final pre-defensa: tonal fixes + Tabla A1"
```

## 2. Empujar tag a remoto

```bash
git push origin v1.0-thesis-results
# o para todos los tags:
git push origin --tags
```

## 3. Citar el commit en la tesis

En el capítulo de metodología o en una nota al pie:

> Los resultados y el código de análisis están disponibles en el repositorio
> `tesis-2026` (commit `e15573e`, tag `v1.0-thesis-results`, febrero 2026).
> El pipeline completo se reproduce con `PYTHONPATH=src python -m tesis_alcaldesas.run_all`.

Para obtener el SHA actual:

```bash
git rev-parse --short HEAD
```

## 4. Checklist de "no tocar"

Los siguientes archivos y carpetas **no deben modificarse** tras el freeze,
salvo corrección de errores verificables:

| Ruta | Razón |
|---|---|
| `outputs/paper/*` | Tablas, figuras y CSVs de resultados |
| `docs/13_MODELADO_ECONOMETRICO.md` | Especificación formal del diseño |
| `docs/17_RESULTADOS_EMPIRICOS.md` | Narrativa de resultados |
| `src/tesis_alcaldesas/models/*.py` | Scripts de modelado |
| `README.md` | Resumen y pipeline |

**Permitido:** documentación nueva (docs/17+), slides, notas para asesor.

## 5. outputs/paper en git

Los outputs están versionados (no excluidos por `.gitignore`).
Si en el futuro se decide excluirlos, agregar al `.gitignore`:

```gitignore
# outputs/paper/  # descomentar para excluir
```

Y para whitelistear solo resultados congelados:

```gitignore
outputs/paper/
!outputs/paper/tabla_*.csv
!outputs/paper/tabla_*.tex
!outputs/paper/figura_*.pdf
!outputs/paper/figura_*.png
```

## 6. Cómo verificar integridad

```bash
# Verificar que el tag apunta al commit correcto:
git show v1.0-thesis-results --oneline --no-patch

# Verificar que los outputs no cambiaron:
git diff v1.0-thesis-results -- outputs/paper/

# Re-generar desde cero y comparar:
PYTHONPATH=src python -m tesis_alcaldesas.run_all
git diff -- outputs/paper/  # debe ser vacío (salvo PDFs con timestamps)
```
