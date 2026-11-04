import hashlib
import logging
import os
from pathlib import Path
from threading import RLock
from time import monotonic
from typing import Any

from model.factory import get_embedding_model, has_dashscope_key
from model.errors import provider_error_code
from rag.corpus import KnowledgeCorpus
from utils.config_handler import load_yaml_config
from utils.path_tool import backend_root

logger = logging.getLogger("jobpilot")


class VectorStoreManager:
    """Reuse a persistent collection; only embed new/changed content IDs."""

    def __init__(self, persist_dir: Path | None = None, data_dir: Path | None = None, corpus: KnowledgeCorpus | None = None):
        config = load_yaml_config("chroma.yaml")
        self.persist_dir = persist_dir or backend_root() / os.getenv(
            "CHROMA_PERSIST_DIRECTORY", config.get("persist_directory", "chroma_db")
        )
        self.collection_name = config.get("collection_name", "jobpilot_knowledge")
        self.corpus = corpus or KnowledgeCorpus(data_dir)
        self._lock = RLock()
        self._store: Any = None
        self._fingerprint = ""
        self._embedding_name = ""
        self._retry_after = 0.0
        self.last_error_type = ""
        self.last_error_code = ""

    def get_retriever(self, top_k: int = 8) -> Any | None:
        if not has_dashscope_key() or monotonic() < self._retry_after:
            return None
        with self._lock:
            try:
                fingerprint, chunks = self.corpus.snapshot()
                if not chunks and self._store is None:
                    return None
                embedding_name = os.getenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v4")
                if self._store is None or embedding_name != self._embedding_name:
                    from langchain_chroma import Chroma
                    suffix = hashlib.sha256(embedding_name.encode()).hexdigest()[:10]
                    self._store = Chroma(
                        collection_name=f"{self.collection_name}_{suffix}",
                        embedding_function=get_embedding_model(), persist_directory=str(self.persist_dir),
                    )
                    self._embedding_name, self._fingerprint = embedding_name, ""
                if fingerprint != self._fingerprint:
                    from langchain_core.documents import Document
                    existing = set(self._store.get(include=[])["ids"])
                    desired = {chunk.chunk_id for chunk in chunks}
                    added = [chunk for chunk in chunks if chunk.chunk_id not in existing]
                    if added:
                        self._store.add_documents([
                            Document(page_content=f"{c.section}\n{c.content}", metadata={
                                "source": c.source, "section": c.section, "domain": c.domain, "chunk_id": c.chunk_id,
                            }) for c in added
                        ], ids=[c.chunk_id for c in added])
                    # Delete stale IDs only after all replacements have been written successfully.
                    removed = existing - desired
                    if removed:
                        self._store.delete(ids=sorted(removed))
                    self._fingerprint = fingerprint
                self.last_error_type = self.last_error_code = ""
                return self._store.as_retriever(search_kwargs={"k": top_k})
            except Exception as exc:
                self.last_error_type = type(exc).__name__
                self.last_error_code = provider_error_code(exc)
                logger.warning("Vector index unavailable (%s); using local retrieval", type(exc).__name__)
                self._retry_after = monotonic() + 60
                return None
