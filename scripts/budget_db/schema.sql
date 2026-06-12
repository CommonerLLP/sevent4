-- ============================================================================
-- Municipal Budget Database — schema v1
-- Canonical store: SQLite. Exports: DuckDB / Parquet / CSV / JSON / Excel.
-- Design principles:
--   1. PROVENANCE ON EVERY FIGURE — source_pdf + page + extraction_method +
--      confidence, so manual-verified / text-extracted / OCR / derived data
--      are never confused.
--   2. NORMALISED — one row = one (city, year, basis, section, flow, head).
--      Answers any cross-year query without reshaping.
--   3. MULTI-CITY READY — city column + source_doc registry; Ahmedabad first.
--   4. APPEND-ONLY BACKFILL — OCR/garble years and new FYs add rows; the
--      schema never changes when data is backfilled.
-- ============================================================================

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

-- ---- source document registry -------------------------------------------------
DROP TABLE IF EXISTS source_doc;
CREATE TABLE source_doc (
    source_pdf      TEXT PRIMARY KEY,         -- file name (stable id)
    city            TEXT NOT NULL DEFAULT 'ahmedabad',
    fiscal_year     TEXT,                     -- '2023-24'
    edition         TEXT,                     -- 'english' | 'gujarati'
    script_kind     TEXT,                     -- 'english' | 'gujarati_unicode' | 'gujarati_legacy'
    extractability  TEXT,                     -- 'text' | 'ocr_needed'
    pages           INTEGER,
    abs_path        TEXT,                     -- absolute path on disk (gitignored data)
    note            TEXT
);

-- ---- the fact table -----------------------------------------------------------
DROP TABLE IF EXISTS budget_line;
CREATE TABLE budget_line (
    id              INTEGER PRIMARY KEY,
    city            TEXT NOT NULL DEFAULT 'ahmedabad',
    fiscal_year     TEXT NOT NULL,            -- '2023-24'
    fy_start        INTEGER,                  -- 2023  (for sort/range queries)
    estimate_basis  TEXT NOT NULL,            -- 'BE' | 'RE' | 'actual'
    section         TEXT,                     -- 'revenue' | 'capital' | NULL(unknown)
    flow            TEXT,                     -- 'income' | 'expenditure'
    head_category   TEXT,                     -- normalised taxonomy (see below)
    head_name       TEXT NOT NULL,            -- canonical English head
    head_name_raw   TEXT,                     -- as printed in source
    entity          TEXT,                     -- undertaking/parastatal tag: 'AMTS','AJL_BRTS','MJ_LIBRARY','VS_HOSPITAL','SRFDCL','SCHOOL_BOARD',... (NULL if not an entity line)
    amount_cr       REAL,                     -- normalised to Rupees crore
    amount_raw      TEXT,                     -- original figure + unit string
    source_pdf      TEXT REFERENCES source_doc(source_pdf),
    page            INTEGER,
    extraction_method TEXT NOT NULL,          -- 'manual_verified' | 'text' | 'ocr' | 'derived'
    confidence      TEXT NOT NULL,            -- 'high' | 'medium' | 'low'
    note            TEXT
);

CREATE INDEX ix_bl_year     ON budget_line(fiscal_year);
CREATE INDEX ix_bl_entity   ON budget_line(entity);
CREATE INDEX ix_bl_cat      ON budget_line(head_category);
CREATE INDEX ix_bl_flow     ON budget_line(section, flow);
CREATE INDEX ix_bl_basis    ON budget_line(estimate_basis);

-- head_category controlled vocabulary (documentation; not enforced):
--   INCOME:  tax_revenue | non_tax_revenue | grant_received | other_income | capital_receipt | loan_receipt
--   EXPEND:  establishment | admin_general | maintenance | energy | service_program |
--            grant_contribution | loan_charges | transfer_to_capital | department_support |
--            capital_works | other_expenditure
--   estimate_basis: BE=budget estimate, RE=revised estimate, actual=prior-year actual

-- ---- convenience views --------------------------------------------------------
DROP VIEW IF EXISTS v_entity_timeseries;
CREATE VIEW v_entity_timeseries AS
SELECT entity, fiscal_year, fy_start, estimate_basis, amount_cr,
       extraction_method, confidence, source_pdf, page
FROM   budget_line
WHERE  entity IS NOT NULL
ORDER  BY entity, fy_start, estimate_basis;

DROP VIEW IF EXISTS v_coverage;
CREATE VIEW v_coverage AS
SELECT fiscal_year, fy_start,
       COUNT(*)                                          AS rows,
       SUM(entity IS NOT NULL)                           AS entity_rows,
       SUM(extraction_method='manual_verified')          AS verified,
       SUM(extraction_method='text')                     AS text_x,
       SUM(extraction_method='ocr')                      AS ocr_x,
       SUM(extraction_method='derived')                  AS derived
FROM   budget_line
GROUP  BY fiscal_year, fy_start
ORDER  BY fy_start;
