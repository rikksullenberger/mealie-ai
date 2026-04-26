"""
Security logging utilities for audit and monitoring.
"""

import json
import logging
from datetime import datetime, timezone

# Dedicated security logger
security_logger = logging.getLogger("mealie.security")


def log_security_event(
    event_type: str,
    user_id: str | None,
    ip_address: str | None = None,
    details: dict | None = None,
) -> None:
    """Log a structured security event for audit purposes.

    Args:
        event_type: Type of security event (e.g., "ai_recipe_generated", "rate_limit_exceeded")
        user_id: ID of the user who triggered the event, or None for anonymous
        ip_address: Client IP address if available
        details: Additional context as a dictionary
    """
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event_type": event_type,
        "user_id": user_id,
        "ip_address": ip_address,
        "details": details or {},
    }
    security_logger.warning(json.dumps(event))


def log_ai_usage(
    user_id: str,
    ip_address: str | None,
    endpoint: str,
    prompt_length: int,
    image_generated: bool = False,
) -> None:
    """Log AI feature usage for cost tracking and monitoring."""
    log_security_event(
        event_type="ai_usage",
        user_id=user_id,
        ip_address=ip_address,
        details={
            "endpoint": endpoint,
            "prompt_length": prompt_length,
            "image_generated": image_generated,
        },
    )
