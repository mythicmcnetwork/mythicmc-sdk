import { MythicMC } from '../src/index.ts'

const api = new MythicMC({ apiKey: process.env.MYTHICMC_API_KEY!, baseUrl: process.env.MYTHICMC_API_URL })

const index = await api.listLeaderboards()
for (const [type, periods] of Object.entries(index.boards)) console.log(`${type}: ${periods.join(', ')}`)

const board = await api.getLeaderboard('kills', 'weekly')
// Periods use America/New_York time; weeks start on Friday.
console.log(`\nkills / weekly, ${board.windowStart} to ${board.windowEnd}`)
if (board.stale) console.log('this board is stale')

// Values are formatted strings. Use player stats for calculations.
for (const row of board.rows) console.log(`#${row.rank} ${row.name}: ${row.value}`)
