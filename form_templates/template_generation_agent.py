"""Agent for provisioning finish_form documents from the standard template."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
STANDARD_TEMPLATE = Path(__file__).with_name("standard template.md")
FINISH_FORM_DIR = PROJECT_ROOT / "finish_form"
MAX_FINISH_FORMS = 8


@dataclass(slots=True)
class GenerationSummary:
    """Record of a template generation pass."""

    status: str
    total_documents: int
    document_paths: Sequence[Path]
    created_document: Path | None = None

    def as_text(self) -> str:
        """Return a human-readable summary."""

        lines = [
            f"状态: {self.status}",
            f"finish_form 中文档数量: {self.total_documents}",
        ]

        if self.created_document:
            lines.append(f"新建文档: {self.created_document}")

        if self.document_paths:
            lines.append("文档位置列表:")
            lines.extend(f"- {path}" for path in self.document_paths)

        return "\n".join(lines)


class TemplateGenerationAgent:
    """Agent that ensures finish_form is populated with up-to-date templates."""

    agent_name: str = "TemplateGenerationAgent"
    agent_stage: str = "bootstrap"
    agent_function: str = "template_provisioning"

    def __init__(
        self,
        *,
        template_path: Path | None = None,
        finish_dir: Path | None = None,
        max_documents: int = MAX_FINISH_FORMS,
    ) -> None:
        self._template_path = template_path or STANDARD_TEMPLATE
        self._finish_dir = finish_dir or FINISH_FORM_DIR
        self._max_documents = max_documents

    def ensure_template(self) -> GenerationSummary:
        """Ensure a new template document exists."""

        self._validate_paths()
        existing_documents = self._enumerate_documents()

        new_document = self._create_document()
        updated_documents = (*existing_documents, new_document)

        return GenerationSummary(
            status="created_new_document",
            total_documents=len(updated_documents),
            document_paths=updated_documents,
            created_document=new_document,
        )

    def _validate_paths(self) -> None:
        """Ensure required paths exist."""

        if not self._template_path.is_file():
            raise FileNotFoundError(f"标准模版不存在: {self._template_path}")

        self._finish_dir.mkdir(parents=True, exist_ok=True)

    def _enumerate_documents(self) -> tuple[Path, ...]:
        """Return all finish_form documents sorted by name."""

        documents: Iterable[Path] = sorted(
            path for path in self._finish_dir.glob("*.md") if path.is_file()
        )
        return tuple(documents)

    def _create_document(self) -> Path:
        """Copy the standard template into finish_form with a timestamp-based filename."""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        destination = self._finish_dir / f"finish_form_{timestamp}.md"
        shutil.copyfile(self._template_path, destination)
        return destination


__all__ = ["TemplateGenerationAgent", "GenerationSummary"]


