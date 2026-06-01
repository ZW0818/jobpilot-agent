from agent.tools.agent_tools import parse_json_output
from agent.tools.middleware import log_step
from model.factory import get_chat_model, has_dashscope_key
from schemas.jobpilot_schema import JDInfo, MatchResult, ResumeInfo, RewriteResult
from services.markdown_service import build_report_markdown
from utils.prompt_loader import load_prompt


class CoachAgent:
    """生成简历优化建议、面试准备题和 Markdown 分析报告。"""

    @log_step("coach")
    def run(
        self,
        resume_info: ResumeInfo,
        jd_info: JDInfo,
        match_result: MatchResult,
        rag_context: str,
    ) -> tuple[RewriteResult, str]:
        rewrite_result = self._build_rewrite_result(resume_info, jd_info, match_result, rag_context)
        markdown_report = build_report_markdown(resume_info, jd_info, match_result, rewrite_result, rag_context)
        return rewrite_result, markdown_report

    def _build_rewrite_result(
        self,
        resume_info: ResumeInfo,
        jd_info: JDInfo,
        match_result: MatchResult,
        rag_context: str,
    ) -> RewriteResult:
        if has_dashscope_key():
            try:
                prompt = load_prompt("rewrite_prompt.txt")
                payload = {
                    "resume_info": resume_info.model_dump(),
                    "jd_info": jd_info.model_dump(),
                    "match_result": match_result.model_dump(),
                    "rag_context": rag_context,
                }
                response = get_chat_model().invoke([("system", prompt), ("user", str(payload))])
                return RewriteResult.model_validate(parse_json_output(getattr(response, "content", str(response))))
            except Exception:
                pass
        return self._build_rewrite_fallback(resume_info, jd_info, match_result)

    def _build_rewrite_fallback(
        self,
        resume_info: ResumeInfo,
        jd_info: JDInfo,
        match_result: MatchResult,
    ) -> RewriteResult:
        role = jd_info.job_title or "目标岗位"
        skills = resume_info.skills or jd_info.keywords
        optimized_summary = (
            f"面向{role}，候选人具备"
            f"{', '.join(skills[:6]) or '软件交付'}等相关能力，能够结合业务目标完成技术方案设计、"
            "工程实现和结果复盘。"
        )
        optimized_projects = [
            "每段项目经历建议按“背景-职责-技术方案-结果”结构重写。",
            "在真实经历范围内突出 Agent、RAG、工具调用、结构化输出、API 集成和部署经验。",
        ]
        interview_questions = [
            "你是如何设计 Agent 工作流并划分工具边界的？",
            "你如何评估 RAG 检索质量？",
            "确定性代码和大模型生成之间，你做过哪些取舍？",
            "上线后你会如何监控失败并迭代 Prompt？",
        ]
        return RewriteResult(
            optimized_summary=optimized_summary,
            optimized_skills=skills[:10],
            optimized_projects=optimized_projects + match_result.suggestions[:2],
            interview_questions=interview_questions,
        )
