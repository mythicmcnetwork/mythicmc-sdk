MythicMC Public API (TypeScript)
======

TypeScript client for the MythicMC Public API. It has no runtime dependencies and
uses only `fetch`, `AbortSignal.timeout` and `setTimeout`, so it runs on Node 18 or
newer and on any other runtime that provides those, such as Bun.

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

Every reply is the response body, with the response headers parsed into a
non-enumerable `meta` property, so `JSON.stringify(reply)` is the body alone.

### Options

| Option | Default | |
| --- | --- | --- |
| `apiKey` | required | Your API key. |
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
