const METRICS = [["skill_match", "核心技能", 40], ["project_relevance", "项目相关", 30], ["engineering_ability", "工程能力", 20], ["resume_quality", "表达完整", 10]];
const DOMAINS = { ai: "AI 应用", backend: "后端开发", frontend: "前端开发", general: "通用岗位" };

export default function ScoreCard({ result, jobClassification, isLoading = false }) {
  const hasResult = Boolean(result);
  const score = result?.score ?? 0;
  return (
    <section className="score-card" aria-busy={isLoading}>
      <div className="panel-heading"><h2>匹配概览</h2><span>{isLoading ? "更新中" : hasResult ? DOMAINS[jobClassification?.domain] || "通用岗位" : "待分析"}</span></div>
      <div className={`score-headline ${hasResult ? "" : "no-score"}`}><strong>{hasResult ? score : "—"}</strong>{hasResult ? <span>/ 100</span> : <span>提交材料后生成</span>}</div>
      <p className="score-level">{hasResult ? result.level : "先找到简历与岗位的连接点"}</p>
      <p className="score-advice">{isLoading ? "保留上次结果，报告完成后更新。" : "评分依据简历证据，知识资料只作为改进参考。"}</p>
      <div className="score-breakdown" aria-label="分项评分">
        {METRICS.map(([key, label, max]) => <div className="score-metric" key={key}><div><span>{label}</span><span className="metric-value">{hasResult ? result.score_detail?.[key] ?? 0 : "—"}<small> / {max}</small></span></div><div className="metric-track" aria-hidden="true"><span style={{ width: `${hasResult ? (result.score_detail?.[key] ?? 0) / max * 100 : 0}%` }}/></div></div>)}
      </div>
      <div className="score-counts">{[["已匹配", "matched_points"], ["待补强", "missing_points"], ["行动建议", "suggestions"]].map(([label, key]) => <div key={key}><span>{label}</span><strong>{hasResult ? result[key]?.length ?? 0 : "—"}</strong></div>)}</div>
      {hasResult ? <div className="score-evidence">{result.matched_points?.[0] ? <p><span>已覆盖</span>{result.matched_points[0]}</p> : null}{result.missing_points?.[0] ? <p><span>优先补强</span>{result.missing_points[0]}</p> : null}</div> : <div className="score-legend"><h3>证据判断方式</h3><dl><div><dt>已匹配</dt><dd>项目或工作经历中有明确佐证</dd></div><div><dt>部分覆盖</dt><dd>仅列出技能，或尚未覆盖完整要求</dd></div><div><dt>未找到证据</dt><dd>需要补充经历，不代表没有能力</dd></div></dl></div>}
    </section>
  );
}
