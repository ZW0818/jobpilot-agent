import os

from utils.path_tool import backend_root
from model.multimodal_client import TextMultimodalClient, needs_multimodal_endpoint

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional during minimal validation
    load_dotenv = None


if load_dotenv:
    load_dotenv(backend_root() / ".env")


def has_dashscope_key() -> bool:
    value = os.getenv("DASHSCOPE_API_KEY", "").strip()
    return bool(value and value.lower() not in {"your api-key", "your-api-key", "your_api_key"})


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

    model = ChatTongyi(model=model_name, dashscope_api_key=api_key, max_retries=1)
    if needs_multimodal_endpoint(model_name):
        from dashscope import MultiModalConversation
        thinking = os.getenv("DASHSCOPE_ENABLE_THINKING", "false").lower() in {"1", "true", "yes"}
        model.client = TextMultimodalClient(MultiModalConversation, enable_thinking=thinking)
    return model


def get_embedding_model():
    api_key = _require_dashscope_key()
    model_name = os.getenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v4")
    if "rerank" in model_name.lower():
        raise ValueError("DASHSCOPE_EMBEDDING_MODEL requires an embedding model, not a rerank model.")
    try:
        from langchain_community.embeddings import DashScopeEmbeddings
        from langchain_community.embeddings.dashscope import BATCH_SIZE
    except ImportError as exc:
        raise RuntimeError(
            "LangChain DashScope embedding dependencies are missing. Install backend requirements.txt."
        ) from exc

    # Older integrations default unknown models to 25 rows; Qwen3.7 allows at most 20.
    if model_name.startswith("qwen3.7-text-embedding"):
        BATCH_SIZE.setdefault(model_name, 20)
    return DashScopeEmbeddings(model=model_name, dashscope_api_key=api_key, max_retries=1)
