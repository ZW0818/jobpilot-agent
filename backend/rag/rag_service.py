from agent.tools.agent_tools import extract_known_skills
from rag.vector_store import VectorStoreManager
from utils.path_tool import backend_root


class RAGService:
    def __init__(self) -> None:
        self.vector_store = VectorStoreManager()

    def retrieve_context(self, query: str) -> str:
        retriever = self.vector_store.get_retriever()
        if retriever is not None:
            try:
                docs = retriever.invoke(query)
                if docs:
                    return "\n\n".join(
                        f"[{doc.metadata.get('source', 'knowledge')}] {doc.page_content[:500]}" for doc in docs
                    )
            except Exception:
                pass

        return self._fallback_context(query)

    def _fallback_context(self, query: str) -> str:
        data_dir = backend_root() / "data"
        skills = set(extract_known_skills(query))
        snippets: list[str] = []
        for path in sorted(data_dir.glob("*.txt")):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError:
                continue
            if not skills or any(skill.lower() in text.lower() for skill in skills):
                snippets.append(f"[{path.name}] {text[:450].strip()}")
            if len(snippets) >= 3:
                break

        if snippets:
            return "RAG fallback context（未启用向量检索）：\n" + "\n\n".join(snippets)
        return "RAG 暂不可用：可能缺少 DASHSCOPE_API_KEY、向量依赖或本地知识库文件。"
