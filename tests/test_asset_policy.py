import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PROJECT_ROOT / "skills" / "slidemax_workflow"
AUDIT_COMMAND = SKILL_ROOT / "commands" / "audit_image_asset.py"
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from slidemax.asset_policy import audit_image_asset, recommend_action
from slidemax.image_source_metadata import build_generated_image_metadata, build_stock_image_metadata, write_source_metadata
from slidemax.watermark_detection import detect_watermark_risk


class AssetPolicyTestCase(unittest.TestCase):
    def test_gemini_generated_asset_routes_to_regenerate(self):
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "cover.png"
            image_path.write_bytes(b"png")
            write_source_metadata(
                image_path,
                build_generated_image_metadata(
                    image_path,
                    provider="gemini",
                    model="gemini-3.1-flash-image-preview",
                    prompt="executive cover",
                ),
            )

            detection = detect_watermark_risk(image_path)
            decision = audit_image_asset(image_path)

            self.assertEqual(detection.status, "blocked")
            self.assertEqual(recommend_action(detection), "regenerate")
            self.assertEqual(decision.recommended_action, "regenerate")

    def test_complete_stock_metadata_routes_to_allow(self):
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "stock.jpg"
            image_path.write_bytes(b"jpg")
            write_source_metadata(
                image_path,
                build_stock_image_metadata(
                    image_path,
                    provider="unsplash",
                    asset_id="abc123",
                    origin_url="https://unsplash.com/photos/abc123",
                    license_name="Unsplash License",
                    license_url="https://unsplash.com/license",
                ),
            )

            decision = audit_image_asset(image_path)
            self.assertEqual(decision.watermark_status, "clean")
            self.assertEqual(decision.recommended_action, "allow")

    def test_audit_command_outputs_json_and_fail_on_suspicious(self):
        with tempfile.TemporaryDirectory() as tmp:
            image_path = Path(tmp) / "unknown.png"
            image_path.write_bytes(b"png")

            result = subprocess.run(
                [
                    sys.executable,
                    str(AUDIT_COMMAND),
                    str(image_path),
                    "--json",
                    "--fail-on",
                    "suspicious",
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 2)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["watermark_status"], "suspicious")
            self.assertEqual(payload["recommended_action"], "register")


if __name__ == "__main__":
    unittest.main()
