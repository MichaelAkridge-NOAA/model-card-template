import tempfile
import unittest
from pathlib import Path

from python.model_catalog import dashboard_totals, infer_commercial_use, load_catalog, normalize_task
from python.build_catalog import build_payload


class ModelCatalogTests(unittest.TestCase):
    def _load(self, text: str):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "catalog.toml"
            path.write_text(text, encoding="utf-8")
            return load_catalog(path)

    def test_normalizes_hugging_face_tasks(self):
        self.assertEqual(normalize_task("image-classification"), "classifier")
        self.assertEqual(normalize_task("object-detection"), "detector")
        self.assertEqual(normalize_task("image-segmentation"), "segmenter")

    def test_commercial_use_policy_is_conservative(self):
        self.assertEqual(infer_commercial_use("MIT")[0], "allowed")
        self.assertEqual(infer_commercial_use("CC-BY-NC-4.0")[0], "restricted")
        self.assertEqual(infer_commercial_use("Custom Research License")[0], "unknown")

    def test_nmfs_ready_total_requires_review_card_source_and_format(self):
        catalog = self._load('''
schema_version = "1.0"
[source]
id = "nmfs-osi"
name = "NMFS-OSI"
[[model]]
id = "NMFS-OSI/ready"
display_name = "Ready"
task = "object-detection"
format = "onnx"
reviewed = true
source_url = "https://example.test/ready"
card_url = "cards/ready.html"
[[model]]
id = "NMFS-OSI/review"
display_name = "Needs review"
task = "image-classification"
format = "pt"
source_url = "https://example.test/review"
card_url = "cards/review.html"
''')
        self.assertEqual(catalog.models[0].namespaced_id, "nmfs-osi:NMFS-OSI/ready")
        self.assertEqual(dashboard_totals(catalog), {
            "total": 2, "detectors": 1, "classifiers": 1, "segmenters": 0,
            "encoders": 0, "cascades": 0, "ready": 1,
        })

    def test_sparrow_ready_total_matches_default_onnx_rule(self):
        catalog = self._load('''
schema_version = "1.1"
[source]
id = "sparrow"
name = "SPARROW"
[[model]]
id = "default-onnx"
task = "detector"
format = "onnx"
commercial_use = true
[[model]]
id = "flavored-onnx"
task = "classifier"
format = "onnx"
flavor = "onnx-fp16"
commercial_use = false
[[model]]
id = "mobile"
task = "classifier"
format = "tflite"
''')
        self.assertEqual(catalog.models[0].commercial_use, "allowed")
        self.assertEqual(catalog.models[1].commercial_use, "restricted")
        self.assertTrue(catalog.models[0].to_dict()["default_onnx"])
        self.assertFalse(catalog.models[1].to_dict()["default_onnx"])
        self.assertEqual(dashboard_totals(catalog)["ready"], 1)

    def test_generated_payload_keeps_sources_separate(self):
        payload = build_payload()
        self.assertEqual(payload["default_source"], "nmfs-osi")
        self.assertEqual(len(payload["sources"]["nmfs-osi"]["models"]), 7)
        self.assertEqual(len(payload["sources"]["sparrow"]["models"]), 75)
        identifiers = {
            model["catalog_id"]
            for source in payload["sources"].values()
            for model in source["models"]
        }
        self.assertEqual(len(identifiers), 82)


if __name__ == "__main__":
    unittest.main()