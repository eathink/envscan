"""遍历目录并扫描文件。"""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

from .patterns import GENERIC, HIGH, MEDIUM, PATTERNS, looks_like_placeholder

SKIP_DIRS = frozenset(
    {
        ".git",
        "node_modules",
        ".venv",
        "venv",
        "__pycache__",
        "dist",
        "build",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
    }
)
_EXAMPLE_NAMES = frozenset({".env.example", ".env.sample", ".env.template"})


class ScanError(ValueError):
    """扫描路径或 git 调用出现问题。"""


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    kind: str
    severity: str
    tracked: bool
    preview: str


@dataclass(frozen=True)
class ScanResult:
    root: str
    files_scanned: int
    findings: list[Finding]

    @property
    def high_count(self) -> int:
        return sum(1 for finding in self.findings if finding.severity == HIGH)


def is_env_file(path: Path) -> bool:
    name = path.name
    if name in _EXAMPLE_NAMES:
        return False
    return name == ".env" or name.startswith(".env.")


def _mask(value: str) -> str:
    return f"<redacted:{len(value)}c>"


def _git(path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(path), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def _tracked_info(root: Path) -> tuple[Path | None, set[str]]:
    top = _git(root, "rev-parse", "--show-toplevel")
    if top.returncode != 0:
        return None, set()

    top_path = Path(top.stdout.strip())
    listing = _git(top_path, "ls-files", "-z")
    if listing.returncode != 0:
        return top_path, set()
    return top_path, {item for item in listing.stdout.split("\0") if item}


def _is_tracked(path: Path, info: tuple[Path | None, set[str]]) -> bool:
    top, tracked = info
    if top is None:
        return False
    try:
        relative = path.resolve().relative_to(top).as_posix()
    except ValueError:
        return False
    return relative in tracked


def _iter_files(root: Path):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(name for name in dirnames if name not in SKIP_DIRS)
        for name in sorted(filenames):
            path = Path(dirpath) / name
            if path.is_symlink():
                continue
            yield path


def scan_file(
    path: Path, relative: str, tracked: bool, max_size: int
) -> list[Finding]:
    try:
        data = path.read_bytes()
    except OSError:
        return []
    if len(data) > max_size or b"\x00" in data[:8192]:
        return []

    findings: list[Finding] = []
    if is_env_file(path):
        severity = HIGH if tracked else MEDIUM
        findings.append(Finding(relative, 0, "env_file", severity, tracked, ""))

    text = data.decode("utf-8", errors="ignore")
    for lineno, line in enumerate(text.splitlines(), 1):
        specific = False
        for kind, severity, pattern in PATTERNS:
            match = pattern.search(line)
            if match:
                specific = True
                findings.append(
                    Finding(relative, lineno, kind, severity, tracked, _mask(match.group(0)))
                )
        if specific:
            continue
        match = GENERIC.search(line)
        if match and not looks_like_placeholder(match.group(1)):
            findings.append(
                Finding(
                    relative,
                    lineno,
                    "generic_secret",
                    MEDIUM,
                    tracked,
                    _mask(match.group(1)),
                )
            )

    return findings


def scan(root: str | Path, max_size: int = 1024 * 1024) -> ScanResult:
    path = Path(root).expanduser().resolve()
    if not path.exists():
        raise ScanError(f"路径不存在：{root}")
    if not path.is_dir():
        raise ScanError(f"不是目录：{root}")

    tracked_info = _tracked_info(path)
    files_scanned = 0
    findings: list[Finding] = []

    for file_path in _iter_files(path):
        files_scanned += 1
        relative = file_path.relative_to(path).as_posix()
        findings.extend(
            scan_file(
                file_path,
                relative,
                _is_tracked(file_path, tracked_info),
                max_size,
            )
        )

    findings.sort(
        key=lambda item: (
            0 if item.severity == HIGH else 1,
            item.path,
            item.line,
        )
    )
    return ScanResult(str(path), files_scanned, findings)
