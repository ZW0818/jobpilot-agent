from schemas.jobpilot_schema import JDInfo, JobClassification, MatchResult, ResumeInfo, RewriteResult


def _items(items: list[str], fallback: str = "暂未识别。") -> list[str]:
    return [f"- {item}" for item in items] if items else [f"- {fallback}"]


def _score_detail_items(match_result: MatchResult) -> list[str]:
    detail = match_result.score_detail
    return [
        f"- 核心技能匹配度：{detail.skill_match} / 40",
        f"- 项目经历相关性：{detail.project_relevance} / 30",
        f"- 工程落地能力：{detail.engineering_ability} / 20",
        f"- 简历表达完整度：{detail.resume_quality} / 10",
    ]


def _evidence_table(match_result: MatchResult) -> list[str]:
    rows = [
        "| JD 要求 | 简历证据 | 状态 | 建议 |",
        "|---|---|---|---|",
    ]
    for item in match_result.evidence_items:
        rows.append(
            "| "
            + " | ".join(
                [
                    _clean_table_cell(item.jd_requirement),
                    _clean_table_cell(item.resume_evidence),
                    _clean_table_cell(item.status),
                    _clean_table_cell(item.suggestion),
                ]
            )
            + " |"
        )
    if len(rows) == 2:
        rows.append("| 暂未识别 | 简历中未找到明确证据 | missing | 建议补充更完整的 JD 要求和简历项目描述。 |")
    return rows


def _clean_table_cell(value: str) -> str:
    return (value or "").replace("|", "\\|").replace("\n", " ").strip()


def build_report_markdown(
    resume_info: ResumeInfo,
    jd_info: JDInfo,
    match_result: MatchResult,
    rewrite_result: RewriteResult,
    rag_context: str,
    job_classification: JobClassification | None = None,
) -> str:
    classification = job_classification or JobClassification()
    lines = [
        "# JobPilot 求职岗位匹配分析报告",
        "",
        "## 1. 岗位信息",
        f"- 岗位名称：{jd_info.job_title or '未识别'}",
        f"- 岗位方向：{classification.domain}（置信度：{classification.confidence:.2f}）",
        f"- 识别原因：{classification.reason or '暂无'}",
        f"- 必备技能：{', '.join(jd_info.required_skills) or '未识别'}",
        f"- 加分技能：{', '.join(jd_info.preferred_skills) or '未识别'}",
        f"- 岗位摘要：{jd_info.summary or '暂无摘要'}",
        "",
        "## 2. 简历摘要",
        f"- 姓名：{resume_info.name or '未识别'}",
        f"- 技能：{', '.join(resume_info.skills) or '未识别'}",
        f"- 简历摘要：{resume_info.summary or '暂无摘要'}",
        "",
        "## 匹配度评分",
        f"总分：{match_result.score} / 100",
        "",
        *_score_detail_items(match_result),
        "",
        f"- 匹配等级：{match_result.level or '未评级'}",
        "",
        "## 匹配证据对照表",
        *_evidence_table(match_result),
        "",
        "## 5. 匹配优势",
        *_items(match_result.matched_points),
        "",
        "## 6. 缺失与不足",
        *_items(match_result.missing_points),
        "",
        "## 7. 简历优化建议",
        *_items(match_result.suggestions),
        "",
        "## 8. 简历改写建议",
        rewrite_result.optimized_summary or "暂无优化摘要。",
        "",
        "### 技能区",
        *_items(rewrite_result.optimized_skills),
        "",
        "### 项目经历",
        *_items(rewrite_result.optimized_projects),
        "",
        "## 9. 面试准备问题",
        *_items(rewrite_result.interview_questions),
        "",
        "## 10. RAG 参考",
        rag_context or "暂无 RAG 参考内容。",
    ]
    return "\n".join(lines).strip() + "\n"
