from __future__ import annotations

from dataclasses import dataclass

from schemas.jobpilot_schema import JobClassification


@dataclass(frozen=True)
class DomainRule:
    domain: str
    keywords: tuple[str, ...]


DOMAIN_RULES = (
    DomainRule(
        domain="ai",
        keywords=(
            "Python",
            "PyTorch",
            "TensorFlow",
            "深度学习",
            "机器学习",
            "RAG",
            "Agent",
            "LLM",
            "NLP",
            "CV",
            "计算机视觉",
            "Embedding",
            "向量数据库",
            "LangChain",
            "Prompt Engineering",
        ),
    ),
    DomainRule(
        domain="backend",
        keywords=(
            "Java",
            "Spring Boot",
            "MySQL",
            "Redis",
            "Kafka",
            "微服务",
            "接口",
            "分布式",
            "高并发",
            "数据库",
            "FastAPI",
        ),
    ),
    DomainRule(
        domain="frontend",
        keywords=(
            "React",
            "Vue",
            "TypeScript",
            "JavaScript",
            "组件",
            "前端",
            "页面",
            "状态管理",
            "Webpack",
            "Vite",
        ),
    ),
)


class JobClassifierAgent:
    """Classify the target job direction with small deterministic rules."""

    def run(self, jd_text: str) -> JobClassification:
        lowered = (jd_text or "").lower()
        scores: dict[str, list[str]] = {}

        for rule in DOMAIN_RULES:
            hits = [keyword for keyword in rule.keywords if keyword.lower() in lowered]
            scores[rule.domain] = hits

        domain, hits = max(scores.items(), key=lambda item: (len(item[1]), item[0] == "ai"))
        if not hits:
            return JobClassification(
                domain="general",
                confidence=0.35,
                reason="JD 中未命中明确的 AI、后端或前端关键词，按通用岗位处理。",
            )

        confidence = min(0.95, round(0.55 + len(hits) * 0.08, 2))
        return JobClassification(
            domain=domain,
            confidence=confidence,
            reason=f"JD 中包含 {', '.join(hits[:6])} 等关键词。",
        )
