import re

from agent.tools.agent_tools import extract_bullets, extract_known_skills, parse_json_output, summarize_text
from agent.tools.middleware import log_step
from model.factory import get_chat_model, has_dashscope_key
from schemas.jobpilot_schema import JDInfo, ResumeInfo
from utils.prompt_loader import load_prompt


class ProfileAgent:
    """解析简历和岗位 JD，生成候选人画像与岗位画像。"""

    @log_step("profile")
    def run(self, resume_text: str, jd_text: str) -> tuple[ResumeInfo, JDInfo]:
        return self._parse_resume(resume_text), self._parse_jd(jd_text)

    def _parse_resume(self, resume_text: str) -> ResumeInfo:
        if has_dashscope_key():
            try:
                prompt = load_prompt("resume_prompt.txt")
                response = get_chat_model().invoke([("system", prompt), ("user", resume_text)])
                return ResumeInfo.model_validate(parse_json_output(getattr(response, "content", str(response))))
            except Exception:
                pass
        return self._parse_resume_fallback(resume_text)

    def _parse_resume_fallback(self, resume_text: str) -> ResumeInfo:
        lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
        name = next((line for line in lines[:5] if 1 <= len(line) <= 40 and "@" not in line), "")
        bullets = extract_bullets(resume_text)
        lowered_keywords = ("project", "agent", "rag", "system", "项目", "系统", "平台", "智能体")
        projects = [item for item in bullets if any(word in item.lower() for word in lowered_keywords)][:4]
        experience = [
            item
            for item in bullets
            if any(word in item.lower() for word in ("built", "developed", "designed", "负责", "开发", "实现", "优化"))
        ][:4]
        education = [
            item
            for item in bullets
            if any(word in item.lower() for word in ("university", "college", "bachelor", "master", "大学", "学院", "本科", "硕士"))
        ][:3]
        return ResumeInfo(
            name=name,
            skills=extract_known_skills(resume_text),
            projects=projects,
            education=education,
            experience=experience,
            summary=summarize_text(resume_text),
        )

    def _parse_jd(self, jd_text: str) -> JDInfo:
        if has_dashscope_key():
            try:
                prompt = load_prompt("jd_prompt.txt")
                response = get_chat_model().invoke([("system", prompt), ("user", jd_text)])
                return JDInfo.model_validate(parse_json_output(getattr(response, "content", str(response))))
            except Exception:
                pass
        return self._parse_jd_fallback(jd_text)

    def _parse_jd_fallback(self, jd_text: str) -> JDInfo:
        lines = [line.strip() for line in jd_text.splitlines() if line.strip()]
        first_line = lines[0] if lines else "目标岗位"
        title = re.sub(r"^(job|role|position|title|岗位|职位)\s*[:：-]\s*", "", first_line, flags=re.I)[:80]
        bullets = extract_bullets(jd_text, limit=12)
        keywords = extract_known_skills(jd_text)
        required = [
            item
            for item in bullets
            if any(word in item.lower() for word in ("require", "must", "familiar", "skill", "要求", "熟悉", "掌握"))
        ][:5]
        responsibilities = [
            item
            for item in bullets
            if any(word in item.lower() for word in ("build", "develop", "design", "responsible", "负责", "开发", "设计"))
        ][:5]
        return JDInfo(
            job_title=title,
            required_skills=required or keywords[:6],
            preferred_skills=keywords[6:12],
            responsibilities=responsibilities,
            keywords=keywords,
            summary=summarize_text(jd_text),
        )
