import { MythicMC } from '../src/index.ts'

const api = new MythicMC({ apiKey: process.env.MYTHICMC_API_KEY!, baseUrl: process.env.MYTHICMC_API_URL })
const player = process.argv[2] ?? 'Vicente_1313'

const { name, team } = await api.getPlayerTeam(player)

if (!team) {
  console.log(`${name} is not in a team`)
} else {
  console.log(`${name} is in [${team.prefix}] ${team.name}, team level ${team.level}, role ${team.role ?? 'unknown'}`)
}
