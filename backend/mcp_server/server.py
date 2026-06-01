try:
    from mcp.server.fastmcp import FastMCP
except ImportError:  # pragma: no cover
    FastMCP = None


def calculate_match_score(candidate_skills: list[str], jd_skills: list[str]) -> dict:
    if not jd_skills:
        return {"score": 0, "matched": []}
    candidate = {skill.lower().replace(" ", "") for skill in candidate_skills}
    matched = [skill for skill in jd_skills if skill.lower().replace(" ", "") in candidate]
    return {"score": round(len(matched) / len(jd_skills) * 100), "matched": matched}


def export_markdown_report(markdown: str) -> str:
    path = "jobpilot_report.md"
    with open(path, "w", encoding="utf-8") as file:
        file.write(markdown)
    return path


if FastMCP:
    mcp = FastMCP("jobpilot-mcp")
    mcp.tool()(calculate_match_score)
    mcp.tool()(export_markdown_report)
else:
    mcp = None


if __name__ == "__main__":
    if mcp is None:
        print("Install mcp to run this optional server: pip install mcp")
    else:
        mcp.run()
