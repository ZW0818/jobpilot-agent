import functools
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar


logger = logging.getLogger("jobpilot")
F = TypeVar("F", bound=Callable[..., Any])


def log_step(step_name: str) -> Callable[[F], F]:
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            started = time.perf_counter()
            logger.info("Starting agent step: %s", step_name)
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = time.perf_counter() - started
                logger.info("Finished agent step: %s in %.2fs", step_name, elapsed)

        return wrapper  # type: ignore[return-value]

    return decorator
