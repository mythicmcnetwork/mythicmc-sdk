"""JSON keys map to snake_case attributes. Timestamps are Unix milliseconds.

Unknown values are None. Raw JSON and metadata are excluded from equality."""

from __future__ import annotations

import dataclasses
import types
from dataclasses import dataclass, field
from datetime import datetime
from functools import cache
from typing import Any, Literal, TypeVar, Union, get_args, get_origin, get_type_hints

T = TypeVar("T")

TeamRole = Literal["leader", "officer", "member"]
LeaderboardType = Literal["kills", "playtime", "wins", "networth"]
LeaderboardPeriod = Literal["daily", "weekly", "monthly", "all_time"]


@dataclass(frozen=True, slots=True)
class ResponseMeta:
    """Missing or invalid response headers become None."""

    data_delay_seconds: int | None
    data_as_of: datetime | None
    """UTC cutoff, preserved on cached responses."""
    cache: Literal["HIT", "MISS", "COALESCED"] | None
    rate_limit_per_minute: int | None
    """Cache hits count toward this allowance."""


@dataclass(frozen=True, slots=True)
class Rank:
    id: str
    label: str
    weight: int
    color: str | None
    """Hex colour, #rrggbb."""


@dataclass(frozen=True, slots=True)
class TeamSummary:
    id: str
    name: str
    prefix: str
    level: int
    role: TeamRole | None = None


@dataclass(frozen=True, slots=True)
class SelectedCosmetic:
    slot: str
    id: str
    name: str
    category: str
    preview: str | None


@dataclass(frozen=True, slots=True)
class Cosmetics:
    selected: list[SelectedCosmetic] | None
    """Empty when nothing is equipped; None when unavailable."""


@dataclass(frozen=True, slots=True)
class Skin:
    texture_url: str
    model: Literal["slim", "classic"]


@dataclass(frozen=True, slots=True)
class Location:
    gamemode: str


@dataclass(frozen=True, slots=True, kw_only=True)
class _Reply:
    meta: ResponseMeta = field(repr=False, compare=False)
    raw: dict[str, Any] = field(repr=False, compare=False)


@dataclass(frozen=True, slots=True, kw_only=True)
class PlayerProfile(_Reply):
    """Login history excludes server transfers and hidden sessions."""

    uuid: str
    name: str
    rank: Rank
    playtime_minutes: int | None
    first_login: int | None
    last_login: int | None
    last_logout: int | None
    """May predate last_login while the player is online."""
    online: bool | None
    """False when offline or hidden; None when presence is unknown."""
    location: Location | None
    """Only available while online is True."""
    level: int | None
    """Network level."""
    team: TeamSummary | None
    """None when unaffiliated."""
    cosmetics: Cosmetics
    skin: Skin | None = None


@dataclass(frozen=True, slots=True)
class StatRanks:
    """0 means unranked."""

    kills: int
    playtime: int


@dataclass(frozen=True, slots=True)
class CombatStats:
    kills: int
    deaths: int
    mob_kills: int
    damage_dealt: float
    """Damage in health points."""
    damage_taken: float


@dataclass(frozen=True, slots=True)
class WorldStats:
    blocks_mined: int
    blocks_placed: int
    items_crafted: int
    distance_km: float
    jumps: int
    fish_caught: int
    animals_bred: int
    villager_trades: int
    items_enchanted: int
    raids_won: int


@dataclass(frozen=True, slots=True)
class EventWins:
    bingo: int
    raffle: int
    chat_game: int


@dataclass(frozen=True, slots=True)
class EventStats:
    points: int
    points_lifetime: int
    tickets: int
    tickets_earned: int
    raffle_luck: float
    raffles_entered: int
    bingo_finished: int
    bingo_podiums: int
    wins: EventWins


@dataclass(frozen=True, slots=True)
class AuctionStats:

    active_listings: int
    sold: int
    sold_value: float
    bought: int
    bought_value: float
    open_orders: int


@dataclass(frozen=True, slots=True)
class BountyStats:
    on_head: float
    claimed: int
    claimed_value: float
    claimed_on: int


@dataclass(frozen=True, slots=True)
class NetWorth:
    total: float
    rank: int


@dataclass(frozen=True, slots=True, kw_only=True)
class SurvivalStats:
    """Only combat and world are required; unpublished groups are None."""

    combat: CombatStats
    world: WorldStats
    level: int | None = None
    """Minecraft experience level."""
    money: float | None = None
    playtime_minutes: int | None = None
    """Survival playtime; may differ from network playtime."""
    spawners: int | None = None
    ranks: StatRanks | None = None
    events: EventStats | None = None
    auction: AuctionStats | None = None
    bounty: BountyStats | None = None
    net_worth: NetWorth | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class PlayerStats(_Reply):
    uuid: str
    name: str
    survival: SurvivalStats


@dataclass(frozen=True, slots=True)
class Achievement:
    id: str
    name: str
    description: str
    progress: float
    target: float
    complete: bool
    unlocked_at: str | None
    """ISO 8601 UTC; None until unlocked."""


@dataclass(frozen=True, slots=True, kw_only=True)
class PlayerProgression(_Reply):

    uuid: str
    name: str
    level: int
    experience: float
    progress: float
    target: float
    maxed: bool
    achievements: list[Achievement] | None = None
    """None when unpublished."""


@dataclass(frozen=True, slots=True, kw_only=True)
class PlayerTeam(_Reply):
    uuid: str
    name: str
    team: TeamSummary | None
    """None when unaffiliated."""


@dataclass(frozen=True, slots=True)
class CrateKey:
    crate_id: str
    key_type: str
    available: int | None
    """0 means empty; None means unknown."""


@dataclass(frozen=True, slots=True, kw_only=True)
class PlayerCrateKeys(_Reply):
    """Missing crates have unpublished balances, not zero balances."""

    uuid: str
    name: str
    keys: list[CrateKey]


@dataclass(frozen=True, slots=True, kw_only=True)
class LeaderboardIndex(_Reply):
    """Supported type/period pairs."""

    types: list[LeaderboardType]
    periods: list[LeaderboardPeriod]
    boards: dict[LeaderboardType, list[LeaderboardPeriod]]


@dataclass(frozen=True, slots=True)
class LeaderboardRow:
    rank: int
    """One-based position."""
    uuid: str
    name: str
    """Name at capture time; may have changed since."""
    value: str
    """Formatted value, e.g. 3d 4h or $2.83B."""


@dataclass(frozen=True, slots=True, kw_only=True)
class Leaderboard(_Reply):
    """Up to 15 rows. Window bounds are ISO 8601 UTC, or None for all_time."""

    type: LeaderboardType
    period: LeaderboardPeriod
    rows: list[LeaderboardRow]
    stale: bool
    """True when outdated or the period has ended."""
    window_start: str | None = None
    window_end: str | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class Health(_Reply):
    ok: bool


def _camel(name: str) -> str:
    head, *rest = name.split("_")
    return head + "".join(part.capitalize() for part in rest)


@cache
def _hints(cls: type) -> dict[str, Any]:
    return get_type_hints(cls)


def _convert(tp: Any, value: Any) -> Any:
    if value is None:
        return None
    origin = get_origin(tp)
    if origin is Union or origin is types.UnionType:
        return _convert(next(arg for arg in get_args(tp) if arg is not type(None)), value)
    if origin is list:
        if not isinstance(value, list):
            raise TypeError(f"expected a JSON array, got {type(value).__name__}")
        return [_convert(get_args(tp)[0], item) for item in value]
    if dataclasses.is_dataclass(tp):
        return parse(tp, value)
    return value


def parse(cls: type[T], data: Any, **extra: Any) -> T:
    """Unknown keys are ignored; missing fields become None, including required fields.

    Object and array shapes are validated. Extra fields supply response metadata."""
    if not isinstance(data, dict):
        raise TypeError(f"expected a JSON object for {cls.__name__}, got {type(data).__name__}")
    hints = _hints(cls)
    values = {
        f.name: _convert(hints[f.name], data.get(_camel(f.name)))
        for f in dataclasses.fields(cls)  # type: ignore[arg-type]
        if f.name not in extra
    }
    return cls(**values, **extra)
