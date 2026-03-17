-- =============================================================================
-- 00_schema_discovery.sql
-- Queries de QC (solo lectura) para inclusion_financiera_clean
-- Base de datos: tesis_db  |  Esquema: public
-- =============================================================================

-- ─────────────────────────────────────────────────────────────────────────────
-- Q1. Inventario de columnas y tipos
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    ordinal_position  AS pos,
    column_name       AS columna,
    data_type         AS tipo,
    is_nullable       AS nullable
FROM information_schema.columns
WHERE table_schema = 'public'
  AND table_name   = 'inclusion_financiera_clean'
ORDER BY ordinal_position;

-- ─────────────────────────────────────────────────────────────────────────────
-- Q2. Conteo total de filas
-- ─────────────────────────────────────────────────────────────────────────────
SELECT COUNT(*) AS n_filas
FROM inclusion_financiera_clean;

-- ─────────────────────────────────────────────────────────────────────────────
-- Q3. Validar unicidad de PK (cve_mun, periodo_trimestre)
--     Si n_distintos = n_filas, la PK es válida.
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    COUNT(*)                                        AS n_filas,
    COUNT(DISTINCT (cve_mun, periodo_trimestre))    AS n_distintos,
    CASE
        WHEN COUNT(*) = COUNT(DISTINCT (cve_mun, periodo_trimestre))
        THEN 'OK: PK única'
        ELSE 'ERROR: duplicados en PK'
    END AS veredicto
FROM inclusion_financiera_clean;

-- ─────────────────────────────────────────────────────────────────────────────
-- Q4. Dimensiones del panel
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    COUNT(DISTINCT cve_mun)              AS n_municipios,
    COUNT(DISTINCT periodo_trimestre)    AS n_periodos,
    MIN(periodo_trimestre)               AS periodo_min,
    MAX(periodo_trimestre)               AS periodo_max,
    COUNT(*)                             AS n_filas,
    COUNT(DISTINCT cve_mun) * COUNT(DISTINCT periodo_trimestre) AS n_esperado_balanceado,
    CASE
        WHEN COUNT(*) = COUNT(DISTINCT cve_mun) * COUNT(DISTINCT periodo_trimestre)
        THEN 'Balanceado'
        ELSE 'No balanceado (' ||
             (COUNT(DISTINCT cve_mun) * COUNT(DISTINCT periodo_trimestre) - COUNT(*))::text ||
             ' celdas faltantes)'
    END AS balance
FROM inclusion_financiera_clean;

-- ─────────────────────────────────────────────────────────────────────────────
-- Q5. Distribución del tratamiento (alcaldesa_final)
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    alcaldesa_final,
    COUNT(*)                                                    AS n,
    ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER () * 100, 2)  AS pct
FROM inclusion_financiera_clean
GROUP BY alcaldesa_final
ORDER BY alcaldesa_final;

-- ─────────────────────────────────────────────────────────────────────────────
-- Q6. Verificar columnas de población
-- ─────────────────────────────────────────────────────────────────────────────
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'inclusion_financiera_clean'
  AND column_name IN ('pob', 'pob_adulta', 'pob_adulta_m', 'pob_adulta_h',
                       'pob_m', 'pob_h', 'pob_total',
                       'log_pob', 'log_pob_adulta', 'log_pob_adulta_m', 'log_pob_adulta_h')
ORDER BY column_name;

-- ─────────────────────────────────────────────────────────────────────────────
-- Q7. NULLs y rango de columnas de población
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    'pob'            AS col, COUNT(*) FILTER (WHERE pob IS NULL)            AS nulls, MIN(pob)            AS mn, MAX(pob)            AS mx FROM inclusion_financiera_clean
UNION ALL SELECT
    'pob_adulta',         COUNT(*) FILTER (WHERE pob_adulta IS NULL),         MIN(pob_adulta),         MAX(pob_adulta)         FROM inclusion_financiera_clean
UNION ALL SELECT
    'pob_adulta_m',       COUNT(*) FILTER (WHERE pob_adulta_m IS NULL),       MIN(pob_adulta_m),       MAX(pob_adulta_m)       FROM inclusion_financiera_clean
UNION ALL SELECT
    'pob_adulta_h',       COUNT(*) FILTER (WHERE pob_adulta_h IS NULL),       MIN(pob_adulta_h),       MAX(pob_adulta_h)       FROM inclusion_financiera_clean;

-- ─────────────────────────────────────────────────────────────────────────────
-- Q8. Listar outcomes por patrón de nombre
-- ─────────────────────────────────────────────────────────────────────────────
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'inclusion_financiera_clean'
  AND (   column_name LIKE 'ncont_%'
       OR column_name LIKE 'numtar_%'
       OR column_name LIKE 'numcontcred_%'
       OR column_name LIKE 'saldocont_%' )
ORDER BY column_name;

-- ─────────────────────────────────────────────────────────────────────────────
-- Q9. Conteo de columnas por grupo (outcome pc / winsor / asinh)
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    CASE
        WHEN column_name LIKE '%_pc_asinh' THEN 'asinh'
        WHEN column_name LIKE '%_pc_w'     THEN 'winsor'
        WHEN column_name LIKE '%_pc'       THEN 'pc'
        ELSE 'raw'
    END AS grupo,
    COUNT(*) AS n_cols
FROM information_schema.columns
WHERE table_name = 'inclusion_financiera_clean'
  AND (   column_name LIKE 'ncont_%'
       OR column_name LIKE 'numtar_%'
       OR column_name LIKE 'numcontcred_%'
       OR column_name LIKE 'saldocont_%' )
GROUP BY 1
ORDER BY 1;

-- ─────────────────────────────────────────────────────────────────────────────
-- Q10. Columnas sospechosas de leakage (leads, lags, transiciones)
-- ─────────────────────────────────────────────────────────────────────────────
SELECT column_name, data_type,
    CASE
        WHEN column_name LIKE '%_f1' OR column_name LIKE '%_f2' OR column_name LIKE '%_f3'
            THEN 'LEAD (futuro)'
        WHEN column_name LIKE '%_l1' OR column_name LIKE '%_l2' OR column_name LIKE '%_l3'
            THEN 'LAG (pasado)'
        WHEN column_name LIKE '%transition%'
            THEN 'TRANSITION'
        WHEN column_name LIKE '%excl_trans%'
            THEN 'EXCL_TRANS'
        ELSE 'otro'
    END AS tipo_riesgo
FROM information_schema.columns
WHERE table_name = 'inclusion_financiera_clean'
  AND (   column_name LIKE '%/_f1' ESCAPE '/'
       OR column_name LIKE '%/_f2' ESCAPE '/'
       OR column_name LIKE '%/_f3' ESCAPE '/'
       OR column_name LIKE '%/_l1' ESCAPE '/'
       OR column_name LIKE '%/_l2' ESCAPE '/'
       OR column_name LIKE '%/_l3' ESCAPE '/'
       OR column_name LIKE '%transition%'
       OR column_name LIKE '%excl/_trans%' ESCAPE '/' )
ORDER BY column_name;

-- ─────────────────────────────────────────────────────────────────────────────
-- Q11. Municipios con panel incompleto (si los hay)
-- ─────────────────────────────────────────────────────────────────────────────
SELECT cve_mun, COUNT(*) AS n_periodos
FROM inclusion_financiera_clean
GROUP BY cve_mun
HAVING COUNT(*) < (SELECT COUNT(DISTINCT periodo_trimestre) FROM inclusion_financiera_clean)
ORDER BY n_periodos, cve_mun;

-- ─────────────────────────────────────────────────────────────────────────────
-- Q12. Índices existentes
-- ─────────────────────────────────────────────────────────────────────────────
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'inclusion_financiera_clean'
ORDER BY indexname;
