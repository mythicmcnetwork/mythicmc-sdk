/** Response metadata; fields are null on `/health`. */
export interface ResponseMeta {
  dataDelaySeconds: number | null
  /** UTC cutoff, preserved on cached responses. */
  dataAsOf: Date | null
  /** COALESCED indicates a shared in-flight read. */
  cache: 'HIT' | 'MISS' | 'COALESCED' | null
  /** Cache hits count toward this allowance. */
  rateLimitPerMinute: number | null
}

/** Metadata is non-enumerable and excluded from JSON serialization. */
export type Reply<T> = T & { readonly meta: ResponseMeta }

export interface Rank {
  id: string
  label: string
  weight: number
  /** Hex colour, e.g. #b983ff. */
  color: string | null
}

export type TeamRole = 'leader' | 'officer' | 'member'

export interface TeamSummary {
  id: string
  name: string
  prefix: string
  level: number
  role?: TeamRole
}

export interface SelectedCosmetic {
  slot: string
  id: string
  name: string
  category: string
  preview: string | null
}

export interface Skin {
  textureUrl: string
  model: 'slim' | 'classic'
}

/** Timestamps are Unix milliseconds; unknown values are null. */
export interface PlayerProfile {
  uuid: string
  name: string
  rank: Rank
  playtimeMinutes: number | null
  firstLogin: number | null
  lastLogin: number | null
  lastLogout: number | null
  /** Null means presence is unknown. */
  online: boolean | null
  /** Only available while online is true. */
  location: { gamemode: string } | null
  /** Network level. */
  level: number | null
  team: TeamSummary | null
  cosmetics: { selected: SelectedCosmetic[] | null }
  skin?: Skin
}

/** Only combat and world are required; unpublished groups are omitted. */
export interface SurvivalStats {
  level?: number
  money?: number
  playtimeMinutes?: number
  spawners?: number
  ranks?: { kills: number; playtime: number }
  /** Damage in health points. */
  combat: { kills: number; deaths: number; mobKills: number; damageDealt: number; damageTaken: number }
  world: {
    blocksMined: number
    blocksPlaced: number
    itemsCrafted: number
    distanceKm: number
    jumps: number
    fishCaught: number
    animalsBred: number
    villagerTrades: number
    itemsEnchanted: number
    raidsWon: number
  }
  events?: {
    points: number
    pointsLifetime: number
    tickets: number
    ticketsEarned: number
    raffleLuck: number
    rafflesEntered: number
    bingoFinished: number
    bingoPodiums: number
    wins: { bingo: number; raffle: number; chatGame: number }
  }
  auction?: { activeListings: number; sold: number; soldValue: number; bought: number; boughtValue: number; openOrders: number }
  bounty?: { onHead: number; claimed: number; claimedValue: number; claimedOn: number }
  netWorth?: { total: number; rank: number }
}

export interface PlayerStats {
  uuid: string
  name: string
  survival: SurvivalStats
}

export interface Achievement {
  id: string
  name: string
  description: string
  progress: number
  target: number
  complete: boolean
  /** ISO 8601 UTC. */
  unlockedAt: string | null
}

export interface PlayerProgression {
  uuid: string
  name: string
  level: number
  experience: number
  progress: number
  target: number
  maxed: boolean
  achievements?: Achievement[]
}

export interface PlayerTeam {
  uuid: string
  name: string
  /** Null when unaffiliated. */
  team: TeamSummary | null
}

export interface CrateKey {
  crateId: string
  keyType: string
  /** Null when unpublished. */
  available: number | null
}

/** Missing crates have unpublished balances, not zero balances. */
export interface PlayerCrateKeys {
  uuid: string
  name: string
  keys: CrateKey[]
}

export type LeaderboardType = 'kills' | 'playtime' | 'wins' | 'networth'
export type LeaderboardPeriod = 'daily' | 'weekly' | 'monthly' | 'all_time'

export interface LeaderboardIndex {
  types: LeaderboardType[]
  /** Supported type/period pairs are listed in boards. */
  periods: LeaderboardPeriod[]
  boards: Record<LeaderboardType, LeaderboardPeriod[]>
}

export interface LeaderboardRow {
  /** One-based position. */
  rank: number
  uuid: string
  name: string
  /** Formatted value, e.g. 3d 4h or $2.83B. */
  value: string
}

export interface Leaderboard {
  type: LeaderboardType
  period: LeaderboardPeriod
  /** Up to 15 rows, excluding unpublished profiles. */
  rows: LeaderboardRow[]
  /** True when outdated or the period has ended. */
  stale: boolean
  /** ISO 8601 UTC. Both bounds are omitted for all_time. */
  windowStart?: string
  windowEnd?: string
}

export interface Health {
  ok: boolean
}
