import re
from dataclasses import dataclass, field

from agent.tools.agent_tools import extract_known_skills
from rag.vector_store import VectorStoreManager
from utils.path_tool import backend_root


@dataclass
class RetrievedChunk:
    source: str
    content: str
    score: float = 0.0


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
        seen: set[str] = set()
        values: list[str] = []
        for chunk in self.chunks:
            if chunk.source not in seen:
                seen.add(chunk.source)
                values.append(chunk.source)
        return values


class RAGService:
    def __init__(self) -> None:
        self.vector_store = VectorStoreManager()

    def retrieve_context(self, query: str, preferred_files: list[str] | None = None) -> str:
        result = self.retrieve(query, preferred_files=preferred_files)
        if result.has_context:
            return result.context
        return result.message or "RAG is unavailable: no relevant local knowledge was found."

    def retrieve(
        self,
        query: str,
        preferred_files: list[str] | None = None,
        min_score: float = 1.0,
        scan_remaining: bool = True,
    ) -> RetrievalResult:
        query = (query or "").strip()
        if not query:
            return RetrievalResult(query=query, message="RAG query is empty.")

        vector_result = self._retrieve_from_vector_store(query, min_score=min_score)
        if vector_result.has_context:
            return vector_result

        fallback_result = self._fallback_context(
            query,
            preferred_files or [],
            min_score=min_score,
            scan_remaining=scan_remaining,
        )
        if fallback_result.has_context:
            return fallback_result

        message = fallback_result.message or vector_result.message or "No relevant local knowledge was found."
        return RetrievalResult(query=query, status="miss", message=message)

    def _retrieve_from_vector_store(self, query: str, min_score: float) -> RetrievalResult:
        retriever = self.vector_store.get_retriever()
        if retriever is None:
            return RetrievalResult(query=query, status="miss", message="Vector RAG is unavailable.")

        try:
            docs = retriever.invoke(query)
        except Exception:
            return RetrievalResult(query=query, status="miss", message="Vector RAG failed.")

        query_terms = self._extract_query_terms(query)
        chunks: list[RetrievedChunk] = []
        for doc in docs or []:
            content = (doc.page_content or "").strip()
            if not content:
                continue
            snippet, score = self._best_snippet(content, query_terms)
            if snippet and score >= min_score:
                chunks.append(
                    RetrievedChunk(
                        source=doc.metadata.get("source", "knowledge"),
                        content=snippet[:500].strip(),
                        score=score,
                    )
                )
        if not chunks:
            return RetrievalResult(query=query, status="miss", message="Vector RAG returned no relevant documents.")

        return RetrievalResult(
            query=query,
            chunks=chunks,
            context=self._format_context(chunks, "Vector RAG context"),
            status="vector",
        )

    def _fallback_context(
        self,
        query: str,
        preferred_files: list[str],
        min_score: float,
        scan_remaining: bool,
    ) -> RetrievalResult:
        data_dir = backend_root() / "data"
        query_terms = self._extract_query_terms(query)
        chunks: list[RetrievedChunk] = []

        preferred_paths = [data_dir / name for name in preferred_files]
        remaining_paths = (
            sorted(path for path in data_dir.glob("*.txt") if path.name not in set(preferred_files))
            if scan_remaining
            else []
        )

        for path in [*preferred_paths, *remaining_paths]:
            if not path.exists():
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue

            snippet, score = self._best_snippet(text, query_terms)
            if snippet and score >= min_score:
                chunks.append(RetrievedChunk(source=path.name, content=snippet, score=score))
            if len(chunks) >= 4:
                break

        if chunks:
            return RetrievalResult(
                query=query,
                chunks=chunks,
                context=self._format_context(chunks, "Local keyword RAG context"),
                status="fallback",
            )

        return RetrievalResult(
            query=query,
            status="miss",
            message="Local knowledge base has no relevant entries for this question.",
        )

    def _format_context(self, chunks: list[RetrievedChunk], title: str) -> str:
        body = "\n\n".join(f"[{chunk.source}] {chunk.content[:700]}" for chunk in chunks)
        return f"{title}:\n{body}"

    def _extract_query_terms(self, query: str) -> list[str]:
        skills = [skill.lower() for skill in extract_known_skills(query)]
        ascii_terms = re.findall(r"[a-zA-Z][a-zA-Z0-9+#.\-]{1,}", query.lower())
        chinese_terms = re.findall(r"[\u4e00-\u9fff]{2,}", query)
        stop_words = {
            "如何",
            "怎么",
            "什么",
            "哪些",
            "求职",
            "问题",
            "相关",
            "可以",
            "应该",
            "需要",
            "准备",
            "面试",
            "简历",
            "岗位",
        }
        terms = [*skills, *ascii_terms, *(term for term in chinese_terms if term not in stop_words)]
        seen: set[str] = set()
        unique_terms: list[str] = []
        for term in terms:
            normalized = term.strip().lower()
            if normalized and normalized not in seen:
                seen.add(normalized)
                unique_terms.append(normalized)
        return [
            term
            for term in unique_terms
            if not any(term != other and len(term) <= 4 and term in other for other in unique_terms)
        ]

    def _best_snippet(self, text: str, query_terms: list[str]) -> tuple[str, float]:
        if not query_terms:
            return "", 0.0

        paragraphs = [part.strip() for part in re.split(r"\n\s*\n|\r\n\s*\r\n", text) if part.strip()]
        if not paragraphs:
            paragraphs = [text.strip()]

        known_skill_hits = {skill.lower() for skill in extract_known_skills(text)}
        best = ""
        best_score = 0.0
        for paragraph in paragraphs:
            score = sum(
                (2.0 if term in known_skill_hits else 1.0)
                for term in query_terms
                if self._term_in_text(term, paragraph)
            )
            if score > best_score:
                best = paragraph
                best_score = score
        return best[:650].strip(), best_score

    def _term_in_text(self, term: str, text: str) -> bool:
        if re.fullmatch(r"[a-z0-9+#.\- ]+", term):
            if term == "react":
                return bool(re.search(r"(?<![A-Za-z0-9])(?:React|react)(?![A-Za-z0-9])", text))
            pattern = rf"(?<![a-z0-9+#.\-]){re.escape(term)}(?![a-z0-9+#.\-])"
            return bool(re.search(pattern, text.lower()))
        return term in text
