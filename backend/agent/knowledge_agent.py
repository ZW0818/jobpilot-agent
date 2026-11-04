from agent.tools.middleware import log_step
from rag.rag_service import RetrievalResult, get_rag_service
from schemas.jobpilot_schema import JDInfo, JobClassification, MatchResult


class KnowledgeAgent:
    """Retrieve role knowledge first, then fill only the observed evidence gaps."""

    def __init__(self) -> None:
        self.rag_service = get_rag_service()

    @log_step("knowledge")
    def retrieve(self, jd_info: JDInfo, jd_text: str, classification: JobClassification) -> RetrievalResult:
        query = " ".join([jd_info.job_title, *jd_info.required_skills, *jd_info.preferred_skills, *jd_info.keywords])
        return self.rag_service.retrieve(query.strip()[:1500] or jd_text[:1500], domain=classification.domain)

    def run(self, jd_info: JDInfo, jd_text: str, job_classification: JobClassification | None = None) -> str:
        result = self.retrieve(jd_info, jd_text, job_classification or JobClassification())
        return result.context if result.has_context else result.message

    def supplement(self, initial: RetrievalResult, match: MatchResult, classification: JobClassification,
                   max_queries: int = 2) -> RetrievalResult:
        gaps = [item.jd_requirement for item in match.evidence_items if item.status != "matched"][:max_queries]
        additions = [self.rag_service.retrieve(f"{gap} 项目证据 面试问题", domain=classification.domain, top_k=2)
                     for gap in gaps]
        # Interleave follow-up and initial hits so the context budget includes both kinds of evidence.
        groups = [initial.chunks, *(result.chunks for result in additions)]
        chunks = [group[index] for index in range(max(map(len, groups), default=0))
                  for group in groups if index < len(group)]
        status = "hybrid" if any(r.status == "hybrid" for r in [initial, *additions]) else "fallback"
        return self.rag_service.build_result(initial.query, chunks, status)
