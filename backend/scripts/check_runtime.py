"""Check runtime configuration; --probe makes real model/embedding API requests."""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from model.factory import get_chat_model, has_dashscope_key
from model.errors import provider_error_code
from rag.rag_service import get_rag_service


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--probe", action="store_true")
    args = parser.parse_args()
    rag = get_rag_service()
    status = {
        "key_configured": has_dashscope_key(),
        "chat_model": os.getenv("DASHSCOPE_CHAT_MODEL", "qwen-plus"),
        "embedding_model": os.getenv("DASHSCOPE_EMBEDDING_MODEL", "text-embedding-v4"),
        "vector_enabled": rag.enable_vector,
        "chroma_api": os.getenv("CHROMA_API_IMPL", "default"),
        "persist_directory": str(rag.vector_store.persist_dir),
    }
    failed = False
    if args.probe:
        try:
            if not has_dashscope_key():
                raise RuntimeError("Missing credentials")
            response = get_chat_model().invoke([("user", "请只回复 OK")])
            status["model_probe"] = "success" if getattr(response, "content", "").strip() else "empty_response"
            failed = status["model_probe"] != "success"
        except Exception as exc:
            status["model_probe"] = "failed"
            status["model_error_type"] = type(exc).__name__
            status["model_error_code"] = provider_error_code(exc)
            failed = True
        try:
            if not rag.enable_vector:
                raise RuntimeError("Vector retrieval disabled")
            result = rag.retrieve("RAG 检索质量如何评估")
            status["retrieval_status"] = result.status
            status["retrieved_chunks"] = len(result.chunks)
            if result.status != "hybrid":
                failed = True
                status["vector_error_type"] = rag.vector_store.last_error_type
                status["vector_error_code"] = rag.vector_store.last_error_code
            if rag.vector_store._store is not None:
                status["indexed_chunks"] = len(rag.vector_store._store.get(include=[])["ids"])
        except Exception as exc:
            status["retrieval_status"] = "failed"
            status["vector_error_type"] = type(exc).__name__
            failed = True
    print(json.dumps(status, ensure_ascii=False, indent=2))
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
