from agent.tools.agent_tools import parse_json_output, unique_preserve_order
from agent.tools.middleware import log_step
from model.factory import get_chat_model, has_dashscope_key
from schemas.jobpilot_schema import JDInfo, MatchResult, ResumeInfo
from utils.prompt_loader import load_prompt


class EvaluationAgent:
    """计算匹配度，归纳优势、缺口和投递前行动建议。"""

    @log_step("evaluation")
    def run(self, resume_info: ResumeInfo, jd_info: JDInfo, rag_context: str) -> MatchResult:
        if has_dashscope_key():
            try:
                prompt = load_prompt("match_prompt.txt")
                payload = {
                    "resume_info": resume_info.model_dump(),
                    "jd_info": jd_info.model_dump(),
                    "rag_context": rag_context,
                }
                response = get_chat_model().invoke([("system", prompt), ("user", str(payload))])
                return MatchResult.model_validate(parse_json_output(getattr(response, "content", str(response))))
            except Exception:
                pass
        return self._run_fallback(resume_info, jd_info)

    def _run_fallback(self, resume_info: ResumeInfo, jd_info: JDInfo) -> MatchResult:
        resume_terms = " ".join(resume_info.skills + resume_info.projects + resume_info.experience).lower()
        jd_terms = unique_preserve_order(jd_info.keywords + jd_info.required_skills)
        matched = [term for term in jd_terms if term and term.lower() in resume_terms]
        missing = [term for term in jd_terms if term and term.lower() not in resume_terms]
        coverage = len(matched) / max(len(jd_terms), 1)
        score = min(100, max(0, int(45 + coverage * 50)))

        if score >= 85:
            level = "强烈推荐投递"
        elif score >= 70:
            level = "推荐投递"
        elif score >= 55:
            level = "可以尝试"
        else:
            level = "暂不推荐"

        suggestions = ["在简历摘要和项目经历中补充与 JD 对齐的关键词。"]
        if missing:
            suggestions.insert(0, "优先补充这些能力证据：" + ", ".join(missing[:5]))

        return MatchResult(
            score=score,
            level=level,
            matched_points=[f"已覆盖：{item}" for item in matched[:8]],
            missing_points=[f"缺少证据：{item}" for item in missing[:8]],
            suggestions=suggestions,
        )
