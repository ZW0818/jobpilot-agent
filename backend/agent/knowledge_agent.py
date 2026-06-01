from agent.tools.middleware import log_step
from rag.rag_service import RAGService
from schemas.jobpilot_schema import JDInfo


class KnowledgeAgent:
    """Retrieve local career knowledge that can support the evaluation."""

    def __init__(self) -> None:
        self.rag_service = RAGService()

    @log_step("knowledge")
    def run(self, jd_info: JDInfo, jd_text: str) -> str:
        rag_query = " ".join(jd_info.required_skills + jd_info.preferred_skills + jd_info.keywords)
        return self.rag_service.retrieve_context(rag_query or jd_text)
