# JobPilot Agent

JobPilot is a multi-agent job matching MVP built with FastAPI, LangChain-style
agent orchestration, local RAG knowledge, a React UI, and an optional MCP tool
server.

## Features

- Upload a resume file.
- Paste a target job description.
- Parse resume and JD into structured JSON.
- Retrieve local career knowledge for RAG context.
- Classify the job direction as AI, backend, frontend, or general.
- Calculate a match score, score breakdown, skill gaps, and evidence table.
- Generate resume rewrite suggestions and interview questions.
- Render and download a Markdown report.
- Run an optional local MCP server for match scoring and Markdown export demos.

## Tech Stack

- Backend: Python, FastAPI, Pydantic, LangChain-compatible DashScope factory.
- RAG: local text knowledge files with optional Chroma vector retrieval.
- Frontend: Vite, React, Axios, React Markdown.
- Extension: MCP Python SDK.

## Backend

```bash
cd jobpilot-agent/backend
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload --port 8000
```

Set `DASHSCOPE_API_KEY` in `.env` to enable LLM calls. Without a key, JobPilot
uses deterministic fallback agents so the API and UI can still be tested.

The analysis response keeps the original `score`, `level`, `matched_points`,
`missing_points`, and `suggestions` fields, and also includes:

- `job_classification`: rule-based job direction, confidence, and reason.
- `match_result.score_detail`: skill, project, engineering, and resume-quality scores.
- `match_result.evidence_items`: JD requirement, resume evidence, status, and suggestion.

## Frontend

```bash
cd jobpilot-agent/frontend
npm install
npm run dev
```

Open `http://localhost:5173`.

## Optional MCP

```bash
cd jobpilot-agent/backend
python mcp_server/server.py
```

MCP is an optional extension layer. The main analysis flow does not depend on
external MCP services or paid third-party keys.

## Security

Do not commit `.env`. API keys are read from environment variables only and are
not stored in YAML configuration files.
