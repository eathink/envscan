import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from envscan.cli import main


class CliTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_clean_directory_returns_zero(self):
        (self.root / "hello.txt").write_text("hello\n", encoding="utf-8")

        code, out, _ = self.run_cli(str(self.root))

        self.assertEqual(code, 0)
        self.assertIn("未发现", out)

    def test_findings_return_one(self):
        (self.root / ".env").write_text("A=1\n", encoding="utf-8")

        code, out, _ = self.run_cli(str(self.root))

        self.assertEqual(code, 1)
        self.assertIn("环境变量文件", out)

    def test_exit_zero_flag(self):
        (self.root / ".env").write_text("A=1\n", encoding="utf-8")

        code, _, _ = self.run_cli(str(self.root), "--exit-zero")

        self.assertEqual(code, 0)

    def test_json_output(self):
        (self.root / ".env").write_text("A=1\n", encoding="utf-8")

        code, out, _ = self.run_cli(str(self.root), "--format", "json")

        payload = json.loads(out)
        self.assertEqual(code, 1)
        self.assertEqual(payload["totals"]["findings"], 1)
        self.assertEqual(payload["findings"][0]["kind"], "env_file")

    def test_missing_path_returns_two(self):
        code, _, err = self.run_cli(str(self.root / "missing"))

        self.assertEqual(code, 2)
        self.assertIn("envscan:", err)


if __name__ == "__main__":
    unittest.main()
