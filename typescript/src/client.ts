import { AuthenticationError, BadRequestError, MythicMCError, NotFoundError, RateLimitError, UnavailableError } from './errors.ts'
import type {
  DuelsLeaderboardIndex, DuelsLadder, DuelsLeaderboard, DuelsMatchPage, PlayerDuelsStats, DuelsMatch, DuelsSummary, DuelsKitPage, DuelsKit, DuelsLeaderboardMetric, DuelsLeaderboardOptions, DuelsMatchOptions,
  Bounty, BountyClaim, BountyClaimPage, BountyPage, EventDetails, EventSchedule, EventSchedulePage, PlayerShopBundles, Stall, StallPage, SurvivalShop, PageOptions,
  Health,
  Leaderboard,
  LeaderboardIndex,
  LeaderboardPeriod,
  LeaderboardType,
  PlayerCrateKeys,
  PlayerProfile,
  PlayerProgression,
  PlayerStats,
  PlayerTeam,
  Reply,
  ResponseMeta,
} from './types.ts'

export const VERSION = '1.2.0'
export const DEFAULT_BASE_URL = 'https://api.mythicmc.net'

const MAX_RETRY_WAIT_SECONDS = 60

export interface MythicMCOptions {
  /** Omit for public leaderboards and health. Keep keys server-side. */
  apiKey?: string
  /** Defaults to `DEFAULT_BASE_URL`; trailing slashes are ignored. */
  baseUrl?: string
  /** Optional transport override. Defaults to global `fetch`. */
  fetch?: typeof fetch
  /** Per-attempt timeout in milliseconds, including the body. Default: 10000. */
  timeoutMs?: number
  /** 429 retries, default 2. Uses Retry-After or 1s; waits over 60s raise RateLimitError. */
  maxRetries?: number
}

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))
const integer = (value: string | null) => (value !== null && /^\d+$/.test(value) ? Number(value) : null)

export class MythicMC {
  readonly #baseUrl: string
  readonly #headers: Record<string, string>
  readonly #fetch: typeof fetch
  readonly #timeoutMs: number
  readonly #maxRetries: number

  constructor(options: MythicMCOptions = {}) {
    if (options.apiKey !== undefined && !options.apiKey) throw new TypeError('apiKey is required')
    this.#baseUrl = (options.baseUrl || DEFAULT_BASE_URL).replace(/\/+$/, '')
    this.#headers = { Accept: 'application/json' }
    if (options.apiKey) this.#headers.Authorization = `Bearer ${options.apiKey}`
    if (typeof window === 'undefined') this.#headers['User-Agent'] = `mythicmc-api-ts/${VERSION}`
    this.#fetch = options.fetch ?? globalThis.fetch.bind(globalThis)
    this.#timeoutMs = options.timeoutMs ?? 10000
    this.#maxRetries = options.maxRetries ?? 2
  }

  /** @param id Case-insensitive username or UUID, with or without dashes. */
  getPlayer(id: string): Promise<Reply<PlayerProfile>> {
    return this.#get(`/v1/players/${encodeURIComponent(id)}`)
  }

  /** @throws NotFoundError if no Survival snapshot is published. */
  getPlayerStats(id: string): Promise<Reply<PlayerStats>> {
    return this.#get(`/v1/players/${encodeURIComponent(id)}/stats`)
  }

  getPlayerProgression(id: string): Promise<Reply<PlayerProgression>> {
    return this.#get(`/v1/players/${encodeURIComponent(id)}/progression`)
  }

  getPlayerTeam(id: string): Promise<Reply<PlayerTeam>> {
    return this.#get(`/v1/players/${encodeURIComponent(id)}/team`)
  }

  getPlayerCrateKeys(id: string): Promise<Reply<PlayerCrateKeys>> {
    return this.#get(`/v1/players/${encodeURIComponent(id)}/crate-keys`)
  }

  getPlayerDuelsStats(id: string): Promise<Reply<PlayerDuelsStats>> {
    return this.#get(`/v1/players/${encodeURIComponent(id)}/stats/duels`)
  }

  getDuels(): Promise<Reply<DuelsSummary>> {
    return this.#get(`/v1/duels`)
  }

  getDuelsLadder(): Promise<Reply<DuelsLadder>> {
    return this.#get(`/v1/duels/ladder`)
  }

  listDuelsKits(options: PageOptions = {}): Promise<Reply<DuelsKitPage>> {
    return this.#get(`/v1/duels/kits` + pageQuery(options))
  }

  getDuelsKit(kit: string): Promise<Reply<DuelsKit>> {
    return this.#get(`/v1/duels/kits/${encodeURIComponent(kit)}`)
  }

  listDuelsMatches(options: DuelsMatchOptions = {}): Promise<Reply<DuelsMatchPage>> {
    return this.#get(`/v1/duels/matches` + pageQuery(options))
  }

  getDuelsMatch(id: string): Promise<Reply<DuelsMatch>> {
    return this.#get(`/v1/duels/matches/${encodeURIComponent(id)}`)
  }

  listDuelsLeaderboards(): Promise<Reply<DuelsLeaderboardIndex>> {
    return this.#get(`/v1/gamemodes/duels/leaderboards`)
  }

  getDuelsLeaderboard(metric: DuelsLeaderboardMetric, period: LeaderboardPeriod, options: DuelsLeaderboardOptions = {}): Promise<Reply<DuelsLeaderboard>> {
    return this.#get(`/v1/gamemodes/duels/leaderboards/${encodeURIComponent(metric)}/${encodeURIComponent(period)}` + pageQuery(options))
  }

  listLeaderboards(): Promise<Reply<LeaderboardIndex>> {
    return this.#get('/v1/leaderboards')
  }

  /** Networth supports `all_time` only. */
  getLeaderboard(type: LeaderboardType, period: LeaderboardPeriod): Promise<Reply<Leaderboard>> {
    return this.#get(`/v1/leaderboards/${encodeURIComponent(type)}/${encodeURIComponent(period)}`)
  }

  getSurvivalShop(ifNoneMatch?: string): Promise<Reply<SurvivalShop> | null> {
    return this.#get(`/v1/survival/shop`, ifNoneMatch)
  }

  getPlayerShopBundles(id: string): Promise<Reply<PlayerShopBundles>> {
    return this.#get(`/v1/players/${encodeURIComponent(id)}/shop-bundles`)
  }

  listBountyClaims(options: PageOptions = {}): Promise<Reply<BountyClaimPage>> {
    return this.#get(`/v1/survival/bounty-claims` + pageQuery(options))
  }

  getBountyClaim(claimId: string): Promise<Reply<BountyClaim>> {
    return this.#get(`/v1/survival/bounty-claims/${encodeURIComponent(claimId)}`)
  }

  getEventDetails(eventId: string): Promise<Reply<EventDetails>> {
    return this.#get(`/v1/survival/events/${encodeURIComponent(eventId)}/details`)
  }

  listEventSchedules(options: PageOptions = {}): Promise<Reply<EventSchedulePage>> {
    return this.#get(`/v1/survival/event-schedules` + pageQuery(options))
  }

  getEventSchedule(scheduleId: string): Promise<Reply<EventSchedule>> {
    return this.#get(`/v1/survival/event-schedules/${encodeURIComponent(scheduleId)}`)
  }

  listStalls(options: PageOptions = {}): Promise<Reply<StallPage>> {
    return this.#get(`/v1/survival/stalls` + pageQuery(options))
  }

  getStall(stallId: string): Promise<Reply<Stall>> {
    return this.#get(`/v1/survival/stalls/${encodeURIComponent(stallId)}`)
  }

  listBounties(options: PageOptions = {}): Promise<Reply<BountyPage>> {
    return this.#get(`/v1/survival/bounties` + pageQuery(options))
  }

  getBounty(id: string): Promise<Reply<Bounty>> {
    return this.#get(`/v1/survival/bounties/${encodeURIComponent(id)}`)
  }

  /** API process health, not game server status. */
  health(): Promise<Reply<Health>> {
    return this.#get('/health')
  }

  #get<T>(path: string): Promise<Reply<T>>
  #get<T>(path: string, ifNoneMatch: string | undefined): Promise<Reply<T> | null>
  async #get<T>(path: string, ifNoneMatch?: string): Promise<Reply<T> | null> {
    for (let attempt = 0; ; attempt++) {
      const response = await this.#fetch(this.#baseUrl + path, {
        headers: ifNoneMatch === undefined ? this.#headers : { ...this.#headers, 'If-None-Match': ifNoneMatch },
        signal: AbortSignal.timeout(this.#timeoutMs),
      })
      if (response.status === 304 && ifNoneMatch !== undefined) return null
      if (response.ok) return parse<T>(response)
      // Release the connection before waiting to retry.
      const message = await errorMessage(response)
      if (response.status === 429) {
        const retryAfter = integer(response.headers.get('retry-after'))
        const wait = retryAfter ?? 1
        if (attempt < this.#maxRetries && wait <= MAX_RETRY_WAIT_SECONDS) {
          await sleep(wait * 1000)
          continue
        }
        throw new RateLimitError(message, retryAfter)
      }
      throw toError(response.status, message)
    }
  }
}

async function parse<T>(response: Response): Promise<Reply<T>> {
  let body: unknown
  try {
    body = await response.json()
  } catch (error) {
    if (error instanceof SyntaxError) throw new MythicMCError(response.status, 'the response body is not JSON')
    throw error
  }
  if (body === null || typeof body !== 'object') throw new MythicMCError(response.status, 'the response body is not a JSON object')
  return Object.defineProperty(body, 'meta', { value: meta(response.headers), enumerable: false }) as Reply<T>
}

function meta(headers: Headers): ResponseMeta {
  const asOf = Date.parse(headers.get('x-data-as-of') ?? '')
  const cache = headers.get('x-cache')
  return {
    etag: headers.get('etag'),
    dataDelaySeconds: integer(headers.get('x-data-delay-seconds')),
    dataAsOf: Number.isNaN(asOf) ? null : new Date(asOf),
    cache: cache === 'HIT' || cache === 'MISS' || cache === 'COALESCED' ? cache : null,
    rateLimitPerMinute: integer(headers.get('x-ratelimit-limit-minute')),
  }
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { error?: unknown }
    if (typeof body?.error === 'string') return body.error
  } catch {}
  return `HTTP ${response.status}`
}

function toError(status: number, message: string): MythicMCError {
  if (status === 400) return new BadRequestError(status, message)
  if (status === 401) return new AuthenticationError(status, message)
  if (status === 404) return new NotFoundError(status, message)
  if (status === 503) return new UnavailableError(status, message)
  return new MythicMCError(status, message)
}

function pageQuery(options: PageOptions & { kit?: string; player?: string }): string {
  const query = new URLSearchParams()
  if (options.limit !== undefined) query.set('limit', String(options.limit))
  if (options.cursor !== undefined) query.set('cursor', options.cursor)
  if (options.kit !== undefined) query.set('kit', options.kit)
  if (options.player !== undefined) query.set('player', options.player)
  return query.size ? `?${query}` : ''
}
