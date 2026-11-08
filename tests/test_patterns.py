import unittest

from envscan.patterns import GENERIC, PATTERNS, looks_like_placeholder


class PatternTests(unittest.TestCase):
    def test_known_token_formats(self):
        samples = {
            "aws_access_key": "AKIA" + "A" * 16,
            "github_token": "ghp_" + "a" * 36,
            "github_pat": "github_pat_" + "a" * 30,
            "openai_key": "sk-" + "a" * 32,
            "google_api_key": "AIza" + "a" * 35,
            "slack_token": "xoxb-1234567890-abcdef",
            "private_key": "-----BEGIN RSA PRIVATE KEY-----",
            "jwt": "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature123",
        }
        patterns = {kind: pattern for kind, _, pattern in PATTERNS}
        for kind, sample in samples.items():
            with self.subTest(kind=kind):
                self.assertIsNotNone(patterns[kind].search(sample))

    def test_generic_assignment(self):
        match = GENERIC.search('API_KEY = "abcdefghijklmnop1234"')

        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), "abcdefghijklmnop1234")

    def test_placeholder_detection(self):
        for value in ("your_key_here_123456", "example_token_123456", "changeme1234567890"):
            with self.subTest(value=value):
                self.assertTrue(looks_like_placeholder(value))

        self.assertFalse(looks_like_placeholder("abcdefghijklmnop1234"))


if __name__ == "__main__":
    unittest.main()
