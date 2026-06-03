import { useMemo, useState } from "react";
import { analyzeJob } from "./api";
import UploadPanel from "./components/UploadPanel";
import ScoreCard from "./components/ScoreCard";
import AgentTimeline from "./components/AgentTimeline";
import ResultTabs from "./components/ResultTabs";

const SAMPLE_JD = `岗位：AI Agent 应用开发工程师
职责：
- 构建 LangChain Agent 与 RAG 应用。
- 开发 FastAPI 后端服务与 React 前端界面。
- 设计 Tool Calling、结构化输出和本地知识库检索能力。
要求：
- 熟悉 Python、FastAPI、LangChain、RAG、Chroma、React、Prompt Engineering。
- 有端到端 AI 应用交付经验优先。
加分项：
- 了解简历解析、岗位画像、候选人评估等招聘场景。
- 能把模型能力封装成稳定可复用的产品功能。`;

function buildErrorMessage(error) {
  const detail = error?.response?.data?.detail;
  if (detail) {
    return typeof detail === "string" ? detail : JSON.stringify(detail);
  }
  return error?.message || "分析请求失败，请确认本地后端服务已启动。";
}

function downloadMarkdown(markdown) {
  const blob = new Blob([markdown || ""], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "jobpilot_report.md";
  anchor.click();
  URL.revokeObjectURL(url);
}

export default function App() {
  const [resumeFile, setResumeFile] = useState(null);
  const [jdText, setJdText] = useState("");
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const canAnalyze = Boolean(resumeFile && jdText.trim() && !isLoading);
  const match = useMemo(() => result?.match_result || {}, [result]);
  const hasResult = Boolean(result);
  const matchedCount = match.matched_points?.length || 0;
  const missingCount = match.missing_points?.length || 0;
  const heroStatus = isLoading ? "正在分析" : hasResult ? match.level || "已生成报告" : "等待分析";
  const heroScore = hasResult ? match.score ?? "--" : "--";

  async function handleAnalyze() {
    if (!resumeFile || !jdText.trim()) {
      setError("请先上传简历文件，并粘贴完整的目标岗位 JD。");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      setResult(await analyzeJob(resumeFile, jdText));
    } catch (requestError) {
      setError(buildErrorMessage(requestError));
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-mark">
          <span className="brand-logo">职</span>
          <div>
            <strong>JobPilot 求职分析台</strong>
            <small>多智能体岗位匹配系统</small>
          </div>
        </div>
        <div className="topbar-status">
          <span className="live-dot" />
          本地后端服务
        </div>
      </header>

      <section className="hero-section">
        <div className="hero-copy">
          <div className="eyebrow">
            <span className="status-dot" />
            多智能体求职决策系统
          </div>
          <h1>把简历和岗位 JD，转化为一份可行动的匹配分析报告。</h1>
          <p>
            JobPilot 会串联 ProfileAgent、KnowledgeAgent、EvaluationAgent 与 CoachAgent 四个角色，
            帮你判断是否值得投递，并明确投递前应该补强什么。
          </p>

          <div className="hero-actions">
            <a className="hero-link primary-link" href="#workspace">
              开始分析
            </a>
            <button className="hero-link subtle-link" onClick={() => setJdText(SAMPLE_JD)} type="button">
              使用示例岗位
            </button>
          </div>

          <div className="hero-metrics" aria-label="产品能力">
            <span>候选人画像</span>
            <span>岗位要求拆解</span>
            <span>匹配证据归纳</span>
            <span>匹配评分</span>
            <span>投递策略建议</span>
          </div>
        </div>

        <aside className="hero-card" aria-label="分析状态">
          <div className="orbit-card">
            <div className="radar-ring">
              <span>{isLoading ? "..." : heroScore}</span>
            </div>
            <p>{heroStatus}</p>
          </div>
          <div className="hero-mini-grid">
            {hasResult ? (
              <>
                <span>{matchedCount} 项优势</span>
                <span>{missingCount} 项缺口</span>
              </>
            ) : (
              <>
                <span>4 个智能体角色</span>
                <span>1 份求职报告</span>
              </>
            )}
          </div>
        </aside>
      </section>

      <section className="process-strip" aria-label="分析流程">
        <span>01 上传简历</span>
        <span>02 粘贴岗位 JD</span>
        <span>03 多智能体分析</span>
        <span>04 查看报告与建议</span>
      </section>

      <section aria-busy={isLoading} className="workspace-grid" id="workspace">
        <UploadPanel
          resumeFile={resumeFile}
          jdText={jdText}
          isLoading={isLoading}
          canAnalyze={canAnalyze}
          onFileChange={setResumeFile}
          onJdChange={setJdText}
          onAnalyze={handleAnalyze}
          onUseSample={() => setJdText(SAMPLE_JD)}
        />

        <aside className="insight-rail">
          <ScoreCard
            result={result?.match_result}
            jobClassification={result?.job_classification}
            isLoading={isLoading}
          />
          <AgentTimeline logs={result?.agent_logs} isLoading={isLoading} />
        </aside>
      </section>

      {error ? (
        <div className="error-banner" role="alert">
          <strong>分析失败</strong>
          <span>{error}</span>
        </div>
      ) : null}

      <section className="results-section">
        <div className="section-heading">
          <div>
            <p className="section-kicker">分析结果</p>
            <h2>求职匹配结果</h2>
          </div>
          <button
            className="secondary-action"
            disabled={!result?.markdown_report}
            onClick={() => downloadMarkdown(result?.markdown_report)}
            title={result?.markdown_report ? "下载完整分析报告" : "分析完成后可下载报告"}
            type="button"
          >
            下载分析报告
          </button>
        </div>
        <ResultTabs result={result} isLoading={isLoading} />
      </section>
    </main>
  );
}
