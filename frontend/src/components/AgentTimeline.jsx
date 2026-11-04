const LABELS = { ProfileAgent: "画像解析", JobClassifierAgent: "岗位分类", KnowledgeAgent: "岗位知识检索", EvaluationAgent: "证据评分", GapKnowledgeAgent: "缺口知识补充", CoachAgent: "求职辅导" };
const MODES = { model: "模型", rules: "规则", retrieval: "检索" };
const STATUSES = { success: "完成", fallback: "已降级", skipped: "跳过" };

export default function AgentTimeline({ logs = [], traces = [], isLoading = false }) {
  return (
    <details className="timeline-card">
      <summary><span>执行记录</span><span>{isLoading ? "分析中" : traces.length ? `${traces.length} 个节点` : "尚未运行"}</span></summary>
      {isLoading ? <p className="timeline-description">完整执行记录会随报告返回。</p> : null}
      {traces.length ? <ol className="agent-timeline">{traces.map((trace) => <li key={trace.stage}><div><strong>{LABELS[trace.stage] || trace.stage}</strong><span>{Math.round(trace.duration_ms).toLocaleString("zh-CN")} ms</span></div><p>{MODES[trace.mode] || trace.mode} · {STATUSES[trace.status] || trace.status}</p>{trace.warnings?.map((warning) => <p className="trace-warning" key={warning}>{warning}</p>)}</li>)}</ol> : logs.length ? <ol className="agent-timeline">{logs.map((log, index) => <li key={index}>{log}</li>)}</ol> : <p className="timeline-description">完成分析后，可核对节点耗时、运行方式和降级原因。</p>}
    </details>
  );
}
