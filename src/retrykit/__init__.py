"""Retry decorator with exponential backoff and jitter."""
from __future__ import annotations

import functools
import random
import time
from typing import Callable, Tuple, Type, TypeVar

__all__ = ["retry", "RetryError"]

F = TypeVar("F", bound=Callable)


class RetryError(Exception):
    """Raised when every attempt failed. The last error is chained as __cause__."""

    def __init__(self, attempts: int):
        super().__init__(f"gave up after {attempts} attempts")
        self.attempts = attempts


def retry(
    attempts: int = 3,
    base_delay: float = 0.1,
    max_delay: float = 30.0,
    factor: float = 2.0,
    jitter: float = 0.1,
    exceptions: Tuple[Type[BaseException], ...] = (Exception,),
    sleep: Callable[[float], None] = time.sleep,
    on_retry: Callable[[int, BaseException, float], None] = lambda *_: None,
) -> Callable[[F], F]:
    """Retry the wrapped callable up to `attempts` times.

    Delay before retry n (1-based) is min(max_delay, base_delay * factor**(n-1)),
    scaled by a random factor in [1 - jitter, 1 + jitter].
    """
    if attempts < 1:
        raise ValueError("attempts must be >= 1")

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    if attempt == attempts:
                        raise RetryError(attempts) from exc
                    delay = min(max_delay, base_delay * factor ** (attempt - 1))
                    delay *= 1 + random.uniform(-jitter, jitter)
                    on_retry(attempt, exc, delay)
                    sleep(delay)

        return wrapper  # type: ignore[return-value]

    return decorator
