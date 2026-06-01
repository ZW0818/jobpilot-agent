from pathlib import Path
from typing import Any

from model.factory import get_embedding_model, has_dashscope_key
from utils.path_tool import backend_root


class VectorStoreManager:
    def __init__(self, persist_dir: Path | None = None, data_dir: Path | None = None) -> None:
        self.persist_dir = persist_dir or backend_root() / "chroma_db"
        self.data_dir = data_dir or backend_root() / "data"

    def get_retriever(self) -> Any | None:
        if not has_dashscope_key():
            return None

        try:
            from langchain_chroma import Chroma
            from langchain_core.documents import Document
            from langchain_text_splitters import RecursiveCharacterTextSplitter
        except ImportError:
            return None

        try:
            embeddings = get_embedding_model()
            docs = self._load_documents(Document)
            if not docs:
                return None

            splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)
            chunks = splitter.split_documents(docs)
            store = Chroma.from_documents(
                documents=chunks,
                embedding=embeddings,
                persist_directory=str(self.persist_dir),
            )
            return store.as_retriever(search_kwargs={"k": 4})
        except Exception:
            return None

    def _load_documents(self, document_cls: Any) -> list[Any]:
        docs: list[Any] = []
        for path in self.data_dir.glob("*.txt"):
            try:
                docs.append(document_cls(page_content=path.read_text(encoding="utf-8"), metadata={"source": path.name}))
            except OSError:
                continue
        return docs
