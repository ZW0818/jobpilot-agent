from types import SimpleNamespace

import pytest

from model.multimodal_client import TextMultimodalClient, needs_multimodal_endpoint


def test_multimodal_client_converts_text_and_preserves_input_messages():
    captured = {}
    def call(**kwargs):
        captured.update(kwargs)
        return {"output": {"choices": [{"message": {"content": [{"text": '{"name":'}, {"text": '"示例"}'}]}}]}}
    messages = [{"role": "system", "content": "Return JSON"}, {"role": "user", "content": "Example"}]
    response = TextMultimodalClient(SimpleNamespace(call=call)).call(messages=messages)
    assert captured["messages"][0]["content"] == [{"text": "Return JSON"}]
    assert messages[0]["content"] == "Return JSON"
    assert captured["enable_thinking"] is False
    assert response["output"]["choices"][0]["message"]["content"] == '{"name":"示例"}'


def test_multimodal_errors_remain_intact():
    error = {"status_code": 403, "output": None, "code": "AllocationQuota.FreeTierOnly"}
    client = TextMultimodalClient(SimpleNamespace(call=lambda **kwargs: error))
    assert client.call(messages=[]) == error


@pytest.mark.parametrize("model,expected", [("qwen3.8-flash", True), ("qwen3.7-plus", True),
    ("qwen3.5-flash", True), ("qwen3.7-max", False), ("qwen-plus", False)])
def test_multimodal_endpoint_routing(model, expected):
    assert needs_multimodal_endpoint(model) == expected


def test_embedding_handles_more_documents_than_provider_batch_limit(monkeypatch):
    pytest.importorskip("langchain_community.embeddings.dashscope")
    from model.factory import get_embedding_model
    monkeypatch.setenv("DASHSCOPE_API_KEY", "test-only")
    monkeypatch.setenv("DASHSCOPE_EMBEDDING_MODEL", "qwen3.7-text-embedding-flash")
    batches = []
    def call(**kwargs):
        texts = kwargs["input"]
        assert len(texts) <= 20
        batches.append(len(texts))
        return SimpleNamespace(status_code=200, output={"embeddings": [{"embedding": [float(text)]} for text in texts]})
    embedding = get_embedding_model()
    embedding.client = SimpleNamespace(call=call)
    result = embedding.embed_documents([str(i) for i in range(27)])
    assert result == [[float(i)] for i in range(27)]
    assert batches == [20, 7]
