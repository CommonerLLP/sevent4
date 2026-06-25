from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


def _sha256(path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class PdftotextRbiSource:
    """-layout pdftotext rendering of an RBI report PDF."""

    def text(self, pdf) -> str:
        proc = subprocess.run(
            ["pdftotext", "-layout", str(pdf), "-"],
            check=True,
            text=True,
            capture_output=True,
        )
        return proc.stdout

    def sha256(self, pdf) -> str:
        return _sha256(pdf)


class PandasRbiHtmlSource:
    """RBI PublicationsView HTML tables via pandas.read_html."""

    def read_tables(self, path) -> list:
        import pandas as pd

        return pd.read_html(path)

    def sha256(self, path) -> str:
        return _sha256(path)


def write_rbi_report(out_path, result: dict[str, Any]) -> None:
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
