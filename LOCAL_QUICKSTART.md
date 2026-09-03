# Local Quickstart

This guide is for running Model Card Builder locally.

## Prerequisites

- Python 3.9+
- pip
- Optional for AI enrichment: GITHUB_TOKEN with GitHub Models access

## Setup

1. Install requirements:

   ```powershell
   pip install -r requirements.txt
   ```

2. Fetch model-card data from Hugging Face:

   ```powershell
   python python/fetch_hf_model_card.py https://huggingface.co/org/model
   ```

   This writes model_data.json using the typed Model Card Data shape.

3. Build HTML model card from local data:

   ```powershell
   python python/build.py --data model_data.json
   ```

4. Optional AI enrichment with prompts:

   ```powershell
   $env:GITHUB_TOKEN = "<token with models access>"
   python python/summarize_model_card.py --url https://huggingface.co/org/model --data model_data.json --prompt prompts/summarize.prompt.yaml --recovery-prompt prompts/recover_model_card_facets.prompt.yaml
   ```

5. One-step flow from URL to HTML:

   ```powershell
   python python/build.py --url https://huggingface.co/org/model --template standard --theme noaa
   ```

## Catalog Dashboard

NMFS-OSI metadata is curated in `catalogs/nmfs-osi.toml`. SPARROW metadata is a pinned copy of its authoritative upstream `catalog.toml` with commit and hash provenance.

1. Rebuild all seven NMFS-OSI detail cards:

   ```powershell
   python python/sync_hf_catalog.py --build-cards
   ```

2. Generate the compatibility registry, normalized browser payload, and dashboard:

   ```powershell
   python python/build_catalog.py
   python python/build_catalog.py --check
   ```

3. Refresh or verify the pinned SPARROW catalog:

   ```powershell
   python python/sync_sparrow_catalog.py
   python python/sync_sparrow_catalog.py --check-remote
   ```

4. Detect NMFS-OSI additions or source revisions:

   ```powershell
   python python/sync_hf_catalog.py --check-remote
   ```

5. Preview the static gallery:

   ```powershell
   python -m http.server 8000
   ```

   Open `http://localhost:8000/gallery/`. The selected source, search, sort, and facets are stored in the URL.

## Notes

- Local output HTML is written to Model_Card.html in the repository root.
- `gallery/cards.json`, `gallery/catalog-data.json`, and `gallery/index.html` are generated files; edit the TOML source rather than those outputs.
- SPARROW model weights are not copied or hosted. SPARROW cards link to the pinned catalog's references and provenance.
- Commercial-use status is catalog metadata, not a substitute for reviewing model, dataset, and content licenses.
