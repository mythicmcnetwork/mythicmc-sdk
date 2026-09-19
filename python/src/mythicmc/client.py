from __future__ import annotations

import asyncio
import re
import time
from datetime import datetime
from typing import Any, TypeVar
from urllib.parse import quote

import httpx

from . import models
from .errors import (
    AuthenticationError,
    BadRequestError,
    MythicMCError,
    NotFoundError,
    RateLimitError,
    UnavailableError,
)

__version__ = "0.1.0"
DEFAULT_BASE_URL = "https://api.mythicmc.net"

T = TypeVar("T")

_ERRORS = {400: BadRequestError, 401: AuthenticationError, 404: NotFoundError, 503: UnavailableError}
_MAX_RETRY_WAIT = 60.0


def _integer(value: str | None) -> int | None:
    # int() also accepts signs, underscores, and non-ASCII digits.
    if value is None or not re.fullmatch(r"[0-9]+", value):
        return None
    return int(value)


def _instant(value: str | None) -> datetime | None:
    # Python 3.10 needs +00:00 instead of Z.
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _meta(headers: httpx.Headers) -> models.ResponseMeta:
    cache = headers.get("x-cache")
    return models.ResponseMeta(
        data_delay_seconds=_integer(headers.get("x-data-delay-seconds")),
        data_as_of=_instant(headers.get("x-data-as-of")),
        cache=cache if cache in ("HIT", "MISS", "COALESCED") else None,
        rate_limit_per_minute=_integer(headers.get("x-ratelimit-limit-minute")),
    )


def _message(response: httpx.Response) -> str:
    try:
        error = response.json().get("error")
        if isinstance(error, str):
            return error
    except (ValueError, AttributeError):
        pass
    return f"HTTP {response.status_code}"


def _options(api_key: str, base_url: str, timeout: float) -> dict[str, Any]:
    if not api_key:
        raise ValueError("api_key is required")
    return {
        "base_url": (base_url or DEFAULT_BASE_URL).rstrip("/"),
        "timeout": timeout,
        "headers": {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": f"mythicmc-api-python/{__version__}",
        },
    }


class _Base:
    _max_retries: int

    def _retry_delay(self, response: httpx.Response, attempt: int) -> float | None:
        if response.status_code != 429:
            return None
        retry_after = _integer(response.headers.get("retry-after"))
        wait = 1.0 if retry_after is None else float(retry_after)
        if attempt >= self._max_retries or wait > _MAX_RETRY_WAIT:
            raise RateLimitError(_message(response), retry_after)
        return wait

    @staticmethod
    def _reply(model: type[T], response: httpx.Response) -> T:
        if not response.is_success:
            raise _ERRORS.get(response.status_code, MythicMCError)(response.status_code, _message(response))
        try:
            body = response.json()
            return models.parse(model, body, meta=_meta(response.headers), raw=body)
        except (TypeError, ValueError) as exc:
            raise MythicMCError(response.status_code, f"malformed response body: {exc}") from exc

    @staticmethod
    def _player(id: str, detail: str = "") -> str:
        return f"/v1/players/{quote(id, safe='')}{detail}"

    @staticmethod
    def _board(type: str, period: str) -> str:
        return f"/v1/leaderboards/{quote(type, safe='')}/{quote(period, safe='')}"


class MythicMC(_Base):
    """Use a context manager or close() to release connections.

    timeout is per attempt, in seconds. max_retries applies to 429 responses only;
    waits over 60 seconds raise RateLimitError. Set max_retries=0 to disable retries."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 10.0,
        max_retries: int = 2,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._max_retries = max_retries
        self._http = httpx.Client(transport=transport, **_options(api_key, base_url, timeout))

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> MythicMC:
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def _get(self, model: type[T], path: str) -> T:
        attempt = 0
        while True:
            response = self._http.get(path)
            delay = self._retry_delay(response, attempt)
            if delay is None:
                return self._reply(model, response)
            time.sleep(delay)
            attempt += 1

    def get_player(self, id: str) -> models.PlayerProfile:
        """Accepts a case-insensitive username or UUID, with or without dashes."""
        return self._get(models.PlayerProfile, self._player(id))

    def get_player_stats(self, id: str) -> models.PlayerStats:
        """Raises NotFoundError when no Survival statistics are published."""
        return self._get(models.PlayerStats, self._player(id, "/stats"))

    def get_player_progression(self, id: str) -> models.PlayerProgression:
        return self._get(models.PlayerProgression, self._player(id, "/progression"))

    def get_player_team(self, id: str) -> models.PlayerTeam:
        return self._get(models.PlayerTeam, self._player(id, "/team"))

    def get_player_crate_keys(self, id: str) -> models.PlayerCrateKeys:
        return self._get(models.PlayerCrateKeys, self._player(id, "/crate-keys"))

    def list_leaderboards(self) -> models.LeaderboardIndex:
        return self._get(models.LeaderboardIndex, "/v1/leaderboards")

    def get_leaderboard(self, type: models.LeaderboardType, period: models.LeaderboardPeriod) -> models.Leaderboard:
        """Networth supports all_time only."""
        return self._get(models.Leaderboard, self._board(type, period))

    def health(self) -> models.Health:
        """API process health, not game server status."""
        return self._get(models.Health, "/health")


class AsyncMythicMC(_Base):
    """Use async with or await close() to release connections."""

    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = 10.0,
        max_retries: int = 2,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._max_retries = max_retries
        self._http = httpx.AsyncClient(transport=transport, **_options(api_key, base_url, timeout))

    async def close(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> AsyncMythicMC:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.close()

    async def _get(self, model: type[T], path: str) -> T:
        attempt = 0
        while True:
            response = await self._http.get(path)
            delay = self._retry_delay(response, attempt)
            if delay is None:
                return self._reply(model, response)
            await asyncio.sleep(delay)
            attempt += 1

    async def get_player(self, id: str) -> models.PlayerProfile:
        """Accepts a case-insensitive username or UUID, with or without dashes."""
        return await self._get(models.PlayerProfile, self._player(id))

    async def get_player_stats(self, id: str) -> models.PlayerStats:
        """Raises NotFoundError when no Survival statistics are published."""
        return await self._get(models.PlayerStats, self._player(id, "/stats"))

    async def get_player_progression(self, id: str) -> models.PlayerProgression:
        return await self._get(models.PlayerProgression, self._player(id, "/progression"))

    async def get_player_team(self, id: str) -> models.PlayerTeam:
        return await self._get(models.PlayerTeam, self._player(id, "/team"))

    async def get_player_crate_keys(self, id: str) -> models.PlayerCrateKeys:
        return await self._get(models.PlayerCrateKeys, self._player(id, "/crate-keys"))

    async def list_leaderboards(self) -> models.LeaderboardIndex:
        return await self._get(models.LeaderboardIndex, "/v1/leaderboards")

    async def get_leaderboard(self, type: models.LeaderboardType, period: models.LeaderboardPeriod) -> models.Leaderboard:
        """Networth supports all_time only."""
        return await self._get(models.Leaderboard, self._board(type, period))

    async def health(self) -> models.Health:
        """API process health, not game server status."""
        return await self._get(models.Health, "/health")
