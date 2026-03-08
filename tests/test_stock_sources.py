import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PROJECT_ROOT / "skills" / "slidemax_workflow"
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from slidemax.stock_sources import (
    PROVIDER_REGISTRY,
    build_record,
    list_providers,
    load_manifest,
    manifest_path,
    stock_dir,
    upsert_record,
)


class StockSourcesTestCase(unittest.TestCase):
    def test_provider_registry_contains_expected_entries(self):
        providers = {provider.name for provider in list_providers()}
        self.assertEqual(providers, {"pexels", "pixabay", "unsplash"})
        self.assertEqual(PROVIDER_REGISTRY["unsplash"].license_url, "https://unsplash.com/license")
        self.assertEqual(PROVIDER_REGISTRY["pexels"].license_url, "https://www.pexels.com/license/")
        self.assertEqual(
            PROVIDER_REGISTRY["pixabay"].license_url,
            "https://pixabay.com/service/license-summary/",
        )

    def test_build_record_copies_external_file_and_sets_defaults(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "demo_project"
            project_dir.mkdir()
            source_file = root / "photo.jpg"
            source_file.write_bytes(b"fake-image-bytes")

            record = build_record(
                project_dir=project_dir,
                provider_name="unsplash",
                source_url="https://unsplash.com/photos/abc123",
                local_file=source_file,
                filename="cover_bg.jpg",
                keywords="hero, office",
            )

            copied_path = project_dir / record.local_path
            self.assertTrue(copied_path.exists())
            self.assertEqual(record.filename, "cover_bg.jpg")
            self.assertEqual(record.source_provider, "unsplash")
            self.assertEqual(record.license_url, "https://unsplash.com/license")
            self.assertTrue(record.commercial_use_allowed)
            self.assertFalse(record.attribution_required)
            self.assertEqual(record.keywords, ["hero", "office"])

    def test_upsert_record_updates_existing_manifest_entry(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project_dir = root / "demo_project"
            stock_dir = project_dir / "images" / "stock"
            stock_dir.mkdir(parents=True)
            image_path = stock_dir / "cover_bg.jpg"
            image_path.write_bytes(b"a")

            first = build_record(
                project_dir=project_dir,
                provider_name="pexels",
                source_url="https://www.pexels.com/photo/1/",
                local_path=image_path.relative_to(project_dir),
                notes="first",
            )
            upsert_record(project_dir, first)

            second = build_record(
                project_dir=project_dir,
                provider_name="pexels",
                source_url="https://www.pexels.com/photo/1/",
                local_path=image_path.relative_to(project_dir),
                notes="updated",
            )
            manifest_file = upsert_record(project_dir, second)

            data = json.loads(manifest_file.read_text(encoding="utf-8"))
            self.assertEqual(len(data["images"]), 1)
            self.assertEqual(data["images"][0]["notes"], "updated")

    def test_stock_dir_can_be_overridden_by_env(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp) / "demo_project"
            project_dir.mkdir()
            original = os.environ.get("SLIDEMAX_STOCK_ROOT_DIR")
            os.environ["SLIDEMAX_STOCK_ROOT_DIR"] = "custom_stock"
            try:
                self.assertEqual(stock_dir(project_dir), project_dir / "custom_stock")
            finally:
                if original is None:
                    os.environ.pop("SLIDEMAX_STOCK_ROOT_DIR", None)
                else:
                    os.environ["SLIDEMAX_STOCK_ROOT_DIR"] = original

    def test_load_manifest_returns_default_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            project_dir = Path(tmp) / "demo_project"
            project_dir.mkdir()
            data = load_manifest(project_dir)
            self.assertEqual(data["version"], 1)
            self.assertEqual(data["images"], [])
            self.assertEqual(manifest_path(project_dir).name, "manifest.json")


if __name__ == "__main__":
    unittest.main()
