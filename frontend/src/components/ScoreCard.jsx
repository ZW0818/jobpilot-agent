function getScoreTone(score) {
  if (score >= 85) return "excellent";
  if (score >= 70) return "good";
  if (score >= 50) return "medium";
  return "low";
}

function getScoreAdvice(score, hasResult) {
  if (!hasResult) return "完成一次分析后，这里会展示岗位匹配指数与投递建议。";
  if (score >= 85) return "匹配度很高，建议优先投递，并在简历中突出与岗位强相关的项目成果。";
  if (score >= 70) return "具备较好的投递基础，建议先补强关键缺口再投递。";
  if (score >= 50) return "存在一定匹配基础，但需要围绕岗位要求重写摘要、技能和项目经历。";
  return "当前匹配度偏低，建议谨慎投递，优先补齐岗位核心能力或选择更贴合的岗位。";
}

export default function ScoreCard({ result, isLoading = false }) {
  const hasResult = Boolean(result);
  const score = Number(result?.score || 0);
  const level = result?.level || (isLoading ? "评估中..." : "暂无评分");
  const tone = getScoreTone(score);
  const matched = result?.matched_points || [];
  const missing = result?.missing_points || [];
  const suggestions = result?.suggestions || [];
  const advice = isLoading ? "正在综合简历信息、岗位要求和知识库证据，请稍候。" : getScoreAdvice(score, hasResult);

  return (
    <section className={`score-card ${tone}`}>
      <div className="card-heading">
        <p className="section-kicker">匹配评分</p>
        <h3>岗位匹配度</h3>
      </div>

      <div className="score-meter" style={{ "--score": `${score}%` }}>
        <div className="score-value">
          <strong>{isLoading ? "..." : score}</strong>
          <span>/100</span>
        </div>
      </div>

      <div className="score-level">{level}</div>
      <p className="score-advice">{advice}</p>

      <div className="score-points">
        <div>
          <span className="mini-label">优势</span>
          <strong>{matched.length}</strong>
        </div>
        <div>
          <span className="mini-label">缺口</span>
          <strong>{missing.length}</strong>
        </div>
        <div>
          <span className="mini-label">建议</span>
          <strong>{suggestions.length}</strong>
        </div>
      </div>

      {hasResult && (matched[0] || missing[0]) ? (
        <div className="score-evidence">
          {matched[0] ? (
            <p>
              <span>主要优势</span>
              {matched[0]}
            </p>
          ) : null}
          {missing[0] ? (
            <p>
              <span>优先补强</span>
              {missing[0]}
            </p>
          ) : null}
        </div>
      ) : null}
    </section>
  );
}
