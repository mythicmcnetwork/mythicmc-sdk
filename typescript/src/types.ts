/** Response metadata; fields are null on `/health`. */
export interface ResponseMeta {
  /** Catalog revision validator, when supplied. */
  etag: string | null
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

/** Only combat is required; unpublished groups are omitted. */
export interface SurvivalStats {
  level?: number
  money?: number
  playtimeMinutes?: number
  spawners?: number
  ranks?: { kills: number; playtime: number }
  /** Damage in health points. */
  combat: { kills: number; deaths: number; mobKills: number; damageDealt: number; damageTaken: number }
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
  /** @deprecated All keys are virtual; retained for compatibility. */
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


export interface SurvivalShopCategoriesItem {
  id: string
  nameKey: string
  icon: string
  color: string
  endsAt: string | null
  items: (string)[]
}

export interface SurvivalShopItemsItem {
  material: string
  buyPrice: number | null
  sellPrice: number | null
}

export interface SurvivalShopSpawnersItem {
  id: string
  entity: string
  icon: string
  buyPrice: number
}

export interface SurvivalShop {
  schemaVersion: 1
  revision: string
  currency: "money"
  pricesIncludePlayerTax: false
  cacheMaxAgeSeconds: number
  validUntil: string | null
  categories: (SurvivalShopCategoriesItem)[]
  items: (SurvivalShopItemsItem)[]
  spawners: (SurvivalShopSpawnersItem)[]
}

export interface PlayerShopBundlesBundlesItemProductsItemVariant1 {
  material: string
  quantity: number
  unitPrice: number | null
  available: boolean
}

export interface PlayerShopBundlesBundlesItem {
  name: string
  icon: string
  products: (PlayerShopBundlesBundlesItemProductsItemVariant1 | null)[]
  available: boolean
  totalPrice: number | null
}

export interface PlayerShopBundles {
  uuid: string
  currency: "money"
  pricesIncludePlayerTax: false
  catalogRevision: string
  bundles: (PlayerShopBundlesBundlesItem)[]
  name: string
}

export interface BountyClaim {
  id: string
  uuid: string
  name: string
  killerUuid: string
  killerName: string
  amount: number
  currency: string
  openedAt: string
  claimedAt: string
  contributorCount: number | null
}

export interface BingoPointRewards {
  perSquare: number
  perLine: number
  maxLines: number
  fullHouse: number
  daily: number
  podium: (number)[]
}

export interface ItemEnchantment {
  id: string
  level: number
}

export interface ItemAttribute {
  id: string
  value: number
}

export interface ItemPrize {
  material: string
  name: string
  rarity: string | null
  enchantments: (ItemEnchantment)[]
  attributes: (ItemAttribute)[]
  quantity: number
}

export interface SpawnerPrize {
  spawner: string
  quantity: number
}

export interface BingoPrize {
  rank: number
  money: number
  items: (ItemPrize | SpawnerPrize)[]
}

export interface BingoDetails {
  id: string
  mode: string
  maxMinutes: number
  freeSpace: boolean
  pointRewards: BingoPointRewards
  prizes: (BingoPrize)[]
}

export interface RaffleDetails {
  id: string
  entryCurrency: string
  entryCost: number
  maxTicketsPerPlayer: number
  basePrize: number
  bonusPerTicket: number
  prizeCurrency: string
}

export type EventDetails = BingoDetails | RaffleDetails

export interface EventScheduleEventsItem {
  id: string
  type: "carnival"
  startsAt: string
  endsAt: string
  summer: boolean
  rescheduled: boolean
}

export interface EventSchedule {
  timezone: string
  enabled: boolean
  suspended: boolean
  activeEventId: string | null
  bingoStartDay: number
  bingoDays: number
  events: (EventScheduleEventsItem)[]
}

export interface StallOffersItemItemEnchantmentsItem {
  id: string
  level: number
}

export interface StallOffersItemItemAttributesItem {
  id: string
  value: number
}

export interface StallOffersItemItem {
  material: string
  name: string
  rarity: string | null
  enchantments: (StallOffersItemItemEnchantmentsItem)[]
  attributes: (StallOffersItemItemAttributesItem)[]
}

export interface StallOffersItem {
  offerId: string
  item: StallOffersItemItem
  unitPrice: number
  currency: string
  stock: number
}

export interface Stall {
  stallId: string
  owner: string
  ownerName: string
  name: string
  icon: string
  leaseEndsAt: string | null
  offers: (StallOffersItem)[]
}

export interface Bounty {
  uuid: string
  name: string
  amount: number
  currency: string
  rank: number
  openedAt?: string
  contributorCount?: number | null
}

export interface BountyClaimPage {
  rows: (BountyClaim)[]
  nextCursor: string | null
}

export interface EventSchedulePage {
  rows: (EventSchedule)[]
  nextCursor: string | null
}

export interface StallPage {
  rows: (Stall)[]
  nextCursor: string | null
}

export interface BountyPage {
  rows: (Bounty)[]
  nextCursor: string | null
}

export interface PageOptions { limit?: number; cursor?: string }
