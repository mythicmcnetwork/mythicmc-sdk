MythicMC Public API (Python)
======

Python client for the MythicMC Public API. Python 3.10 or newer, synchronous and
asynchronous, built on [httpx](https://www.python-httpx.org/).

Create an API key in the [developer portal](https://developer.mythicmc.net/) with your MythicMC forum account. Production keys use development limits until approved.

### Install

```sh
pip install mythicmc-sdk
```

### Install from source

```sh
pip install "git+https://github.com/mythicmcnetwork/mythicmc-sdk.git#subdirectory=python"
```

### Usage

```python
import os
from mythicmc import MythicMC, NotFoundError

with MythicMC(os.environ["MYTHICMC_API_KEY"]) as api:
    player = api.get_player("Vicente_1313")  # username or UUID
    print(player.rank.label, "unknown" if player.online is None else player.online)
    print(player.meta.data_as_of)  # UTC cutoff this response reflects

    try:
        survival = api.get_player_stats("Vicente_1313").survival
        print(survival.combat.kills, survival.net_worth.total if survival.net_worth else "unpublished")
    except NotFoundError:
        print("no published Survival statistics")

    for row in api.get_leaderboard("kills", "weekly").rows:
        print(row.rank, row.name, row.value)
```

`AsyncMythicMC` has the same methods as coroutines, for Discord bots and other
asyncio programs:

```python
import asyncio
import os
from mythicmc import AsyncMythicMC

async def main() -> None:
    async with AsyncMythicMC(os.environ["MYTHICMC_API_KEY"]) as api:
        profile, team = await asyncio.gather(api.get_player("Vicente_1313"), api.get_player_team("Vicente_1313"))
    print(profile.rank.label, team.team.name if team.team else "no team")

asyncio.run(main())
```

Both clients hold an httpx connection pool. Use them as context managers, or call
`close()` yourself — `await api.close()` on the asynchronous one.

| Method | Endpoint |
| --- | --- |
| `get_player(id)` | `GET /v1/players/{id}` |
| `get_player_stats(id)` | `GET /v1/players/{id}/stats` |
| `get_player_progression(id)` | `GET /v1/players/{id}/progression` |
| `get_player_team(id)` | `GET /v1/players/{id}/team` |
| `get_player_crate_keys(id)` | `GET /v1/players/{id}/crate-keys` |
| `list_leaderboards()` | `GET /v1/leaderboards` |
| `get_leaderboard(type, period)` | `GET /v1/leaderboards/{type}/{period}` |
| `health()` | `GET /health` |

`id` is a username, case-insensitive, or a UUID with or without dashes.

The [full API reference](https://developer.mythicmc.net/#reference) includes additional endpoints you can call directly over HTTP.

Replies are frozen dataclasses whose `snake_case` attributes come from the JSON's
`camelCase` keys. Each reply also carries `meta`, parsed from the response headers,
and `raw`, the decoded JSON body as a `dict`. Keys the models do not know about are
ignored, so a field the API adds later reaches you through `raw` rather than breaking
an older client.

### Options

| Argument | Default | |
| --- | --- | --- |
| `api_key` | `None` | Required for keyed endpoints; omit for public leaderboards and health. Positional; the rest are keyword-only. |
| `base_url` | `https://api.mythicmc.net` | |
| `timeout` | `10.0` | Seconds, per attempt. |
| `max_retries` | `2` | Retries after a `429`, each waiting for `Retry-After`, or a second when there is none. A wait over a minute raises instead. `0` disables. |
| `transport` | `None` | An httpx transport, for tests or proxies. |

### Errors

Every response the client cannot turn into data raises a `MythicMCError`. `status` is
the HTTP status; `message` is the API's `error` string, or a stand-in when the
response carried none.

| Class | Status | |
| --- | --- | --- |
| `BadRequestError` | 400 | Not a valid username or UUID. |
| `AuthenticationError` | 401 | Missing or invalid key. |
| `NotFoundError` | 404 | Unknown player or board, or no published Survival statistics. |
| `RateLimitError` | 429 | Retries exhausted. `retry_after` is seconds, or `None`. |
| `UnavailableError` | 503 | Not published yet, an ambiguous username, or a server fault. Retrying later can work. |

Any other status, and a 2xx whose body is not the shape the model declares, raises
`MythicMCError` itself. Network failures and timeouts raise httpx's own exceptions.

### Examples

[examples](examples) holds one file per group of endpoints, plus `async_lookup.py`
for `AsyncMythicMC`.

```sh
pip install .
MYTHICMC_API_KEY=mmc_... python examples/get_player.py Vicente_1313
```

Set `MYTHICMC_API_URL` to run them against a mock server instead of the live API.

### Development

```sh
pip install -e .
python -m unittest discover -s tests
```

## Previous release: API 1.1.0

See [release notes](../RELEASE_NOTES.md) for breaking changes and migration instructions.

| Resource | TypeScript | Python (sync and async) |
| --- | --- | --- |
| SurvivalShop | `getSurvivalShop` | `get_survival_shop` |
| PlayerShopBundles | `getPlayerShopBundles` | `get_player_shop_bundles` |
| BountyClaimPage | `listBountyClaims` | `list_bounty_claims` |
| BountyClaim | `getBountyClaim` | `get_bounty_claim` |
| EventDetails | `getEventDetails` | `get_event_details` |
| EventSchedulePage | `listEventSchedules` | `list_event_schedules` |
| EventSchedule | `getEventSchedule` | `get_event_schedule` |
| StallPage | `listStalls` | `list_stalls` |
| Stall | `getStall` | `get_stall` |
| BountyPage | `listBounties` | `list_bounties` |
| Bounty | `getBounty` | `get_bounty` |

List methods take pagination options (`{ limit, cursor }` in TypeScript; keyword arguments in Python). Follow `nextCursor` / `next_cursor` until null. IDs are URL-encoded. Shop reads optionally accept an ETag and return null / None on 304; otherwise use `reply.meta.etag` for the next conditional request.

## API 1.2.0 — Duels

Duels now has typed player stats, summaries, ladder rules, kits, match history
and leaderboards. Wins support rolling `daily`, `weekly`, `monthly` windows and
`all_time`. Ratings require a `kit` and `all_time`; streaks use `all_time` without
a kit. Get available kit IDs from leaderboard discovery.

Leaderboards and health need no API key. Other endpoints require one. Existing
keyed clients work unchanged. Gameplay data is delayed by at least five minutes
and filtered for player privacy. Unknown or stale counts can be null.

```python
import os
from mythicmc import MythicMC

with MythicMC() as api:
    index = api.list_duels_leaderboards()
    board = api.get_duels_leaderboard("wins", "weekly", limit=25)
    if index.kits:
        ratings = api.get_duels_leaderboard("rating", "all_time", kit=index.kits[0])
        print(ratings.rows)

with MythicMC(os.environ["MYTHICMC_API_KEY"]) as api:
    stats = api.get_player_duels_stats("Vicente_1313")
    matches = api.list_duels_matches(player=stats.uuid, limit=25)
```

New methods: `get_player_duels_stats`, `get_duels`, `get_duels_ladder`,
`list_duels_kits`, `get_duels_kit`, `list_duels_matches`, `get_duels_match`,
`list_duels_leaderboards`, and `get_duels_leaderboard`. All are also available
on `AsyncMythicMC`; use `async with` and await each call.

Follow `nextCursor` (Python: `next_cursor`) until null, passing the same filters
to each call. Cursors expire after 15 minutes. Match history retains up to 2,000
finished public matches from the last 15 days; private duels and bot matches are
excluded.
