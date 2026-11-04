from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from time import perf_counter

from agent.coach_agent import CoachAgent
from agent.evaluation_agent import EvaluationAgent
from agent.execution import fallback_events
from agent.job_classifier_agent import JobClassifierAgent
from agent.knowledge_agent import KnowledgeAgent
from agent.profile_agent import ProfileAgent
from model.factory import has_dashscope_key
from schemas.jobpilot_schema import AgentTrace, JobPilotResult, KnowledgeEvidence
from utils.config_handler import load_yaml_config


class SupervisorService:
    """Dependency-aware workflow with bounded gap retrieval and request-local traces."""

    def __init__(self) -> None:
        self.profile_agent = ProfileAgent()
        self.job_classifier_agent = JobClassifierAgent()
        self.knowledge_agent = KnowledgeAgent()
        self.evaluation_agent = EvaluationAgent()
        self.coach_agent = CoachAgent()
        self.config = load_yaml_config("agent.yaml")

    @staticmethod
    def _execute(stage, operation, mode):
        events: list[str] = []
        token = fallback_events.set(events)
        started = perf_counter()
        try:
            result = operation()
            return result, AgentTrace(
                stage=stage, status="fallback" if events else "success",
                mode="rules" if events else mode, duration_ms=round((perf_counter() - started) * 1000, 2),
                message=f"{stage} 已完成。", warnings=list(events),
            )
        finally:
            fallback_events.reset(token)

    def run(self, resume_text: str, jd_text: str) -> JobPilotResult:
        if not resume_text.strip() or not jd_text.strip():
            raise ValueError("简历与 JD 不能为空。")
        mode = "model" if has_dashscope_key() else "rules"
        logs = ["Supervisor：候选人与岗位画像、岗位分类并行执行。"]
        with ThreadPoolExecutor(max_workers=2, thread_name_prefix="jobpilot") as pool:
            profile = pool.submit(self._execute, "ProfileAgent", lambda: self.profile_agent.run(resume_text, jd_text), mode)
            classifier = pool.submit(self._execute, "JobClassifierAgent", lambda: self.job_classifier_agent.run(jd_text), "rules")
            (resume_info, jd_info), profile_trace = profile.result()
            classification, classifier_trace = classifier.result()
        traces = [profile_trace, classifier_trace]
        logs.append(f"岗位方向：{classification.domain}；{classification.reason}")

        retrieval, trace = self._execute("KnowledgeAgent", lambda: self.knowledge_agent.retrieve(jd_info, jd_text, classification), "retrieval")
        traces.append(trace)
        logs.append(f"KnowledgeAgent：{retrieval.status}，检索到 {len(retrieval.chunks)} 段岗位知识。")
        context = retrieval.context if retrieval.has_context else "知识库没有相关参考；只能依据简历与 JD 评估。"
        match, trace = self._execute("EvaluationAgent", lambda: self.evaluation_agent.run(resume_info, jd_info, context, classification), "rules")
        traces.append(trace)

        gaps = [item for item in match.evidence_items if item.status != "matched"]
        max_queries = min(3, max(0, int(self.config.get("max_gap_queries", 2))))
        if gaps and max_queries:
            retrieval, trace = self._execute("GapKnowledgeAgent", lambda: self.knowledge_agent.supplement(retrieval, match, classification, max_queries), "retrieval")
            trace.message = f"针对前 {min(len(gaps), max_queries)} 项能力证据缺口补充检索，未重复评分。"
            traces.append(trace)
        else:
            traces.append(AgentTrace(stage="GapKnowledgeAgent", status="skipped", mode="retrieval", message="无待补充缺口或已关闭补充检索。"))
        context = retrieval.context if retrieval.has_context else "知识库没有相关参考；不推断额外经历。"
        (rewrite, report), trace = self._execute("CoachAgent", lambda: self.coach_agent.run(resume_info, jd_info, match, context, classification), mode)
        traces.append(trace)
        warnings = [warning for trace in traces for warning in trace.warnings]
        if not retrieval.has_context:
            warnings.append("知识库未命中，本次报告仅依据简历和 JD 生成。")
        logs.extend(f"{trace.stage}：{trace.status} / {trace.mode} / {trace.duration_ms:.0f} ms；{trace.message}" for trace in traces)
        logs.extend(warnings)
        return JobPilotResult(
            resume_info=resume_info, jd_info=jd_info, job_classification=classification,
            match_result=match, rewrite_result=rewrite, markdown_report=report, agent_logs=logs,
            agent_traces=traces, retrieval_status=retrieval.status,
            knowledge_evidence=[KnowledgeEvidence(**asdict(chunk)) for chunk in retrieval.chunks], warnings=warnings,
        )
