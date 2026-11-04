"""Request-local model fallback diagnostics; never include private prompt text."""
import logging
from contextvars import ContextVar

from model.errors import PROVIDER_ERRORS, provider_error_code

logger = logging.getLogger("jobpilot")
fallback_events: ContextVar[list[str] | None] = ContextVar("fallback_events", default=None)


def record_fallback(operation: str, error: Exception) -> None:
    message = f"{operation} 模型调用或输出校验失败（{type(error).__name__}），已使用规则结果。"
    code = provider_error_code(error)
    if code:
        message += f" {code}：{PROVIDER_ERRORS[code]}。"
    logger.warning(message)
    events = fallback_events.get()
    if events is not None:
        events.append(message)
