# envscan

**扫描工作区中的 `.env` 与疑似密钥，标出是否已被 git 跟踪。**

提交前跑一遍，避免把环境配置或密钥带进仓库。纯标准库，离线，只读。

[![Python](https://img.shields.io/badge/python-3.10%2B-3776ab?logo=python&logoColor=white)](https://www.python.org/)
[![Zero deps](https://img.shields.io/badge/dependencies-0-brightgreen)](#设计取舍)
[![License](https://img.shields.io/badge/license-MIT-lightgrey)](LICENSE)
[![CI](https://github.com/eathink/envscan/actions/workflows/ci.yml/badge.svg)](https://github.com/eathink/envscan/actions/workflows/ci.yml)

## 为什么需要它

`.env` 被误提交、测试密钥写死在代码里、示例配置混进真实 token——这些问题的共同点是：**本地看没问题，推上去才出事**。

`envscan` 的定位是"提交前的最后一道本地检查"：

- 找出 `.env*` 文件（`.env.example` 等模板除外）
- 按已知格式识别常见密钥（AWS / GitHub / OpenAI / Google / Slack / PEM / JWT）
- 对 `API_KEY=`、`token:` 这类赋值做通用检测，过滤占位符
- 告诉你文件**是否已经被 git 跟踪**——已跟踪的风险高一级

它不是完整的安全扫描器：不扫 git 历史、不做熵检测、不替代 gitleaks / trufflehog。它要的是零依赖、秒级、随手可跑。

## 快速开始

```bash
pipx install git+https://github.com/eathink/envscan

# 扫描当前目录
envscan .

# 扫描当前目录；有发现时返回 1，可直接当提交前检查
envscan .
```

```console
$ envscan .
扫描 /home/me/project：2 个文件，3 处发现

[高] src/config.py:1  AWS Access Key
     <redacted:20c>
[中] .env.production  环境变量文件
[中] src/config.py:2  疑似密钥赋值
     <redacted:20c>
```

命中的值不会打印原文，只显示长度；这个工具是发现问题的，不是用来抄密钥的。

## 检测项

| 类型 | 级别 | 说明 |
| --- | --- | --- |
| AWS Access Key | 高 | `AKIA` / `ASIA` 开头 |
| GitHub Token | 高 | `ghp_` / `gho_` / `ghu_` / `ghs_` / `ghr_` |
| GitHub Fine-grained PAT | 高 | `github_pat_` |
| OpenAI Key | 高 | `sk-` 开头 |
| Google API Key | 高 | `AIza` 开头 |
| Slack Token | 高 | `xox[baprs]-` |
| PEM 私钥 | 高 | `-----BEGIN ... PRIVATE KEY-----` |
| JWT | 高 | 三段式 `eyJ...` |
| 疑似密钥赋值 | 中 | `api_key` / `secret` / `token` / `password` 后跟 16 位以上值；`your_`、`example`、`changeme` 等占位符不报 |
| 环境变量文件 | 中 / 高 | `.env`、`.env.*`；已被 git 跟踪时升为高 |

## 是否已提交

如果扫描目录位于 git 仓库内，`envscan` 会用 `git ls-files` 判断每个命中文件是否已被跟踪：

- 已跟踪的 `.env` → 高
- 未跟踪的 `.env` → 中
- 已跟踪的源码文件里发现密钥 → 仍然标"已提交"

> 注意：只检查工作区当前状态，不扫描 git 历史。曾经提交过、后来删掉的文件不在检测范围内。

## 用法

```bash
envscan [PATH] [--max-size BYTES] [--format text|markdown|json] [--exit-zero]
```

| 参数 | 说明 |
| --- | --- |
| `PATH` | 扫描目录，默认当前目录 |
| `--max-size BYTES` | 单文件最大扫描字节数，默认 1 MiB，超过跳过 |
| `-f, --format` | `text`（默认）、`markdown`、`json` |
| `--exit-zero` | 有发现也返回 0，只出报告 |
| `--version` | 版本号 |

### 退出码

| 码 | 含义 |
| --- | --- |
| 0 | 未发现，或使用了 `--exit-zero` |
| 1 | 有发现 |
| 2 | 路径不存在或不是目录 |

### 跳过规则

默认跳过 `.git`、`node_modules`、`.venv`、`venv`、`__pycache__`、`dist`、`build`、`.mypy_cache`、`.pytest_cache`、`.ruff_cache`；跳过二进制文件（前 8 KiB 含 NUL 字节）和符号链接。

## 设计取舍

- **只读、零依赖**：不修改文件，不上传任何内容，适合放进最小化 CI 镜像
- **只看工作区，不看历史**：历史泄漏交给专门的工具；本地检查追求快和低误报
- **严格过滤占位符**：`your_key_here`、`example_token`、`changeme` 不报，避免示例配置刷屏
- **脱敏输出**：报告里不出现密钥原文，只能看到类型、位置和长度
- **跳过依赖目录**：`node_modules` 里的测试夹具会让报告失去意义

## 已知边界

- 正则匹配，不做熵分析；随机生成的弱格式密钥可能漏掉
- 不扫描 git 历史、不扫描压缩包
- 只识别单行内的密钥；跨行拼接的字符串可能漏报
- `.gitignore` 中的文件仍会被扫描（只看是否被 git 跟踪，不看是否被忽略）

## 开发

```bash
git clone https://github.com/eathink/envscan
cd envscan

# 仅用标准库，无需安装依赖
PYTHONPATH=src python3 -m unittest discover -s tests -v

# 本地运行
PYTHONPATH=src python3 -m envscan . --exit-zero
```

## License

[MIT](LICENSE)
