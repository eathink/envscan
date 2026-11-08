"""密钥特征、风险级别与占位符判断。"""

from __future__ import annotations

import re

HIGH = "high"
MEDIUM = "medium"

KIND_LABELS = {
    "aws_access_key": "AWS Access Key",
    "github_token": "GitHub Token",
    "github_pat": "GitHub Fine-grained PAT",
    "openai_key": "OpenAI Key",
    "google_api_key": "Google API Key",
    "slack_token": "Slack Token",
    "private_key": "PEM 私钥",
    "jwt": "JWT",
    "generic_secret": "疑似密钥赋值",
    "env_file": "环境变量文件",
}

PATTERNS: tuple[tuple[str, str, re.Pattern[str]], ...] = (
    ("aws_access_key", HIGH, re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    (
        "github_token",
        HIGH,
        re.compile(r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}\b"),
    ),
    ("github_pat", HIGH, re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("openai_key", HIGH, re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")),
    ("google_api_key", HIGH, re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("slack_token", HIGH, re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    (
        "private_key",
        HIGH,
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
    (
        "jwt",
        HIGH,
        re.compile(
            r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b"
        ),
    ),
)

GENERIC = re.compile(
    r"(?i)(?:api[_-]?key|secret|token|password|passwd|access[_-]?key)"
    r"\s*[:=]\s*[\"']?([A-Za-z0-9_\-]{16,})"
)

_PLACEHOLDER_MARKERS = (
    "example",
    "your_",
    "your-",
    "changeme",
    "change-me",
    "placeholder",
    "dummy",
    "sample",
    "xxxx",
    "<",
)


def looks_like_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in _PLACEHOLDER_MARKERS)
