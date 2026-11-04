import math
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from rag.corpus import KnowledgeChunk, KnowledgeCorpus
from rag.tokenizer import tokenize
from rag.vector_store import VectorStoreManager
from utils.config_handler import load_yaml_config


@dataclass
class RetrievedChunk:
    source: str
    content: str
    score: float = 0.0
    chunk_id: str = ""
    section: str = ""
    domain: str = "general"
    references: list[str] = field(default_factory=list)


@dataclass
class RetrievalResult:
    query: str
    context: str = ""
    chunks: list[RetrievedChunk] = field(default_factory=list)
    status: str = "miss"
    message: str = ""

    @property
    def has_context(self) -> bool:
        return bool(self.chunks and self.context.strip() and self.status != "miss")

    @property
    def sources(self) -> list[str]:
        return list(dict.fromkeys(chunk.source for chunk in self.chunks))


class RAGService:
    def __init__(self, data_dir: Path | None = None, vector_store: VectorStoreManager | None = None, enable_vector: bool | None = None):
        config = load_yaml_config("rag.yaml")
        self.top_k = max(1, int(config.get("top_k", 4)))
        self.context_budget = max(600, int(config.get("context_max_chars", 5000)))
        self.max_per_source = max(1, int(config.get("max_chunks_per_source", 2)))
        self.corpus = KnowledgeCorpus(data_dir, int(config.get("chunk_size", 600)), int(config.get("chunk_overlap", 80)))
        self.vector_store = vector_store or VectorStoreManager(corpus=self.corpus)
        configured = os.getenv("RAG_ENABLE_VECTOR")
        self.enable_vector = (enable_vector if enable_vector is not None else
                              configured.lower() in {"1", "true", "yes"} if configured is not None else
                              bool(config.get("vector_enabled", False)))

    def retrieve_context(self, query: str, preferred_files: list[str] | None = None) -> str:
        result = self.retrieve(query, preferred_files=preferred_files)
        return result.context if result.has_context else result.message

    def retrieve(self, query: str, preferred_files: list[str] | None = None, min_score: float = 1.0,
                 scan_remaining: bool = True, domain: str | None = None, top_k: int | None = None) -> RetrievalResult:
        query = (query or "").strip()
        terms = set(tokenize(query))
        if not terms:
            return RetrievalResult(query=query, message="检索问题为空或缺少有效关键词。")
        _, corpus = self.corpus.snapshot()
        preferred = set(preferred_files or [])
        candidates = [c for c in corpus
                      if (scan_remaining or c.source in preferred)
                      and (not domain or domain == "general" or c.domain in {domain, "general"})]
        sparse = self._rank_sparse(terms, candidates, preferred, min_score)
        vector_ids = []
        retriever = self.vector_store.get_retriever(top_k=max(self.top_k * 4, 12)) if self.enable_vector and sparse else None
        if retriever is not None:
            try:
                allowed = {c.chunk_id for c in candidates}
                vector_ids = list(dict.fromkeys(doc.metadata.get("chunk_id") for doc in retriever.invoke(query)
                                               if doc.metadata.get("chunk_id") in allowed))
            except Exception:
                vector_ids = []
        # Lexical support is required: an arbitrary nearest neighbor is insufficient evidence.
        scores = {c.chunk_id: 1 / (60 + rank) for rank, (c, _) in enumerate(sparse, 1)}
        for rank, chunk_id in enumerate(vector_ids, 1):
            if chunk_id in scores:
                scores[chunk_id] += 1 / (60 + rank)
        ordered = sorted(sparse, key=lambda pair: (-scores[pair[0].chunk_id], -pair[1], pair[0].chunk_id))
        selected, per_source, size = [], Counter(), 0
        for chunk, score in ordered:
            if per_source[chunk.source] >= self.max_per_source:
                continue
            if size + len(chunk.content) > self.context_budget:
                continue
            selected.append(RetrievedChunk(
                source=chunk.source, content=chunk.content, score=round(score, 4), chunk_id=chunk.chunk_id,
                section=chunk.section, domain=chunk.domain, references=list(chunk.references),
            ))
            per_source[chunk.source] += 1
            size += len(chunk.content)
            if len(selected) >= (top_k or self.top_k):
                break
        return self.build_result(query, selected, "hybrid" if vector_ids else "fallback")

    @staticmethod
    def _rank_sparse(terms: set[str], chunks: list[KnowledgeChunk], preferred: set[str], min_score: float):
        token_counts = [Counter(tokenize(f"{c.section}\n{c.content}")) for c in chunks]
        frequency = Counter(term for counts in token_counts for term in counts)
        average = sum(sum(counts.values()) for counts in token_counts) / max(len(chunks), 1)
        ranked = []
        for chunk, counts in zip(chunks, token_counts):
            hits = terms & counts.keys()
            if not hits:
                continue
            ascii_hits = {term for term in hits if re.search(r"[a-z]", term)}
            support = 2 * len(ascii_hits) + len(hits - ascii_hits)
            if support < min_score or (len(terms) >= 3 and not ascii_hits and len(hits) < 2):
                continue
            length = sum(counts.values())
            score = sum(
                math.log(1 + (len(chunks) - frequency[t] + 0.5) / (frequency[t] + 0.5))
                * counts[t] * 2.2 / (counts[t] + 1.2 * (0.25 + 0.75 * length / max(average, 1)))
                for t in hits
            )
            if chunk.source in preferred:
                score *= 1.1
            ranked.append((chunk, score))
        return sorted(ranked, key=lambda pair: (-pair[1], pair[0].chunk_id))

    def build_result(self, query: str, chunks: list[RetrievedChunk], status: str = "fallback") -> RetrievalResult:
        selected, seen, size = [], set(), 0
        for chunk in chunks:
            key = chunk.chunk_id or (chunk.source, chunk.content)
            entry = self._format_chunk(chunk)
            entry_size = len(entry) + (2 if selected else 0)
            if key in seen or size + entry_size > self.context_budget:
                continue
            selected.append(chunk)
            seen.add(key)
            size += entry_size
        if not selected:
            return RetrievalResult(query=query, message="本地知识库未找到足够相关的内容。")
        context = "\n\n".join(self._format_chunk(c) for c in selected)
        return RetrievalResult(query=query, chunks=selected, context=context, status=status)

    @staticmethod
    def _format_chunk(chunk: RetrievedChunk) -> str:
        return (f"[{chunk.source}#{chunk.chunk_id}] {chunk.section}\n{chunk.content}"
                + ("\n参考来源：" + "、".join(chunk.references) if chunk.references else ""))


@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:
    return RAGService()
