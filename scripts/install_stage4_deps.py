"""Install all Python dependencies required by the Stage4 tool sandbox.

Run this script with the Python interpreter that Stage4 uses (typically the
same interpreter that launches `run_gaia_validation_tests.py`).  It will:

1. Install core PDF/text-processing libraries via `pip install`.
2. Download small spaCy language models needed for POS tagging.

Example:
    python scripts/install_stage4_deps.py
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from typing import Iterable

CORE_PACKAGES = [
    "PyPDF2>=3.0.0",
    "pdfplumber>=0.10.0",
    "spacy>=3.7.0",
]

SPACY_MODELS = [
    "en_core_web_sm",
]


def _run(cmd: Iterable[str]) -> None:
    """Execute command and stream output."""
    print(f"[INFO] Running: {' '.join(cmd)}")
    subprocess.check_call(list(cmd))


def install_packages(python_exe: str) -> None:
    for pkg in CORE_PACKAGES:
        _run([python_exe, "-m", "pip", "install", pkg])


def download_models(python_exe: str, skip_models: bool) -> None:
    if skip_models:
        print("[INFO] Skipping spaCy model downloads (per flag).")
        return
    for model in SPACY_MODELS:
        _run([python_exe, "-m", "spacy", "download", model])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Install PDF parsing dependencies for Stage4 sandbox.",
    )
    parser.add_argument(
        "--skip-models",
        action="store_true",
        help="Skip downloading spaCy language models.",
    )
    args = parser.parse_args(argv)

    python_exe = sys.executable
    print(f"[INFO] Using interpreter: {python_exe}")

    try:
        install_packages(python_exe)
        download_models(python_exe, skip_models=args.skip_models)
    except subprocess.CalledProcessError as exc:
        print(f"[ERROR] Command failed with exit code {exc.returncode}")
        return exc.returncode

    print("[INFO] Stage4 dependencies installed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

