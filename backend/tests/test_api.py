from fastapi.testclient import TestClient

from main import app


def test_analyze_and_chat_contracts_offline():
    with TestClient(app) as client:
        response = client.post("/api/analyze", files={"resume_file": ("resume.txt", "示例\n项目：使用 React TypeScript 实现前端页面与状态管理。".encode(), "text/plain")},
                               data={"jd_text": "前端工程师\n要求：熟悉 React、TypeScript"})
        assert response.status_code == 200
        data = response.json()
        assert data["job_classification"]["domain"] == "frontend"
        assert data["agent_logs"] and data["agent_traces"] and data["knowledge_evidence"]
        assert "frontend_engineering.md" in data["markdown_report"]
        assert client.post("/api/chat", json={"question": "没有实习经历怎么写简历"}).json()["knowledge_evidence"]
        assert client.post("/api/chat", json={"question": "  "}).status_code == 400
        assert client.post("/api/analyze", files={"resume_file": ("empty.txt", b"", "text/plain")}, data={"jd_text": "JD"}).status_code == 400
