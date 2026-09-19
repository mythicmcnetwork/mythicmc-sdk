import os
import sys

from mythicmc import DEFAULT_BASE_URL, MythicMC

key = os.environ["MYTHICMC_API_KEY"]
base_url = os.environ.get("MYTHICMC_API_URL", DEFAULT_BASE_URL)
player = sys.argv[1] if len(sys.argv) > 1 else "Vicente_1313"

with MythicMC(key, base_url=base_url) as api:
    crate_keys = api.get_player_crate_keys(player).keys

# Missing crates and unpublished balances are unknown, not zero.
for crate_key in crate_keys:
    available = crate_key.available
    print(f"{crate_key.crate_id} ({crate_key.key_type}): {available if available is not None else 'unknown'}")
if not crate_keys:
    print(f"no crate key balances are published for {player}")
