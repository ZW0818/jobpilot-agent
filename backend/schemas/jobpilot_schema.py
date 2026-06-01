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


class MatchResult(BaseModel):
    score: int = Field(default=0, ge=0, le=100)
    level: str = ""
    matched_points: list[str] = Field(default_factory=list)
    missing_points: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class RewriteResult(BaseModel):
    optimized_summary: str = ""
    optimized_skills: list[str] = Field(default_factory=list)
    optimized_projects: list[str] = Field(default_factory=list)
    interview_questions: list[str] = Field(default_factory=list)


class JobPilotResult(BaseModel):
    resume_info: ResumeInfo
    jd_info: JDInfo
    match_result: MatchResult
    rewrite_result: RewriteResult
    markdown_report: str
    agent_logs: list[str] = Field(default_factory=list)
