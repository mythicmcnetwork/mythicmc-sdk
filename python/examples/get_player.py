import os
import sys
from datetime import datetime, timezone

from mythicmc import DEFAULT_BASE_URL, MythicMC

key = os.environ["MYTHICMC_API_KEY"]
base_url = os.environ.get("MYTHICMC_API_URL", DEFAULT_BASE_URL)
player = sys.argv[1] if len(sys.argv) > 1 else "Vicente_1313"

with MythicMC(key, base_url=base_url) as api:
    profile = api.get_player(player)  # username or UUID

print(f"[{profile.rank.label}] {profile.name} ({profile.uuid})")

print("online:", "unknown" if profile.online is None else profile.online)
print("gamemode:", profile.location.gamemode if profile.location else "unknown")
print("network level:", profile.level if profile.level is not None else "unknown")
print("team:", profile.team.name if profile.team else "none")

last_login = profile.last_login
print("last login:", datetime.fromtimestamp(last_login / 1000, timezone.utc) if last_login is not None else "unknown")
print("data as of:", profile.meta.data_as_of or "unknown")
