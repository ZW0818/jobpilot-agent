from agent.coach_agent import CoachAgent
from agent.evaluation_agent import EvaluationAgent
from agent.knowledge_agent import KnowledgeAgent
from agent.profile_agent import ProfileAgent
from schemas.jobpilot_schema import JobPilotResult


class SupervisorService:
    """调度四个角色 Agent，并保持 API 返回结构稳定。"""

    def __init__(self) -> None:
        self.profile_agent = ProfileAgent()
        self.knowledge_agent = KnowledgeAgent()
        self.evaluation_agent = EvaluationAgent()
        self.coach_agent = CoachAgent()

    def run(self, resume_text: str, jd_text: str) -> JobPilotResult:
        logs: list[str] = []

        logs.append("ProfileAgent 正在解析简历与岗位 JD，生成候选人与岗位画像。")
        resume_info, jd_info = self.profile_agent.run(resume_text, jd_text)
        logs.append("ProfileAgent 已完成简历画像与岗位画像。")

        logs.append("KnowledgeAgent 正在检索本地求职知识库，补充评估依据。")
        rag_context = self.knowledge_agent.run(jd_info, jd_text)
        logs.append("KnowledgeAgent 已完成 RAG 知识检索。")

        logs.append("EvaluationAgent 正在计算匹配评分，并归纳优势与缺口。")
        match_result = self.evaluation_agent.run(resume_info, jd_info, rag_context)
        logs.append("EvaluationAgent 已完成匹配度评估。")

        logs.append("CoachAgent 正在生成简历优化、面试准备题和 Markdown 报告。")
        rewrite_result, markdown_report = self.coach_agent.run(resume_info, jd_info, match_result, rag_context)
        logs.append("CoachAgent 已完成求职辅导建议与分析报告。")

        logs.append("JobPilot 四角色多智能体分析完成。")
        return JobPilotResult(
            resume_info=resume_info,
            jd_info=jd_info,
            match_result=match_result,
            rewrite_result=rewrite_result,
            markdown_report=markdown_report,
            agent_logs=logs,
        )
