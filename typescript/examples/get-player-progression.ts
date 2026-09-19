import { MythicMC } from '../src/index.ts'

const api = new MythicMC({ apiKey: process.env.MYTHICMC_API_KEY!, baseUrl: process.env.MYTHICMC_API_URL })
const player = process.argv[2] ?? 'Vicente_1313'

const progression = await api.getPlayerProgression(player)

console.log(`level ${progression.level}, ${progression.experience} XP in total`)

// Progress and target are XP within the current level.
console.log(progression.maxed ? 'max level' : `${progression.progress} / ${progression.target} XP to the next level`)

const achievements = progression.achievements
console.log('achievements:', achievements ? `${achievements.filter(a => a.complete).length} of ${achievements.length}` : 'unknown')
