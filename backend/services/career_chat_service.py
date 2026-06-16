from agent.tools.agent_tools import extract_known_skills, summarize_text
from model.factory import get_chat_model, has_dashscope_key
from rag.rag_service import RAGService, RetrievalResult
from schemas.jobpilot_schema import CareerChatResponse, ChatMessage


class CareerChatService:
    """RAG-first career Q&A. The model is never asked to answer without retrieved context."""

    def __init__(self) -> None:
        self.rag_service = RAGService()

    def answer(self, question: str, history: list[ChatMessage] | None = None) -> CareerChatResponse:
        question = (question or "").strip()
        history = history or []
        logs: list[str] = []

        logs.append("QuestionOptimizerAgent: 正在结合上下文优化检索问题。")
        optimized_query = self._optimize_question(question, history)
        logs.append(f"QuestionOptimizerAgent: 检索问题已优化为：{optimized_query}")

        logs.append("KnowledgeSearchAgent: 正在检索本地求职知识库。")
        retrieval = self.rag_service.retrieve(
            optimized_query,
            preferred_files=self._preferred_files(optimized_query),
            min_score=1.0,
            scan_remaining=False,
        )

        if not retrieval.has_context:
            topic = self._topic_label(optimized_query)
            logs.append("KnowledgeSearchAgent: 未检索到可支撑回答的知识片段，已阻止模型自由发挥。")
            return CareerChatResponse(
                answer=f"目前知识库没有相关「{topic}」信息，暂时无法基于平台知识库给出可靠回答。你可以补充更具体的岗位、技术栈或面试场景后再试。",
                optimized_query=optimized_query,
                retrieval_status="miss",
                sources=[],
                agent_logs=logs,
                used_model=False,
            )

        logs.append(f"KnowledgeSearchAgent: 已命中 {len(retrieval.chunks)} 段知识，来源：{', '.join(retrieval.sources)}。")
        logs.append("AnswerAgent: 正在基于检索结果生成受约束回答。")
        answer, used_model = self._answer_from_context(question, optimized_query, history, retrieval)
        logs.append("AnswerAgent: 回答已生成，且只允许使用检索到的知识库内容。")

        return CareerChatResponse(
            answer=answer,
            optimized_query=optimized_query,
            retrieval_status=retrieval.status,
            sources=retrieval.sources,
            agent_logs=logs,
            used_model=used_model,
        )

    def _optimize_question(self, question: str, history: list[ChatMessage]) -> str:
        skills = extract_known_skills(question)
        recent_user_terms = [
            item.content.strip()
            for item in history[-4:]
            if item.role == "user" and item.content.strip() and len(item.content.strip()) <= 80
        ]
        parts = [question, *skills, *recent_user_terms[-2:]]
        return " ".join(dict.fromkeys(part for part in parts if part))[:500]

    def _answer_from_context(
        self,
        question: str,
        optimized_query: str,
        history: list[ChatMessage],
        retrieval: RetrievalResult,
    ) -> tuple[str, bool]:
        if has_dashscope_key():
            try:
                recent_history = [
                    {"role": item.role, "content": item.content}
                    for item in history[-6:]
                    if item.content.strip()
                ]
                system_prompt = (
                    "你是 JobPilot 求职问答智能体。必须只依据提供的 knowledge_context 回答。"
                    "如果上下文不足以回答，就明确说知识库没有相关信息，不要编造。"
                    "回答要面向求职场景，给出可执行建议，避免泛泛而谈。"
                )
                payload = {
                    "question": question,
                    "optimized_query": optimized_query,
                    "history": recent_history,
                    "knowledge_context": retrieval.context,
                    "sources": retrieval.sources,
                }
                response = get_chat_model().invoke([("system", system_prompt), ("user", str(payload))])
                content = getattr(response, "content", str(response)).strip()
                if content:
                    return content, True
            except Exception:
                pass

        snippets = [summarize_text(chunk.content, max_chars=240) for chunk in retrieval.chunks[:3]]
        bullet_text = "\n".join(f"{index}. {snippet}" for index, snippet in enumerate(snippets, start=1))
        answer = (
            "已在知识库中找到相关内容，但当前未成功调用模型服务。"
            "先给你一版基于检索片段的保守回答：\n"
            f"{bullet_text}\n"
            "建议围绕上述来源继续追问更具体的岗位、技术栈或简历场景。"
        )
        return answer, False

    def _preferred_files(self, query: str) -> list[str]:
        lowered = query.lower()
        if any(term in lowered for term in ("react", "vue", "typescript", "javascript", "frontend", "vite")):
            return ["frontend_job_requirements.txt", "resume_optimization_rules.txt"]
        if any(term in lowered for term in ("rag", "agent", "llm", "langchain", "prompt", "ai")):
            return ["ai_job_requirements.txt", "rag_interview_questions.txt", "agent_interview_questions.txt"]
        if (
            any(term in lowered for term in ("spring", "mysql", "redis", "kafka", "backend"))
            or "java " in lowered
            or " java" in lowered
            or lowered.endswith("java")
        ):
            return ["backend_job_requirements.txt", "resume_optimization_rules.txt"]
        return ["resume_optimization_rules.txt", "project_resume_templates.txt"]

    def _topic_label(self, query: str) -> str:
        skills = extract_known_skills(query)
        if skills:
            return "、".join(skills[:3])
        return summarize_text(query, max_chars=30) or "该问题"
