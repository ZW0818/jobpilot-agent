from agent.tools.agent_tools import contains_term, extract_known_skills, unique_preserve_order
from agent.tools.middleware import log_step
from schemas.jobpilot_schema import EvidenceItem, JDInfo, JobClassification, MatchResult, ResumeInfo, ScoreDetail


class EvaluationAgent:
    """计算匹配度，归纳优势、缺口和投递前行动建议。"""

    @log_step("evaluation")
    def run(
        self,
        resume_info: ResumeInfo,
        jd_info: JDInfo,
        rag_context: str,
        job_classification: JobClassification | None = None,
    ) -> MatchResult:
        # Scores and evidence use resume/JD only; reference documents cannot prove candidate skills.
        return self._run_fallback(resume_info, jd_info, job_classification)

    def _run_fallback(
        self,
        resume_info: ResumeInfo,
        jd_info: JDInfo,
        job_classification: JobClassification | None = None,
    ) -> MatchResult:
        return self._with_deterministic_details(MatchResult(), resume_info, jd_info, job_classification)

    def _with_deterministic_details(
        self,
        result: MatchResult,
        resume_info: ResumeInfo,
        jd_info: JDInfo,
        job_classification: JobClassification | None = None,
    ) -> MatchResult:
        result.score_detail = self._build_score_detail(resume_info, jd_info, job_classification)
        result.score = (
            result.score_detail.skill_match
            + result.score_detail.project_relevance
            + result.score_detail.engineering_ability
            + result.score_detail.resume_quality
        )
        result.level = self._level_for_score(result.score)
        result.evidence_items = self._build_evidence_items(resume_info, jd_info)

        result.matched_points = [
            f"已覆盖：{item.jd_requirement}" for item in result.evidence_items if item.status == "matched"
        ][:8]
        result.missing_points = [
            f"{'缺少证据' if item.status == 'missing' else '证据待补强'}：{item.jd_requirement}"
            for item in result.evidence_items if item.status != "matched"
        ][:8]
        result.suggestions = unique_preserve_order([item.suggestion for item in result.evidence_items if item.status != "matched"]
                                                  + [item.suggestion for item in result.evidence_items if item.status == "matched"])[:8]
        return result

    def _build_score_detail(
        self,
        resume_info: ResumeInfo,
        jd_info: JDInfo,
        job_classification: JobClassification | None = None,
    ) -> ScoreDetail:
        resume_blob = self._resume_blob(resume_info)
        required = self._skill_terms(jd_info.required_skills)
        preferred = [s for s in self._skill_terms(jd_info.preferred_skills) if s.lower() not in {r.lower() for r in required}]
        if not required:
            required = [s for s in jd_info.keywords if s.lower() not in {p.lower() for p in preferred}]

        def coverage(skills):
            return sum(contains_term(skill, resume_blob) for skill in skills) / max(len(skills), 1)

        if required and preferred:
            skill_coverage = 0.85 * coverage(required) + 0.15 * coverage(preferred)
        else:
            skill_coverage = coverage(required or preferred)

        domain = (job_classification.domain if job_classification else "general") or "general"
        domain_terms = {
            "ai": ("rag", "agent", "llm", "langchain", "python", "pytorch", "tensorflow", "向量", "模型"),
            "backend": ("java", "spring boot", "mysql", "redis", "kafka", "接口", "微服务", "数据库", "分布式"),
            "frontend": ("react", "vue", "typescript", "javascript", "组件", "页面", "状态管理", "vite", "webpack"),
            "general": ("项目", "系统", "平台", "负责", "优化", "实现", "协作"),
        }
        project_text = " ".join(resume_info.projects + resume_info.experience).lower()
        project_hits = sum(1 for term in domain_terms.get(domain, domain_terms["general"]) if contains_term(term, project_text))

        engineering_terms = (
            "fastapi",
            "react",
            "接口",
            "api",
            "部署",
            "docker",
            "git",
            "mysql",
            "redis",
            "数据库",
            "可视化",
            "报告下载",
            "vite",
        )
        engineering_hits = sum(1 for term in engineering_terms if contains_term(term, resume_blob))
        quality_units = [
            bool(resume_info.name),
            bool(resume_info.skills),
            bool(resume_info.projects),
            bool(resume_info.experience or resume_info.summary),
            any(len(item) >= 30 for item in resume_info.projects + resume_info.experience),
        ]

        return ScoreDetail(
            skill_match=min(40, int(round(skill_coverage * 40))),
            project_relevance=min(30, int(round(min(project_hits, 6) / 6 * 30))),
            engineering_ability=min(20, int(round(min(engineering_hits, 8) / 8 * 20))),
            resume_quality=min(10, int(round(sum(quality_units) / len(quality_units) * 10))),
        )

    def _build_evidence_items(self, resume_info: ResumeInfo, jd_info: JDInfo) -> list[EvidenceItem]:
        requirements = unique_preserve_order(jd_info.required_skills + jd_info.responsibilities + jd_info.keywords[:6])[
            :10
        ]
        if not requirements:
            requirements = unique_preserve_order(jd_info.keywords + [jd_info.summary])[:6]

        evidence_items: list[EvidenceItem] = []
        resume_blob = self._resume_blob(resume_info)
        for requirement in requirements:
            if not requirement:
                continue
            keywords = extract_known_skills(requirement) or [requirement]
            matched_keywords = [keyword for keyword in keywords if contains_term(keyword, resume_blob)]
            evidence = self._find_resume_evidence(resume_info, requirement, matched_keywords)
            concrete = " ".join(resume_info.projects + resume_info.experience)
            concrete_coverage = all(contains_term(keyword, concrete) for keyword in keywords)

            if evidence and len(matched_keywords) == len(keywords) and concrete_coverage:
                status = "matched"
                suggestion = f"建议补充 {requirement} 的量化结果、技术细节或个人贡献。"
            elif evidence or matched_keywords:
                status = "partial"
                suggestion = f"已有相关经历，但建议更直接写出与 {requirement} 对应的职责、技术栈和结果。"
            else:
                status = "missing"
                evidence = "简历中未找到明确证据"
                suggestion = f"如真实具备 {requirement}，请补充项目证据；否则建议先补齐该能力后再投递。"

            evidence_items.append(
                EvidenceItem(
                    jd_requirement=requirement,
                    resume_evidence=evidence,
                    status=status,
                    suggestion=suggestion,
                )
            )
        return evidence_items

    def _find_resume_evidence(self, resume_info: ResumeInfo, requirement: str, keywords: list[str]) -> str:
        requirement_lower = requirement.lower()
        sources = resume_info.projects + resume_info.experience + resume_info.skills + [resume_info.summary]
        for source in sources:
            source_text = str(source).strip()
            source_lower = source_text.lower()
            if not source_text:
                continue
            if contains_term(requirement_lower, source_lower) or any(contains_term(keyword, source_lower) for keyword in keywords):
                return source_text[:180]
        return ""

    @staticmethod
    def _skill_terms(items: list[str]) -> list[str]:
        return unique_preserve_order([term for item in items for term in (extract_known_skills(item) or [item])])

    def _resume_blob(self, resume_info: ResumeInfo) -> str:
        return " ".join(
            resume_info.skills
            + resume_info.projects
            + resume_info.education
            + resume_info.experience
            + [resume_info.summary]
        ).lower()

    def _level_for_score(self, score: int) -> str:
        if score >= 85:
            return "强烈推荐投递"
        if score >= 70:
            return "推荐投递"
        if score >= 55:
            return "可以尝试"
        return "暂不推荐"
