from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import Lock
from typing import Callable, Generic, Optional, TypeVar


T = TypeVar("T")


class CircuitOpenError(Exception):
    """Raised when the breaker is open and calls must fail fast."""


@dataclass(slots=True)
class CircuitStats:
    state: str
    consecutive_failures: int
    opened_until: Optional[datetime]


class CircuitBreaker(Generic[T]):
    """
    Simple thread-safe circuit breaker with closed/open/half-open states.
    """

    def __init__(self, failure_threshold: int = 3, recovery_timeout_seconds: int = 30) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1")
        if recovery_timeout_seconds < 1:
            raise ValueError("recovery_timeout_seconds must be >= 1")

        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self._state = "closed"
        self._consecutive_failures = 0
        self._opened_until: Optional[datetime] = None
        self._lock = Lock()

    def call(self, fn: Callable[..., T], *args: object, **kwargs: object) -> T:
        self._before_call()

        try:
            result = fn(*args, **kwargs)
        except Exception:
            self._record_failure()
            raise

        self._record_success()
        return result

    def stats(self) -> CircuitStats:
        with self._lock:
            return CircuitStats(
                state=self._state,
                consecutive_failures=self._consecutive_failures,
                opened_until=self._opened_until,
            )

    def _before_call(self) -> None:
        now = datetime.now(timezone.utc)
        with self._lock:
            if self._state == "open":
                if self._opened_until is not None and now >= self._opened_until:
                    self._state = "half-open"
                else:
                    raise CircuitOpenError("Circuit is open; external call skipped.")

    def _record_success(self) -> None:
        with self._lock:
            self._state = "closed"
            self._consecutive_failures = 0
            self._opened_until = None

    def _record_failure(self) -> None:
        now = datetime.now(timezone.utc)
        with self._lock:
            if self._state == "half-open":
                self._trip(now)
                return

            self._consecutive_failures += 1
            if self._consecutive_failures >= self.failure_threshold:
                self._trip(now)

    def _trip(self, now: datetime) -> None:
        self._state = "open"
        self._opened_until = now + timedelta(seconds=self.recovery_timeout_seconds)
