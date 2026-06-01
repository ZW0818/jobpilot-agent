from schemas.jobpilot_schema import JDInfo, MatchResult, ResumeInfo, RewriteResult


def _items(items: list[str], fallback: str = "暂未识别。") -> list[str]:
    return [f"- {item}" for item in items] if items else [f"- {fallback}"]


def build_report_markdown(
    resume_info: ResumeInfo,
    jd_info: JDInfo,
    match_result: MatchResult,
    rewrite_result: RewriteResult,
    rag_context: str,
) -> str:
    lines = [
        "# JobPilot 求职岗位匹配分析报告",
        "",
        "## 1. 岗位信息",
        f"- 岗位名称：{jd_info.job_title or '未识别'}",
        f"- 必备技能：{', '.join(jd_info.required_skills) or '未识别'}",
        f"- 加分技能：{', '.join(jd_info.preferred_skills) or '未识别'}",
        f"- 岗位摘要：{jd_info.summary or '暂无摘要'}",
        "",
        "## 2. 简历摘要",
        f"- 姓名：{resume_info.name or '未识别'}",
        f"- 技能：{', '.join(resume_info.skills) or '未识别'}",
        f"- 简历摘要：{resume_info.summary or '暂无摘要'}",
        "",
        "## 3. 匹配度评分",
        f"- 匹配分数：{match_result.score}/100",
        f"- 匹配等级：{match_result.level or '未评级'}",
        "",
        "## 4. 匹配优势",
        *_items(match_result.matched_points),
        "",
        "## 5. 缺失与不足",
        *_items(match_result.missing_points),
        "",
        "## 6. 简历优化建议",
        *_items(match_result.suggestions),
        "",
        "## 7. 简历改写建议",
        rewrite_result.optimized_summary or "暂无优化摘要。",
        "",
        "### 技能区",
        *_items(rewrite_result.optimized_skills),
        "",
        "### 项目经历",
        *_items(rewrite_result.optimized_projects),
        "",
        "## 8. 面试准备问题",
        *_items(rewrite_result.interview_questions),
        "",
        "## 9. RAG 参考",
        rag_context or "暂无 RAG 参考内容。",
    ]
    return "\n".join(lines).strip() + "\n"
