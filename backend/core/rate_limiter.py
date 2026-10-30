import os
import time
import math
import threading
from collections import defaultdict
from typing import Optional, Tuple, Dict, Any
from fastapi import Request, HTTPException, status
from models import User

logger = logging = __import__("logging").getLogger("obe.rate_limiter")

# In-memory sliding window rate limits: key -> list of float timestamps
_rate_limits: Dict[str, list] = defaultdict(list)
_rate_lock = threading.Lock()

# In-memory tutor explanation cache: key -> (timestamp, response_dict)
_tutor_cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_cache_lock = threading.Lock()
TUTOR_CACHE_TTL_SEC = 3600  # 1 hour in-memory cache


def get_client_ip(request: Request) -> str:
    """
    Retrieves the client IP address.
    Strictly reads X-Forwarded-For header ONLY when TRUST_PROXY=true.
    Otherwise, uses request.client.host (defaults to 127.0.0.1).
    """
    trust_proxy = os.getenv("TRUST_PROXY", "false").strip().lower() in ("true", "1", "yes")
    if trust_proxy and request:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # First IP in comma-separated chain is the client IP
            first_ip = forwarded.split(",")[0].strip()
            if first_ip:
                return first_ip

    if request and request.client and request.client.host:
        return request.client.host

    return "127.0.0.1"


def get_requester_key(request: Request, user: Optional[User] = None, prefix: str = "") -> str:
    """
    Returns rate limit key: per authenticated user if user is present,
    otherwise per client IP (respecting TRUST_PROXY).
    """
    if user and getattr(user, "id", None):
        return f"{prefix}:user:{user.id}"
    return f"{prefix}:ip:{get_client_ip(request)}"


def check_rate_limit(key: str, limit: int, window_seconds: int = 60) -> Tuple[bool, int]:
    """
    Checks whether key has exceeded limit within window_seconds.
    Returns (allowed: bool, retry_after: int).
    """
    now = time.time()
    cutoff = now - window_seconds
    with _rate_lock:
        timestamps = _rate_limits[key]
        _rate_limits[key] = [t for t in timestamps if t >= cutoff]
        current_history = _rate_limits[key]

        if len(current_history) >= limit:
            oldest = current_history[0]
            retry_after = max(1, math.ceil(oldest + window_seconds - now))
            return False, retry_after

        current_history.append(now)
        return True, 0


def enforce_rate_limit(
    key: str,
    limit: int,
    window_seconds: int = 60,
    detail: str = "Too many requests. Please try again later."
) -> None:
    """
    Raises HTTP 429 with Retry-After header if key exceeds limit.
    """
    allowed, retry_after = check_rate_limit(key, limit, window_seconds)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers={"Retry-After": str(retry_after)}
        )


def reset_rate_limits() -> None:
    """Helper for testing to reset rate limit states."""
    with _rate_lock:
        _rate_limits.clear()


# ==============================================================================
# In-Memory Tutor Explanation Caching
# ==============================================================================

def get_cached_tutor_explanation(cache_key: str) -> Optional[Dict[str, Any]]:
    """Retrieves cached tutor response if within TTL."""
    now = time.time()
    with _cache_lock:
        if cache_key in _tutor_cache:
            ts, data = _tutor_cache[cache_key]
            if now - ts <= TUTOR_CACHE_TTL_SEC:
                return dict(data)
            else:
                del _tutor_cache[cache_key]
    return None


def set_cached_tutor_explanation(cache_key: str, data: Dict[str, Any]) -> None:
    """Stores tutor response in memory."""
    now = time.time()
    with _cache_lock:
        _tutor_cache[cache_key] = (now, dict(data))


def clear_tutor_cache() -> None:
    """Helper for testing to clear cached tutor explanations."""
    with _cache_lock:
        _tutor_cache.clear()
