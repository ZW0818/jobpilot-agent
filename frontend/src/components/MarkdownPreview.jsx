import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

export default function MarkdownPreview({ markdown, compact = false }) {
  if (!markdown) {
    return (
      <div className="empty-state compact">
        <strong>暂无报告正文</strong>
        <span>分析完成后，后端返回的报告正文会在这里以可阅读格式展示。</span>
      </div>
    );
  }

  return (
    <article className="markdown-preview">
      {!compact ? <div className="report-toolbar">
        <span>分析报告预览</span>
        <small>可在右上角下载完整报告文件</small>
      </div> : null}
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={{
        h1: ({ children }) => <h2>{children}</h2>,
        h2: ({ children }) => <h3>{children}</h3>,
        h3: ({ children }) => <h4>{children}</h4>,
        a: ({ children, href }) => <a href={href} target="_blank" rel="noreferrer">{children}</a>,
        table: ({ children }) => <div className="report-table-scroll" role="region" aria-label="报告表格，可横向滚动" tabIndex={0}><table>{children}</table></div>,
      }}>{markdown}</ReactMarkdown>
    </article>
  );
}
