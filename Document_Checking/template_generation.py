"""Utilities for ensuring finish_form contains enough standard templates."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Sequence

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TEMPLATE_NAME = "standard template.md"


@dataclass(slots=True)
class TemplateGenerationConfig:
    """Configuration options for :class:`TemplateGenerationAgent`."""

    threshold: int = 8
    finish_form_dir: str | Path | None = None
    template_path: str | Path | None = None
    encoding: str = "utf-8"
    filename_prefix: str = "auto_generated_template"


class TemplateGenerationAgent:
    """Agent that ensures finish_form contains a fresh copy of the standard template."""

    def __init__(
        self,
        config: TemplateGenerationConfig | None = None,
        **overrides: Any,
    ) -> None:
        config_dict = asdict(config or TemplateGenerationConfig())
        config_dict.update(overrides)

        self._threshold = max(int(config_dict.get("threshold", 8) or 0), 0)
        self._encoding = str(config_dict.get("encoding", "utf-8") or "utf-8")
        self._filename_prefix = str(
            config_dict.get("filename_prefix", "auto_generated_template") or "auto_generated_template"
        )

        finish_form_dir = config_dict.get("finish_form_dir")
        template_path = config_dict.get("template_path")

        self._project_root = PROJECT_ROOT
        self._finish_form_dir = Path(finish_form_dir or self._project_root / "finish_form").expanduser().resolve()
        self._finish_form_dir.mkdir(parents=True, exist_ok=True)

        default_template_path = self._project_root / "form_templates" / DEFAULT_TEMPLATE_NAME
        self._template_path = Path(template_path or default_template_path).expanduser().resolve()

        if not self._template_path.is_file():
            raise FileNotFoundError(f"Template file not found: {self._template_path}")

    @property
    def finish_form_dir(self) -> Path:
        """Return the directory that stores finish_form documents."""

        return self._finish_form_dir

    @property
    def template_path(self) -> Path:
        """Return the template document path."""

        return self._template_path

    def run(self) -> dict[str, Any]:
        """Ensure the finish_form directory contains a fresh template if needed.

        Returns:
            A dictionary with keys:
                - ``created``: Path of the created document or ``None``.
                - ``documents``: List of relative paths of all documents in finish_form.
        """

        existing_docs = list(self._list_documents())
        created_path: Path | None = None

        if len(existing_docs) <= self._threshold:
            created_path = self._create_document(existing_docs)
            existing_docs.append(created_path)

        summary = {
            "created": self._to_relative_string(created_path) if created_path else None,
            "documents": [self._to_relative_string(path) for path in sorted(existing_docs)],
        }
        return summary

    def _list_documents(self) -> Iterable[Path]:
        """Yield all markdown documents under finish_form."""

        yield from sorted(self._finish_form_dir.glob("*.md"))

    def _create_document(self, existing_docs: Sequence[Path]) -> Path:
        """Create a new document copied from the standard template."""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        candidate = self._finish_form_dir / f"{self._filename_prefix}_{timestamp}.md"
        suffix = 1
        while candidate.exists():
            candidate = self._finish_form_dir / f"{self._filename_prefix}_{timestamp}_{suffix}.md"
            suffix += 1

        template_content = self._template_path.read_text(encoding=self._encoding)
        all_docs = list(existing_docs) + [candidate]
        doc_lines = "\n".join(
            f"- `{self._to_relative_string(path)}`" for path in sorted(all_docs)
        )
        if doc_lines:
            appendix = (
                "\n\n---\n\n"
                "## 完成文档位置索引\n\n"
                f"{doc_lines}\n"
            )
        else:
            appendix = ""

        candidate.write_text(template_content + appendix, encoding=self._encoding)
        return candidate

    def _to_relative_string(self, path: Path) -> str:
        """Convert an absolute path to a project-relative POSIX string."""

        try:
            relative_path = path.relative_to(self._project_root)
        except ValueError:
            relative_path = path
        return relative_path.as_posix()


def main() -> None:
    """CLI entry point."""

    import argparse
    import json

    parser = argparse.ArgumentParser(description="Template generation agent for finish_form.")
    parser.add_argument("--threshold", type=int, default=8, help="Maximum allowed finished documents before skipping.")
    parser.add_argument("--finish-dir", type=str, help="Override finish_form directory.")
    parser.add_argument("--template", type=str, help="Override template file path.")
    parser.add_argument("--filename-prefix", type=str, default="auto_generated_template", help="Prefix for new documents.")
    parser.add_argument("--encoding", type=str, default="utf-8", help="File encoding for reading/writing documents.")
    args = parser.parse_args()

    agent = TemplateGenerationAgent(
        threshold=args.threshold,
        finish_form_dir=args.finish_dir,
        template_path=args.template,
        filename_prefix=args.filename_prefix,
        encoding=args.encoding,
    )
    result = agent.run()

    created = result.get("created")
    if created:
        print(f"Created document: {agent._to_relative_string(created)}")  # pylint: disable=protected-access
    else:
        print("No document created; threshold exceeded.")

    print("Documents in finish_form:")
    print(json.dumps(result.get("documents", []), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
