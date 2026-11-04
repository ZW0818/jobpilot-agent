"""Adapt text-only prompts to DashScope multimodal models for ChatTongyi."""
from typing import Any


class TextMultimodalClient:
    def __init__(self, client: Any, enable_thinking: bool = False):
        self.client = client
        self.enable_thinking = enable_thinking

    def call(self, **kwargs: Any) -> Any:
        params = dict(kwargs)
        params["messages"] = [
            {**message, "content": [{"text": message["content"]}]}
            if isinstance(message.get("content"), str) else dict(message)
            for message in params.get("messages", [])
        ]
        params.setdefault("enable_thinking", self.enable_thinking)
        response = self.client.call(**params)
        if params.get("stream"):
            return (self._text_response(chunk) for chunk in response)
        return self._text_response(response)

    @staticmethod
    def _text_response(response: Any) -> Any:
        output = response.get("output") or {}
        for choice in output.get("choices", []):
            message = choice.get("message", {})
            content = message.get("content")
            if isinstance(content, list):
                message["content"] = "".join(part.get("text", "") for part in content if isinstance(part, dict))
        return response


def needs_multimodal_endpoint(model_name: str) -> bool:
    name = model_name.lower()
    return name.startswith(("qwen3.5-", "qwen3.6-", "qwen3.7-plus", "qwen3.7-flash", "qwen3.8-"))
