#!/usr/bin/env python
"""Check NMFS-OSI Hugging Face drift and rebuild its model cards."""

import argparse
import json
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from python.build import build_model_card
from python.fetch_hf_model_card import fetch_model_card
from python.model_catalog import load_catalog


ROOT = Path(__file__).resolve().parent.parent
CATALOG_PATH = ROOT / "catalogs" / "nmfs-osi.toml"
API_URL = "https://huggingface.co/api/models?" + urllib.parse.urlencode({
    "author": "NMFS-OSI",
    "limit": 100,
    "full": "true",
})


def fetch_inventory() -> List[Dict[str, Any]]:
    request = urllib.request.Request(API_URL, headers={"User-Agent": "model-card-builder"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def check_remote() -> bool:
    catalog = load_catalog(CATALOG_PATH)
    expected = {model.id: model.source_revision for model in catalog.models}
    remote = {item.get("modelId", item.get("id")): item.get("sha", "") for item in fetch_inventory()}
    missing = sorted(set(remote) - set(expected))
    removed = sorted(set(expected) - set(remote))
    revised = sorted(model_id for model_id in set(expected) & set(remote) if expected[model_id] != remote[model_id])
    if missing or removed or revised:
        if missing:
            print("Unindexed Hugging Face models: " + ", ".join(missing), file=sys.stderr)
        if removed:
            print("Catalog models missing upstream: " + ", ".join(removed), file=sys.stderr)
        if revised:
            print("Models with source revision drift: " + ", ".join(revised), file=sys.stderr)
        return False
    print(f"NMFS-OSI catalog is current for {len(remote)} models")
    return True


def build_cards(model_id: str = "") -> bool:
    catalog = load_catalog(CATALOG_PATH)
    models = [model for model in catalog.models if not model_id or model.id == model_id]
    if not models:
        print(f"Model is not indexed: {model_id}", file=sys.stderr)
        return False
    failures = []
    with tempfile.TemporaryDirectory() as directory:
        data_path = Path(directory) / "model_data.json"
        for model in models:
            output_path = ROOT / "gallery" / model.card_url
            output_path.parent.mkdir(parents=True, exist_ok=True)
            try:
                fetch_model_card(model.source_url, str(data_path))
                if not build_model_card(str(data_path), str(output_path)):
                    failures.append(model.id)
            except Exception as error:
                failures.append(model.id)
                print(f"Failed to build {model.id}: {error}", file=sys.stderr)
    if failures:
        print("Failed model cards: " + ", ".join(failures), file=sys.stderr)
        return False
    print(f"Built {len(models)} NMFS-OSI model cards")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-remote", action="store_true", help="Compare catalog IDs and revisions with Hugging Face")
    parser.add_argument("--build-cards", action="store_true", help="Fetch and render indexed detail cards")
    parser.add_argument("--model-id", default="", help="Limit card rendering to one indexed Hugging Face ID")
    args = parser.parse_args()
    if not args.check_remote and not args.build_cards:
        parser.error("select --check-remote or --build-cards")
    try:
        valid = True
        if args.check_remote:
            valid = check_remote() and valid
        if args.build_cards:
            valid = build_cards(args.model_id) and valid
        return 0 if valid else 1
    except Exception as error:
        print(f"NMFS-OSI synchronization failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())