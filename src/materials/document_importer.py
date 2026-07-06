"""Local document import helpers for material library."""
from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree


SUPPORTED_EXTENSIONS = {".txt", ".json", ".docx", ".doc"}
WORD_TAGS = ["法律文书", "导入", "Word文档"]
TEXT_TAGS = ["法律文书", "导入"]

_WORD_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def load_local_materials(file_path: str | Path) -> list[dict]:
    """Load local text-like files into material dictionaries."""
    path = Path(file_path)
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"unsupported import file type: {suffix}")

    if suffix == ".json":
        return _load_json_materials(path)
    if suffix == ".txt":
        return _materials_from_text(_read_text(path), tags=TEXT_TAGS)
    if suffix == ".docx":
        return _materials_from_text(_extract_docx_text(path), tags=WORD_TAGS)
    return _materials_from_text(_extract_doc_text(path), tags=WORD_TAGS)


def _load_json_materials(path: Path) -> list[dict]:
    text = _read_text(path)
    items = json.loads(text)
    if not isinstance(items, list):
        items = [items]

    materials = []
    for item in items:
        if not isinstance(item, dict):
            continue
        content = str(item.get("content", "")).strip()
        if not content:
            continue
        materials.append({
            "title": str(item.get("title", "导入文本")).strip() or "导入文本",
            "content": content,
            "author": str(item.get("author", "")).strip(),
            "category": "legal",
            "difficulty": item.get("difficulty", 3),
            "tags": item.get("tags", TEXT_TAGS),
            "source": "local_import",
        })
    return materials


def _materials_from_text(text: str, tags: list[str]) -> list[dict]:
    entries = [entry.strip() for entry in re.split(r"\n\s*\n", text.strip()) if entry.strip()]
    if not entries and text.strip():
        entries = [text.strip()]

    materials = []
    for entry in entries:
        lines = [line.strip() for line in entry.splitlines() if line.strip()]
        title = lines[0][:50] if lines else "导入文本"
        materials.append({
            "title": title,
            "content": entry,
            "author": "",
            "category": "legal",
            "difficulty": 3,
            "tags": list(tags),
            "source": "local_import",
        })
    return materials


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").strip()


def _extract_docx_text(path: Path) -> str:
    try:
        with zipfile.ZipFile(path) as archive:
            xml = archive.read("word/document.xml")
    except (KeyError, zipfile.BadZipFile) as exc:
        raise ValueError(f"invalid docx file: {path}") from exc

    root = ElementTree.fromstring(xml)
    paragraphs = []
    for paragraph in root.iter(f"{_WORD_NS}p"):
        parts = []
        for node in paragraph.iter():
            if node.tag == f"{_WORD_NS}t" and node.text:
                parts.append(node.text)
            elif node.tag == f"{_WORD_NS}tab":
                parts.append("\t")
            elif node.tag == f"{_WORD_NS}br":
                parts.append("\n")
        line = "".join(parts).strip()
        if line:
            paragraphs.append(line)
    return "\n".join(paragraphs).strip()


def _extract_doc_text(path: Path) -> str:
    try:
        import win32com.client  # type: ignore[import-not-found]
    except ImportError as exc:
        raise ValueError("legacy .doc import requires Microsoft Word and pywin32; save as .docx and import again") from exc

    word = None
    document = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        document = word.Documents.Open(
            str(path),
            ReadOnly=True,
            ConfirmConversions=False,
            AddToRecentFiles=False,
        )
        return str(document.Content.Text).replace("\r", "\n").strip()
    except Exception as exc:
        raise ValueError(f"failed to read legacy .doc file: {path}") from exc
    finally:
        if document is not None:
            document.Close(False)
        if word is not None:
            word.Quit()
