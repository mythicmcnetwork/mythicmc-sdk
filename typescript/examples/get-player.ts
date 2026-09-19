import { MythicMC } from '../src/index.ts'

const api = new MythicMC({ apiKey: process.env.MYTHICMC_API_KEY!, baseUrl: process.env.MYTHICMC_API_URL })
const player = process.argv[2] ?? 'Vicente_1313'

const profile = await api.getPlayer(player) // username or UUID
console.log(`[${profile.rank.label}] ${profile.name} (${profile.uuid})`)

console.log('online:', profile.online ?? 'unknown')
console.log('gamemode:', profile.location?.gamemode ?? 'unknown')
console.log('network level:', profile.level ?? 'unknown')
console.log('team:', profile.team?.name ?? 'none')

console.log('last login:', profile.lastLogin === null ? 'unknown' : new Date(profile.lastLogin).toISOString())
console.log('data as of:', profile.meta.dataAsOf?.toISOString() ?? 'unknown')
