import { useMemo, useState } from "react";
import { askCareerQuestion } from "../api";

const QUICK_PROMPTS = [
  "AI Agent 岗位面试应该重点准备什么？",
  "项目经历怎么写得更像工程交付？",
  "后端岗位简历需要突出哪些能力？",
  "前端岗位如何描述 React 项目？",
];

function buildChatError(error) {
  const detail = error?.response?.data?.detail;
  if (detail) {
    return typeof detail === "string" ? detail : JSON.stringify(detail);
  }
  return error?.message || "问答请求失败，请确认后端服务已经启动。";
}

export default function CareerChatPanel() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content: "你可以问我简历优化、岗位匹配、面试准备、项目包装和投递策略。我会先检索本地知识库，找不到依据时不会编造答案。",
      meta: "KnowledgeSearchAgent 待命",
    },
  ]);
  const [question, setQuestion] = useState("");
  const [isAsking, setIsAsking] = useState(false);
  const [error, setError] = useState("");

  const canSend = Boolean(question.trim() && !isAsking);
  const apiHistory = useMemo(
    () =>
      messages
        .filter((message) => message.role === "user" || message.role === "assistant")
        .slice(-8)
        .map((message) => ({ role: message.role, content: message.content })),
    [messages],
  );

  async function submitQuestion(nextQuestion = question) {
    const trimmed = nextQuestion.trim();
    if (!trimmed || isAsking) {
      return;
    }

    setQuestion("");
    setError("");
    setIsAsking(true);
    setMessages((current) => [...current, { role: "user", content: trimmed }]);

    try {
      const response = await askCareerQuestion(trimmed, apiHistory);
      setMessages((current) => [
        ...current,
        {
          role: "assistant",
          content: response.answer,
          meta:
            response.retrieval_status === "miss"
              ? "知识库未命中，已拒绝自由发挥"
              : `来源：${response.sources?.join("、") || "本地知识库"}`,
          logs: response.agent_logs || [],
        },
      ]);
    } catch (requestError) {
      setError(buildChatError(requestError));
    } finally {
      setIsAsking(false);
    }
  }

  function handleKeyDown(event) {
    if (event.key === "Enter" && (event.ctrlKey || event.metaKey)) {
      submitQuestion();
    }
  }

  return (
    <section className="chat-panel" aria-busy={isAsking}>
      <div className="chat-heading">
        <div>
          <p className="section-kicker">求职问答</p>
          <h2>和知识库对话</h2>
        </div>
        <span className="secure-pill">RAG 先检索再回答</span>
      </div>

      <div className="chat-layout">
        <div className="chat-messages" aria-live="polite">
          {messages.map((message, index) => (
            <article className={`chat-message ${message.role}`} key={`${message.role}-${index}`}>
              <div className="chat-bubble">
                <span className="chat-role">{message.role === "user" ? "你" : "JobPilot"}</span>
                <p>{message.content}</p>
                {message.meta ? <small>{message.meta}</small> : null}
              </div>
              {message.logs?.length ? (
                <details className="chat-agent-logs">
                  <summary>查看智能体链路</summary>
                  <ol>
                    {message.logs.map((log, logIndex) => (
                      <li key={`${log}-${logIndex}`}>{log}</li>
                    ))}
                  </ol>
                </details>
              ) : null}
            </article>
          ))}
          {isAsking ? (
            <article className="chat-message assistant">
              <div className="chat-bubble">
                <span className="chat-role">JobPilot</span>
                <p>正在优化问题、检索知识库并生成回答...</p>
              </div>
            </article>
          ) : null}
        </div>

        <div className="chat-side">
          <div className="quick-prompts" aria-label="推荐问题">
            {QUICK_PROMPTS.map((prompt) => (
              <button disabled={isAsking} key={prompt} onClick={() => submitQuestion(prompt)} type="button">
                {prompt}
              </button>
            ))}
          </div>

          <label className="chat-composer">
            <span>输入你的求职问题</span>
            <textarea
              disabled={isAsking}
              onChange={(event) => setQuestion(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="例如：RAG 项目经历在简历里怎么描述更有说服力？"
              value={question}
            />
          </label>

          {error ? (
            <div className="chat-error" role="alert">
              {error}
            </div>
          ) : null}

          <button className="primary-action" disabled={!canSend} onClick={() => submitQuestion()} type="button">
            {isAsking ? "正在回答..." : "发送问题"}
          </button>
        </div>
      </div>
    </section>
  );
}
