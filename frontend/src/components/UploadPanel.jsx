export default function UploadPanel({ resumeFile, jdText, isLoading, canAnalyze, onFileChange, onJdChange, onAnalyze, onUseSample, error }) {
  const jdLength = jdText.trim().length;
  return (
    <section className="upload-panel">
      <div className="panel-heading"><h2>分析材料</h2><span>{resumeFile && jdLength ? "材料已就绪" : "简历与岗位各一份"}</span></div>
      <div className="resume-field">
        <span className="field-label" id="resume-label">候选人简历</span>
        <label className={`file-drop ${resumeFile ? "has-file" : ""}`}>
          <input aria-labelledby="resume-label" aria-describedby="resume-formats" accept=".pdf,.docx,.txt,.md" disabled={isLoading} onChange={(event) => onFileChange(event.target.files?.[0] || null)} type="file"/>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true"><path d="M6 3h8l4 4v14H6z M14 3v5h4 M9 12h6 M9 16h6"/></svg>
          <span className="file-description"><strong>{resumeFile?.name || "选择简历文件"}</strong><small id="resume-formats">{resumeFile ? `${(resumeFile.size / 1024).toFixed(1)} KB · 点击可更换` : "支持 PDF、DOCX、TXT、Markdown"}</small></span>
          <span className="file-select" aria-hidden="true">{resumeFile ? "更换" : "浏览文件"}</span>
        </label>
      </div>
      <div className="jd-field">
        <div className="field-heading"><label htmlFor="jd-text">目标岗位 JD</label><button className="text-action" disabled={isLoading} onClick={onUseSample} type="button">填入示例</button></div>
        <textarea id="jd-text" disabled={isLoading} onChange={(event) => onJdChange(event.target.value)} placeholder={"粘贴岗位名称、职责、任职要求和加分项。\n保留完整要求，便于逐项核对简历证据。"} value={jdText} aria-describedby="jd-count"/>
        <div className="field-footnote"><span>必备要求与加分项将分别评估</span><span id="jd-count">{jdLength.toLocaleString("zh-CN")} 字</span></div>
      </div>
      <div className="submission-note" id="submission-note">简历将发送至已配置的模型服务用于本次分析，建议先移除与求职无关的敏感信息。</div>
      {error ? <div className="inline-error" role="alert"><strong>本次分析未完成</strong><p>{error}</p></div> : null}
      <div className="form-actions"><span aria-live="polite">{isLoading ? "正在核对材料并生成报告…" : canAnalyze ? "材料已就绪" : "请添加简历和目标岗位"}</span><button className="primary-action" disabled={!canAnalyze} aria-describedby="submission-note" onClick={onAnalyze} type="button">{isLoading ? "分析中…" : error ? "重新分析" : "生成匹配报告"}<span aria-hidden="true"> →</span></button></div>
    </section>
  );
}
