import os
import sys

from mythicmc import DEFAULT_BASE_URL, MythicMC, NotFoundError

key = os.environ["MYTHICMC_API_KEY"]
base_url = os.environ.get("MYTHICMC_API_URL", DEFAULT_BASE_URL)
player = sys.argv[1] if len(sys.argv) > 1 else "Vicente_1313"

try:
    with MythicMC(key, base_url=base_url) as api:
        survival = api.get_player_stats(player).survival
except NotFoundError as error:
    sys.exit(f"no Survival statistics for {player}: {error.message}")

combat = survival.combat
print(f"kills {combat.kills}, deaths {combat.deaths}, K/D {combat.kills / max(combat.deaths, 1):.2f}")

# Missing groups are unknown, not zero.
net_worth = survival.net_worth
print("net worth:", f"${net_worth.total} (#{net_worth.rank})" if net_worth else "unknown")
print("balance:", survival.money if survival.money is not None else "unknown")
events = survival.events
print("events won:", events.wins.bingo + events.wins.raffle if events else "unknown")
