import os
import sys

from mythicmc import DEFAULT_BASE_URL, MythicMC

key = os.environ["MYTHICMC_API_KEY"]
base_url = os.environ.get("MYTHICMC_API_URL", DEFAULT_BASE_URL)
player = sys.argv[1] if len(sys.argv) > 1 else "Vicente_1313"

with MythicMC(key, base_url=base_url) as api:
    reply = api.get_player_team(player)

team = reply.team
if team is None:
    print(f"{reply.name} is not in a team")
else:
    print(f"{reply.name} is in [{team.prefix}] {team.name}, team level {team.level}, role {team.role or 'unknown'}")
