export default function UploadPanel({
  resumeFile,
  jdText,
  isLoading,
  canAnalyze,
  onFileChange,
  onJdChange,
  onAnalyze,
  onUseSample,
}) {
  const jdLength = jdText.trim().length;
  const hasResume = Boolean(resumeFile);
  const hasJd = jdLength > 0;
  const readinessText = hasResume && hasJd ? "材料已就绪，可以开始分析" : "请先补齐简历与岗位 JD";

  return (
    <section className="upload-panel">
      <div className="panel-topline">
        <div>
          <p className="section-kicker">步骤 01</p>
          <h2>输入候选人与岗位信息</h2>
          <p className="panel-description">
            建议上传最新版简历，并粘贴完整岗位职责、任职要求和加分项，匹配结论会更稳定。
          </p>
        </div>
        <span className="secure-pill">本地服务处理</span>
      </div>

      <label className={`file-drop ${hasResume ? "has-file" : ""}`}>
        <input
          accept=".pdf,.doc,.docx,.txt,.md"
          disabled={isLoading}
          onChange={(event) => onFileChange(event.target.files?.[0] || null)}
          type="file"
        />
        <span className="file-icon">简</span>
        <span>
          <strong>{resumeFile ? resumeFile.name : "上传简历文件"}</strong>
          <small>
            {resumeFile ? "已选择简历，将作为候选人画像输入。" : "支持 PDF、Word、TXT 和 Markdown。"}
          </small>
        </span>
      </label>

      <label className="jd-field">
        <span>目标岗位 JD</span>
        <textarea
          disabled={isLoading}
          onChange={(event) => onJdChange(event.target.value)}
          placeholder="粘贴目标岗位、工作职责、技能要求、加分项等内容。内容越完整，岗位画像和缺口建议越准确。"
          value={jdText}
        />
      </label>

      <div className="input-insights" aria-label="输入状态">
        <span className={hasResume ? "ready" : ""}>{hasResume ? "简历已上传" : "等待简历"}</span>
        <span className={hasJd ? "ready" : ""}>{hasJd ? `JD 已输入 ${jdLength} 字` : "等待岗位 JD"}</span>
        <span>{readinessText}</span>
      </div>

      <div className="form-actions">
        <button className="ghost-action" disabled={isLoading} onClick={onUseSample} type="button">
          使用示例岗位
        </button>
        <button className="primary-action" disabled={!canAnalyze} onClick={onAnalyze} type="button">
          {isLoading ? "正在生成求职分析..." : "开始岗位匹配分析"}
        </button>
      </div>
    </section>
  );
}
