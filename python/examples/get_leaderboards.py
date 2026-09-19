import os

from mythicmc import DEFAULT_BASE_URL, MythicMC

key = os.environ["MYTHICMC_API_KEY"]
base_url = os.environ.get("MYTHICMC_API_URL", DEFAULT_BASE_URL)

with MythicMC(key, base_url=base_url) as api:
    index = api.list_leaderboards()
    board = api.get_leaderboard("kills", "weekly")

for board_type, periods in index.boards.items():
    print(f"{board_type}: {', '.join(periods)}")

# Periods use America/New_York time; weeks start on Friday.
print(f"\nkills / weekly, {board.window_start} to {board.window_end}")
if board.stale:
    print("this board is stale")

# Values are formatted strings. Use player stats for calculations.
for row in board.rows:
    print(f"#{row.rank} {row.name}: {row.value}")
