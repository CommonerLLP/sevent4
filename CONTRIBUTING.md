# Contributing to The Unelected City

Thanks for your interest in improving this atlas. It is a civic-data project: most of
what matters here is **data provenance and honest claims**, so the contribution rules
lean as much on sourcing discipline as on code.

## Report issues

1. Open a GitHub issue with a clear title and reproduction details.
2. Include the command(s) you ran, the city/page affected, expected vs actual behaviour.
3. For a data problem, point at the layer/file and, where you can, the upstream source.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
make hooks            # install the pre-commit hook — REQUIRED before your first commit
```

Serve the built site locally to eyeball changes:

```bash
bash scripts/serve.sh          # then open http://127.0.0.1:9174/
```

## Branch & PR workflow (org policy)

- **Never commit directly to `main`.** All engineering happens on a named branch and
  integrates through a pull request. The pre-commit hook enforces this.
- Keep PRs focused and small. Reference related issues in the description.
- **Do not add authorship or tool-attribution trailers to commits** — this is
  an org-wide rule for CommonerLLP repos.

## Quality checks (run before opening a PR)

```bash
python3 -m unittest discover -s tests       # the full suite must pass (currently 319 tests)
git ls-files '*.py' | xargs -I{} python3 -m py_compile {}   # every tracked .py must compile
```

- Add or update tests for behaviour changes.
- If you change a city console or the generator, **rebuild and eyeball the affected
  consoles** (`bash scripts/build-city.sh <city>`), preferably in more than one browser.
- The structural invariant: `public/cities/registry.json`, `scorecard.json`, and the
  built consoles must all list the **same** cities (the registry test enforces this).

## Contributing data (the important part)

If you add or refresh a layer, finding, or figure:

1. **Provenance is mandatory.** Record the source URL, publisher, license, retrieval date,
   and feature counts in the city's `source/PROVENANCE.md` and a machine-readable
   `source/sources.json`. A number with no traceable source does not ship.
2. **Preserve the original.** Keep the original PDF / shapefile / download; do not delete
   source material. Government budget PDFs and similar primary records are preserved
   (with external archive copies where possible).
3. **Respect the upstream license and attribute it.** This atlas redistributes
   OpenStreetMap (ODbL), WorldPop (CC-BY), DataMeet, OpenCity, Census of India, and
   government data — each under its own terms. New sources must be added to
   [`ATTRIBUTION.md`](ATTRIBUTION.md). ODbL/CC-BY-SA layers stay open + attributed; never
   relicense third-party data.
4. **Keep caveats out of result tables.** Coordinate/geocoding/vintage limitations belong
   in a Limitations/Future-Work note or popup flag, not buried inside a finding's headline.
5. **Honesty over polish.** `console-built` or `selectable` is not `publication-grade`;
   disclose what a layer can and cannot support.

## What stays local (gitignored by design)

Local working material and large raw datasets are gitignored by design. Do not
commit secrets, personal email addresses, internal strategy notes, or raw source
archives. The pre-commit hook runs a leak check; do not bypass it with
`--no-verify`.

## Papers

Library/finance papers use **Quarto**, structured as: Abstract · Conceptual/Measurement
Frame · Data/Methods · Results · Interpretation · Limitations/Future Work · Conclusion ·
References. Figures must be reproducible from a script, not pasted images.

## Conduct

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md).
