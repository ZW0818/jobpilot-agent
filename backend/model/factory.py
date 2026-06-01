import os

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional during minimal validation
    load_dotenv = None


if load_dotenv:
    load_dotenv()


def has_dashscope_key() -> bool:
    return bool(os.getenv("DASHSCOPE_API_KEY"))


def _require_dashscope_key() -> str:
    api_key = os.getenv("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError(
            "DASHSCOPE_API_KEY is not configured. Set it in your environment or .env file. "
            "Without a key, JobPilot agents should use heuristic fallback mode."
        )
    return api_key


def get_chat_model():
    api_key = _require_dashscope_key()
    model_name = os.getenv("DASHSCOPE_CHAT_MODEL", "qwen-plus")
    try:
        from langchain_community.chat_models import ChatTongyi
    except ImportError as exc:
        raise RuntimeError(
            "LangChain DashScope chat dependencies are missing. Install backend requirements.txt."
        ) from exc

    return ChatTongyi(model=model_name, dashscope_api_key=api_key)


def get_embedding_model():
    api_key = _require_dashscope_key()
    model_name = os.getenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v4")
    try:
        from langchain_community.embeddings import DashScopeEmbeddings
    except ImportError as exc:
        raise RuntimeError(
            "LangChain DashScope embedding dependencies are missing. Install backend requirements.txt."
        ) from exc

    return DashScopeEmbeddings(model=model_name, dashscope_api_key=api_key)
