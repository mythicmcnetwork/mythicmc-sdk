import dataclasses
import unittest

from mythicmc import models

UUID = "53eefb84-3ed8-4efb-9bb0-ddaaf3e01e9f"

PROFILE = {
    "uuid": UUID,
    "name": "Vicente_1313",
    "rank": {"id": "divine", "label": "DIVINE", "weight": 40, "color": "#b983ff"},
    "playtimeMinutes": 18240,
    "firstLogin": 1719878400000,
    "lastLogin": 1758226800000,
    "lastLogout": 1758140400000,
    "online": True,
    "location": {"gamemode": "survival"},
    "level": 37,
    "team": {"id": "6f1c2a9e-3b7d-4e0a-9c55-1d2e3f4a5b6c", "name": "Nightfall", "prefix": "NF",
             "level": 12, "role": "officer"},
    "cosmetics": {"selected": [{"slot": "hat", "id": "witch-hat", "name": "Witch Hat",
                                "category": "hats", "preview": "https://example.invalid/hat.png"}]},
    "skin": {"textureUrl": "https://textures.minecraft.net/texture/2c7a608fb2917a75164dc04dfbc7d4fe0d1e5b05b929381df20bb26853cb60f2", "model": "classic"},
}

STATS = {
    "uuid": UUID,
    "name": "Vicente_1313",
    "survival": {
        "level": 42,
        "money": 1250340.5,
        "playtimeMinutes": 9120,
        "spawners": 3,
        "ranks": {"kills": 14, "playtime": 52},
        "combat": {"kills": 318, "deaths": 97, "mobKills": 12044, "damageDealt": 88412.5, "damageTaken": 40210},
        "world": {"blocksMined": 402118, "blocksPlaced": 188305, "itemsCrafted": 22190, "distanceKm": 1840.2,
                  "jumps": 96012, "fishCaught": 410, "animalsBred": 233, "villagerTrades": 1502,
                  "itemsEnchanted": 188, "raidsWon": 4},
        "events": {"points": 120, "pointsLifetime": 2210, "tickets": 3, "ticketsEarned": 41, "raffleLuck": 1.25,
                   "rafflesEntered": 18, "bingoFinished": 6, "bingoPodiums": 2,
                   "wins": {"bingo": 1, "raffle": 2, "chatGame": 19}},
        "auction": {"activeListings": 2, "sold": 88, "soldValue": 412000, "bought": 51,
                    "boughtValue": 198500, "openOrders": 1},
        "bounty": {"onHead": 25000, "claimed": 7, "claimedValue": 61000, "claimedOn": 3},
        "netWorth": {"total": 2830000.75, "rank": 9},
    },
}


def unset(value, path=""):
    if dataclasses.is_dataclass(value):
        found = []
        for f in dataclasses.fields(value):
            if f.name not in ("meta", "raw"):
                found += unset(getattr(value, f.name), f"{path}.{f.name}")
        return found
    if isinstance(value, list):
        found = []
        for index, item in enumerate(value):
            found += unset(item, f"{path}[{index}]")
        return found
    return [path] if value is None else []


def build(cls, data):
    return models.parse(cls, data, meta=None, raw=data)


class KeyNames(unittest.TestCase):

    def test_profile(self):
        self.assertEqual(unset(build(models.PlayerProfile, PROFILE)), [])

    def test_stats(self):
        self.assertEqual(unset(build(models.PlayerStats, STATS)), [])

    def test_progression(self):
        body = {"uuid": UUID, "name": "Vicente_1313", "level": 37, "experience": 67410.0, "progress": 810.0,
                "target": 3700.0, "maxed": True,
                "achievements": [{"id": "a", "name": "A", "description": "d", "progress": 1.0, "target": 1.0,
                                  "complete": True, "unlockedAt": "2026-09-18T04:00:00.000Z"}]}
        self.assertEqual(unset(build(models.PlayerProgression, body)), [])

    def test_crate_keys(self):
        body = {"uuid": UUID, "name": "Vicente_1313", "keys": [{"crateId": "vote", "keyType": "virtual", "available": 12}]}
        self.assertEqual(unset(build(models.PlayerCrateKeys, body)), [])

    def test_leaderboard(self):
        body = {"type": "kills", "period": "weekly", "stale": False,
                "windowStart": "2026-09-18T04:00:00.000Z", "windowEnd": "2026-09-25T04:00:00.000Z",
                "rows": [{"rank": 1, "uuid": UUID, "name": "Vicente_1313", "value": "412"}]}
        self.assertEqual(unset(build(models.Leaderboard, body)), [])


class Conversion(unittest.TestCase):
    def test_unknown_keys_are_ignored(self):
        profile = build(models.PlayerProfile, dict(PROFILE, addedInAFutureRelease=1))
        self.assertEqual(profile.name, "Vicente_1313")

    def test_missing_keys_become_none(self):
        stats = build(models.PlayerStats, {"name": "Vicente_1313", "survival": STATS["survival"]})
        self.assertIsNone(stats.uuid)

    def test_nullable_nested_object(self):
        profile = build(models.PlayerProfile, dict(PROFILE, team=None, location=None))
        self.assertIsNone(profile.team)
        self.assertIsNone(profile.location)

    def test_empty_and_absent_lists_differ(self):
        self.assertEqual(build(models.PlayerProfile, dict(PROFILE, cosmetics={"selected": []})).cosmetics.selected, [])
        self.assertIsNone(build(models.PlayerProfile, dict(PROFILE, cosmetics={})).cosmetics.selected)

    def test_mapping_of_lists_passes_through(self):
        boards = {"kills": ["daily", "all_time"], "networth": ["all_time"]}
        index = build(models.LeaderboardIndex, {"types": ["kills"], "periods": ["daily"], "boards": boards})
        self.assertEqual(index.boards, boards)

    def test_extra_arguments_win_over_the_body(self):
        reply = models.parse(models.Health, {"ok": True, "meta": "ignored"}, meta=None, raw={})
        self.assertIsNone(reply.meta)

    def test_replies_are_frozen_and_slotted(self):
        reply = build(models.Health, {"ok": True})
        with self.assertRaises(dataclasses.FrozenInstanceError):
            reply.ok = False
        self.assertFalse(hasattr(reply, "__dict__"))


class WrongShapes(unittest.TestCase):
    def test_body_is_not_an_object(self):
        for body in ([], "text", 3):
            with self.assertRaises(TypeError) as raised:
                build(models.Health, body)
            self.assertIn("expected a JSON object for Health", str(raised.exception))

    def test_nested_object_is_not_an_object(self):
        with self.assertRaises(TypeError) as raised:
            build(models.PlayerProfile, dict(PROFILE, rank="divine"))
        self.assertIn("expected a JSON object for Rank", str(raised.exception))

    def test_list_field_is_not_a_list(self):
        with self.assertRaises(TypeError) as raised:
            build(models.PlayerCrateKeys, {"uuid": UUID, "name": "Vicente_1313", "keys": {"vote": 1}})
        self.assertIn("expected a JSON array", str(raised.exception))

    def test_list_of_objects_holding_a_scalar(self):
        with self.assertRaises(TypeError):
            build(models.PlayerCrateKeys, {"uuid": UUID, "name": "Vicente_1313", "keys": ["vote"]})


class Camel(unittest.TestCase):
    def test_conversion(self):
        cases = {"uuid": "uuid", "net_worth": "netWorth", "distance_km": "distanceKm",
                 "playtime_minutes": "playtimeMinutes", "crate_id": "crateId", "chat_game": "chatGame"}
        for snake, camel in cases.items():
            self.assertEqual(models._camel(snake), camel)


if __name__ == "__main__":
    unittest.main()
