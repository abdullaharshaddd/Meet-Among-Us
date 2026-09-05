import time
from collections import defaultdict, deque

from fastapi import Request

from app.core.exceptions import RateLimitedError

# ponytail: per-process in-memory sliding window — fine for one dev/single
# instance backend this milestone. Resets on restart and doesn't share state
# across workers/instances; move to Redis if the API ever scales beyond one
# process. See docs/adr/0011-in-memory-rate-limiting.md.
_attempts: dict[str, deque[float]] = defaultdict(deque)


def reset() -> None:
    """Test-only: clears all buckets so one test's attempts don't count against
    the next (TestClient reuses the same synthetic client IP for every test)."""
    _attempts.clear()


def _check(key: str, max_attempts: int, window_seconds: int) -> None:
    now = time.monotonic()
    bucket = _attempts[key]
    while bucket and now - bucket[0] > window_seconds:
        bucket.popleft()
    if len(bucket) >= max_attempts:
        raise RateLimitedError("Too many attempts — try again in a minute")
    bucket.append(now)


def rate_limiter(bucket_name: str, *, max_attempts: int, window_seconds: int):
    """FastAPI dependency factory — keys the sliding window on client IP + a
    per-endpoint bucket name, so /login and /signup don't share one counter."""

    def dependency(request: Request) -> None:
        client_ip = request.client.host if request.client else "unknown"
        _check(f"{bucket_name}:{client_ip}", max_attempts, window_seconds)

    return dependency
