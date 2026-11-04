import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    from rag.rag_service import get_rag_service
    monkeypatch.setenv("DASHSCOPE_API_KEY", "")
    monkeypatch.setenv("RAG_ENABLE_VECTOR", "false")
    service = get_rag_service()
    monkeypatch.setattr(service, "enable_vector", False)
