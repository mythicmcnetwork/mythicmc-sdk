MythicMC Public API (TypeScript)
======

TypeScript client for the MythicMC Public API. It has no runtime dependencies and
uses only `fetch`, `AbortSignal.timeout` and `setTimeout`, so it runs on Node 18 or
newer and on any other runtime that provides those, such as Bun.

Create an API key in the [developer portal](https://developer.mythicmc.net/) with your MythicMC forum account. Production keys use development limits until approved.

### Install

```sh
npm install @mythicmcnetwork/typescript-sdk
```

### Build from source

```sh
git clone https://github.com/mythicmcnetwork/mythicmc-sdk.git
cd mythicmc-sdk/typescript
npm install
```

### Usage

```ts
import { MythicMC, NotFoundError } from '@mythicmcnetwork/typescript-sdk'

const api = new MythicMC({ apiKey: process.env.MYTHICMC_API_KEY! })

const player = await api.getPlayer('Vicente_1313') // username or UUID
console.log(player.rank.label, player.online ?? 'unknown')
console.log(player.meta.dataAsOf) // UTC cutoff this response reflects

try {
  const { survival } = await api.getPlayerStats('Vicente_1313')
  console.log(survival.combat.kills, survival.netWorth?.total ?? 'unpublished')
} catch (error) {
  if (error instanceof NotFoundError) console.log('no published Survival statistics')
  else throw error
}

const board = await api.getLeaderboard('kills', 'weekly')
for (const row of board.rows) console.log(row.rank, row.name, row.value)
```

| Method | Endpoint |
| --- | --- |
| `getPlayer(id)` | `GET /v1/players/{id}` |
| `getPlayerStats(id)` | `GET /v1/players/{id}/stats` |
| `getPlayerProgression(id)` | `GET /v1/players/{id}/progression` |
| `getPlayerTeam(id)` | `GET /v1/players/{id}/team` |
| `getPlayerCrateKeys(id)` | `GET /v1/players/{id}/crate-keys` |
| `listLeaderboards()` | `GET /v1/leaderboards` |
| `getLeaderboard(type, period)` | `GET /v1/leaderboards/{type}/{period}` |
| `health()` | `GET /health` |

`id` is a username, case-insensitive, or a UUID with or without dashes.

The [full API reference](https://developer.mythicmc.net/#reference) includes additional endpoints you can call directly over HTTP.

Every reply is the response body, with the response headers parsed into a
non-enumerable `meta` property, so `JSON.stringify(reply)` is the body alone.

### Options

| Option | Default | |
| --- | --- | --- |
| `apiKey` | omitted | Required for keyed endpoints; omit for public leaderboards and health. |
| `baseUrl` | `https://api.mythicmc.net` | |
| `timeoutMs` | `10000` | Per attempt. |
| `maxRetries` | `2` | Retries after a `429`, each waiting for `Retry-After`, or a second when there is none. A wait over a minute throws instead. `0` disables. |
| `fetch` | global `fetch` | Replace the transport, for tests, proxies or instrumentation. |

### Errors

Every response the client cannot turn into data throws a `MythicMCError`. `status` is
the HTTP status; `message` is the API's `error` string, or a stand-in when the
response carried none.

| Class | Status | |
| --- | --- | --- |
| `BadRequestError` | 400 | Not a valid username or UUID. |
| `AuthenticationError` | 401 | Missing or invalid key. |
| `NotFoundError` | 404 | Unknown player or board, or no published Survival statistics. |
| `RateLimitError` | 429 | Retries exhausted, or the wait was too long. `retryAfter` is seconds, or null. |
| `UnavailableError` | 503 | Not published yet, an ambiguous username, or a server fault. Retrying later can work. |

Any other status, and a 2xx whose body is not a JSON object, throws `MythicMCError`
itself. Network failures and timeouts reject with the transport's own error.

### Examples

[examples](examples) holds one file per group of endpoints. They import the client
from `src/`, and Node 22.18+ and Node 24+ strip TypeScript types themselves, so there
is no build step:

```sh
MYTHICMC_API_KEY=mmc_... node examples/get-player.ts Vicente_1313
```

Set `MYTHICMC_API_URL` to run them against a mock server instead of the live API.

### Development

```sh
npm install
npm run typecheck && npm test && npm run build
```

`npm run typecheck` covers `src`, `test` and `examples`.

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

Follow `nextCursor` (Python: `next_cursor`) until null, passing the same filters
to each call. Cursors expire after 15 minutes. Match history retains up to 2,000
finished public matches from the last 15 days; private duels and bot matches are
excluded.
