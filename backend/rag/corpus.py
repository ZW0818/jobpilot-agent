"""Shared, deterministic document loading and section-aware chunking."""
import hashlib
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from threading import RLock

from utils.path_tool import backend_root

logger = logging.getLogger("jobpilot")


@dataclass(frozen=True)
class KnowledgeChunk:
    chunk_id: str
    source: str
    section: str
    content: str
    domain: str = "general"
    tags: tuple[str, ...] = ()
    references: tuple[str, ...] = ()


class KnowledgeCorpus:
    def __init__(self, data_dir: Path | None = None, chunk_size: int = 600, chunk_overlap: int = 80):
        if chunk_size < 100 or not 0 <= chunk_overlap < chunk_size:
            raise ValueError("Invalid knowledge chunk size/overlap")
        self.data_dir = data_dir or backend_root() / "data"
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self._lock = RLock()
        self._signature: tuple | None = None
        self._chunks: tuple[KnowledgeChunk, ...] = ()
        self._fingerprint = ""

    def snapshot(self) -> tuple[str, tuple[KnowledgeChunk, ...]]:
        with self._lock:
            paths = sorted(p for p in self.data_dir.rglob("*") if p.suffix.lower() in {".txt", ".md"} and p.is_file())
            catalog_path = self.data_dir / "catalog.json"
            tracked = [*paths, *([catalog_path] if catalog_path.exists() else [])]
            signature = tuple((str(p), p.stat().st_mtime_ns, p.stat().st_size) for p in tracked)
            if signature == self._signature:
                return self._fingerprint, self._chunks
            catalog = json.loads(catalog_path.read_text(encoding="utf-8")) if catalog_path.exists() else {}
            digest = hashlib.sha256(f"section-v1:{self.chunk_size}:{self.chunk_overlap}".encode())
            digest.update(json.dumps(catalog, sort_keys=True, ensure_ascii=False).encode())
            chunks = []
            for path in paths:
                source = path.relative_to(self.data_dir).as_posix()
                try:
                    text = path.read_text(encoding="utf-8-sig")
                except (OSError, UnicodeError) as exc:
                    logger.warning("Knowledge file skipped: %s (%s)", source, type(exc).__name__)
                    continue
                digest.update(source.encode())
                digest.update(text.encode())
                metadata = catalog.get(source, {})
                title = metadata.get("title", path.stem)
                section, lines = title, []
                sections = []
                for line in text.splitlines():
                    if re.match(r"^#{1,6}\s+", line):
                        if lines:
                            sections.append((section, "\n".join(lines).strip()))
                        section, lines = line.lstrip("# ").strip(), []
                    else:
                        lines.append(line)
                sections.append((section, "\n".join(lines).strip()))
                for heading, body in sections:
                    for content in self._split(body):
                        domain = metadata.get("domain", "general")
                        chunk_id = hashlib.sha256(f"{source}\0{heading}\0{domain}\0{content}".encode()).hexdigest()[:24]
                        chunks.append(KnowledgeChunk(
                            chunk_id=chunk_id, source=source, section=heading, content=content,
                            domain=domain,
                            tags=tuple(metadata.get("tags", [])), references=tuple(metadata.get("references", [])),
                        ))
            self._signature, self._fingerprint = signature, digest.hexdigest()
            self._chunks = tuple({chunk.chunk_id: chunk for chunk in chunks}.values())
            return self._fingerprint, self._chunks

    def _split(self, text: str) -> list[str]:
        parts = []
        start = 0
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            if end < len(text):
                boundary = max(text.rfind("\n", start + self.chunk_size // 2, end), text.rfind("。", start + self.chunk_size // 2, end))
                if boundary > start:
                    end = boundary + 1
            part = text[start:end].strip()
            if part:
                parts.append(part)
            if end == len(text):
                break
            start = max(start + 1, end - self.chunk_overlap)
        return parts
