"""Install Python dependencies required to run ``workflow/full_pipeline_runner.py``.

The full pipeline stitches together all Stage 1–4 agents, the capability /
strategy upgrade agents, MCP-based tools (Tavily search, Firecrawl scrape),
and the Watcher audit agent.  This installer focuses on the shared runtime
dependencies that are not part of the standard library.

Usage:
    python scripts/install_full_pipeline_deps.py

Common flags:
    --groups core stage4     # Install specific dependency groups (default: both)
    --no-stage4-extras       # Skip Stage 4 PDF / spaCy packages
    --spacy-model en_core_web_sm
    --skip-spacy-model
    --upgrade                # Pass --upgrade to pip install
    --dry-run                # Print commands without executing them
    --export requirements-full.txt

中文速览：
    - 用于一键安装 FullPipelineRunner 运行所需依赖（Stage1–4、能力/策略升级、Watcher、MCP 工具）。
    - 默认安装 core 与 stage4 两组依赖，可用 --groups / --no-stage4-extras 做精细选择。
    - 通过 --spacy-model / --skip-spacy-model 控制 spaCy 语言模型下载，支持 --dry-run 仅查看命令。
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence

# fmt: off
CORE_PACKAGES: list[tuple[str, str]] = [
    ("python-dotenv>=1.0.1", "Loads .env for workflow/full_pipeline_runner"),
    ("httpx>=0.27.0", "Async HTTP client used across model wrappers and MCP helpers"),
    ("openai>=1.13.0", "AsyncOpenAI client used by every stage agent"),
    ("pydantic>=2.6.0", "Structured output/validation in model wrappers"),
    ("mcp>=1.0.0", "Model Context Protocol client for Tavily / Firecrawl tools"),
]

STAGE4_PACKAGES: list[tuple[str, str]] = [
    ("PyPDF2>=3.0.0", "Stage4 tool sandbox PDF ingestion"),
    ("pdfplumber>=0.11.0", "Higher fidelity PDF text extraction"),
    ("spacy>=3.7.2", "Executor agent language analysis + POS tagging"),
]
# fmt: on

PACKAGE_GROUPS = {
    "core": CORE_PACKAGES,
    "stage4": STAGE4_PACKAGES,
}

DEFAULT_GROUPS = ("core", "stage4")


def _run(cmd: Sequence[str], *, dry_run: bool) -> None:
    """Execute a subprocess command or echo it when dry-run is enabled."""

    printable = " ".join(cmd)
    print(f"[INFO] Running: {printable}")
    if dry_run:
        return
    subprocess.check_call(list(cmd))


def _install_packages(
    packages: Iterable[tuple[str, str]],
    *,
    python_exe: str,
    upgrade: bool,
    dry_run: bool,
) -> None:
    for spec, reason in packages:
        print(f"[INFO] Installing {spec} — {reason}")
        cmd = [python_exe, "-m", "pip", "install"]
        if upgrade:
            cmd.append("--upgrade")
        cmd.append(spec)
        _run(cmd, dry_run=dry_run)


def _download_spacy_model(
    *,
    python_exe: str,
    model: str,
    dry_run: bool,
) -> None:
    print(f"[INFO] Downloading spaCy model '{model}'")
    cmd = [python_exe, "-m", "spacy", "download", model]
    _run(cmd, dry_run=dry_run)


def _export_requirements(
    path: Path,
    packages: Iterable[tuple[str, str]],
) -> None:
    lines = [spec for spec, _ in packages]
    content = "\n".join(lines) + "\n"
    path.write_text(content, encoding="utf-8")
    print(f"[INFO] Wrote {path} with {len(lines)} packages.")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install dependencies for workflow/full_pipeline_runner.py",
    )
    parser.add_argument(
        "--groups",
        choices=PACKAGE_GROUPS.keys(),
        nargs="+",
        default=list(DEFAULT_GROUPS),
        help="Dependency groups to install (default: core stage4).",
    )
    parser.add_argument(
        "--no-stage4-extras",
        action="store_true",
        help="Shortcut to skip Stage 4 PDF/spaCy dependencies.",
    )
    parser.add_argument(
        "--spacy-model",
        default="en_core_web_sm",
        help="spaCy language model to download (default: en_core_web_sm).",
    )
    parser.add_argument(
        "--skip-spacy-model",
        "--skip-spaCy-model",
        dest="skip_spacy_model",
        action="store_true",
        help="Do not download any spaCy language model.",
    )
    parser.add_argument(
        "--upgrade",
        action="store_true",
        help="Pass --upgrade to pip install.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print pip commands without executing them.",
    )
    parser.add_argument(
        "--export",
        type=Path,
        help="Write the resolved package list to the given requirements file.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    python_exe = sys.executable
    print(f"[INFO] Using interpreter: {python_exe}")

    groups = list(dict.fromkeys(args.groups or []))
    if args.no_stage4_extras and "stage4" in groups:
        groups.remove("stage4")

    if not groups:
        print("[WARN] No dependency groups selected. Nothing to install.")
        return 0

    combined_packages: list[tuple[str, str]] = []
    for group in groups:
        combined_packages.extend(PACKAGE_GROUPS[group])

    if args.export:
        _export_requirements(Path(args.export), combined_packages)

    for group in groups:
        print(f"[INFO] Installing group: {group}")
        _install_packages(
            PACKAGE_GROUPS[group],
            python_exe=python_exe,
            upgrade=args.upgrade,
            dry_run=args.dry_run,
        )

    if (
        not args.skip_spacy_model
        and not args.no_stage4_extras
        and "stage4" in groups
    ):
        _download_spacy_model(
            python_exe=python_exe,
            model=args.spacy_model,
            dry_run=args.dry_run,
        )

    print("[INFO] Dependency installation completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


