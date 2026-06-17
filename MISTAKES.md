# Mistakes

## 2026-06-15 - source PDFs left in scratch instead of durable external archive

**Failure.** During the Delhi Public Library staffing extraction, original annual-report PDFs were downloaded to `/private/tmp` and text was extracted from there before the source PDFs were copied to durable external storage. That made the extraction fragile and violated the repo's provenance discipline: derived text/CSV is not enough, and scratch paths are not archives.

**How caught.** User corrected the workflow directly: never delete or strand original source material; always keep copies of original source material on the external disk that is symlinked/associated with each CommonerLLP repo.

**Remediation.** Copied the DPL annual-report PDFs and text sidecars to the repo's external source archive, added `data/cities/delhi/source/libraries/dpl_annual_report_archive_manifest.csv` with sizes and SHA-256 hashes, and added `data/cities/delhi/source/libraries/dpl_staffing_time_series.csv`.

**Rule.** Never treat `/private/tmp`, browser downloads, generated text, or parsed CSVs as preservation. Before claiming extraction work is complete, copy every original source document to the repo's external source archive, record path + URL + size + hash in a tracked manifest, and only then generate derived text/CSV outputs. Never delete original source material from disk unless the user explicitly orders it.
