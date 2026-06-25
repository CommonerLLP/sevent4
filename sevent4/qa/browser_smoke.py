from __future__ import annotations

import argparse
from dataclasses import dataclass
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading


SMOKE_PATHS = (
    "/index.html",
    "/public/index.html",
    "/public/cities/ahmedabad/index.html",
)


@dataclass(frozen=True)
class SmokeViewport:
    label: str
    width: int
    height: int


SMOKE_VIEWPORTS = (
    SmokeViewport("mobile", 390, 844),
    SmokeViewport("tablet", 768, 1024),
    SmokeViewport("desktop", 1366, 900),
)


class RecordingHandler(SimpleHTTPRequestHandler):
    records: list[tuple[int, str]] = []
    quiet = True

    def log_request(self, code: int | str = "-", size: int | str = "-") -> None:
        try:
            status = int(code)
        except (TypeError, ValueError):
            status = 0
        self.records.append((status, self.path))

    def log_message(self, format: str, *args) -> None:
        if not self.quiet:
            super().log_message(format, *args)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Playwright CLI smoke checks against the static public surface.")
    parser.add_argument("--root", default=".", help="Repository root to serve. Defaults to current directory.")
    parser.add_argument("--playwright", default=shutil.which("playwright") or "playwright", help="Playwright CLI path.")
    parser.add_argument("--out-dir", help="Directory for screenshots. Defaults to a temporary directory.")
    parser.add_argument("--keep-screenshots", action="store_true", help="Keep screenshots when using a temporary directory.")
    parser.add_argument("--verbose-server", action="store_true", help="Print HTTP server request logs.")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()
    if not (root / "index.html").exists() or not (root / "public" / "index.html").exists():
        parser.error(f"{root} does not look like the sevent4 static root")

    with _screenshot_dir(args.out_dir, args.keep_screenshots) as out_dir:
        return run_smoke(root, Path(args.playwright), out_dir, verbose_server=args.verbose_server)


def run_smoke(root: Path, playwright: Path, out_dir: Path, *, verbose_server: bool = False) -> int:
    RecordingHandler.records = []
    RecordingHandler.quiet = not verbose_server
    handler = partial(RecordingHandler, directory=str(root))
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    base_url = f"http://{host}:{port}"

    try:
        for viewport in SMOKE_VIEWPORTS:
            for path in SMOKE_PATHS:
                subprocess.run(
                    build_screenshot_command(
                        playwright,
                        f"{base_url}{path}",
                        out_dir / screenshot_path(path, viewport.label),
                        viewport,
                    ),
                    check=True,
                )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    failures = [
        f"{status} {path}"
        for status, path in RecordingHandler.records
        if status >= 400 and not is_ignored_request(path)
    ]
    if failures:
        print("Browser smoke saw failed local requests:", file=sys.stderr)
        for failure in failures:
            print(f"  {failure}", file=sys.stderr)
        return 1
    print(
        f"browser smoke OK: {len(SMOKE_PATHS)} routes x {len(SMOKE_VIEWPORTS)} viewports, "
        f"screenshots in {out_dir}"
    )
    return 0


def is_ignored_request(path: str) -> bool:
    return path.split("?", 1)[0] == "/favicon.ico"


def build_screenshot_command(playwright: Path, url: str, screenshot: Path, viewport: SmokeViewport) -> list[str]:
    return [
        str(playwright),
        "screenshot",
        "--full-page",
        f"--viewport-size={viewport.width},{viewport.height}",
        url,
        str(screenshot),
    ]


def screenshot_path(route: str, viewport_label: str) -> str:
    return f"{viewport_label}-{route.strip('/').replace('/', '-')}.png"


class _screenshot_dir:
    def __init__(self, out_dir: str | None, keep: bool) -> None:
        self.out_dir = Path(out_dir).resolve() if out_dir else None
        self.keep = keep
        self._tmp: tempfile.TemporaryDirectory[str] | None = None

    def __enter__(self) -> Path:
        if self.out_dir is not None:
            self.out_dir.mkdir(parents=True, exist_ok=True)
            return self.out_dir
        self._tmp = tempfile.TemporaryDirectory(prefix="sevent4-browser-smoke-")
        return Path(self._tmp.name)

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._tmp is not None and not self.keep:
            self._tmp.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
