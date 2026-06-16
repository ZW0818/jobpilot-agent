from pydantic import BaseModel, Field


class ResumeInfo(BaseModel):
    name: str = ""
    skills: list[str] = Field(default_factory=list)
    projects: list[str] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    experience: list[str] = Field(default_factory=list)
    summary: str = ""


class JDInfo(BaseModel):
    job_title: str = ""
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    summary: str = ""


class JobClassification(BaseModel):
    domain: str = Field(default="general", pattern="^(ai|backend|frontend|general)$")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reason: str = ""


class ScoreDetail(BaseModel):
    skill_match: int = Field(default=0, ge=0, le=40)
    project_relevance: int = Field(default=0, ge=0, le=30)
    engineering_ability: int = Field(default=0, ge=0, le=20)
    resume_quality: int = Field(default=0, ge=0, le=10)


class EvidenceItem(BaseModel):
    jd_requirement: str = ""
    resume_evidence: str = ""
    status: str = Field(default="missing", pattern="^(matched|partial|missing)$")
    suggestion: str = ""


class MatchResult(BaseModel):
    score: int = Field(default=0, ge=0, le=100)
    level: str = ""
    matched_points: list[str] = Field(default_factory=list)
    missing_points: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)
    score_detail: ScoreDetail = Field(default_factory=ScoreDetail)
    evidence_items: list[EvidenceItem] = Field(default_factory=list)


class RewriteResult(BaseModel):
    optimized_summary: str = ""
    optimized_skills: list[str] = Field(default_factory=list)
    optimized_projects: list[str] = Field(default_factory=list)
    interview_questions: list[str] = Field(default_factory=list)


class JobPilotResult(BaseModel):
    resume_info: ResumeInfo
    jd_info: JDInfo
    job_classification: JobClassification = Field(default_factory=JobClassification)
    match_result: MatchResult
    rewrite_result: RewriteResult
    markdown_report: str
    agent_logs: list[str] = Field(default_factory=list)


class ChatMessage(BaseModel):
    role: str = Field(default="user", pattern="^(user|assistant)$")
    content: str = Field(default="", max_length=2000)


class CareerChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)
    history: list[ChatMessage] = Field(default_factory=list, max_length=8)


class CareerChatResponse(BaseModel):
    answer: str
    optimized_query: str = ""
    retrieval_status: str = "miss"
    sources: list[str] = Field(default_factory=list)
    agent_logs: list[str] = Field(default_factory=list)
    used_model: bool = False
