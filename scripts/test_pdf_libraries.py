"""PDF library availability smoke test.

Usage:
    python scripts/test_pdf_libraries.py [optional_pdf_path]

The script attempts to import `PyPDF2` and `pdfplumber`, load the target PDF,
extract a small amount of text, and print a status report for each library.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path
from typing import Tuple


def _resolve_pdf_path(cli_arg: str | None) -> Path:
    """Return an existing PDF path, defaulting to data/ai_reg_2022.pdf."""
    if cli_arg:
        path = Path(cli_arg).expanduser().resolve()
    else:
        path = (Path(__file__).resolve().parent.parent / "data" / "ai_reg_2022.pdf").resolve()
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")
    return path


def _test_pypdf2(pdf_path: Path) -> Tuple[bool, str]:
    """Attempt to import PyPDF2 and extract text from the first page."""
    try:
        pypdf2 = importlib.import_module("PyPDF2")
    except Exception as exc:  # pragma: no cover - import side effect
        return False, f"PyPDF2 import failed: {exc}"

    try:
        with pdf_path.open("rb") as fh:
            reader = pypdf2.PdfReader(fh)
            num_pages = len(reader.pages)
            first_page_text = (reader.pages[0].extract_text() or "").strip()
        snippet = first_page_text[:120].replace("\n", " ")
        return True, f"PyPDF2 OK — pages={num_pages}, snippet='{snippet}'"
    except Exception as exc:
        return False, f"PyPDF2 runtime error: {exc}"


def _test_pdfplumber(pdf_path: Path) -> Tuple[bool, str]:
    """Attempt to import pdfplumber and extract text from the first page."""
    try:
        pdfplumber = importlib.import_module("pdfplumber")
    except Exception as exc:  # pragma: no cover - import side effect
        return False, f"pdfplumber import failed: {exc}"

    try:
        with pdfplumber.open(pdf_path) as pdf:
            first_page = pdf.pages[0]
            text = (first_page.extract_text() or "").strip()
        snippet = text[:120].replace("\n", " ")
        return True, f"pdfplumber OK — pages={len(pdf.pages)}, snippet='{snippet}'"
    except Exception as exc:
        return False, f"pdfplumber runtime error: {exc}"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Test availability of PDF parsing libraries.")
    parser.add_argument(
        "pdf_path",
        nargs="?",
        help="Path to a PDF file (defaults to data/ai_reg_2022.pdf).",
    )
    args = parser.parse_args(argv)

    try:
        pdf_path = _resolve_pdf_path(args.pdf_path)
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}")
        return 1

    print(f"[INFO] Using PDF: {pdf_path}")

    tests = [
        ("PyPDF2", _test_pypdf2),
        ("pdfplumber", _test_pdfplumber),
    ]

    exit_code = 0
    for name, fn in tests:
        ok, message = fn(pdf_path)
        status = "PASS" if ok else "FAIL"
        print(f"[{status}] {message}")
        if not ok:
            exit_code = 1

    if exit_code == 0:
        print("[INFO] All PDF libraries responded successfully.")
    else:
        print("[WARN] One or more PDF libraries failed. See messages above.")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())

