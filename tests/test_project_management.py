import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PROJECT_ROOT / "skills" / "slidemax_workflow"
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from slidemax.project_management import build_parser, build_preflight_checks, run_cli


class ProjectManagementTestCase(unittest.TestCase):
    def _create_delivery_ready_project(self, root: Path) -> Path:
        project = root / "demo_ppt169_20260308"
        (project / "svg_output").mkdir(parents=True)
        (project / "svg_final").mkdir()
        (project / "images").mkdir()
        (project / "templates").mkdir()
        (project / "notes").mkdir()
        (project / "README.md").write_text("# demo\n", encoding="utf-8")
        (project / "design_specification.md").write_text("# spec\n", encoding="utf-8")
        (project / "svg_output" / "01_封面.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720"></svg>',
            encoding="utf-8",
        )
        (project / "svg_final" / "01_封面.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720"></svg>',
            encoding="utf-8",
        )
        (project / "notes" / "01_封面.md").write_text("hello\n", encoding="utf-8")
        (project / "demo_ppt169_20260308.pptx").write_bytes(b"pptx")
        return project

    def test_build_parser_accepts_doctor_command(self):
        parser = build_parser()

        args = parser.parse_args(["doctor"])

        self.assertEqual(args.command, "doctor")
        self.assertIsNone(args.project_path)

    def test_build_parser_accepts_audit_command(self):
        parser = build_parser()

        args = parser.parse_args(["audit", "demo_project"])

        self.assertEqual(args.command, "audit")
        self.assertEqual(args.project_path, "demo_project")

    def test_build_parser_accepts_doctor_smoke_test_arguments(self):
        parser = build_parser()

        args = parser.parse_args(
            [
                "doctor",
                "demo_project",
                "--provider",
                "doubao",
                "--model",
                "doubao-seedream-5",
                "--smoke-test",
                "--smoke-output",
                "tmp/smoke",
            ]
        )

        self.assertTrue(args.smoke_test)
        self.assertEqual(args.smoke_output, "tmp/smoke")

    def test_build_parser_accepts_doctor_json_output_argument(self):
        parser = build_parser()

        args = parser.parse_args(
            [
                "doctor",
                "demo_project",
                "--json-output",
                "tmp/preflight.json",
            ]
        )

        self.assertEqual(args.json_output, "tmp/preflight.json")

    def test_build_preflight_checks_normalizes_doubao_alias(self):
        with mock.patch.dict(
            os.environ,
            {
                "DOUBAO_API_KEY": "secret",
                "DOUBAO_BASE_URL": "https://doubao.example/api/v3",
            },
            clear=False,
        ):
            checks = build_preflight_checks(provider="doubao", model="doubao-seedream-5")

        provider_checks = [check for check in checks if check.name == "image_provider"]
        self.assertEqual(len(provider_checks), 1)
        self.assertEqual(provider_checks[0].status, "ok")
        self.assertIn("doubao-seedream-5-0-260128", provider_checks[0].message)

    def test_build_preflight_checks_includes_provider_sdk_check(self):
        with mock.patch(
            "slidemax.project_management.provider_sdk_dependency_status",
            return_value=(False, "Provider SDK is missing for doubao"),
        ), mock.patch.dict(
            os.environ,
            {
                "DOUBAO_API_KEY": "secret",
                "DOUBAO_BASE_URL": "https://ark.example/api/v3",
            },
            clear=False,
        ):
            checks = build_preflight_checks(provider="doubao")

        sdk_checks = [check for check in checks if check.name == "image_provider_sdk"]
        self.assertEqual(len(sdk_checks), 1)
        self.assertEqual(sdk_checks[0].status, "error")
        self.assertIn("Provider SDK is missing", sdk_checks[0].message)

    def test_run_cli_doctor_warns_when_total_notes_not_split(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo_ppt169_20260308"
            (project / "svg_output").mkdir(parents=True)
            (project / "svg_final").mkdir()
            (project / "images").mkdir()
            (project / "templates").mkdir()
            (project / "notes").mkdir()
            (project / "README.md").write_text("# demo\n", encoding="utf-8")
            (project / "设计规范与内容大纲.md").write_text("# spec\n", encoding="utf-8")
            (project / "svg_output" / "01_封面.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720"></svg>',
                encoding="utf-8",
            )
            (project / "notes" / "total.md").write_text("## 01 封面\nhello\n", encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = run_cli(["doctor", str(project)])

        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        self.assertIn("notes_status", output)
        self.assertIn("warning", output.lower())

    def test_run_cli_doctor_can_run_smoke_test(self):
        with tempfile.TemporaryDirectory() as tmp:
            stdout = io.StringIO()
            with mock.patch(
                "slidemax.project_management.run_preflight_smoke_test",
                return_value=Path(tmp) / "smoke_test.png",
            ) as smoke_test_mock:
                with mock.patch.dict(
                    os.environ,
                    {
                        "DOUBAO_API_KEY": "secret",
                        "DOUBAO_BASE_URL": "https://doubao.example/api/v3",
                    },
                    clear=False,
                ):
                    with redirect_stdout(stdout):
                        exit_code = run_cli(
                            [
                                "doctor",
                                "--provider",
                                "doubao",
                                "--model",
                                "doubao-seedream-5",
                                "--smoke-test",
                                "--smoke-output",
                                tmp,
                            ]
                        )

        self.assertEqual(exit_code, 0)
        smoke_test_mock.assert_called_once()
        self.assertIn("smoke_test", stdout.getvalue())

    def test_run_cli_doctor_writes_json_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo_ppt169_20260308"
            report_path = Path(tmp) / "preflight.json"
            (project / "svg_output").mkdir(parents=True)
            (project / "svg_final").mkdir()
            (project / "images").mkdir()
            (project / "templates").mkdir()
            (project / "notes").mkdir()
            (project / "README.md").write_text("# demo\n", encoding="utf-8")
            (project / "设计规范与内容大纲.md").write_text("# spec\n", encoding="utf-8")
            (project / "svg_output" / "01_封面.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720"></svg>',
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = run_cli(["doctor", str(project), "--json-output", str(report_path)])

            payload = json.loads(report_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["project_path"], str(project))
        self.assertTrue(any(check["name"] == "project_structure" for check in payload["checks"]))

    def test_run_cli_init_creates_project_state_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = run_cli(
                    [
                        "init",
                        "demo",
                        "--format",
                        "ppt169",
                        "--dir",
                        tmp,
                    ]
                )

            project_dirs = list(Path(tmp).glob("demo_ppt169_*"))
            self.assertEqual(exit_code, 0)
            self.assertEqual(len(project_dirs), 1)
            state_path = project_dirs[0] / "project_state.json"
            self.assertTrue(state_path.exists())
            payload = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["current_stage"], "project_initialized")
        self.assertEqual(payload["last_command"]["name"], "project_manager init")

    def test_run_cli_audit_reports_current_stage_and_updates_state_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo_ppt169_20260308"
            (project / "svg_output").mkdir(parents=True)
            (project / "svg_final").mkdir()
            (project / "images").mkdir()
            (project / "templates").mkdir()
            (project / "notes").mkdir()
            (project / "README.md").write_text("# demo\n", encoding="utf-8")
            (project / "design_specification.md").write_text("# spec\n", encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = run_cli(["audit", str(project)])

            payload = json.loads((project / "project_state.json").read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertIn("Current stage: strategy_ready", stdout.getvalue())
        self.assertEqual(payload["current_stage"], "strategy_ready")
        self.assertEqual(payload["last_command"]["name"], "project_manager audit")

    def test_run_cli_audit_fails_when_export_exists_without_finalized_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo_ppt169_20260308"
            (project / "svg_output").mkdir(parents=True)
            (project / "svg_final").mkdir()
            (project / "images").mkdir()
            (project / "templates").mkdir()
            (project / "notes").mkdir()
            (project / "README.md").write_text("# demo\n", encoding="utf-8")
            (project / "design_specification.md").write_text("# spec\n", encoding="utf-8")
            (project / "svg_output" / "01_封面.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 720"></svg>',
                encoding="utf-8",
            )
            (project / "notes" / "total.md").write_text("## 01 封面\nhello\n", encoding="utf-8")
            (project / "demo_ppt169_20260308.pptx").write_bytes(b"pptx")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = run_cli(["audit", str(project)])

        self.assertEqual(exit_code, 1)
        self.assertIn("Blocking issues", stdout.getvalue())
        self.assertIn("exported", stdout.getvalue())

    def test_run_cli_doctor_treats_optional_templates_and_notes_as_not_applicable_before_slides_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo_ppt169_20260308"
            (project / "svg_output").mkdir(parents=True)
            (project / "svg_final").mkdir()
            (project / "images").mkdir()
            (project / "templates").mkdir()
            (project / "notes").mkdir()
            (project / "README.md").write_text("# demo\n", encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = run_cli(["doctor", str(project)])

        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        self.assertIn("project_structure: ok", output)
        self.assertIn("template_svg_quality: ok", output)
        self.assertIn("notes_status: ok", output)

    def test_run_cli_validate_fails_when_finalized_svg_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._create_delivery_ready_project(Path(tmp))
            (project / "svg_final" / "01_封面.svg").unlink()

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = run_cli(["validate", str(project)])

        self.assertEqual(exit_code, 1)
        self.assertIn("svg_final", stdout.getvalue())

    def test_run_cli_validate_fails_when_exported_pptx_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._create_delivery_ready_project(Path(tmp))
            (project / "demo_ppt169_20260308.pptx").unlink()

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = run_cli(["validate", str(project)])

        self.assertEqual(exit_code, 1)
        self.assertIn(".pptx", stdout.getvalue())

    def test_run_cli_validate_fails_when_no_svg_slides_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "demo_ppt169_20260308"
            (project / "svg_output").mkdir(parents=True)
            (project / "svg_final").mkdir()
            (project / "images").mkdir()
            (project / "templates").mkdir()
            (project / "notes").mkdir()
            (project / "README.md").write_text("# demo\n", encoding="utf-8")
            (project / "design_specification.md").write_text("# spec\n", encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = run_cli(["validate", str(project)])

        self.assertEqual(exit_code, 1)
        self.assertIn("No SVG slides", stdout.getvalue())

    def test_run_cli_validate_fails_when_only_total_notes_exist(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._create_delivery_ready_project(Path(tmp))
            (project / "notes" / "01_封面.md").unlink()
            (project / "notes" / "total.md").write_text("## 01 封面\nhello\n", encoding="utf-8")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = run_cli(["validate", str(project)])

        self.assertEqual(exit_code, 1)
        self.assertIn("total_md_split", stdout.getvalue())

    def test_run_cli_validate_fails_when_finalized_svg_viewbox_is_invalid(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._create_delivery_ready_project(Path(tmp))
            (project / "svg_final" / "01_封面.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"></svg>',
                encoding="utf-8",
            )

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = run_cli(["validate", str(project)])

        self.assertEqual(exit_code, 1)
        self.assertIn("viewBox", stdout.getvalue())

    def test_run_cli_validate_updates_project_state_on_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._create_delivery_ready_project(Path(tmp))

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = run_cli(["validate", str(project)])

            payload = json.loads((project / "project_state.json").read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(payload["current_stage"], "validated")
        self.assertEqual(payload["last_command"]["name"], "project_manager validate")
        self.assertEqual(payload["last_validation"]["status"], "passed")

    def test_run_cli_validate_fails_when_slide_notes_are_incomplete(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self._create_delivery_ready_project(Path(tmp))
            (project / "notes" / "01_封面.md").unlink()

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = run_cli(["validate", str(project)])

        self.assertEqual(exit_code, 1)
        self.assertIn("notes", stdout.getvalue().lower())


if __name__ == "__main__":
    unittest.main()
