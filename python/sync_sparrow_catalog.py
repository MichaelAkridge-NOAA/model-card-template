#!/usr/bin/env python
"""Pin and verify SPARROW's authoritative model catalog."""

import argparse
import hashlib
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


RAW_URL = "https://raw.githubusercontent.com/microsoft/SPARROW-Engine/main/sparrow-engine/scripts/catalog.toml"
COMMITS_URL = "https://api.github.com/repos/microsoft/SPARROW-Engine/commits?path=sparrow-engine/scripts/catalog.toml&per_page=1"
ROOT = Path(__file__).resolve().parent.parent
SNAPSHOT_PATH = ROOT / "catalogs" / "sparrow.catalog.toml"
PROVENANCE_PATH = ROOT / "catalogs" / "sparrow.provenance.json"


def _fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "model-card-builder"})
    with urllib.request.urlopen(request, timeout=30) as response:
        return response.read()


def fetch_upstream():
    content = _fetch(RAW_URL)
    commits = json.loads(_fetch(COMMITS_URL).decode("utf-8"))
    commit = commits[0]["sha"] if commits else "unknown"
    digest = hashlib.sha256(content).hexdigest()
    return content, commit, digest


def write_snapshot(content: bytes, commit: str, digest: str) -> None:
    SNAPSHOT_PATH.parent.mkdir(parents=True, exist_ok=True)
    SNAPSHOT_PATH.write_bytes(content)
    provenance = {
        "source_url": RAW_URL,
        "source_commit": commit,
        "sha256": digest,
        "retrieved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    PROVENANCE_PATH.write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")


def check_snapshot(content: bytes, commit: str, digest: str) -> bool:
    if not SNAPSHOT_PATH.exists() or not PROVENANCE_PATH.exists():
        return False
    provenance = json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
    local_digest = hashlib.sha256(SNAPSHOT_PATH.read_bytes()).hexdigest()
    return (
        local_digest == provenance.get("sha256")
        and digest == provenance.get("sha256")
        and commit == provenance.get("source_commit")
        and content == SNAPSHOT_PATH.read_bytes()
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-remote", action="store_true", help="Fail when the pinned snapshot differs from upstream")
    args = parser.parse_args()
    try:
        content, commit, digest = fetch_upstream()
    except Exception as error:
        print(f"Unable to fetch SPARROW catalog: {error}", file=sys.stderr)
        return 2

    if args.check_remote:
        if check_snapshot(content, commit, digest):
            print(f"SPARROW snapshot is current at {commit[:12]}")
            return 0
        print(f"SPARROW catalog drift detected at {commit[:12]}", file=sys.stderr)
        return 1

    write_snapshot(content, commit, digest)
    print(f"Pinned SPARROW catalog at {commit[:12]} ({digest[:12]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())