import re

from agent.tools.agent_tools import extract_known_skills

STOP_WORDS = {
    "how", "what", "the", "and", "for", "with", "is", "to", "of", "in",
    "如何", "怎么", "什么", "哪些", "求职", "问题", "相关", "可以", "应该", "需要", "准备",
    "一下", "请问", "一个", "以及", "进行", "是否", "能够", "中的", "这个", "关于", "有什么",
}


def tokenize(text: str) -> list[str]:
    """ASCII technology tokens and Chinese bigrams, without external tokenizers."""
    normalized = re.sub(r"\bReAct\b", "reason_act", text)
    terms = re.findall(r"[a-z][a-z0-9]*(?:[+#.\-/]+[a-z0-9+#]*)*", normalized.lower())
    chinese = re.sub("|".join(sorted((w for w in STOP_WORDS if re.search(r"[\u4e00-\u9fff]", w)), key=len, reverse=True)), " ", text)
    for phrase in re.findall(r"[\u4e00-\u9fff]{2,}", chinese):
        terms.extend(phrase[i:i + 2] for i in range(len(phrase) - 1))
    terms.extend(skill.lower() for skill in extract_known_skills(text))
    return [term for term in terms if term not in STOP_WORDS]
