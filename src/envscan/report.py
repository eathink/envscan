"""渲染扫描结果。"""

from __future__ import annotations

import json

from .patterns import HIGH, KIND_LABELS
from .scanner import ScanResult

_SEVERITY_LABEL = {HIGH: "高", "medium": "中"}


def _location(finding) -> str:
    if finding.line:
        return f"{finding.path}:{finding.line}"
    return finding.path


def render_text(result: ScanResult) -> str:
    if not result.findings:
        return f"扫描 {result.root}：{result.files_scanned} 个文件，未发现疑似密钥。"

    lines = [
        f"扫描 {result.root}：{result.files_scanned} 个文件，{len(result.findings)} 处发现",
        "",
    ]
    for finding in result.findings:
        severity = _SEVERITY_LABEL[finding.severity]
        kind = KIND_LABELS[finding.kind]
        tracked = "  （已提交）" if finding.tracked else ""
        lines.append(f"[{severity}] {_location(finding)}  {kind}{tracked}")
        if finding.preview:
            lines.append(f"     {finding.preview}")
    return "\n".join(lines)


def render_markdown(result: ScanResult) -> str:
    if not result.findings:
        return (
            f"扫描 `{result.root}`：{result.files_scanned} 个文件，未发现疑似密钥。"
        )

    lines = [
        f"扫描 `{result.root}`：{result.files_scanned} 个文件，{len(result.findings)} 处发现",
        "",
        "| 级别 | 位置 | 类型 | 已提交 |",
        "| --- | --- | --- | --- |",
    ]
    for finding in result.findings:
        severity = _SEVERITY_LABEL[finding.severity]
        kind = KIND_LABELS[finding.kind]
        location = _location(finding).replace("|", "\\|")
        lines.append(
            f"| {severity} | `{location}` | {kind} | {'是' if finding.tracked else '否'} |"
        )
    return "\n".join(lines)


def render_json(result: ScanResult) -> str:
    payload = {
        "root": result.root,
        "files_scanned": result.files_scanned,
        "totals": {
            "findings": len(result.findings),
            "high": result.high_count,
            "medium": len(result.findings) - result.high_count,
        },
        "findings": [
            {
                "path": finding.path,
                "line": finding.line,
                "kind": finding.kind,
                "severity": finding.severity,
                "tracked": finding.tracked,
            }
            for finding in result.findings
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


RENDERERS = {
    "text": render_text,
    "markdown": render_markdown,
    "json": render_json,
}
