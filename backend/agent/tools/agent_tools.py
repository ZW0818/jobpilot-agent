import json
import re
from typing import Any


COMMON_SKILLS = [
    "Python",
    "Java",
    "FastAPI",
    "Django",
    "Flask",
    "Spring Boot",
    "LangChain",
    "RAG",
    "LLM",
    "Agent",
    "MCP",
    "React",
    "Vue",
    "TypeScript",
    "JavaScript",
    "SQL",
    "MySQL",
    "PostgreSQL",
    "Redis",
    "Kafka",
    "Docker",
    "Kubernetes",
    "Linux",
    "Git",
    "PyTorch",
    "TensorFlow",
    "Chroma",
    "FAISS",
    "Prompt Engineering",
    "Tool Calling",
    "Embedding",
    "Webpack",
    "Vite",
]


def clean_json_text(text: str) -> str:
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    match = re.search(r"\{.*\}", cleaned, flags=re.DOTALL)
    return match.group(0) if match else cleaned


def parse_json_object(text: str, default: dict[str, Any] | None = None) -> dict[str, Any]:
    try:
        parsed = json.loads(clean_json_text(text))
    except json.JSONDecodeError:
        return default or {}
    return parsed if isinstance(parsed, dict) else (default or {})


def parse_json_output(text: str) -> dict[str, Any]:
    parsed = parse_json_object(text)
    if not parsed:
        raise ValueError(f"Model did not return valid JSON: {(text or '')[:300]}")
    return parsed


def unique_preserve_order(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        value = str(item).strip()
        key = value.lower()
        if value and key not in seen:
            seen.add(key)
            result.append(value)
    return result


def extract_known_skills(text: str) -> list[str]:
    lowered = (text or "").lower()
    hits = [skill for skill in COMMON_SKILLS if skill.lower() in lowered]
    return unique_preserve_order(hits)


def extract_bullets(text: str, limit: int = 8) -> list[str]:
    candidates: list[str] = []
    for raw_line in (text or "").splitlines():
        line = raw_line.strip().lstrip("-*0123456789. ")
        if len(line) >= 8:
            candidates.append(line)
    if not candidates:
        candidates = [part.strip() for part in re.split(r"[.!?\n]+", text or "") if len(part.strip()) >= 8]
    return unique_preserve_order(candidates)[:limit]


def summarize_text(text: str, max_chars: int = 220) -> str:
    compact = re.sub(r"\s+", " ", text or "").strip()
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3].rstrip() + "..."
