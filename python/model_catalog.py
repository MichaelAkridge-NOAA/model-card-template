"""Normalized catalog records shared by NMFS-OSI and SPARROW."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import tomllib
except ImportError:  # pragma: no cover - Python 3.9 compatibility
    import tomli as tomllib


TASK_ALIASES = {
    "image-classification": "classifier",
    "object-detection": "detector",
    "image-segmentation": "segmenter",
    "segmentation": "segmenter",
}

COMMERCIAL_LICENSES = {
    "AGPL-3.0", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "CC-BY-4.0",
    "CC-BY-SA-4.0", "CC0-1.0", "GPL-3.0", "MIT",
}


@dataclass(frozen=True)
class CatalogSource:
    id: str
    name: str
    description: str
    version: str = ""
    source_url: str = ""
    source_revision: str = ""


@dataclass(frozen=True)
class CatalogModel:
    source_id: str
    id: str
    display_name: str
    description: str
    status: str
    domain: str
    task: str
    formats: List[str]
    family: List[str] = field(default_factory=list)
    geo_scope: str = "unknown"
    geo_regions: List[str] = field(default_factory=list)
    developer: str = "Unknown"
    owner: str = ""
    license: str = "unknown"
    commercial_use: str = "unknown"
    commercial_use_reason: str = "License policy could not determine commercial-use permission."
    dataset_license: str = "unknown"
    reference: str = ""
    card_url: str = ""
    source_url: str = ""
    reviewed: bool = False
    class_count: Optional[int] = None
    labels: List[str] = field(default_factory=list)
    datasets: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    flavor: str = ""
    ai4g_relationship: str = ""
    alias: List[str] = field(default_factory=list)
    architecture: str = ""
    input_size: str = ""
    source_revision: str = ""
    last_modified: str = ""
    thumbnail_url: str = ""

    @property
    def namespaced_id(self) -> str:
        return f"{self.source_id}:{self.id}"

    @property
    def catalog_ready(self) -> bool:
        return bool(
            self.status == "active"
            and self.reviewed
            and self.task != "unknown"
            and self.source_url
            and self.card_url
            and self.formats
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "catalog_id": self.namespaced_id,
            "source_id": self.source_id,
            "id": self.id,
            "display_name": self.display_name,
            "description": self.description,
            "status": self.status,
            "domain": self.domain,
            "task": self.task,
            "formats": self.formats,
            "family": self.family,
            "geo_scope": self.geo_scope,
            "geo_regions": self.geo_regions,
            "developer": self.developer,
            "owner": self.owner,
            "license": self.license,
            "commercial_use": self.commercial_use,
            "commercial_use_reason": self.commercial_use_reason,
            "dataset_license": self.dataset_license,
            "reference": self.reference,
            "card_url": self.card_url,
            "source_url": self.source_url,
            "reviewed": self.reviewed,
            "catalog_ready": self.catalog_ready,
            "class_count": self.class_count,
            "labels": self.labels,
            "datasets": self.datasets,
            "artifacts": self.artifacts,
            "tags": self.tags,
            "flavor": self.flavor,
            "ai4g_relationship": self.ai4g_relationship,
            "alias": self.alias,
            "architecture": self.architecture,
            "input_size": self.input_size,
            "source_revision": self.source_revision,
            "last_modified": self.last_modified,
            "thumbnail_url": self.thumbnail_url,
            "default_onnx": self.source_id == "sparrow" and self.formats == ["onnx"] and not self.flavor,
        }


@dataclass(frozen=True)
class ModelCatalog:
    source: CatalogSource
    models: List[CatalogModel]


def normalize_task(value: str) -> str:
    normalized = str(value or "unknown").strip().lower().replace("_", "-")
    return TASK_ALIASES.get(normalized, normalized)


def _string_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return [str(value)] if str(value).strip() else []


def infer_commercial_use(license_name: str, value: Any = None):
    if value is True:
        return "allowed", "The source catalog explicitly permits commercial use."
    if value is False:
        return "restricted", "The source catalog explicitly restricts commercial use."
    normalized = str(value or "unknown").lower()
    if normalized in {"allowed", "restricted"}:
        return normalized, "The curated catalog explicitly records this commercial-use status."
    if "-NC" in license_name.upper() or "NONCOMMERCIAL" in license_name.upper():
        return "restricted", f"{license_name} contains a noncommercial restriction."
    parts = {part.strip(" ()") for part in license_name.replace(" AND ", " OR ").split(" OR ")}
    if parts and all(part in COMMERCIAL_LICENSES for part in parts):
        return "allowed", f"{license_name} does not prohibit commercial use, subject to its conditions."
    return "unknown", f"Commercial-use permission could not be inferred from {license_name or 'an unknown license'}."


def load_catalog(path: Path, source_id: Optional[str] = None) -> ModelCatalog:
    with path.open("rb") as catalog_file:
        raw = tomllib.load(catalog_file)

    source_raw = raw.get("source", {})
    resolved_source_id = source_id or source_raw.get("id")
    if not resolved_source_id:
        raise ValueError(f"Catalog {path} is missing source.id")

    source = CatalogSource(
        id=resolved_source_id,
        name=str(source_raw.get("name", resolved_source_id)),
        description=str(source_raw.get("description", "")),
        version=str(source_raw.get("version", raw.get("schema_version", ""))),
        source_url=str(source_raw.get("source_url", "")),
        source_revision=str(source_raw.get("source_revision", "")),
    )

    models = []
    seen_ids = set()
    for item in raw.get("model", []):
        model_id = str(item.get("id", "")).strip()
        if not model_id:
            raise ValueError(f"Catalog {path} contains a model without an id")
        if model_id in seen_ids:
            raise ValueError(f"Catalog {path} contains duplicate model id {model_id}")
        seen_ids.add(model_id)
        formats = _string_list(item.get("formats", item.get("format")))
        license_name = str(item.get("license", "unknown"))
        commercial_use, commercial_use_reason = infer_commercial_use(license_name, item.get("commercial_use"))
        models.append(CatalogModel(
            source_id=resolved_source_id,
            id=model_id,
            display_name=str(item.get("display_name", model_id)),
            description=str(item.get("description", "")),
            status=str(item.get("status", "active")),
            domain=str(item.get("domain", "unknown")),
            task=normalize_task(str(item.get("task", item.get("pipeline_type", "unknown")))),
            formats=formats,
            family=_string_list(item.get("family")),
            geo_scope=str(item.get("geo_scope", "unknown")),
            geo_regions=_string_list(item.get("geo_regions")),
            developer=str(item.get("developer", "Unknown")),
            owner=str(item.get("owner", "")),
            license=license_name,
            commercial_use=commercial_use,
            commercial_use_reason=commercial_use_reason,
            dataset_license=str(item.get("dataset_license", "unknown")),
            reference=str(item.get("reference", "")),
            card_url=str(item.get("card_url", "")),
            source_url=str(item.get("source_url", "")),
            reviewed=bool(item.get("reviewed", resolved_source_id == "sparrow")),
            class_count=item.get("class_count"),
            labels=_string_list(item.get("labels")),
            datasets=_string_list(item.get("datasets")),
            artifacts=_string_list(item.get("artifacts")),
            tags=_string_list(item.get("tags")),
            flavor=str(item.get("flavor", "")),
            ai4g_relationship=str(item.get("ai4g_relationship", "")),
            alias=_string_list(item.get("alias")),
            architecture=str(item.get("architecture", "")),
            input_size=str(item.get("input_size", "")),
            source_revision=str(item.get("source_revision", "")),
            last_modified=str(item.get("last_modified", "")),
            thumbnail_url=str(item.get("thumbnail_url", "")),
        ))

    return ModelCatalog(source=source, models=models)


def dashboard_totals(catalog: ModelCatalog) -> Dict[str, int]:
    active = [model for model in catalog.models if model.status == "active"]
    totals = {
        "total": len(active),
        "detectors": sum(model.task == "detector" for model in active),
        "classifiers": sum(model.task == "classifier" for model in active),
        "segmenters": sum(model.task == "segmenter" for model in active),
        "encoders": sum(model.task == "encoder" for model in active),
        "cascades": sum(model.task == "cascade" for model in active),
    }
    if catalog.source.id == "sparrow":
        totals["ready"] = sum(model.formats == ["onnx"] and not model.flavor for model in active)
    else:
        totals["ready"] = sum(model.catalog_ready for model in active)
    return totals