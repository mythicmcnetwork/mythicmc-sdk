import assert from 'node:assert/strict'
import { test } from 'node:test'
import {
  AuthenticationError,
  BadRequestError,
  MythicMC,
  MythicMCError,
  NotFoundError,
  RateLimitError,
  UnavailableError,
} from '../src/index.ts'

type Call = { url: string; headers: Record<string, string> }

function stub(...responses: Response[]) {
  const calls: Call[] = []
  const fetch = (async (url: string, init: RequestInit) => {
    calls.push({ url, headers: init.headers as Record<string, string> })
    const next = responses.shift()
    if (!next) throw new Error('unexpected request')
    return next
  }) as typeof globalThis.fetch
  return { calls, fetch }
}

const json = (body: unknown, status = 200, headers: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), { status, headers: { 'content-type': 'application/json', ...headers } })

const limited = (retryAfter?: string) =>
  json({ error: 'too many requests' }, 429, retryAfter === undefined ? {} : { 'Retry-After': retryAfter })

test('sends the key as a bearer token and parses response metadata', async () => {
  const { calls, fetch } = stub(
    json({ uuid: '53eefb84-3ed8-4efb-9bb0-ddaaf3e01e9f', name: 'Vicente_1313' }, 200, {
      'X-Data-Delay-Seconds': '300',
      'X-Data-As-Of': '2026-09-19T12:00:00.000Z',
      'X-Cache': 'HIT',
      'X-RateLimit-Limit-Minute': '120',
    }),
  )
  const player = await new MythicMC({ apiKey: 'mmc_test', fetch }).getPlayer('Vicente_1313')
  assert.equal(calls[0]?.url, 'https://api.mythicmc.net/v1/players/Vicente_1313')
  assert.equal(calls[0]?.headers.Authorization, 'Bearer mmc_test')
  assert.equal(calls[0]?.headers.Accept, 'application/json')
  assert.match(calls[0]?.headers['User-Agent'] ?? '', /^mythicmc-api-ts\/\d+\.\d+\.\d+$/)
  assert.equal(player.name, 'Vicente_1313')
  assert.deepEqual(player.meta, {
    etag: null,
    dataDelaySeconds: 300,
    dataAsOf: new Date('2026-09-19T12:00:00.000Z'),
    cache: 'HIT',
    rateLimitPerMinute: 120,
  })
  assert.deepEqual(Object.keys(player), ['uuid', 'name'])
  assert.equal(JSON.stringify(player), '{"uuid":"53eefb84-3ed8-4efb-9bb0-ddaaf3e01e9f","name":"Vicente_1313"}')
})

test('leaves meta null when the headers are absent or unusable', async () => {
  const { fetch } = stub(json({ ok: true }, 200, { 'X-Cache': 'BYPASS', 'X-Data-As-Of': 'shortly' }))
  const reply = await new MythicMC({ apiKey: 'k', fetch }).health()
  assert.deepEqual(reply.meta, { etag: null, dataDelaySeconds: null, dataAsOf: null, cache: null, rateLimitPerMinute: null })
})

test('builds every route and encodes path segments', async () => {
  const { calls, fetch } = stub(...Array.from({ length: 8 }, () => json({})))
  const api = new MythicMC({ apiKey: 'k', fetch, baseUrl: 'http://localhost:8080/' })
  await api.getPlayer('a/b')
  await api.getPlayerStats('.Bedrock')
  await api.getPlayerProgression('n')
  await api.getPlayerTeam('n')
  await api.getPlayerCrateKeys('n')
  await api.listLeaderboards()
  await api.getLeaderboard('networth', 'all_time')
  await api.health()
  assert.deepEqual(
    calls.map(call => call.url.replace('http://localhost:8080', '')),
    [
      '/v1/players/a%2Fb',
      '/v1/players/.Bedrock/stats',
      '/v1/players/n/progression',
      '/v1/players/n/team',
      '/v1/players/n/crate-keys',
      '/v1/leaderboards',
      '/v1/leaderboards/networth/all_time',
      '/health',
    ],
  )
})

test('maps statuses to error classes', async () => {
  const cases = [
    [400, BadRequestError, 'invalid player identifier'],
    [401, AuthenticationError, 'missing or invalid API key'],
    [404, NotFoundError, 'unknown player'],
    [503, UnavailableError, 'required data is unavailable'],
    [502, MythicMCError, 'bad gateway'],
  ] as const
  for (const [status, type, message] of cases) {
    const { fetch } = stub(json({ error: message }, status))
    await assert.rejects(new MythicMC({ apiKey: 'k', fetch }).getPlayer('n'), error => {
      assert.ok(error instanceof type)
      assert.equal(error.status, status)
      assert.equal(error.message, message)
      return true
    })
  }
})

test('falls back to the status when an error body is not JSON', async () => {
  const { fetch } = stub(new Response('<html>502</html>', { status: 502 }))
  await assert.rejects(new MythicMC({ apiKey: 'k', fetch }).health(), { name: 'MythicMCError', message: 'HTTP 502' })
})

test('rejects a 200 body that is not a JSON object', async () => {
  for (const body of ['null', '12', '"Vicente_1313"', 'not json at all', '']) {
    const { fetch } = stub(new Response(body, { status: 200, headers: { 'content-type': 'application/json' } }))
    await assert.rejects(new MythicMC({ apiKey: 'k', fetch }).health(), error => {
      assert.ok(error instanceof MythicMCError, `${body} threw ${error}`)
      assert.equal(error.status, 200)
      return true
    })
  }
})

test('retries a 429 after Retry-After, then succeeds', async () => {
  const { calls, fetch } = stub(limited('0'), json({ ok: true }))
  const reply = await new MythicMC({ apiKey: 'k', fetch }).health()
  assert.equal(reply.ok, true)
  assert.equal(calls.length, 2)
})

test('makes one attempt plus maxRetries', async () => {
  const { calls, fetch } = stub(limited('0'), limited('0'), limited('0'))
  await assert.rejects(new MythicMC({ apiKey: 'k', fetch }).health(), RateLimitError)
  assert.equal(calls.length, 3)
})

test('waits a second when a 429 carries no Retry-After', async () => {
  const { calls, fetch } = stub(limited(), json({ ok: true }))
  const started = Date.now()
  await new MythicMC({ apiKey: 'k', fetch }).health()
  assert.equal(calls.length, 2)
  assert.ok(Date.now() - started >= 900, 'retried without waiting out the window')
})

test('hands back a Retry-After longer than a minute instead of sleeping through it', async () => {
  const { calls, fetch } = stub(limited('3600'))
  await assert.rejects(new MythicMC({ apiKey: 'k', fetch }).health(), error => {
    assert.ok(error instanceof RateLimitError)
    assert.equal(error.retryAfter, 3600)
    return true
  })
  assert.equal(calls.length, 1)
})

test('throws RateLimitError once retries are exhausted', async () => {
  const { calls, fetch } = stub(limited('7'))
  await assert.rejects(new MythicMC({ apiKey: 'k', fetch, maxRetries: 0 }).health(), error => {
    assert.ok(error instanceof RateLimitError)
    assert.equal(error.retryAfter, 7)
    return true
  })
  assert.equal(calls.length, 1)
})

test('aborts an attempt that outlives timeoutMs', async () => {
  // AbortSignal.timeout does not keep the event loop alive.
  const fetch = ((_url: string, init: RequestInit) =>
    new Promise<Response>((_resolve, reject) => {
      const stuck = setTimeout(() => reject(new Error('the attempt was never aborted')), 1000)
      init.signal?.addEventListener('abort', () => {
        clearTimeout(stuck)
        reject(init.signal?.reason)
      })
    })) as unknown as typeof globalThis.fetch
  await assert.rejects(new MythicMC({ apiKey: 'k', fetch, timeoutMs: 5 }).health(), { name: 'TimeoutError' })
})

test('rejects an explicitly empty API key', () => {
  assert.throws(() => new MythicMC({ apiKey: '' }), TypeError)
})

test('API 1.1.0 routes encode identifiers and pagination cursors', async () => {
  const { calls, fetch } = stub(...Array.from({ length: 11 }, () => json({})))
  const api = new MythicMC({ apiKey: 'k', fetch })
  await api.getSurvivalShop()
  await api.getPlayerShopBundles('a/b')
  await api.listBountyClaims({ limit: 2, cursor: 'a+/=' })
  await api.getBountyClaim('a/b')
  await api.getEventDetails('a/b')
  await api.listEventSchedules({ limit: 2, cursor: 'a+/=' })
  await api.getEventSchedule('a/b')
  await api.listStalls({ limit: 2, cursor: 'a+/=' })
  await api.getStall('a/b')
  await api.listBounties({ limit: 2, cursor: 'a+/=' })
  await api.getBounty('a/b')
  assert.deepEqual(calls.map(call => call.url), ["https://api.mythicmc.net/v1/survival/shop", "https://api.mythicmc.net/v1/players/a%2Fb/shop-bundles", "https://api.mythicmc.net/v1/survival/bounty-claims?limit=2&cursor=a%2B%2F%3D", "https://api.mythicmc.net/v1/survival/bounty-claims/a%2Fb", "https://api.mythicmc.net/v1/survival/events/a%2Fb/details", "https://api.mythicmc.net/v1/survival/event-schedules?limit=2&cursor=a%2B%2F%3D", "https://api.mythicmc.net/v1/survival/event-schedules/a%2Fb", "https://api.mythicmc.net/v1/survival/stalls?limit=2&cursor=a%2B%2F%3D", "https://api.mythicmc.net/v1/survival/stalls/a%2Fb", "https://api.mythicmc.net/v1/survival/bounties?limit=2&cursor=a%2B%2F%3D", "https://api.mythicmc.net/v1/survival/bounties/a%2Fb"])
})

test('conditional shop reads expose ETags and handle bodyless 304 responses', async () => {
  const { calls, fetch } = stub(json({ revision: 'abc', items: [{ buyPrice: null }] }, 200, { ETag: '"abc"' }), new Response(null, { status: 304 }))
  const api = new MythicMC({ apiKey: 'k', fetch })
  const shop = await api.getSurvivalShop()
  assert.equal(shop?.meta.etag, '"abc"')
  assert.equal(shop?.items[0]?.buyPrice, null)
  assert.equal(await api.getSurvivalShop(shop!.meta.etag!), null)
  assert.equal(calls[1]?.headers['If-None-Match'], '"abc"')
})

test('Duels methods encode identifiers, filters and cursors without requiring a key', async () => {
  const { calls, fetch } = stub(...Array.from({ length: 9 }, () => json({})))
  const api = new MythicMC({ fetch })
  await api.getPlayerDuelsStats('a/b')
  await api.getDuels()
  await api.getDuelsLadder()
  await api.listDuelsKits({ limit: 2, cursor: 'a+/=' })
  await api.getDuelsKit('a/b')
  await api.listDuelsMatches({ player: 'A B', limit: 2, cursor: 'a+/=' })
  await api.getDuelsMatch('a/b')
  await api.listDuelsLeaderboards()
  await api.getDuelsLeaderboard('rating', 'all_time', { kit: 'a/b', limit: 2, cursor: 'a+/=' })
  assert.deepEqual(calls.map(call => call.url.replace('https://api.mythicmc.net', '')), [
    '/v1/players/a%2Fb/stats/duels', '/v1/duels', '/v1/duels/ladder',
    '/v1/duels/kits?limit=2&cursor=a%2B%2F%3D', '/v1/duels/kits/a%2Fb',
    '/v1/duels/matches?limit=2&cursor=a%2B%2F%3D&player=A+B', '/v1/duels/matches/a%2Fb',
    '/v1/gamemodes/duels/leaderboards',
    '/v1/gamemodes/duels/leaderboards/rating/all_time?limit=2&cursor=a%2B%2F%3D&kit=a%2Fb',
  ])
  assert.ok(calls.every(call => call.headers.Authorization === undefined))
  assert.doesNotThrow(() => new MythicMC())
})

test('anonymous clients preserve server authentication errors for keyed endpoints', async () => {
  const { fetch } = stub(json({ error: 'missing or invalid API key' }, 401))
  await assert.rejects(new MythicMC({ fetch }).getDuels(), AuthenticationError)
})
