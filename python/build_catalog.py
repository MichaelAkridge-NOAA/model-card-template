#!/usr/bin/env python
"""Generate the dual-source static model catalog and compatibility registry."""

import argparse
import base64
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    from .model_catalog import ModelCatalog, dashboard_totals, load_catalog
except ImportError:  # Allow running as python/build_catalog.py.
    from model_catalog import ModelCatalog, dashboard_totals, load_catalog


ROOT = Path(__file__).resolve().parent.parent
NMFS_PATH = ROOT / "catalogs" / "nmfs-osi.toml"
SPARROW_PATH = ROOT / "catalogs" / "sparrow.catalog.toml"
DATA_PATH = ROOT / "gallery" / "catalog-data.json"
REGISTRY_PATH = ROOT / "gallery" / "cards.json"
TEMPLATE_PATH = ROOT / "gallery" / "catalog_template.html"
INDEX_PATH = ROOT / "gallery" / "index.html"


def _plain_text(value: str) -> str:
    value = re.sub(r"!\[[^]]*\]\([^)]*\)", "", value)
    value = re.sub(r"\[([^]]+)\]\([^)]*\)", r"\1", value)
    value = re.sub(r"[*_`#>]", "", value)
    return re.sub(r"\s+", " ", value).strip()


def _source_payload(catalog: ModelCatalog, source: Dict[str, str]) -> Dict[str, Any]:
    models = []
    for model in catalog.models:
        record = model.to_dict()
        record["description"] = _plain_text(record["description"] or record["reference"])
        models.append(record)
    return {**source, "totals": dashboard_totals(catalog), "models": models}


def build_payload() -> Dict[str, Any]:
    nmfs = load_catalog(NMFS_PATH)
    sparrow = load_catalog(SPARROW_PATH, source_id="sparrow")
    provenance_path = ROOT / "catalogs" / "sparrow.provenance.json"
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    return {
        "schema_version": "1.0",
        "default_source": "nmfs-osi",
        "sources": {
            "nmfs-osi": _source_payload(nmfs, {
                "id": "nmfs-osi",
                "name": "NMFS-OSI",
                "description": nmfs.source.description,
                "about_title": "",
                "about": "",
                "project_url": "",
                "source_url": nmfs.source.source_url,
                "freshness": f"Indexed {nmfs.source.source_revision}",
                "ready_label": "catalog-ready",
            }),
            "sparrow": _source_payload(sparrow, {
                "id": "sparrow",
                "name": "SPARROW",
                "description": "Versioned conservation AI model zoo distributed by Microsoft SPARROW Engine.",
                "about_title": "About the SPARROW catalog",
                "about": "This tab presents a pinned, normalized view of SPARROW's versioned conservation AI model zoo. SPARROW provides open-source tooling for discovering and running biodiversity models across camera-trap, acoustic, overhead, marine-imagery, and general AI workflows.",
                "project_url": "https://github.com/microsoft/SPARROW",
                "source_url": provenance["source_url"],
                "freshness": f"Pinned {provenance['source_commit'][:12]}",
                "ready_label": "default ONNX",
            }),
        },
    }


def build_registry(payload: Dict[str, Any]) -> Dict[str, Any]:
    old_dates = {}
    if REGISTRY_PATH.exists():
        old = json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
        old_dates = {card["model_id"]: card.get("date_added") for card in old.get("cards", [])}
    cards: List[Dict[str, Any]] = []
    for model in payload["sources"]["nmfs-osi"]["models"]:
        cards.append({
            "model_id": model["id"],
            "model_name": model["display_name"],
            "model_url": model["source_url"],
            "card_url": model["card_url"],
            "pipeline_type": {
                "classifier": "image-classification",
                "detector": "object-detection",
                "segmenter": "image-segmentation",
            }.get(model["task"], model["task"]),
            "date_added": old_dates.get(model["id"]) or model["last_modified"],
            "description": model["description"],
            "organization": "NMFS-OSI",
            "thumbnail_url": model["thumbnail_url"],
        })
    return {
        "_schema_version": "2.0",
        "_schema_description": "Generated NMFS-OSI compatibility registry. Edit catalogs/nmfs-osi.toml instead.",
        "cards": cards,
    }


def render_files(check: bool = False) -> bool:
    payload = build_payload()
    data_text = json.dumps(payload, indent=2, ensure_ascii=True) + "\n"
    registry_text = json.dumps(build_registry(payload), indent=2, ensure_ascii=True) + "\n"
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    embedded = json.dumps(payload, separators=(",", ":"), ensure_ascii=True).replace("</", "<\\/")
    logo_bytes = (ROOT / "assets" / "optics_si_logo_v1.png").read_bytes()
    logo_data = "data:image/png;base64," + base64.b64encode(logo_bytes).decode("ascii")
    index_text = template.replace("{CATALOG_DATA}", embedded).replace("{OPTICS_LOGO}", logo_data)
    outputs = ((DATA_PATH, data_text), (REGISTRY_PATH, registry_text), (INDEX_PATH, index_text))
    if check:
        stale = [str(path.relative_to(ROOT)) for path, text in outputs if not path.exists() or path.read_text(encoding="utf-8") != text]
        if stale:
            print("Generated catalog files are stale: " + ", ".join(stale), file=sys.stderr)
            return False
        print("Generated catalog files are current")
        return True
    for path, text in outputs:
        path.write_text(text, encoding="utf-8")
    print(f"Generated dual catalog with {len(payload['sources']['nmfs-osi']['models'])} NMFS-OSI and {len(payload['sources']['sparrow']['models'])} SPARROW models")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if committed generated files are stale")
    args = parser.parse_args()
    return 0 if render_files(args.check) else 1


if __name__ == "__main__":
    sys.exit(main())