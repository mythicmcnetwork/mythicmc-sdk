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
| `api_key` | required | Positional; the rest are keyword-only. |
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
