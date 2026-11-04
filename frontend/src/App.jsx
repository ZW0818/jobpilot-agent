import { useState } from "react";
import { analyzeJob } from "./api";
import UploadPanel from "./components/UploadPanel";
import ScoreCard from "./components/ScoreCard";
import AgentTimeline from "./components/AgentTimeline";
import ResultTabs from "./components/ResultTabs";
import CareerChatPanel from "./components/CareerChatPanel";

const SAMPLE_JD = `岗位：AI Agent 应用开发工程师
职责：
- 构建 LangChain Agent 与 RAG 应用。
- 开发 FastAPI 服务，设计工具调用和结构化输出。
要求：
- 熟悉 Python、FastAPI、LangChain、RAG 和向量数据库。
- 能用测试集验证检索质量，处理模型调用失败。
加分项：
- 有 Docker 部署和端到端应用交付经验。`;

const VIEWS = [
  { id: "workspace", label: "岗位匹配", description: "把目标岗位的要求，与简历中的实际证据逐项对照。", path: "M4 5h16v14H4z M8 3v4 M16 3v4 M8 11h8 M8 15h5" },
  { id: "report", label: "分析报告", description: "核对匹配依据、能力缺口与简历改写建议。", path: "M7 3h7l4 4v14H7z M14 3v5h4 M10 12h5 M10 16h5" },
  { id: "chat", label: "求职问答", description: "从岗位准备到项目表达，结合知识资料继续追问。", path: "M4 4h16v12H9l-5 4z M8 8h8 M8 12h5" },
];

function downloadMarkdown(markdown) {
  const url = URL.createObjectURL(new Blob([markdown], { type: "text/markdown;charset=utf-8" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "jobpilot_report.md";
  anchor.click();
  URL.revokeObjectURL(url);
}

export default function App() {
  const [activeView, setActiveView] = useState("workspace");
  const [resumeFile, setResumeFile] = useState(null);
  const [jdText, setJdText] = useState("");
  const [result, setResult] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [updatedAt, setUpdatedAt] = useState(null);
  const view = VIEWS.find((item) => item.id === activeView);
  const canAnalyze = Boolean(resumeFile && jdText.trim() && !isLoading);
  const timestamp = updatedAt?.toLocaleTimeString("zh-CN", { timeZone: "Asia/Shanghai", hour: "2-digit", minute: "2-digit" });

  async function handleAnalyze() {
    if (!canAnalyze) return;
    setIsLoading(true);
    setError("");
    try {
      const nextResult = await analyzeJob(resumeFile, jdText);
      setResult(nextResult);
      setUpdatedAt(new Date());
    } catch (requestError) {
      const detail = requestError?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : requestError.message || "分析失败，请检查后端服务后重试。");
    } finally {
      setIsLoading(false);
    }
  }

  function useSample() {
    setJdText(SAMPLE_JD);
    document.getElementById("jd-text")?.focus();
  }

  return (
    <div className="app-frame">
      <a className="skip-link" href="#main-content">跳转到工作区</a>
      <aside className="navigation-rail" aria-label="应用导航">
        <a className="product-mark" href="#workspace" onClick={() => setActiveView("workspace")} aria-label="JobPilot 首页" title="JobPilot">
          <svg viewBox="0 0 28 28" fill="none" aria-hidden="true"><path d="M4 5 24 13 15 16 11 24 4 5Z" stroke="currentColor" strokeWidth="1.7" strokeLinejoin="round"/><path d="m4 5 11 11" stroke="currentColor" strokeWidth="1.7"/></svg>
        </a>
        <nav>
          {VIEWS.map((item) => (
            <button key={item.id} className={`nav-item ${activeView === item.id ? "selected" : ""}`} aria-current={activeView === item.id ? "page" : undefined} onClick={() => setActiveView(item.id)} title={item.label} type="button">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true"><path d={item.path}/></svg>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>
        <span className="rail-caption" aria-hidden="true">JP</span>
      </aside>

      <main className="app-shell" id="main-content" tabIndex={-1}>
        <header className="workspace-bar">
          <a className="wordmark" href="#workspace" onClick={() => setActiveView("workspace")}>JobPilot<span>求职工作区</span></a>
          <span className="workspace-scope">简历 · 岗位 · 证据</span>
        </header>
        <div className="page-heading">
          <div><h1>{view.label}</h1><p>{view.description}</p></div>
          {activeView === "report" ? (
            <button className="secondary-action" disabled={!result?.markdown_report} onClick={() => downloadMarkdown(result.markdown_report)} type="button">下载 Markdown</button>
          ) : timestamp ? <span className="freshness">上次生成 {timestamp}</span> : <span className="freshness">尚未提交分析</span>}
        </div>

        <div hidden={activeView !== "workspace"}>
          <section className="workspace-grid" aria-busy={isLoading} aria-label="岗位匹配工作台">
            <div className="materials-column">
              <UploadPanel resumeFile={resumeFile} jdText={jdText} isLoading={isLoading} canAnalyze={canAnalyze} onFileChange={setResumeFile} onJdChange={setJdText} onAnalyze={handleAnalyze} onUseSample={useSample} error={error}/>
              <div className="report-entry">
                <div><strong>{result ? "本次分析报告已就绪" : "从要求到证据，再到行动"}</strong><p>{result ? "查看逐项匹配、优化建议、面试问题与知识来源。" : "匹配结果会同时保留岗位要求、简历依据和下一步建议。"}</p></div>
                <button className="text-action" type="button" onClick={() => setActiveView("report")}>{result ? "查看报告" : "报告工作区"}<span aria-hidden="true"> →</span></button>
              </div>
            </div>
            <aside className="insight-rail" aria-label="匹配结果摘要">
              <ScoreCard result={result?.match_result} jobClassification={result?.job_classification} isLoading={isLoading}/>
              <AgentTimeline logs={result?.agent_logs} traces={result?.agent_traces} isLoading={isLoading}/>
            </aside>
          </section>
        </div>

        <section hidden={activeView !== "report"} aria-label="分析报告内容">
          {!result && !isLoading ? (
            <div className="empty-report"><h2>还没有分析报告</h2><p>上传一份简历和目标岗位 JD，生成带匹配证据的求职分析。</p><button className="primary-action" onClick={() => setActiveView("workspace")} type="button">添加分析材料</button></div>
          ) : <ResultTabs result={result} isLoading={isLoading}/>}
        </section>
        <div hidden={activeView !== "chat"}><CareerChatPanel/></div>
        <footer className="workspace-footer"><span>JobPilot</span><span>建议基于真实经历修改，评分供投递准备参考。</span></footer>
      </main>
    </div>
  );
}
