from __future__ import annotations


class MythicMCError(Exception):
    """HTTP or response-parsing failure."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


class BadRequestError(MythicMCError):
    """400: invalid username or UUID."""


class AuthenticationError(MythicMCError):
    """401: missing or invalid API key."""


class NotFoundError(MythicMCError):
    """404: unknown player, board, or missing published data."""


class RateLimitError(MythicMCError):
    """429: retries exhausted or Retry-After exceeds 60 seconds."""

    def __init__(self, message: str, retry_after: int | None) -> None:
        super().__init__(429, message)
        self.retry_after = retry_after
        """Retry-After in seconds, or None when unavailable."""


class UnavailableError(MythicMCError):
    """503: unavailable data, ambiguous username, or server failure."""
