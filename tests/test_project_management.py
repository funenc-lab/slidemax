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
SKILL_ROOT = PROJECT_ROOT / "skills" / "ppt_master_workflow"
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from pptmaster.project_management import build_parser, build_preflight_checks, run_cli


class ProjectManagementTestCase(unittest.TestCase):
    def test_build_parser_accepts_doctor_command(self):
        parser = build_parser()

        args = parser.parse_args(["doctor"])

        self.assertEqual(args.command, "doctor")
        self.assertIsNone(args.project_path)

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
            "pptmaster.project_management.provider_sdk_dependency_status",
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
                "pptmaster.project_management.run_preflight_smoke_test",
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


if __name__ == "__main__":
    unittest.main()
