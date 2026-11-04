import hashlib
import os
import sys
from types import SimpleNamespace

import pytest

from rag.vector_store import VectorStoreManager


def test_persistent_index_reuses_ids_and_incrementally_adds_updates_deletes(tmp_path, monkeypatch):
    monkeypatch.setattr("rag.vector_store.has_dashscope_key", lambda: True)
    monkeypatch.setattr("rag.vector_store.get_embedding_model", lambda: object())
    database, added, removed = {}, [], []

    class FakeChroma:
        def __init__(self, collection_name, **kwargs):
            self.docs = database.setdefault(collection_name, {})

        def get(self, **kwargs):
            return {"ids": list(self.docs)}

        def add_documents(self, docs, ids):
            added.extend(ids)
            self.docs.update(zip(ids, docs))

        def delete(self, ids):
            removed.extend(ids)
            for key in ids:
                del self.docs[key]

        def as_retriever(self, **kwargs):
            return self

    monkeypatch.setitem(sys.modules, "langchain_chroma", SimpleNamespace(Chroma=FakeChroma))
    monkeypatch.setitem(sys.modules, "langchain_core.documents", SimpleNamespace(Document=SimpleNamespace))
    file = tmp_path / "a.md"
    file.write_text("# Redis\n缓存数据", encoding="utf-8")
    manager = VectorStoreManager(persist_dir=tmp_path / "index", data_dir=tmp_path)
    assert manager.get_retriever() is not None
    original_id = added[0]
    manager.get_retriever()
    assert len(added) == 1
    restarted = VectorStoreManager(persist_dir=tmp_path / "index", data_dir=tmp_path)
    restarted.get_retriever()
    assert len(added) == 1  # Restart reuses persisted IDs without embedding again.
    file.write_text("# Redis\n更新缓存数据与失效策略", encoding="utf-8")
    restarted.get_retriever()
    assert len(added) == 2 and original_id in removed
    second = tmp_path / "b.txt"
    second.write_text("MySQL 执行计划", encoding="utf-8")
    restarted.get_retriever()
    assert len(added) == 3
    file.unlink()
    restarted.get_retriever()
    assert set(restarted._store.docs) == {c.chunk_id for c in restarted.corpus.snapshot()[1]}
    monkeypatch.setenv("DASHSCOPE_EMBEDDING_MODEL", "another-model")
    restarted.get_retriever()
    assert len(database) == 2 and len(added) == 4
    second.unlink()
    restarted.get_retriever()
    assert restarted._store.docs == {}


def test_failed_index_update_preserves_old_ids_and_cools_down(tmp_path, monkeypatch):
    monkeypatch.setattr("rag.vector_store.has_dashscope_key", lambda: True)
    manager = VectorStoreManager(data_dir=tmp_path)
    (tmp_path / "new.txt").write_text("新知识", encoding="utf-8")
    deleted = []
    def failed_add(*args, **kwargs):
        raise RuntimeError("embedding service down")
    manager._store = SimpleNamespace(get=lambda **kw: {"ids": ["old"]}, add_documents=failed_add, delete=lambda **kw: deleted.append(kw))
    monkeypatch.setenv("DASHSCOPE_EMBEDDING_MODEL", "test-embedding")
    manager._embedding_name = "test-embedding"
    monkeypatch.setitem(sys.modules, "langchain_core.documents", SimpleNamespace(Document=SimpleNamespace))
    assert manager.get_retriever() is None
    assert manager.get_retriever() is None
    assert not deleted
    assert manager._retry_after > 0


@pytest.mark.skipif(os.getenv("JOBPILOT_RUN_CHROMA_INTEGRATION") != "1", reason="Opt-in native Chroma integration; set JOBPILOT_RUN_CHROMA_INTEGRATION=1")
def test_real_chroma_persistence_with_offline_embeddings(tmp_path, monkeypatch):
    monkeypatch.setenv("ANONYMIZED_TELEMETRY", "False")
    pytest.importorskip("langchain_chroma")
    from langchain_core.embeddings import Embeddings

    class OfflineEmbeddings(Embeddings):
        document_count = 0

        def embed_documents(self, texts):
            self.document_count += len(texts)
            return [self.embed_query(text) for text in texts]

        def embed_query(self, text):
            return [value / 255 for value in hashlib.sha256(text.encode()).digest()[:8]]

    embeddings = OfflineEmbeddings()
    monkeypatch.setattr("rag.vector_store.has_dashscope_key", lambda: True)
    monkeypatch.setattr("rag.vector_store.get_embedding_model", lambda: embeddings)
    monkeypatch.setenv("DASHSCOPE_EMBEDDING_MODEL", "offline-test-v1")
    data = tmp_path / "data"
    data.mkdir()
    source = data / "knowledge.md"
    source.write_text("# 知识\n## Redis\n缓存过期。\n## MySQL\n索引优化。", encoding="utf-8")
    manager = VectorStoreManager(data_dir=data, persist_dir=tmp_path / "index")
    retriever = manager.get_retriever()
    assert retriever is not None
    assert retriever.invoke("Redis")
    assert embeddings.document_count == 2
    restarted = VectorStoreManager(data_dir=data, persist_dir=tmp_path / "index")
    assert restarted.get_retriever() is not None
    assert embeddings.document_count == 2
    source.write_text("# 知识\n## Redis\n缓存过期和回源。", encoding="utf-8")
    assert restarted.get_retriever() is not None
    assert embeddings.document_count == 3
    assert len(restarted._store.get(include=[])["ids"]) == 1
