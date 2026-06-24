from __future__ import annotations

import shutil
import subprocess
from urllib.request import Request, urlopen

USER_AGENT = "The Unelected City finance-book fetcher"


class UrllibFinanceBookSource:
    """Fetches finance-book index HTML and PDF bytes over HTTP, falling back to
    curl when urllib is blocked."""

    def fetch_text(self, url: str) -> str:
        return self.fetch_bytes(url).decode("utf-8", errors="ignore")

    def fetch_bytes(self, url: str) -> bytes:
        request = Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urlopen(request, timeout=60) as response:
                return response.read()
        except Exception as exc:
            curl = shutil.which("curl")
            if not curl:
                raise
            result = subprocess.run(
                [curl, "-L", "--fail", "--silent", "--show-error", url],
                check=False,
                capture_output=True,
            )
            if result.returncode == 0:
                return result.stdout
            raise RuntimeError(
                result.stderr.decode("utf-8", errors="ignore").strip() or str(exc)
            ) from exc
