import { MythicMC } from '../src/index.ts'

const api = new MythicMC({ apiKey: process.env.MYTHICMC_API_KEY!, baseUrl: process.env.MYTHICMC_API_URL })
const player = process.argv[2] ?? 'Vicente_1313'

const { keys } = await api.getPlayerCrateKeys(player)

// Missing crates and unpublished balances are unknown, not zero.
for (const key of keys) console.log(`${key.crateId} (${key.keyType}): ${key.available ?? 'unknown'}`)
if (keys.length === 0) console.log(`no crate key balances are published for ${player}`)
