from agent.tools.middleware import log_step
from rag.rag_service import RAGService
from schemas.jobpilot_schema import JDInfo, JobClassification


class KnowledgeAgent:
    """Retrieve local career knowledge that can support the evaluation."""

    def __init__(self) -> None:
        self.rag_service = RAGService()

    @log_step("knowledge")
    def run(self, jd_info: JDInfo, jd_text: str, job_classification: JobClassification | None = None) -> str:
        domain = (job_classification.domain if job_classification else "general") or "general"
        rag_query = " ".join(jd_info.required_skills + jd_info.preferred_skills + jd_info.keywords)
        domain_keywords = {
            "ai": "AI RAG Agent LLM LangChain Python 向量数据库 Prompt Engineering",
            "backend": "后端 Java Spring Boot MySQL Redis Kafka 微服务 接口 分布式 高并发 数据库",
            "frontend": "前端 React Vue TypeScript JavaScript 组件 页面 状态管理 Webpack Vite",
            "general": "简历优化 项目经历 技能表达 投递建议 面试准备",
        }
        preferred_files = {
            "ai": ["ai_job_requirements.txt", "rag_interview_questions.txt", "agent_interview_questions.txt"],
            "backend": ["backend_job_requirements.txt", "resume_optimization_rules.txt"],
            "frontend": ["frontend_job_requirements.txt", "resume_optimization_rules.txt"],
            "general": ["resume_optimization_rules.txt", "project_resume_templates.txt"],
        }
        query = " ".join([domain_keywords.get(domain, domain_keywords["general"]), rag_query or jd_text])
        return self.rag_service.retrieve_context(query, preferred_files=preferred_files.get(domain, []))
