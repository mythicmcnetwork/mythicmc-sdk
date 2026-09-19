import os
import sys

from mythicmc import DEFAULT_BASE_URL, MythicMC

key = os.environ["MYTHICMC_API_KEY"]
base_url = os.environ.get("MYTHICMC_API_URL", DEFAULT_BASE_URL)
player = sys.argv[1] if len(sys.argv) > 1 else "Vicente_1313"

with MythicMC(key, base_url=base_url) as api:
    progression = api.get_player_progression(player)

print(f"level {progression.level}, {progression.experience} XP in total")

# Progress and target are XP within the current level.
print("max level" if progression.maxed else f"{progression.progress} / {progression.target} XP to the next level")

achievements = progression.achievements
print("achievements:", f"{sum(a.complete for a in achievements)} of {len(achievements)}" if achievements else "unknown")
