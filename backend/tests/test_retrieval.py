import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from rag.corpus import KnowledgeCorpus
from rag.rag_service import RAGService

CASES = json.loads((Path(__file__).parent / "fixtures/retrieval_cases.json").read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES, ids=[case["question"] for case in CASES])
def test_curated_retrieval_cases(case):
    result = RAGService(enable_vector=False).retrieve(case["question"])
    if case["source"] is None:
        assert not result.has_context
    else:
        assert any(c.source == case["source"] and c.section == case["section"] for c in result.chunks)


def test_global_ranking_and_preference_do_not_hide_better_file(tmp_path):
    (tmp_path / "a.txt").write_text("React 是前端组件工具。", encoding="utf-8")
    (tmp_path / "z.txt").write_text("Redis 缓存过期与一致性，热点缓存的回源问题。", encoding="utf-8")
    rag = RAGService(data_dir=tmp_path, enable_vector=False)
    result = rag.retrieve("Redis 缓存一致性", preferred_files=["a.txt"])
    assert result.chunks[0].source == "z.txt"
    assert not rag.retrieve("Redis", preferred_files=["a.txt"], scan_remaining=False).has_context


def test_domain_filter_and_context_budget():
    rag = RAGService(enable_vector=False)
    result = rag.retrieve("React 状态管理 项目", domain="frontend")
    assert result.has_context
    assert all(c.domain in {"frontend", "general"} for c in result.chunks)
    rag.context_budget = 700
    result = rag.retrieve("MySQL Redis FastAPI 项目 简历")
    assert len(result.context) <= 700
    assert len({c.chunk_id for c in result.chunks}) == len(result.chunks)


def test_section_chunks_are_stable_and_refresh_after_edits(tmp_path):
    file = tmp_path / "knowledge.md"
    file.write_text("# 知识\n## Redis\n" + "缓存回源。" * 100 + "\n## MySQL\n索引优化。", encoding="utf-8")
    corpus = KnowledgeCorpus(tmp_path, chunk_size=120, chunk_overlap=20)
    fingerprint, chunks = corpus.snapshot()
    assert all(len(c.content) <= 120 for c in chunks)
    assert len(chunks) == len({c.chunk_id for c in chunks})
    assert corpus.snapshot() == (fingerprint, chunks)
    mysql_id = next(c.chunk_id for c in chunks if c.section == "MySQL")
    file.write_text(file.read_text(encoding="utf-8") + "新增执行计划。", encoding="utf-8")
    updated, updated_chunks = corpus.snapshot()
    assert updated != fingerprint
    assert mysql_id not in {c.chunk_id for c in updated_chunks}
    file.unlink()
    assert not corpus.snapshot()[1]


def test_hybrid_fuses_only_supported_candidates_and_survives_vector_failure(tmp_path):
    (tmp_path / "a.txt").write_text("Python 文档解析", encoding="utf-8")
    (tmp_path / "b.txt").write_text("Python API 开发", encoding="utf-8")
    rag = RAGService(data_dir=tmp_path, enable_vector=False)
    chunks = rag.corpus.snapshot()[1]
    second = next(c for c in chunks if c.source == "b.txt")
    retriever = SimpleNamespace(invoke=lambda q: [SimpleNamespace(metadata={"chunk_id": second.chunk_id})])
    rag.vector_store = SimpleNamespace(get_retriever=lambda **kwargs: retriever)
    rag.enable_vector = True
    result = rag.retrieve("Python")
    assert result.status == "hybrid"
    assert result.chunks[0].source == "b.txt"
    def broken(query):
        raise RuntimeError("service unavailable")
    retriever.invoke = broken
    assert rag.retrieve("Python").status == "fallback"
    assert not rag.retrieve("unrelated weather").has_context
