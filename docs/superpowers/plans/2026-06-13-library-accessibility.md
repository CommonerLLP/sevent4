# Library Accessibility Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reusable library accessibility pipeline for Ahmedabad, Delhi, and Toronto, starting with deterministic walk/proxy access metrics and auditable DPL address geocoding inputs.

**Architecture:** Keep shared accessibility math in `scripts/recipes/accessibility/library_access.py`. City adapters normalize local source data into canonical `library_locations.csv` and derived `library_access/*` outputs. The comparator consumes city summaries and never embeds city-specific parsing logic.

**Tech Stack:** Python standard library, `unittest`, CSV/JSON/GeoJSON files, existing SevenT4 recipe conventions.

---

### Task 1: Shared Access Engine

**Files:**
- Create: `scripts/recipes/accessibility/__init__.py`
- Create: `scripts/recipes/accessibility/library_access.py`
- Test: `tests/test_library_access.py`

- [ ] **Step 1: Write the failing tests**

```python
from scripts.recipes.accessibility.library_access import (
    haversine_m,
    threshold_share,
    weighted_quantile,
)


def test_weighted_quantile_uses_population_weights():
    rows = [
        {"minutes": 5.0, "population": 10.0},
        {"minutes": 20.0, "population": 80.0},
        {"minutes": 60.0, "population": 10.0},
    ]
    assert weighted_quantile(rows, "minutes", "population", 0.50) == 20.0
    assert weighted_quantile(rows, "minutes", "population", 0.90) == 60.0


def test_threshold_share_reports_population_share():
    rows = [
        {"minutes": 10.0, "population": 25.0},
        {"minutes": 35.0, "population": 75.0},
    ]
    assert threshold_share(rows, "minutes", "population", 30.0) == 25.0


def test_haversine_m_is_reasonable_for_short_city_distance():
    distance = haversine_m(28.6599438, 77.2291808, 28.6572918, 77.2303200)
    assert 250.0 < distance < 400.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_library_access`

Expected: fails with `ModuleNotFoundError` or missing function imports.

- [ ] **Step 3: Implement minimal shared engine**

Create the module with:

```python
def weighted_quantile(rows, value_key, weight_key, quantile):
    if not 0 <= quantile <= 1:
        raise ValueError("quantile must be between 0 and 1")
    pairs = sorted(
        (float(row[value_key]), float(row[weight_key]))
        for row in rows
        if row.get(value_key) not in ("", None) and row.get(weight_key) not in ("", None)
    )
    total_weight = sum(weight for _, weight in pairs)
    if total_weight <= 0:
        raise ValueError("total weight must be positive")
    target = total_weight * quantile
    cumulative = 0.0
    for value, weight in pairs:
        cumulative += weight
        if cumulative >= target:
            return value
    return pairs[-1][0]
```

Also add `threshold_share`, `haversine_m`, and nearest-library walk-access helpers.

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m unittest tests.test_library_access`

Expected: all tests pass.

- [ ] **Step 5: Commit**

Run:

```bash
git add scripts/recipes/accessibility tests/test_library_access.py
git commit -m "Add shared library accessibility engine"
```

### Task 2: Delhi DPL Location Parser

**Files:**
- Modify: `scripts/recipes/delhi/extract_dpl_library.py`
- Test: `tests/test_delhi_dpl_locations.py`
- Output: `data/cities/delhi/source/libraries/dpl_library_locations.csv`
- Output: `data/cities/delhi/source/geocoding/geocode_cache.csv`

- [ ] **Step 1: Write parser tests**

```python
from pathlib import Path
from scripts.recipes.delhi.extract_dpl_library import extract_dpl_locations


def test_extract_dpl_locations_reads_zone_addresses(tmp_path):
    html_dir = tmp_path / "html"
    html_dir.mkdir()
    (html_dir / "operations__central_zone.html").write_text(
        """
        <strong style="color: #000000; font-size: 20px;">Central Library</strong>
        <iframe src="https://www.google.com/maps/embed?pb=!2d77.229180829205!3d28.659943775695407"></iframe>
        <td><span><strong>Address</strong></span></td>
        <td><p>Delhi Public Library, Dr. Shyama Prasad Mukherjee Marg, Delhi-110006</p></td>
        """,
        encoding="utf-8",
    )
    rows = extract_dpl_locations(html_dir)
    assert rows[0]["name"] == "Central Library"
    assert rows[0]["address"].endswith("Delhi-110006")
    assert rows[0]["latitude"] == "28.659943775695407"
    assert rows[0]["longitude"] == "77.229180829205"
    assert rows[0]["coordinate_source"] == "google_maps_embed"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_delhi_dpl_locations`

Expected: fails because `extract_dpl_locations` does not exist.

- [ ] **Step 3: Implement parser and geocode cache scaffolding**

Add:

```python
def extract_dpl_locations(html_dir: Path) -> list[dict[str, str]]:
    rows = []
    for path in sorted(html_dir.glob("operations__*_zone.html")):
        html = path.read_text(encoding="utf-8", errors="ignore")
        rows.extend(parse_dpl_zone_locations(path, html))
    rows.extend(parse_dpl_mobile_points(html_dir / "operations__schedule_and_points_of_mobile_van.html"))
    return rows
```

The parser writes published addresses to `dpl_library_locations.csv` and creates `geocode_cache.csv` rows for address-only records.

- [ ] **Step 4: Run extraction**

Run: `python3 scripts/recipes/delhi/extract_dpl_library.py`

Expected: existing DPL metrics are regenerated, plus DPL location/geocode files are written.

- [ ] **Step 5: Commit**

Run:

```bash
git add scripts/recipes/delhi/extract_dpl_library.py tests/test_delhi_dpl_locations.py data/cities/delhi/source/libraries/dpl_library_locations.csv data/cities/delhi/source/geocoding/geocode_cache.csv
git commit -m "Extract Delhi library locations"
```

### Task 3: Delhi Atlas Source Inventory

**Files:**
- Create: `scripts/recipes/delhi/build_atlas_source_inventory.py`
- Test: `tests/test_delhi_atlas_source_inventory.py`
- Output: `data/cities/delhi/source/opencity/delhi_opencity_inventory.csv`
- Output: `data/cities/delhi/source/opencity/delhi_opencity_atlas_shortlist.csv`
- Output: `data/cities/delhi/source/opencity/delhi_opencity_manifest.json`

- [ ] **Step 1: Write inventory tests**

```python
from scripts.recipes.delhi.build_atlas_source_inventory import classify_dataset, delhi_candidate


def test_delhi_candidate_matches_group_and_title():
    assert delhi_candidate({"groups": ["delhi"], "title": "Municipal Corporation Budget"})
    assert delhi_candidate({"groups": [], "title": "Delhi Road Crashes Data"})
    assert not delhi_candidate({"groups": ["bengaluru"], "title": "Bengaluru Budget"})


def test_classify_dataset_marks_budget_as_pays():
    dataset = {
        "title": "Municipal Corporation of Delhi Budget 2025-26",
        "tags": [],
        "notes": "",
        "organization": "government-of-delhi",
        "name": "municipal-corporation-of-delhi-budget-2025-26",
    }
    assert "pays" in classify_dataset(dataset)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_delhi_atlas_source_inventory`

Expected: fails because the inventory script does not exist.

- [ ] **Step 3: Implement inventory builder**

Read `data/sources/opencity/_catalogue/opencity_catalogue.json`, select Delhi datasets by group/name/title, classify them with the same atlas axes used by `scope_opencity_for_atlas.py`, and write CSV/JSON outputs preserving publisher, OpenCity URL, resource URL, format, modified date, axis labels, and shortlist flag.

- [ ] **Step 4: Run inventory builder**

Run: `python3 scripts/recipes/delhi/build_atlas_source_inventory.py`

Expected: writes Delhi OpenCity inventory, shortlist, and manifest under `data/cities/delhi/source/opencity`.

- [ ] **Step 5: Commit**

Run:

```bash
git add scripts/recipes/delhi/build_atlas_source_inventory.py tests/test_delhi_atlas_source_inventory.py data/cities/delhi/source/opencity
git commit -m "Inventory Delhi OpenCity atlas sources"
```

### Task 4: Ahmedabad Adapter

**Files:**
- Create: `scripts/recipes/ahmedabad/build_library_access.py`
- Output: `data/cities/ahmedabad/derived/library_access/library_access_summary.csv`

- [ ] **Step 1: Write adapter test**

```python
from scripts.recipes.ahmedabad.build_library_access import summarize_ahmedabad_libraries


def test_summarize_ahmedabad_libraries_counts_locations():
    rows = summarize_ahmedabad_libraries()
    assert rows[0]["city"] == "ahmedabad"
    assert int(rows[0]["branches"]) > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_ahmedabad_library_access`

Expected: fails because the adapter does not exist.

- [ ] **Step 3: Implement adapter**

Read `data/cities/ahmedabad/source/libraries/ahmedabad_library_locations.csv`, compute branch counts and nearest-library walk baseline over a small deterministic service-area proxy if no population origins exist yet.

- [ ] **Step 4: Run adapter**

Run: `python3 scripts/recipes/ahmedabad/build_library_access.py`

Expected: writes Ahmedabad derived summary.

- [ ] **Step 5: Commit**

Run:

```bash
git add scripts/recipes/ahmedabad/build_library_access.py tests/test_ahmedabad_library_access.py data/cities/ahmedabad/derived/library_access
git commit -m "Add Ahmedabad library access adapter"
```

### Task 5: Toronto Adapter And Pairwise Comparator

**Files:**
- Create: `scripts/recipes/toronto/build_library_access.py`
- Create: `scripts/recipes/comparators/build_library_access_comparison.py`
- Output: `data/comparators/library_access/*.csv`

- [ ] **Step 1: Write comparator test**

```python
from scripts.recipes.comparators.build_library_access_comparison import pair_key


def test_pair_key_is_stable():
    assert pair_key("delhi", "toronto") == "delhi_toronto"
    assert pair_key("toronto", "ahmedabad") == "ahmedabad_toronto"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m unittest tests.test_library_access_comparison`

Expected: fails because the comparator does not exist.

- [ ] **Step 3: Implement comparator**

Read each city summary and emit pairwise comparison rows for Delhi-Toronto, Ahmedabad-Delhi, and Ahmedabad-Toronto.

- [ ] **Step 4: Run comparator**

Run: `python3 scripts/recipes/comparators/build_library_access_comparison.py`

Expected: writes pairwise comparator CSVs.

- [ ] **Step 5: Commit**

Run:

```bash
git add scripts/recipes/toronto/build_library_access.py scripts/recipes/comparators/build_library_access_comparison.py tests/test_library_access_comparison.py data/comparators/library_access
git commit -m "Add library access comparators"
```

### Task 6: Verification And Report Hook

**Files:**
- Create: `docs/library-accessibility-comparison.qmd`
- Output: `docs/library-accessibility-comparison.html`
- Output: `docs/library-accessibility-comparison.pdf`

- [ ] **Step 1: Run all focused tests**

Run:

```bash
python3 -m unittest tests.test_library_access tests.test_delhi_dpl_locations tests.test_ahmedabad_library_access tests.test_library_access_comparison
```

Expected: all tests pass.

- [ ] **Step 2: Run all build scripts**

Run:

```bash
python3 scripts/recipes/delhi/extract_dpl_library.py
python3 scripts/recipes/ahmedabad/build_library_access.py
python3 scripts/recipes/comparators/build_library_access_comparison.py
```

Expected: all target CSV outputs are regenerated.

- [ ] **Step 3: Render report**

Run:

```bash
quarto render docs/library-accessibility-comparison.qmd --to html
quarto render docs/library-accessibility-comparison.qmd --to pdf
```

Expected: HTML and PDF are rendered.

- [ ] **Step 4: Final commit**

Run:

```bash
git add docs/library-accessibility-comparison.qmd docs/library-accessibility-comparison.html docs/library-accessibility-comparison.pdf
git commit -m "Render library accessibility comparison report"
```

## Self-Review

- Spec coverage: The plan covers shared engine, canonical city outputs, Delhi address/geocoding policy, Ahmedabad proof, pairwise comparators, and report hooks.
- Delhi atlas coverage: The plan includes an OpenCity-backed Delhi source inventory before the city accessibility adapters.
- Scope: The first build uses deterministic walk/proxy access. Full OpenTripPlanner routing remains a later Tier A implementation once feeds are locally available.
- Placeholder scan: No unresolved placeholder markers are present.
- Type consistency: Metric names use `p50_minutes_to_nearest_library`, matching the design spec.
