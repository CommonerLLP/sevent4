from __future__ import annotations

from pathlib import Path

from sevent4.domain.mj_library import (
    DOCUMENTS,
    document_manifest_row,
    governance_rows,
    membership_rows,
    parse_civic_centres,
    parse_service_locations,
    rti_form_rows,
    rti_officer_rows,
    staff_rows,
)


def enrich_mj_library(store) -> None:
    """Fetch the M.J. Library sources, extract text/TSV/OCR via the store, and
    write the normalized curated CSVs. `store` provides all IO."""
    store.ensure_dirs()
    content = store.parse_content_js()
    store.fetch_about()

    document_rows = []
    for doc in DOCUMENTS:
        pdf_path = store.doc_path(doc["local_name"])
        store.fetch(doc["url"], pdf_path)
        text_path = store.text_path(Path(doc["local_name"]).stem)
        method = store.export_text(pdf_path, text_path)
        document_rows.append(document_manifest_row(
            doc,
            store.rel(pdf_path),
            store.rel(text_path) if text_path.exists() else "",
            store.sha256(pdf_path),
            pdf_path.stat().st_size,
            store.pdf_pages(pdf_path),
            method,
        ))

    store.render_page(store.doc_path("admissionformeng.pdf"), 1, store.image_path("admissionformeng-1.png"))
    store.render_page(store.doc_path("mj_discloser_rti_2025-26.pdf"), 70, store.image_path("mj_discloser_rti_2025-26_page70-70.png"))
    store.ocr_image(store.image_path("admissionformeng-1.png"), store.text_path("admissionformeng_ocr"), "eng")
    store.ocr_image(store.image_path("mj_discloser_rti_2025-26_page70-70.png"), store.text_path("mj_discloser_rti_2025-26_page70_ocr_guj"), "guj+eng")

    store.write_csv("mj_library_source_documents.csv", document_rows)
    store.write_csv(
        "mj_library_service_locations_2025.csv",
        parse_service_locations(store.pdf_words(store.doc_path("amc_library_balbhavan_mj_library_list_2025-07-08.pdf"))),
    )
    store.write_csv("mj_library_staff_establishment_2025.csv", staff_rows())
    store.write_csv("mj_library_rti_officers_2025.csv", rti_officer_rows())
    store.write_csv("mj_library_governance_roster_current.csv", governance_rows(content))
    store.write_csv("mj_library_membership_requirements.csv", membership_rows(content))
    store.write_csv("mj_library_rti_application_fields.csv", rti_form_rows())
    store.write_csv(
        "mj_library_civic_centres_rti_submission.csv",
        parse_civic_centres(store.pdf_words(store.doc_path("list_of_ccc.pdf"))),
    )
