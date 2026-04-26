"""
Simple in-memory rate limiter for AI endpoints.
Uses token bucket algorithm per user IP.
"""

import time
from collections import defaultdict
from typing import Any

from fastapi import HTTPException, Request, status


class TokenBucket:
    """Token bucket rate limiter."""

    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = float(capacity)
        self.refill_rate = refill_rate
        self.last_refill = time.monotonic()

    def consume(self, tokens: int = 1) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False


class RateLimiter:
    """In-memory rate limiter for FastAPI endpoints."""

    def __init__(self):
        # Standard endpoints: 30 requests per minute
        self.buckets: dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(capacity=30, refill_rate=0.5)  # 30 tokens, 1 per 2 seconds
        )
        # AI endpoints: 5 requests per minute (slower)
        self.ai_buckets: dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(capacity=5, refill_rate=1 / 12)  # 5 tokens, 1 per 12 seconds
        )

    def _check_rate_limit(self, request: Request, ai_endpoint: bool = False) -> None:
        """Check if the request should be rate limited."""
        client_ip = request.client.host if request.client else "unknown"
        bucket = self.ai_buckets[client_ip] if ai_endpoint else self.buckets[client_ip]

        if not bucket.consume():
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
            )

    def limit(self, ai_endpoint: bool = False):
        """Decorator factory that properly handles FastAPI dependency injection.

        Usage:
            @router.post("/create/ai")
            @rate_limiter.limit(ai_endpoint=True)
            async def create_recipe_from_ai(..., request: Request):
                ...
        """

        def decorator(func: Any) -> Any:
            # Store the original function
            func._rate_limit_ai = ai_endpoint
            return func

        return decorator


# Global rate limiter instance
rate_limiter = RateLimiter()
