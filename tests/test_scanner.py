import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from envscan.scanner import scan


class ScanTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.root = Path(self._tmp.name)

    def test_env_file_is_flagged(self):
        (self.root / ".env.production").write_text("A=1\n", encoding="utf-8")

        result = scan(self.root)

        self.assertEqual(len(result.findings), 1)
        finding = result.findings[0]
        self.assertEqual(finding.kind, "env_file")
        self.assertEqual(finding.severity, "medium")
        self.assertFalse(finding.tracked)

    def test_env_example_is_ignored(self):
        (self.root / ".env.example").write_text("A=your_value\n", encoding="utf-8")

        self.assertEqual(scan(self.root).findings, [])

    def test_known_token_is_high_severity(self):
        (self.root / "config.txt").write_text(
            "aws = AKIA" + "A" * 16 + "\n", encoding="utf-8"
        )

        result = scan(self.root)

        self.assertEqual(len(result.findings), 1)
        self.assertEqual(result.findings[0].kind, "aws_access_key")
        self.assertEqual(result.findings[0].severity, "high")
        self.assertIn("<redacted:", result.findings[0].preview)

    def test_generic_assignment_is_medium(self):
        (self.root / "settings.py").write_text(
            'API_KEY = "abcdefghijklmnop1234"\n', encoding="utf-8"
        )

        result = scan(self.root)

        self.assertEqual(len(result.findings), 1)
        self.assertEqual(result.findings[0].kind, "generic_secret")
        self.assertEqual(result.findings[0].severity, "medium")

    def test_placeholder_is_not_flagged(self):
        (self.root / "settings.py").write_text(
            'API_KEY = "your_key_here_123456"\n', encoding="utf-8"
        )

        self.assertEqual(scan(self.root).findings, [])

    def test_binary_file_is_skipped(self):
        (self.root / "blob.bin").write_bytes(
            b"\x00\x01" + b"AKIA" + b"A" * 16
        )

        self.assertEqual(scan(self.root).findings, [])

    def test_skip_directories(self):
        skipped = self.root / "node_modules" / "pkg"
        skipped.mkdir(parents=True)
        (skipped / "config.js").write_text(
            "token = 'abcdefghijklmnop1234'\n", encoding="utf-8"
        )

        result = scan(self.root)

        self.assertEqual(result.files_scanned, 0)
        self.assertEqual(result.findings, [])

    def test_max_size_is_respected(self):
        (self.root / "big.txt").write_text(
            "AKIA" + "A" * 16 + "\n", encoding="utf-8"
        )

        self.assertEqual(scan(self.root, max_size=5).findings, [])

    def test_symlink_is_skipped(self):
        target = self.root / "target.txt"
        target.write_text("AKIA" + "A" * 16 + "\n", encoding="utf-8")
        link = self.root / "link.txt"
        os.symlink(target, link)

        result = scan(self.root)

        self.assertEqual([finding.path for finding in result.findings], ["target.txt"])

    def test_tracked_env_file_is_high_severity(self):
        subprocess.run(["git", "init", "-q", "-b", "main", str(self.root)], check=True)
        subprocess.run(
            ["git", "-C", str(self.root), "config", "user.email", "t@example.com"],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(self.root), "config", "user.name", "Test"],
            check=True,
        )
        (self.root / ".env").write_text("A=1\n", encoding="utf-8")
        subprocess.run(
            ["git", "-C", str(self.root), "add", "-f", ".env"], check=True
        )
        subprocess.run(
            ["git", "-C", str(self.root), "commit", "-q", "-m", "init"], check=True
        )

        result = scan(self.root)

        finding = next(item for item in result.findings if item.kind == "env_file")
        self.assertTrue(finding.tracked)
        self.assertEqual(finding.severity, "high")


if __name__ == "__main__":
    unittest.main()
