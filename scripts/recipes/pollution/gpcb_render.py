#!/usr/bin/env python3
"""Render the GPCB UX4G SPA through the India SOCKS proxy and capture the
AES-decrypted network JSON + DOM, to recover annual-report PDF URLs.

The GPCB portal (gpcb.gujarat.gov.in) wraps its content API in client-side AES
(/Admin/js/secure/aes.js). Rather than reverse the cipher, we drive headless
Chromium — the page decrypts its own responses — and we intercept the JSON the
app receives, plus the post-render DOM links.

Prereq: a venv with `playwright` (+ `playwright install chromium`), and an India
        SOCKS exit:  ssh -i <key> -D 1080 -N -f <user>@<india-host>
Usage:  <venv-python> gpcb_render.py <url> [nav-text-regex]
"""
import sys, re, json, os
from playwright.sync_api import sync_playwright

url = sys.argv[1] if len(sys.argv) > 1 else "https://gpcb.gujarat.gov.in/"
nav_kw = re.compile(sys.argv[2] if len(sys.argv) > 2 else r"annual\s*report", re.I)

api_log = []

def on_response(resp):
    try:
        ct = (resp.headers.get("content-type") or "").lower()
        u = resp.url
        if u.endswith((".js", ".css", ".png", ".jpg", ".jpeg", ".svg", ".woff", ".woff2", ".ico")):
            return
        if "json" in ct or "/webcontroller/" in u or "/api/" in u or "getdata" in u.lower():
            body = resp.text()
            api_log.append({"url": u, "status": resp.status, "ct": ct, "body": body[:6000]})
    except Exception:
        pass

with sync_playwright() as p:
    b = p.chromium.launch(headless=True, proxy={"server": "socks5://127.0.0.1:1080"},
                          args=["--no-sandbox"])
    ctx = b.new_context(ignore_https_errors=True, user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36")
    pg = ctx.new_page()
    pg.on("response", on_response)
    pg.goto(url, wait_until="networkidle", timeout=70000)
    pg.wait_for_timeout(3000)

    # Find an "annual report" nav link/onclick and follow it.
    nav = pg.eval_on_selector_all(
        "a,[onclick],button,li",
        "els=>els.map(e=>[e.tagName,(e.href||e.getAttribute('onclick')||''),(e.innerText||'').trim().replace(/\\s+/g,' ').slice(0,60)])")
    followed = None
    for tag, attr, txt in nav:
        if nav_kw.search(txt) and "annual" in attr.lower():
            # only a real http route that actually names the section is a nav target;
            # an SPA placeholder like href="#" resolves to the current page URL and
            # would silently "succeed" onto the home page, so fall through to the click.
            target = attr if attr.startswith("http") else None
            if target:
                try:
                    pg.goto(target, wait_until="networkidle", timeout=60000)
                    pg.wait_for_timeout(2500)
                    followed = target
                    break
                except Exception:
                    pass
    if not followed:
        # try clicking the matching element in-page (SPA route)
        for sel in ["a", "[onclick]", "button", "li"]:
            try:
                loc = pg.get_by_text(re.compile(r"annual\s*report", re.I)).first
                loc.click(timeout=4000)
                pg.wait_for_load_state("networkidle", timeout=30000)
                pg.wait_for_timeout(2500)
                followed = "in-page-click"
                break
            except Exception:
                continue

    final, title = pg.url, pg.title()
    links = pg.eval_on_selector_all(
        "a", "els=>els.map(e=>[e.href,(e.innerText||'').trim().replace(/\\s+/g,' ')])")
    page_text = pg.inner_text("body")[:4000]
    b.close()

os.makedirs("data/national/pollution/raw/gpcb", exist_ok=True)
json.dump({"final": final, "title": title, "followed": followed,
           "links": links, "api_log": api_log, "page_text": page_text},
          open("data/national/pollution/raw/gpcb/_render.json", "w"),
          ensure_ascii=False, indent=1)

print(f"FINAL: {final}\nTITLE: {title}\nFOLLOWED: {followed}")
print(f"API responses captured: {len(api_log)}")
pdfs = sorted({h for h, t in links if h and h.lower().endswith(".pdf")})
print(f"\n== PDF links in DOM ({len(pdfs)}) ==")
for h in pdfs[:40]:
    print("  ", h)
print("\n== API endpoints (json) ==")
for e in api_log:
    has_pdf = ".pdf" in e["body"].lower()
    print(f"  [{e['status']}] {e['url'][:90]}  {'<<PDF in body>>' if has_pdf else ''}")
