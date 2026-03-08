import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = PROJECT_ROOT / "skills" / "slidemax_workflow"
if str(SKILL_ROOT) not in sys.path:
    sys.path.insert(0, str(SKILL_ROOT))

from slidemax.command_bridge import run_entrypoint


class CommandBridgeTestCase(unittest.TestCase):
    def test_run_entrypoint_raises_system_exit_for_return_code(self):
        with self.assertRaises(SystemExit) as context:
            run_entrypoint(lambda: 7)

        self.assertEqual(context.exception.code, 7)

    def test_run_entrypoint_preserves_existing_system_exit(self):
        def raise_exit():
            raise SystemExit(3)

        with self.assertRaises(SystemExit) as context:
            run_entrypoint(raise_exit)

        self.assertEqual(context.exception.code, 3)

    def test_run_entrypoint_catches_exception_when_enabled(self):
        messages = []

        def raise_error():
            raise ValueError("boom")

        with self.assertRaises(SystemExit) as context:
            run_entrypoint(raise_error, catch_exceptions=True, error_output=messages.append)

        self.assertEqual(context.exception.code, 1)
        self.assertEqual(messages, ["Error: boom"])


if __name__ == "__main__":
    unittest.main()
