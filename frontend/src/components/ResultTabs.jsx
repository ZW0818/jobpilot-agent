import { useState } from "react";
import MarkdownPreview from "./MarkdownPreview";

const TABS = [
  { id: "markdown", label: "报告正文" },
  { id: "evidence", label: "匹配证据" },
  { id: "rewrite", label: "简历优化" },
  { id: "interview", label: "面试准备" },
  { id: "json", label: "原始数据" },
];

function normalizeList(items) {
  return Array.isArray(items) ? items : [];
}

function ListBlock({ title, items = [], emptyText, description }) {
  const normalizedItems = normalizeList(items);

  return (
    <section className="list-block">
      <div className="block-heading">
        <h3>{title}</h3>
        {description ? <p>{description}</p> : null}
      </div>
      {normalizedItems.length ? (
        <ul>
          {normalizedItems.map((item, index) => (
            <li key={`${title}-${index}`}>{item}</li>
          ))}
        </ul>
      ) : (
        <p className="muted-text">{emptyText}</p>
      )}
    </section>
  );
}

function EvidencePanel({ items = [] }) {
  const normalizedItems = normalizeList(items);

  if (!normalizedItems.length) {
    return (
      <section className="list-block">
        <div className="block-heading">
          <h3>匹配证据对照表</h3>
          <p>这里会展示岗位要求、简历证据、匹配状态和优化建议。</p>
        </div>
        <p className="muted-text">暂无匹配证据。</p>
      </section>
    );
  }

  return (
    <section className="evidence-panel">
      <div className="block-heading">
        <h3>匹配证据对照表</h3>
        <p>逐项核对 JD 要求和简历中的实际证据。</p>
      </div>
      <div className="evidence-list">
        {normalizedItems.map((item, index) => (
          <article className="evidence-row" key={`${item.jd_requirement || "requirement"}-${index}`}>
            <div>
              <span className="mini-label">JD 要求</span>
              <strong>{item.jd_requirement || "未识别"}</strong>
            </div>
            <div>
              <span className="mini-label">简历证据</span>
              <p>{item.resume_evidence || "简历中未找到明确证据"}</p>
            </div>
            <div>
              <span className={`status-badge ${item.status || "missing"}`}>
                {item.status || "missing"}
              </span>
            </div>
            <p>{item.suggestion || "暂无建议。"}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

function ResultSummary({ match, rewrite }) {
  const score = match?.score ?? "--";
  const level = match?.level || "暂无评级";
  const matchedCount = normalizeList(match?.matched_points).length;
  const missingCount = normalizeList(match?.missing_points).length;
  const suggestionCount = normalizeList(match?.suggestions).length;
  const questionCount = normalizeList(rewrite?.interview_questions).length;

  return (
    <section className="result-summary-card">
      <div>
        <p className="section-kicker">结果摘要</p>
        <h3>{level}</h3>
        <span>综合匹配分：{score}/100</span>
      </div>
      <div className="summary-metrics" aria-label="结果指标">
        <span>{matchedCount} 项优势</span>
        <span>{missingCount} 项缺口</span>
        <span>{suggestionCount} 条建议</span>
        <span>{questionCount} 道面试题</span>
      </div>
    </section>
  );
}

export default function ResultTabs({ result, isLoading = false }) {
  const [activeTab, setActiveTab] = useState("markdown");
  const rewrite = result?.rewrite_result || {};
  const match = result?.match_result || {};

  if (isLoading) {
    return (
      <div className="result-shell loading-shell" aria-live="polite">
        <div className="loading-copy">
          <strong>正在生成分析结果</strong>
          <span>系统正在汇总评分依据、简历优化建议、面试问题和报告正文。</span>
        </div>
        <div className="skeleton wide" />
        <div className="skeleton" />
        <div className="skeleton short" />
      </div>
    );
  }

  if (!result) {
    return (
      <div className="result-shell">
        <div className="empty-state">
          <strong>还没有分析结果</strong>
          <span>上传简历并粘贴岗位 JD 后，JobPilot 会生成匹配评分、证据摘要、简历优化建议和面试准备清单。</span>
        </div>
      </div>
    );
  }

  return (
    <div className="result-shell">
      <ResultSummary match={match} rewrite={rewrite} />

      <div className="tab-list" role="tablist" aria-label="分析结果标签">
        {TABS.map((tab) => (
          <button
            aria-controls={`panel-${tab.id}`}
            aria-selected={activeTab === tab.id}
            className={activeTab === tab.id ? "active" : ""}
            id={`tab-${tab.id}`}
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            role="tab"
            tabIndex={activeTab === tab.id ? 0 : -1}
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div
        aria-labelledby={`tab-${activeTab}`}
        className="tab-panel"
        id={`panel-${activeTab}`}
        role="tabpanel"
      >
        {activeTab === "markdown" ? <MarkdownPreview markdown={result.markdown_report} /> : null}

        {activeTab === "evidence" ? <EvidencePanel items={match.evidence_items} /> : null}

        {activeTab === "rewrite" ? (
          <div className="rewrite-grid">
            <section className="list-block highlight-block">
              <div className="block-heading">
                <h3>优化后的简历摘要</h3>
                <p>适合作为简历开头或个人优势概览的参考。</p>
              </div>
              <p>{rewrite.optimized_summary || "暂无优化摘要。"}</p>
            </section>
            <ListBlock
              description="围绕岗位关键词补齐技能表达，减少简历与 JD 的语义断层。"
              emptyText="暂无技能区优化建议。"
              items={rewrite.optimized_skills}
              title="技能区优化"
            />
            <ListBlock
              description="优先突出技术栈、个人职责、项目难点和业务价值。"
              emptyText="暂无项目经历改写建议。"
              items={rewrite.optimized_projects}
              title="项目经历改写"
            />
            <ListBlock
              description="这些内容可以作为投递时重点保留和强调的证据。"
              emptyText="暂无匹配优势。"
              items={match.matched_points}
              title="匹配优势"
            />
            <ListBlock
              description="建议在投递前通过简历改写、作品集或补充学习进行弥补。"
              emptyText="暂无能力缺口。"
              items={match.missing_points}
              title="能力缺口"
            />
            <ListBlock
              description="将分析结论转化为投递前可以执行的具体动作。"
              emptyText="暂无行动建议。"
              items={match.suggestions}
              title="投递前行动建议"
            />
          </div>
        ) : null}

        {activeTab === "interview" ? (
          <ListBlock
            description="围绕岗位要求和简历内容生成，可用于自测、模拟面试或项目复盘。"
            emptyText="暂无面试题。"
            items={rewrite.interview_questions}
            title="面试准备问题"
          />
        ) : null}

        {activeTab === "json" ? (
          <section className="raw-data-panel">
            <div className="block-heading">
              <h3>后端原始返回</h3>
              <p>保留完整结构，便于核对字段、排查链路或二次接入。</p>
            </div>
            <pre className="json-view">{JSON.stringify(result, null, 2)}</pre>
          </section>
        ) : null}
      </div>
    </div>
  );
}
