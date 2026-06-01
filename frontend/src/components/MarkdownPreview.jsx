import ReactMarkdown from "react-markdown";

export default function MarkdownPreview({ markdown }) {
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
      <div className="report-toolbar">
        <span>分析报告预览</span>
        <small>可在右上角下载完整报告文件</small>
      </div>
      <ReactMarkdown>{markdown}</ReactMarkdown>
    </article>
  );
}
