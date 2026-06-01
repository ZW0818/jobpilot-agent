const LOADING_LOGS = [
  "ProfileAgent 正在解析简历与岗位 JD，生成候选人与岗位画像。",
  "KnowledgeAgent 正在检索本地求职知识库，补充评估依据。",
  "EvaluationAgent 正在计算匹配评分，并归纳优势与能力缺口。",
  "CoachAgent 正在生成简历优化、面试准备题和 Markdown 报告。",
];

export default function AgentTimeline({ logs = [], isLoading = false }) {
  const hasLogs = Boolean(logs?.length);
  const items = hasLogs ? logs : isLoading ? LOADING_LOGS : [];
  const statusText = isLoading ? "分析进行中" : hasLogs ? "链路已完成" : "等待启动";

  return (
    <section className="timeline-card">
      <div className="card-heading">
        <p className="section-kicker">智能体链路</p>
        <h3>执行过程</h3>
      </div>

      <div className="timeline-summary">
        <span>{statusText}</span>
        <small>{items.length ? `共 ${items.length} 个节点` : "提交材料后开始编排"}</small>
      </div>

      {items.length ? (
        <ol className="agent-timeline">
          {items.map((log, index) => {
            const itemState = isLoading && index === 0 ? "active" : hasLogs ? "done" : "";
            return (
              <li className={itemState} key={`${log}-${index}`}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <p>{log}</p>
              </li>
            );
          })}
        </ol>
      ) : (
        <div className="empty-state compact">
          <strong>暂无执行日志</strong>
          <span>完成一次分析后，这里会展示四角色多智能体协作过程。</span>
        </div>
      )}
    </section>
  );
}
