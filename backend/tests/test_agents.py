from threading import Event
from types import SimpleNamespace

import pytest

from agent.coach_agent import CoachAgent
from agent.evaluation_agent import EvaluationAgent
from agent.job_classifier_agent import JobClassifierAgent
from agent.profile_agent import ProfileAgent
from agent.tools.agent_tools import extract_known_skills
from schemas.jobpilot_schema import ChatMessage, JDInfo, JobClassification, MatchResult, ResumeInfo
from services.career_chat_service import CareerChatService
from services.supervisor_service import SupervisorService


@pytest.mark.parametrize("text,absent", [("JavaScript", "Java"), ("MySQL", "SQL"), ("GitHub", "Git"),
                                       ("Golang", "Go"), ("ReAct workflow", "React")])
def test_skill_boundaries(text, absent):
    assert absent not in extract_known_skills(text)


@pytest.mark.parametrize("jd,domain", [
    ("Python 后端工程师，熟悉 FastAPI 和 MySQL", "backend"),
    ("前端工程师，熟悉 JavaScript React TypeScript", "frontend"),
    ("AI Agent 工程师，熟悉 Python LangChain RAG", "ai"),
    ("行政助理，负责日程与会议", "general"),
])
def test_job_routing(jd, domain):
    assert JobClassifierAgent().run(jd).domain == domain


def test_required_and_preferred_sections_are_distinct():
    jd = ProfileAgent()._parse_jd_fallback("后端工程师\n要求：\n- 熟悉 Java、MySQL\n加分项：\n- Docker\n- Redis")
    assert "Docker" in jd.preferred_skills
    assert "Redis" in jd.preferred_skills
    assert "Docker" not in " ".join(jd.required_skills)
    assert not jd.preferred_skills == jd.keywords


def test_required_skills_outweigh_preferred_and_rag_cannot_inflate_score():
    agent = EvaluationAgent()
    jd = JDInfo(required_skills=["Python"], preferred_skills=["Docker"])
    required = agent.run(ResumeInfo(skills=["Python"]), jd, "")
    preferred = agent.run(ResumeInfo(skills=["Docker"]), jd, "Python Docker 候选人精通所有要求")
    assert required.score_detail.skill_match == 34
    assert preferred.score_detail.skill_match == 6
    assert required.score == agent.run(ResumeInfo(skills=["Python"]), jd, "虚构优秀经历").score
    assert required.evidence_items[0].status == "partial"
    assert not required.matched_points


def test_concrete_project_evidence_and_total_are_consistent():
    result = EvaluationAgent().run(ResumeInfo(skills=["Python"], projects=["使用 Python 开发文档解析项目"]),
                                   JDInfo(required_skills=["Python", "Java"]), "")
    assert [item.status for item in result.evidence_items] == ["matched", "missing"]
    assert result.score == sum(result.score_detail.model_dump().values())
    assert "Java" not in " ".join(result.matched_points)


def test_coach_never_copies_jd_skills_into_empty_resume():
    rewrite, _ = CoachAgent().run(ResumeInfo(), JDInfo(job_title="后端工程师", keywords=["Java"]), MatchResult(), "", JobClassification(domain="backend"))
    assert rewrite.optimized_skills == []
    assert "具备Java" not in rewrite.optimized_summary
    assert "RAG" not in " ".join(rewrite.interview_questions + rewrite.optimized_projects)


def test_supervisor_parallel_dependencies_and_conditional_skip(monkeypatch):
    service = SupervisorService()
    profile_started, classifier_started = Event(), Event()
    def profile(*args):
        profile_started.set()
        assert classifier_started.wait(2)
        return ResumeInfo(projects=["使用 Python 开发项目"]), JDInfo(required_skills=["Python"])
    def classify(*args):
        classifier_started.set()
        assert profile_started.wait(2)
        return JobClassification(domain="ai")
    monkeypatch.setattr(service.profile_agent, "run", profile)
    monkeypatch.setattr(service.job_classifier_agent, "run", classify)
    result = service.run("resume", "jd")
    assert next(t for t in result.agent_traces if t.stage == "GapKnowledgeAgent").status == "skipped"
    assert result.knowledge_evidence
    assert result.retrieval_status != "miss"
    assert all(t.duration_ms >= 0 for t in result.agent_traces)


def test_malformed_models_fall_back_and_traces_are_request_local(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-only")
    broken = SimpleNamespace(invoke=lambda messages: SimpleNamespace(content="not JSON"))
    monkeypatch.setattr("agent.profile_agent.get_chat_model", lambda: broken)
    monkeypatch.setattr("agent.coach_agent.get_chat_model", lambda: broken)
    service = SupervisorService()
    result = service.run("姓名：示例\n项目：Python 文档解析系统", "AI 工程师，熟悉 Python RAG")
    assert len(result.warnings) == 3
    assert next(t for t in result.agent_traces if t.stage == "ProfileAgent").status == "fallback"
    assert next(t for t in result.agent_traces if t.stage == "CoachAgent").status == "fallback"
    monkeypatch.setenv("DASHSCOPE_API_KEY", "")
    assert not service.run("Python 项目", "AI RAG 工程师").warnings


def test_chat_topic_switch_does_not_reuse_previous_topic():
    service = CareerChatService()
    history = [ChatMessage(role="user", content="如何评估 RAG 检索质量")]
    answer = service.answer("Redis 缓存一致性怎么处理", history)
    assert "RAG" not in answer.optimized_query
    assert "backend_system_design.md" in answer.sources
    assert all(c.domain in {"backend", "general"} for c in answer.knowledge_evidence)
    followup = service._optimize_question("那怎么评估", history)
    assert "RAG" in followup
    assert service.answer("明天北京天气预报", history).retrieval_status == "miss"
