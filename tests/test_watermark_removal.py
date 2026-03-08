import argparse
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PROJECT_ROOT / "skills" / "ppt_master_workflow"
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from pptmaster.watermark_removal import (
    DEFAULT_OUTPUT_SUFFIX,
    GeminiWatermarkRemover,
    execute_parsed_command,
)


class _FakeParser:
    def __init__(self) -> None:
        self.help_called = False

    def print_help(self) -> None:
        self.help_called = True


class _FakeRemover:
    def __init__(self, output_path: Path) -> None:
        self.output_path = output_path
        self.calls = []

    def process_image(self, input_path: Path, output_path: Optional[Path] = None, *, verbose: bool = True) -> Path:
        self.calls.append((input_path, output_path, verbose))
        return self.output_path


class WatermarkRemovalTestCase(unittest.TestCase):
    def test_build_output_path_appends_default_suffix(self):
        path = GeminiWatermarkRemover.build_output_path(Path("image.png"))

        self.assertEqual(path.name, f"image{DEFAULT_OUTPUT_SUFFIX}.png")

    def test_execute_parsed_command_reports_missing_input(self):
        outputs = []
        args = argparse.Namespace(input=Path("missing.png"), output=None, quiet=False)

        exit_code = execute_parsed_command(args, output_fn=outputs.append)

        self.assertEqual(exit_code, 1)
        self.assertEqual(outputs, ["[ERROR] File does not exist: missing.png"])

    def test_execute_parsed_command_processes_image_and_prints_summary(self):
        outputs = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "input.png"
            input_path.write_bytes(b"fake")
            output_path = root / "clean.png"
            remover = _FakeRemover(output_path)
            args = argparse.Namespace(input=input_path, output=None, quiet=False)

            exit_code = execute_parsed_command(
                args,
                output_fn=outputs.append,
                remover_factory=lambda: remover,
            )

        self.assertEqual(exit_code, 0)
        self.assertEqual(remover.calls, [(input_path, None, True)])
        self.assertIn("PPT Master - Gemini watermark remover", outputs[0])
        self.assertEqual(outputs[-1], f"[DONE] Saved: {output_path}")

    def test_execute_parsed_command_returns_error_when_processing_fails(self):
        outputs = []
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            input_path = root / "input.png"
            input_path.write_bytes(b"fake")
            args = argparse.Namespace(input=input_path, output=None, quiet=True)

            def failing_factory():
                class _FailingRemover:
                    def process_image(self, input_path: Path, output_path: Optional[Path] = None, *, verbose: bool = True) -> Path:
                        raise RuntimeError("boom")

                return _FailingRemover()

            exit_code = execute_parsed_command(
                args,
                output_fn=outputs.append,
                remover_factory=failing_factory,
            )

        self.assertEqual(exit_code, 1)
        self.assertEqual(outputs, ["[ERROR] Watermark removal failed: boom"])


if __name__ == "__main__":
    unittest.main()
