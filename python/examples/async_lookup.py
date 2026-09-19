import asyncio
import os
import sys

from mythicmc import DEFAULT_BASE_URL, AsyncMythicMC

key = os.environ["MYTHICMC_API_KEY"]
base_url = os.environ.get("MYTHICMC_API_URL", DEFAULT_BASE_URL)


async def main(player: str) -> None:
    async with AsyncMythicMC(key, base_url=base_url) as api:
        profile, progression, team = await asyncio.gather(
            api.get_player(player),
            api.get_player_progression(player),
            api.get_player_team(player),
        )

    print(f"[{profile.rank.label}] {profile.name}: network level {progression.level}")
    print("team:", team.team.name if team.team else "none")

    # Separate cache entries can have different cutoffs; show the oldest.
    cutoffs = [reply.meta.data_as_of for reply in (profile, progression, team) if reply.meta.data_as_of]
    print("data as of:", min(cutoffs) if cutoffs else "unknown")


asyncio.run(main(sys.argv[1] if len(sys.argv) > 1 else "Vicente_1313"))
