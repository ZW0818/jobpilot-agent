# JobPilot Agent

JobPilot Agent 是一个面向求职场景的多智能体简历匹配 MVP。它可以根据上传的简历和目标岗位 JD，完成岗位方向识别、简历信息解析、匹配度评分、能力差距分析、改写建议生成，并输出可下载的 Markdown 分析报告。

项目后端基于 FastAPI，结合 LangChain 风格的 Agent 编排、本地 RAG 知识库和可选 MCP 工具服务；前端基于 Vite + React，提供简历上传、JD 输入、结果展示和报告下载能力。

## 核心功能

- 上传简历文件并提取可读文本。
- 粘贴目标岗位 JD，解析岗位要求和关键词。
- 将简历和 JD 结构化为 JSON 数据。
- 基于本地职业知识文件检索 RAG 上下文。
- 自动识别岗位方向：AI、后端、前端或通用岗位。
- 计算综合匹配分、分项得分、匹配证据和能力缺口。
- 生成简历摘要、技能、项目经历的优化建议。
- 生成面试问题和 Markdown 格式分析报告。
- 提供职业问答接口，用于基于知识库回答求职相关问题。
- 可选运行本地 MCP Server，用于匹配评分和 Markdown 导出演示。

## 技术栈

- 后端：Python、FastAPI、Pydantic、DashScope 兼容模型工厂。
- Agent：多 Agent 编排、规则兜底、简历解析、岗位分类、匹配评估、改写建议。
- RAG：本地文本知识文件，支持可选 Chroma 向量检索。
- 前端：Vite、React、Axios、React Markdown。
- 扩展：MCP Python SDK。

## 项目结构

```text
jobpilot-agent/
|-- backend/
|   |-- agent/          # 各类 Agent 与工具逻辑
|   |-- api/            # FastAPI 路由
|   |-- config/         # 模型与配置读取
|   |-- data/           # 本地 RAG 知识文件
|   |-- mcp_server/     # 可选 MCP 服务
|   |-- rag/            # 知识检索服务
|   |-- schemas/        # Pydantic 数据模型
|   |-- services/       # 业务编排服务
|   `-- main.py         # 后端入口
|-- frontend/
|   |-- src/            # React 应用源码
|   |-- package.json
|   `-- vite.config.js
`-- README.md
```

## 后端启动

```bash
cd backend
pip install -r requirements.txt
copy .env.example .env
uvicorn main:app --reload --port 8000
```

如果在 PowerShell 中复制环境变量文件，也可以使用：

```powershell
Copy-Item .env.example .env
```

在 `backend/.env` 中配置 `DASHSCOPE_API_KEY` 后，系统会调用大模型能力。未配置 API Key 时，项目会使用确定性的兜底 Agent，因此仍然可以启动后端、联调接口和体验前端主流程。

后端启动后可访问：

- 健康检查：`http://localhost:8000/`
- Swagger 文档：`http://localhost:8000/docs`
- 简历分析接口：`POST /api/analyze`
- 职业问答接口：`POST /api/chat`

## 前端启动

```bash
cd frontend
npm install
npm run dev
```

默认访问地址：

```text
http://localhost:5173
```

前端会请求本地后端服务，请确保后端已经运行在 `http://localhost:8000`。

## 环境变量

后端示例配置位于 `backend/.env.example`：

```env
DASHSCOPE_API_KEY=your api-key
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
DASHSCOPE_CHAT_MODEL=qwen3.7-plus
DASHSCOPE_EMBEDDING_MODEL=tongyi-embedding-vision-plus-2026-03-06
```

说明：

- `DASHSCOPE_API_KEY`：DashScope API Key，用于启用真实大模型调用。
- `DASHSCOPE_BASE_URL`：DashScope 兼容模式接口地址。
- `DASHSCOPE_CHAT_MODEL`：聊天和分析任务使用的模型名称。
- `DASHSCOPE_EMBEDDING_MODEL`：向量检索使用的 Embedding 模型名称。

## 分析结果字段

`/api/analyze` 的响应保留基础匹配字段：

- `score`：综合匹配分。
- `level`：匹配等级。
- `matched_points`：已匹配优势。
- `missing_points`：缺失能力点。
- `suggestions`：优化建议。

同时包含更细的分析信息：

- `job_classification`：岗位方向、置信度和判断原因。
- `match_result.score_detail`：技能匹配、项目相关性、工程能力、简历质量分项得分。
- `match_result.evidence_items`：JD 要求、简历证据、匹配状态和改进建议。
- `rewrite_result`：简历摘要、技能、项目经历优化建议和面试问题。
- `markdown_report`：可下载或渲染展示的 Markdown 报告。
- `agent_logs`：Agent 执行过程日志。

## 可选 MCP 服务

```bash
cd backend
python mcp_server/server.py
```

MCP 是扩展层能力，主分析流程不依赖外部 MCP 服务，也不强制依赖付费第三方 Key。

## 安全说明

- 不要提交 `.env` 文件。
- API Key 仅从环境变量读取，不写入 YAML 或代码文件。
- 简历内容通常包含个人隐私，演示和测试时建议使用脱敏样例。
