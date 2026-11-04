import json
import re

from agent.execution import record_fallback
from agent.tools.agent_tools import contains_term, extract_known_skills, parse_json_output, unique_preserve_order
from agent.tools.middleware import log_step
from model.factory import get_chat_model, has_dashscope_key
from schemas.jobpilot_schema import JDInfo, JobClassification, MatchResult, ResumeInfo, RewriteResult
from services.markdown_service import build_report_markdown
from utils.prompt_loader import load_structured_prompt


class CoachAgent:
    """生成简历优化建议、面试准备题和 Markdown 分析报告。"""

    @log_step("coach")
    def run(
        self,
        resume_info: ResumeInfo,
        jd_info: JDInfo,
        match_result: MatchResult,
        rag_context: str,
        job_classification: JobClassification | None = None,
    ) -> tuple[RewriteResult, str]:
        rewrite_result = self._build_rewrite_result(resume_info, jd_info, match_result, rag_context, job_classification)
        markdown_report = build_report_markdown(
            resume_info,
            jd_info,
            match_result,
            rewrite_result,
            rag_context,
            job_classification,
        )
        return rewrite_result, markdown_report

    def _build_rewrite_result(
        self,
        resume_info: ResumeInfo,
        jd_info: JDInfo,
        match_result: MatchResult,
        rag_context: str,
        job_classification: JobClassification | None = None,
    ) -> RewriteResult:
        if has_dashscope_key():
            try:
                prompt = load_structured_prompt("rewrite_prompt.txt", RewriteResult)
                payload = {
                    "resume_info": resume_info.model_dump(),
                    "jd_info": jd_info.model_dump(),
                    "match_result": match_result.model_dump(),
                    "rag_context": rag_context,
                    "job_classification": job_classification.model_dump() if job_classification else {},
                }
                response = get_chat_model().invoke([("system", prompt), ("user", json.dumps(payload, ensure_ascii=False))])
                result = RewriteResult.model_validate(parse_json_output(getattr(response, "content", str(response))))
                resume_blob = " ".join(resume_info.skills + resume_info.projects + resume_info.experience + [resume_info.summary])
                proposed_skills = extract_known_skills(" ".join(result.optimized_skills))
                if any(not contains_term(skill, resume_blob) for skill in proposed_skills):
                    raise ValueError("Rewrite introduced unsupported skills")
                return result
            except Exception as exc:
                record_fallback("CoachAgent", exc)
        return self._build_rewrite_fallback(resume_info, jd_info, match_result, rag_context, job_classification)

    def _build_rewrite_fallback(
        self,
        resume_info: ResumeInfo,
        jd_info: JDInfo,
        match_result: MatchResult,
        rag_context: str = "",
        job_classification: JobClassification | None = None,
    ) -> RewriteResult:
        role = jd_info.job_title or "目标岗位"
        skills = resume_info.skills
        optimized_summary = (f"目标岗位：{role}。简历已列出的技能：{', '.join(skills[:6])}。"
                             if skills else f"目标岗位：{role}。当前简历尚未提供足够明确的技能证据，建议补充真实项目职责后再完善摘要。")
        domain = job_classification.domain if job_classification else "general"
        role_advice = {
            "ai": "在真实经历范围内说明检索、工具调用、评测与部署中的个人贡献。",
            "backend": "在真实经历范围内说明接口设计、数据存储、并发处理和故障排查中的个人贡献。",
            "frontend": "在真实经历范围内说明组件设计、状态管理、接口交互和用户体验中的个人贡献。",
            "general": "围绕目标岗位写清真实职责、解决的问题、协作方式和可核验结果。",
        }
        optimized_projects = [
            "每段项目经历建议按“背景-职责-技术方案-结果”结构重写。",
            role_advice[domain],
        ]
        domain_questions = {
            "ai": ["如何评估 RAG 的检索质量与回答忠实度？", "Agent 工具失败时如何恢复并限制调用次数？"],
            "backend": ["如何定位慢查询并验证索引优化效果？", "如何设计接口幂等性、缓存一致性和失败恢复？"],
            "frontend": ["如何划分组件边界与共享状态？", "如何处理请求竞态、加载失败和键盘可访问性？"],
            "general": ["请介绍与你目标岗位最相关的项目和个人贡献。", "项目中的关键结果如何验证？"],
        }
        contextual = re.findall(r"面试问题[：:]([^\n]+)", rag_context)
        gap_questions = [f"关于“{item.jd_requirement}”，你有哪些实际使用经历或补齐计划？"
                         for item in match_result.evidence_items if item.status != "matched"][:2]
        interview_questions = unique_preserve_order(gap_questions + contextual[:2] + domain_questions[domain])[:6]
        return RewriteResult(
            optimized_summary=optimized_summary,
            optimized_skills=skills[:10],
            optimized_projects=optimized_projects + match_result.suggestions[:2],
            interview_questions=interview_questions,
        )
