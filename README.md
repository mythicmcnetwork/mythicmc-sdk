<p align="center">
  <img src="https://cdn.mythicmc.net/sdk/logo.png?v=5764cfc9e6aa" alt="MythicMC API SDK" width="640">
</p>

<p align="center">
  <strong>Official TypeScript and Python SDKs for MythicMC.</strong><br>
  Player profiles, Survival statistics, progression, teams, crate keys, and leaderboards.
</p>

<p align="center">
  <a href="https://developer.mythicmc.net/">Developer portal</a> ·
  <a href="https://developer.mythicmc.net/#reference">API reference</a> ·
  <a href="typescript/README.md">TypeScript</a> ·
  <a href="python/README.md">Python</a> ·
  <a href="openapi.yaml">OpenAPI</a> ·
  <a href="https://github.com/mythicmcnetwork/mythicmc-sdk/issues">Issues</a>
</p>

---

## Get started

| SDK | Package | Runtime | |
| --- | --- | --- | --- |
| **TypeScript** | `@mythicmcnetwork/typescript-sdk` | Node.js 18+ | [Installation & usage →](typescript/README.md) |
| **Python** | `mythicmc-sdk` | Python 3.10+ | [Installation & usage →](python/README.md) |

TypeScript has no runtime dependencies. Python includes synchronous and asynchronous clients, built on `httpx`.

Create an API key in the [developer portal](https://developer.mythicmc.net/) using your MythicMC forum account. Production keys use development limits until approved.

### TypeScript

```sh
npm install @mythicmcnetwork/typescript-sdk
```

```ts
import { MythicMC } from '@mythicmcnetwork/typescript-sdk'

const api = new MythicMC({ apiKey: process.env.MYTHICMC_API_KEY! })
const player = await api.getPlayer('Vicente_1313')

console.log(player.name, player.rank.label)
console.log(player.meta.dataAsOf)
```

### Python

```sh
pip install mythicmc-sdk
```

```python
import os
from mythicmc import MythicMC

with MythicMC(os.environ["MYTHICMC_API_KEY"]) as api:
    player = api.get_player("Vicente_1313")
    print(player.name, player.rank.label)
    print(player.meta.data_as_of)
```

Both clients handle authentication, response metadata, typed errors, and rate-limit retries. Keep API keys server-side.

## Explore

| Resource | TypeScript | Python |
| --- | --- | --- |
| Player profiles | [Example](typescript/examples/get-player.ts) | [Example](python/examples/get_player.py) |
| Survival statistics | [Example](typescript/examples/get-player-stats.ts) | [Example](python/examples/get_player_stats.py) |
| Network progression | [Example](typescript/examples/get-player-progression.ts) | [Example](python/examples/get_player_progression.py) |
| Teams | [Example](typescript/examples/get-player-team.ts) | [Example](python/examples/get_player_team.py) |
| Crate keys | [Example](typescript/examples/get-player-crate-keys.ts) | [Example](python/examples/get_player_crate_keys.py) |
| Leaderboards | [Example](typescript/examples/get-leaderboards.ts) | [Example](python/examples/get_leaderboards.py) |

For concurrent Python requests, see [async lookup](python/examples/async_lookup.py). The [OpenAPI 3.1 specification](openapi.yaml) covers the SDK endpoints. The [full API reference](https://developer.mythicmc.net/#reference) also documents additional player directories, history, network status, and catalogs that can be called directly over HTTP.

## Working with the data

- **Delayed snapshots.** Gameplay data is at least five minutes old. `meta.dataAsOf` / `meta.data_as_of` identifies the response cutoff.
- **Unknown values.** Null values and missing statistic groups mean unknown, not zero.
- **Timestamps.** Numeric timestamps use Unix milliseconds.
- **Leaderboards.** On Survival boards, `value` is the raw number as a string, such as `"2183269850.41"` for net worth; it is never abbreviated. Playtime is in minutes; kills and wins are counts. Apply display formatting in your app. Duels boards return a numeric `value` and a `displayValue` such as `"1,234 wins"`. Check `stale`; daily, weekly, and monthly Survival boards also include `windowStart` and `windowEnd`, while `all_time` boards do not.
- **Rate limits.** Limits apply per key, per minute; cache hits count. Both clients retry `429` twice by default, respecting `Retry-After`. Waits over 60 seconds raise a rate-limit error.
- **Errors.** `404` means an unknown resource or missing player data. `503` can mean unavailable data, an ambiguous username, or a server failure. See each SDK's error reference.

## Contributing

[Open an issue](https://github.com/mythicmcnetwork/mythicmc-sdk/issues) for bugs or questions. Changes to response shapes should update the OpenAPI specification, both SDKs, and their tests together.

## License & API terms

The SDK code is [MIT licensed](LICENSE). Access to the API and use of its data are governed separately by the [MythicMC Terms of Service](https://mythicmc.net/terms), including restrictions on model training, selling API data and sharing API keys.

## Previous release: API 1.1.0

See the [1.1.0 changelog](changelog/1.1.0-changelog.md) for that release’s changes.

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

## API 2.0.0: Duels

Upgrade to SDK 2.0.0. The API no longer accepts `practice` as a URL alias:
replace `/stats/practice` with `/stats/duels` and
`/gamemodes/practice/leaderboards` with `/gamemodes/duels/leaderboards`, including
metric and period suffixes. The `/v1` prefix stays unchanged. The SDK's Duels
method names already use the canonical routes and do not need renaming.

Duels now has typed player stats, summaries, ladder rules, kits, match history
and leaderboards. Wins support rolling `daily`, `weekly`, `monthly` windows and
`all_time`. Ratings require a `kit` and `all_time`; streaks use `all_time` without
a kit. Get available kit IDs from leaderboard discovery.

Leaderboards and health need no API key. Other endpoints require one. Existing
keyed clients work unchanged. Gameplay data is delayed by at least five minutes
and filtered for player privacy. Unknown or stale counts can be null.

```ts
import { MythicMC } from '@mythicmcnetwork/typescript-sdk'

const api = new MythicMC()
const index = await api.listDuelsLeaderboards()
const board = await api.getDuelsLeaderboard('wins', 'weekly', { limit: 25 })
const kit = index.kits[0]
if (kit) {
  const ratings = await api.getDuelsLeaderboard('rating', 'all_time', { kit })
  console.log(ratings.rows)
}

const keyed = new MythicMC({ apiKey: process.env.MYTHICMC_API_KEY! })
const stats = await keyed.getPlayerDuelsStats('Vicente_1313')
const matches = await keyed.listDuelsMatches({ player: stats.uuid, limit: 25 })
```

New methods: `getPlayerDuelsStats`, `getDuels`, `getDuelsLadder`,
`listDuelsKits`, `getDuelsKit`, `listDuelsMatches`, `getDuelsMatch`,
`listDuelsLeaderboards`, and `getDuelsLeaderboard`.

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
