from __future__ import annotations

from dataclasses import dataclass

from agent.tools.agent_tools import contains_term
from schemas.jobpilot_schema import JobClassification


@dataclass(frozen=True)
class DomainRule:
    domain: str
    keywords: tuple[str, ...]


DOMAIN_RULES = (
    DomainRule(
        domain="ai",
        keywords=(
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
            "Django",
            "后端",
            "backend",
            "Golang",
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
        text = jd_text or ""
        title = next((line for line in text.splitlines() if line.strip()), "")
        scores: dict[str, list[str]] = {}

        for rule in DOMAIN_RULES:
            hits = [keyword for keyword in rule.keywords if contains_term(keyword, text)]
            scores[rule.domain] = hits

        title_terms = {"ai": ("AI", "人工智能", "算法", "大模型", "机器学习", "Agent"),
                       "backend": ("后端", "backend", "服务端"), "frontend": ("前端", "frontend")}
        weights = {domain: len(hits) + 4 * any(contains_term(t, title) for t in title_terms[domain])
                   for domain, hits in scores.items()}
        domain = max(weights, key=weights.get)
        hits = scores[domain]
        if not hits and weights[domain]:
            hits = [term for term in title_terms[domain] if contains_term(term, title)]
        if not hits:
            return JobClassification(
                domain="general",
                confidence=0.35,
                reason="JD 中未命中明确的 AI、后端或前端关键词，按通用岗位处理。",
            )

        total = sum(weights.values())
        confidence = min(0.95, round(0.45 + 0.5 * weights[domain] / max(total, 1), 2))
        return JobClassification(
            domain=domain,
            confidence=confidence,
            reason=f"JD 中包含 {', '.join(hits[:6])} 等关键词。",
        )
