import { MythicMC, NotFoundError } from '../src/index.ts'

const api = new MythicMC({ apiKey: process.env.MYTHICMC_API_KEY!, baseUrl: process.env.MYTHICMC_API_URL })
const player = process.argv[2] ?? 'Vicente_1313'

try {
  const { survival } = await api.getPlayerStats(player)

  const { kills, deaths } = survival.combat
  console.log(`kills ${kills}, deaths ${deaths}, K/D ${(kills / Math.max(deaths, 1)).toFixed(2)}`)
  console.log('blocks mined:', survival.world.blocksMined)

  // Missing groups are unknown, not zero.
  console.log('net worth:', survival.netWorth ? `$${survival.netWorth.total} (#${survival.netWorth.rank})` : 'unknown')
  console.log('balance:', survival.money ?? 'unknown')
  console.log('events won:', survival.events ? survival.events.wins.bingo + survival.events.wins.raffle : 'unknown')
} catch (error) {
  if (!(error instanceof NotFoundError)) throw error
  console.log(`no Survival statistics for ${player}: ${error.message}`)
}
