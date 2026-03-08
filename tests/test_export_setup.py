import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PROJECT_ROOT / "skills" / "slidemax_workflow"
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from slidemax.export_setup import build_parser, build_install_command, run_cli


class ExportSetupTestCase(unittest.TestCase):
    def test_build_install_command_prefers_cairosvg_renderer(self):
        command = build_install_command(renderer="cairosvg")

        self.assertEqual(command[:4], [sys.executable, "-m", "pip", "install"])
        self.assertIn("python-pptx", command)
        self.assertIn("cairosvg", command)
        self.assertNotIn("svglib", command)

    def test_build_parser_accepts_dry_run(self):
        parser = build_parser()

        args = parser.parse_args(["--dry-run", "--renderer", "svglib"])

        self.assertTrue(args.dry_run)
        self.assertEqual(args.renderer, "svglib")

    def test_run_cli_dry_run_prints_command(self):
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            exit_code = run_cli(["--dry-run", "--renderer", "svglib"])

        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        self.assertIn("python-pptx", output)
        self.assertIn("svglib", output)

    def test_run_cli_executes_pip_install(self):
        with mock.patch("slidemax.export_setup.subprocess.run") as run_mock:
            run_mock.return_value = mock.Mock(returncode=0)
            exit_code = run_cli(["--renderer", "none"])

        self.assertEqual(exit_code, 0)
        run_mock.assert_called_once()


if __name__ == "__main__":
    unittest.main()
