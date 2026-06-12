# BMC Facility Lists — what's captured

## Captured (open, verified)
- **parks.csv** — 161 parks developed/maintained by BMC, ward + zone tagged. Source: BMC official "Parks and Recreation" page (https://www.bmc.gov.in/services/parks-and-recreation). Page states 137 parks; the live table actually enumerates 161 rows (captured verbatim). Two duplicate-looking rows (e.g. "Bharatpur B1" ward 22, "Kalinga Nagar K-2" ward 23) appear in the source itself and were retained.

## Source PDFs (provenance copies)
- **SEC_elected_corporators_2022.pdf** — Odisha SEC official "Names of Elected Corporators" list (KHORDHA → Bhubaneswar Municipal Corporation, wards 1-67, with party + reservation). Retrieved via Internet Archive (live sec.odisha.gov.in copy now returns 404): http://web.archive.org/web/20240208161520/https://sec.odisha.gov.in/wp-content/uploads/2023/02/NAME-OF-ELECTED-CORPORATORS.pdf
- **BMC_corporator_directory_2022.pdf** — BMC "Corporators of BMC-2022" directory (names + contact numbers, no party). Scanned image PDF (no text layer); names/contacts in councillors.csv were OCR-extracted (tesseract) and cross-checked against the SEC list. Source: https://cms.bhubaneswarone.in/uploadDocuments/Directory/Corporator%20Details/Directory20220520_122810.pdf

## Known but NOT captured (gated / unparseable / not published as a clean list)
- **Schools** — No standalone BMC schools list found as an open, parseable file. BMC oversees government-aided/primary schools (one search snippet cited "89 primary schools" in an annexure) but no clean public CSV/PDF located.
- **Health centres (UPHC/UCHC/UHWC)** — BMC runs urban health centres under NUHM (a search snippet cited ~44 centres). The Health & Sanitation department page (https://www.bmc.gov.in/departments/health--sanitation) lists no facility directory. No clean open list located; only individual facilities surface via Facebook/maps.
- **Libraries** — No BMC-published library list found.
- **BMC council/agenda PDF (32267_BMC_dt_26.6.25.pdf, 43 pp)** — downloaded but the text layer is corrupt (broken font tags); not reliably parseable and content type uncertain. URL: https://cms.bhubaneswarone.in/uploadDocuments/content/32267_BMC_dt_26.6.25.pdf — recorded for reference, contents NOT transcribed (no fabrication).
