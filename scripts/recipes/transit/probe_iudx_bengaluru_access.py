#!/usr/bin/env python3
"""Probe whether IUDX has granted Bengaluru BMTC/BMRCL resource access.

The script prints only redacted status summaries. It never writes client
credentials or returned resource tokens.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from sevent4.transit.iudx_access_probe import (
    classify_token_response,
    iter_request_resources,
    load_access_request_packet,
    normalize_probe_payload,
    summarize_probe_results,
    token_request_payload,
)


AUTH_TOKEN_URL = "https://authorization.iudx.org.in/auth/v1/token"


def main() -> None:
    parser = argparse.ArgumentParser(description="Probe Bengaluru IUDX resource-token access.")
    parser.add_argument(
        "--packet",
        type=Path,
        default=Path("notes/transit/bengaluru-iudx-access-request-packet.json"),
    )
    parser.add_argument("--out", type=Path)
    parser.add_argument("--max-priority", type=int)
    parser.add_argument("--static-only", action="store_true")
    parser.add_argument(
        "--normalize-existing",
        type=Path,
        help="Normalize an existing probe-result JSON file without reading credentials or contacting IUDX.",
    )
    parser.add_argument("--token-url", default=AUTH_TOKEN_URL)
    args = parser.parse_args()

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if args.normalize_existing:
        existing = json.loads(args.normalize_existing.read_text(encoding="utf-8"))
        payload = normalize_probe_payload(existing, normalized_at=generated_at)
        text = json.dumps(payload, ensure_ascii=False, indent=1) + "\n"
        out = args.out or args.normalize_existing
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, encoding="utf-8")
        return

    client_id = _read_keychain_password("iudx-portal-client-id", "client_id")
    client_secret = _read_keychain_password("iudx-portal-client-secret", "client_secret")
    packet = load_access_request_packet(args.packet)
    resources = list(
        iter_request_resources(
            packet,
            static_only=args.static_only,
            max_priority=args.max_priority,
        )
    )
    results = [
        _probe_resource(args.token_url, client_id, client_secret, resource)
        for resource in resources
    ]
    payload = {
        "schema": "sevent4.iudx_access_probe_results.v1",
        "generated_at": generated_at,
        "packet": str(args.packet),
        "token_url": args.token_url,
        "resource_count": len(results),
        "summary": summarize_probe_results(results),
        "results": results,
    }
    text = json.dumps(payload, ensure_ascii=False, indent=1) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def _probe_resource(
    token_url: str,
    client_id: str,
    client_secret: str,
    resource: Any,
) -> dict[str, Any]:
    body = json.dumps(token_request_payload(resource)).encode("utf-8")
    request = urllib.request.Request(
        token_url,
        data=body,
        headers={
            "content-type": "application/json",
            "clientId": client_id,
            "clientSecret": client_secret,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            response_payload = _load_json_response(response.read())
            return classify_token_response(resource, response.status, response_payload)
    except urllib.error.HTTPError as exc:
        response_payload = _load_json_response(exc.read())
        return classify_token_response(resource, exc.code, response_payload)


def _load_json_response(body: bytes) -> dict[str, Any]:
    if not body:
        return {}
    try:
        loaded = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError as exc:
        return {
            "title": "Non-JSON response",
            "detail": str(exc),
        }
    return loaded if isinstance(loaded, dict) else {"results": loaded}


def _read_keychain_password(service: str, account: str) -> str:
    try:
        completed = subprocess.run(
            ["security", "find-generic-password", "-s", service, "-a", account, "-w"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"missing Keychain credential: service={service} account={account}") from exc
    value = completed.stdout.strip()
    if not value:
        raise SystemExit(f"empty Keychain credential: service={service} account={account}")
    return value


if __name__ == "__main__":
    main()
