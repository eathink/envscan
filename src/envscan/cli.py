"""命令行入口。"""

from __future__ import annotations

import argparse
import sys

from . import __version__
from .report import RENDERERS
from .scanner import ScanError, scan


def _positive_int(raw: str) -> int:
    try:
        value = int(raw)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("必须是整数") from exc
    if value <= 0:
        raise argparse.ArgumentTypeError("必须是正整数")
    return value


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envscan",
        description="扫描工作区中的 .env 与疑似密钥，标出是否已被 git 跟踪。",
    )
    parser.add_argument("path", nargs="?", default=".", help="扫描目录（默认当前目录）")
    parser.add_argument(
        "--max-size",
        type=_positive_int,
        default=1024 * 1024,
        metavar="BYTES",
        help="单个文件的最大扫描字节数（默认 1 MiB）",
    )
    parser.add_argument(
        "-f", "--format", choices=sorted(RENDERERS), default="text", help="输出格式"
    )
    parser.add_argument("--exit-zero", action="store_true", help="有发现也返回 0")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        result = scan(args.path, args.max_size)
    except ScanError as exc:
        print(f"envscan: {exc}", file=sys.stderr)
        return 2

    print(RENDERERS[args.format](result))

    if result.findings and not args.exit_zero:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
