import unittest
from datetime import datetime, timezone
from unittest.mock import patch

import httpx

from mythicmc import (
    AsyncMythicMC,
    AuthenticationError,
    BadRequestError,
    MythicMC,
    MythicMCError,
    NotFoundError,
    RateLimitError,
    UnavailableError,
)

PROFILE = {
    "uuid": "53eefb84-3ed8-4efb-9bb0-ddaaf3e01e9f",
    "name": "Vicente_1313",
    "rank": {"id": "divine", "label": "DIVINE", "weight": 40, "color": "#b983ff"},
    "playtimeMinutes": 18240,
    "firstLogin": 1719878400000,
    "lastLogin": 1758226800000,
    "lastLogout": None,
    "online": True,
    "location": {"gamemode": "survival"},
    "level": 37,
    "team": {"id": "6f1c2a9e-3b7d-4e0a-9c55-1d2e3f4a5b6c", "name": "Nightfall", "prefix": "NF", "level": 12},
    "cosmetics": {"selected": [{"slot": "hat", "id": "witch-hat", "name": "Witch Hat", "category": "hats"}]},
    "addedLater": "ignored",
}
DATA_HEADERS = {
    "X-Data-Delay-Seconds": "300",
    "X-Data-As-Of": "2026-09-19T12:00:00.000Z",
    "X-Cache": "HIT",
    "X-RateLimit-Limit-Minute": "120",
}
def too_many(retry_after="0"):
    """Fresh response for each attempt; httpx responses are single-use."""
    headers = {} if retry_after is None else {"Retry-After": retry_after}
    return httpx.Response(429, json={"error": "too many requests"}, headers=headers)


def stub(*responses):
    queue, requests = list(responses), []

    def handler(request):
        requests.append(request)
        return queue.pop(0)

    return requests, httpx.MockTransport(handler)


def client(*responses, **kwargs):
    requests, transport = stub(*responses)
    return requests, MythicMC("k", transport=transport, **kwargs)


class Decoding(unittest.TestCase):
    def test_profile_fields_and_metadata(self):
        requests, api = client(httpx.Response(200, json=PROFILE, headers=DATA_HEADERS))
        with api:
            player = api.get_player("Vicente_1313")
        self.assertEqual(str(requests[0].url), "https://api.mythicmc.net/v1/players/Vicente_1313")
        self.assertEqual(requests[0].headers["authorization"], "Bearer k")
        self.assertEqual(requests[0].headers["accept"], "application/json")
        self.assertTrue(requests[0].headers["user-agent"].startswith("mythicmc-api-python/"))
        self.assertEqual(player.rank.label, "DIVINE")
        self.assertEqual(player.playtime_minutes, 18240)
        self.assertIsNone(player.last_logout)
        self.assertEqual(player.location.gamemode, "survival")
        self.assertIsNone(player.team.role)
        self.assertEqual(player.cosmetics.selected[0].id, "witch-hat")
        self.assertFalse(hasattr(player.cosmetics.selected[0], "preview"))
        self.assertIsNone(player.skin)
        self.assertEqual(player.raw["addedLater"], "ignored")
        self.assertEqual(player.meta.data_delay_seconds, 300)
        self.assertEqual(player.meta.data_as_of, datetime(2026, 9, 19, 12, tzinfo=timezone.utc))
        self.assertEqual(player.meta.cache, "HIT")
        self.assertEqual(player.meta.rate_limit_per_minute, 120)

    def test_meta_and_raw_are_excluded_from_equality(self):
        _, first = client(httpx.Response(200, json=PROFILE, headers=DATA_HEADERS))
        _, second = client(httpx.Response(200, json=PROFILE))
        with first, second:
            self.assertEqual(first.get_player("Vicente_1313"), second.get_player("Vicente_1313"))

    def test_optional_stat_groups_stay_none(self):
        body = {
            "uuid": PROFILE["uuid"],
            "name": "Vicente_1313",
            "survival": {
                "combat": {"kills": 318, "deaths": 97, "mobKills": 12044, "damageDealt": 88412.5, "damageTaken": 40210},
                "events": {"points": 1, "pointsLifetime": 2, "tickets": 3, "ticketsEarned": 4, "raffleLuck": 1.25,
                           "rafflesEntered": 5, "bingoFinished": 6, "bingoPodiums": 7,
                           "wins": {"bingo": 1, "raffle": 2, "chatGame": 19}},
            },
        }
        _, api = client(httpx.Response(200, json=body))
        with api:
            survival = api.get_player_stats("Vicente_1313").survival
        self.assertEqual(survival.combat.mob_kills, 12044)
        self.assertFalse(hasattr(survival, "world"))
        self.assertEqual(survival.events.wins.chat_game, 19)
        self.assertIsNone(survival.net_worth)
        self.assertIsNone(survival.money)

    def test_progression_achievements(self):
        body = {"uuid": PROFILE["uuid"], "name": "Vicente_1313", "level": 37, "experience": 67410.0, "progress": 810.0,
                "target": 3700.0, "maxed": False,
                "achievements": [{"id": "first-night", "name": "First Night", "description": "Survive.",
                                  "progress": 1.0, "target": 1.0, "complete": True,
                                  "unlockedAt": "2026-09-18T04:00:00.000Z"}]}
        _, api = client(httpx.Response(200, json=body))
        with api:
            progression = api.get_player_progression("Vicente_1313")
        self.assertFalse(progression.maxed)
        self.assertEqual(progression.achievements[0].unlocked_at, "2026-09-18T04:00:00.000Z")

    def test_progression_without_achievements(self):
        body = {"uuid": PROFILE["uuid"], "name": "Vicente_1313", "level": 1, "experience": 0.0, "progress": 0.0,
                "target": 100.0, "maxed": False}
        _, api = client(httpx.Response(200, json=body))
        with api:
            self.assertIsNone(api.get_player_progression("Vicente_1313").achievements)

    def test_crate_keys_keep_unknown_balances_apart_from_zero(self):
        body = {"uuid": PROFILE["uuid"], "name": "Vicente_1313",
                "keys": [{"crateId": "vote", "keyType": "virtual", "available": 0},
                         {"crateId": "legendary", "keyType": "virtual", "available": None}]}
        _, api = client(httpx.Response(200, json=body))
        with api:
            keys = api.get_player_crate_keys("Vicente_1313").keys
        self.assertEqual(keys[0].available, 0)
        self.assertIsNone(keys[1].available)

    def test_player_without_a_team(self):
        _, api = client(httpx.Response(200, json={"uuid": PROFILE["uuid"], "name": "Vicente_1313", "team": None}))
        with api:
            self.assertIsNone(api.get_player_team("Vicente_1313").team)

    def test_leaderboard_index(self):
        body = {"types": ["kills", "networth"], "periods": ["daily", "all_time"],
                "boards": {"kills": ["daily", "all_time"], "networth": ["all_time"]}}
        _, api = client(httpx.Response(200, json=body))
        with api:
            index = api.list_leaderboards()
        self.assertEqual(index.boards["networth"], ["all_time"])

    def test_leaderboard_all_time_has_no_window(self):
        body = {"type": "networth", "period": "all_time", "stale": False,
                "rows": [{"rank": 1, "uuid": PROFILE["uuid"], "name": "Vicente_1313", "value": "$2.83B"}]}
        _, api = client(httpx.Response(200, json=body))
        with api:
            board = api.get_leaderboard("networth", "all_time")
        self.assertEqual(board.rows[0].value, "$2.83B")
        self.assertIsNone(board.window_start)
        self.assertIsNone(board.window_end)

    def test_leaderboard_window(self):
        body = {"type": "kills", "period": "weekly", "stale": True, "rows": [],
                "windowStart": "2026-09-18T04:00:00.000Z", "windowEnd": "2026-09-25T04:00:00.000Z"}
        _, api = client(httpx.Response(200, json=body))
        with api:
            board = api.get_leaderboard("kills", "weekly")
        self.assertTrue(board.stale)
        self.assertEqual(board.rows, [])
        self.assertEqual(board.window_end, "2026-09-25T04:00:00.000Z")

    def test_health_has_no_data_headers(self):
        _, api = client(httpx.Response(200, json={"ok": True}))
        with api:
            health = api.health()
        self.assertTrue(health.ok)
        self.assertIsNone(health.meta.data_delay_seconds)
        self.assertIsNone(health.meta.data_as_of)
        self.assertIsNone(health.meta.cache)

    def test_unreadable_metadata_headers_do_not_fail_the_call(self):
        headers = {"X-Data-As-Of": "whenever", "X-Data-Delay-Seconds": "-1", "X-RateLimit-Limit-Minute": "many"}
        _, api = client(httpx.Response(200, json={"ok": True}, headers=headers))
        with api:
            meta = api.health().meta
        self.assertIsNone(meta.data_as_of)
        self.assertIsNone(meta.data_delay_seconds)
        self.assertIsNone(meta.rate_limit_per_minute)

    def test_as_of_without_milliseconds(self):
        _, api = client(httpx.Response(200, json={"ok": True}, headers={"X-Data-As-Of": "2026-09-19T12:00:00Z"}))
        with api:
            self.assertEqual(api.health().meta.data_as_of, datetime(2026, 9, 19, 12, tzinfo=timezone.utc))


class Routes(unittest.TestCase):
    def test_paths_and_escaping(self):
        requests, api = client(*[httpx.Response(200, json={}) for _ in range(8)])
        with api:
            api.get_player("a/b")
            api.get_player_stats(".Bedrock")
            api.get_player_progression("n")
            api.get_player_team("n")
            api.get_player_crate_keys("n")
            api.list_leaderboards()
            api.get_leaderboard("networth", "all_time")
            api.health()
        self.assertEqual(
            [request.url.raw_path.decode() for request in requests],
            ["/v1/players/a%2Fb", "/v1/players/.Bedrock/stats", "/v1/players/n/progression", "/v1/players/n/team",
             "/v1/players/n/crate-keys", "/v1/leaderboards", "/v1/leaderboards/networth/all_time", "/health"],
        )

    def test_base_url_may_carry_a_path_and_a_trailing_slash(self):
        for base, expected in [("http://localhost:8080", "http://localhost:8080/health"),
                               ("http://localhost:8080/", "http://localhost:8080/health"),
                               ("http://localhost:8080/api", "http://localhost:8080/api/health"),
                               ("http://localhost:8080/api/", "http://localhost:8080/api/health")]:
            requests, api = client(httpx.Response(200, json={"ok": True}), base_url=base)
            with api:
                api.health()
            self.assertEqual(str(requests[0].url), expected)


class Errors(unittest.TestCase):
    def test_status_to_exception(self):
        cases = [(400, BadRequestError, "invalid player identifier"),
                 (401, AuthenticationError, "missing or invalid API key"),
                 (404, NotFoundError, "unknown player"),
                 (503, UnavailableError, "required data is unavailable")]
        for status, error, message in cases:
            _, api = client(httpx.Response(status, json={"error": message}))
            with api, self.assertRaises(error) as raised:
                api.get_player("n")
            self.assertEqual(raised.exception.status, status)
            self.assertEqual(raised.exception.message, message)
            self.assertEqual(str(raised.exception), message)

    def test_unmapped_status_falls_back_to_the_base_error(self):
        _, api = client(httpx.Response(502, text="<html>bad gateway</html>"))
        with api, self.assertRaises(MythicMCError) as raised:
            api.health()
        self.assertIs(type(raised.exception), MythicMCError)
        self.assertEqual(raised.exception.status, 502)
        self.assertEqual(raised.exception.message, "HTTP 502")

    def test_error_body_that_is_not_an_object(self):
        _, api = client(httpx.Response(404, json=["unknown player"]))
        with api, self.assertRaises(NotFoundError) as raised:
            api.get_player("n")
        self.assertEqual(raised.exception.message, "HTTP 404")

    def test_non_json_success_body(self):
        _, api = client(httpx.Response(200, text="<html>proxy error page</html>"))
        with api, self.assertRaises(MythicMCError) as raised:
            api.health()
        self.assertIn("malformed response body", raised.exception.message)

    def test_success_body_that_is_not_an_object(self):
        _, api = client(httpx.Response(200, json=[1, 2, 3]))
        with api, self.assertRaises(MythicMCError) as raised:
            api.health()
        self.assertIn("expected a JSON object", raised.exception.message)

    def test_nested_value_of_the_wrong_type(self):
        body = dict(PROFILE, rank="divine")
        _, api = client(httpx.Response(200, json=body))
        with api, self.assertRaises(MythicMCError) as raised:
            api.get_player("Vicente_1313")
        self.assertIn("expected a JSON object", raised.exception.message)

    def test_list_field_given_a_scalar(self):
        _, api = client(httpx.Response(200, json={"types": "kills", "periods": [], "boards": {}}))
        with api, self.assertRaises(MythicMCError) as raised:
            api.list_leaderboards()
        self.assertIn("expected a JSON array", raised.exception.message)

    def test_requires_key(self):
        with self.assertRaises(ValueError):
            MythicMC("")

    def test_closed_client_refuses_requests(self):
        _, api = client(httpx.Response(200, json={"ok": True}))
        api.close()
        with self.assertRaises(RuntimeError):
            api.health()


class Retries(unittest.TestCase):
    def test_retries_then_succeeds(self):
        requests, api = client(too_many(), httpx.Response(200, json={"ok": True}))
        with api:
            self.assertTrue(api.health().ok)
        self.assertEqual(len(requests), 2)

    def test_one_attempt_per_retry_then_raises(self):
        requests, api = client(too_many(), too_many(), too_many(), max_retries=2)
        with api, self.assertRaises(RateLimitError):
            api.health()
        self.assertEqual(len(requests), 3)

    def test_no_retries_by_request(self):
        requests, api = client(too_many("7"), max_retries=0)
        with api, self.assertRaises(RateLimitError) as raised:
            api.health()
        self.assertEqual(raised.exception.retry_after, 7)
        self.assertEqual(raised.exception.status, 429)
        self.assertEqual(len(requests), 1)

    def test_missing_retry_after_waits_one_second(self):
        requests, api = client(too_many(None), httpx.Response(200, json={"ok": True}))
        with patch("mythicmc.client.time.sleep") as sleep, api:
            api.health()
        self.assertEqual(sleep.call_args.args, (1.0,))
        self.assertEqual(len(requests), 2)

    def test_retry_after_over_a_minute_is_handed_back(self):
        requests, api = client(too_many("86400"), httpx.Response(200, json={"ok": True}))
        with patch("mythicmc.client.time.sleep") as sleep, api, self.assertRaises(RateLimitError) as raised:
            api.health()
        self.assertEqual(raised.exception.retry_after, 86400)
        sleep.assert_not_called()
        self.assertEqual(len(requests), 1)

    def test_header_integers_are_plain_digits_only(self):
        for value in ("+7", "1_0", "-1", "7.5"):
            _, api = client(too_many(value), max_retries=0)
            with api, self.assertRaises(RateLimitError) as raised:
                api.health()
            self.assertIsNone(raised.exception.retry_after, value)

    def test_unknown_cache_status_is_none(self):
        _, api = client(httpx.Response(200, json={"ok": True}, headers={"X-Cache": "BYPASS"}))
        with api:
            self.assertIsNone(api.health().meta.cache)

    def test_empty_base_url_falls_back_to_the_default(self):
        requests, api = client(httpx.Response(200, json={"ok": True}), base_url="")
        with api:
            api.health()
        self.assertEqual(str(requests[0].url), "https://api.mythicmc.net/health")

    def test_unusable_retry_after_is_ignored(self):
        # This latin-1 digit passes str.isdigit() but fails int().
        header = [(b"retry-after", b"\xb2")]
        _, api = client(httpx.Response(429, json={"error": "too many requests"}, headers=header), max_retries=0)
        with api, self.assertRaises(RateLimitError) as raised:
            api.health()
        self.assertIsNone(raised.exception.retry_after)


class Async(unittest.IsolatedAsyncioTestCase):
    async def test_every_route(self):
        requests, transport = stub(*[httpx.Response(200, json={}) for _ in range(8)])
        async with AsyncMythicMC("k", transport=transport) as api:
            await api.get_player("n")
            await api.get_player_stats("n")
            await api.get_player_progression("n")
            await api.get_player_team("n")
            await api.get_player_crate_keys("n")
            await api.list_leaderboards()
            await api.get_leaderboard("kills", "daily")
            await api.health()
        self.assertEqual(
            [request.url.raw_path.decode() for request in requests],
            ["/v1/players/n", "/v1/players/n/stats", "/v1/players/n/progression", "/v1/players/n/team",
             "/v1/players/n/crate-keys", "/v1/leaderboards", "/v1/leaderboards/kills/daily", "/health"],
        )

    async def test_get_player_and_retry(self):
        requests, transport = stub(too_many(), httpx.Response(200, json=PROFILE, headers=DATA_HEADERS))
        async with AsyncMythicMC("k", transport=transport) as api:
            player = await api.get_player("Vicente_1313")
        self.assertEqual(player.name, "Vicente_1313")
        self.assertEqual(player.meta.cache, "HIT")
        self.assertEqual(len(requests), 2)
        self.assertEqual(requests[1].headers["authorization"], "Bearer k")

    async def test_retries_are_counted(self):
        requests, transport = stub(too_many(), too_many())
        async with AsyncMythicMC("k", transport=transport, max_retries=1) as api:
            with self.assertRaises(RateLimitError):
                await api.health()
        self.assertEqual(len(requests), 2)

    async def test_not_found(self):
        _, transport = stub(httpx.Response(404, json={"error": "unknown player"}))
        async with AsyncMythicMC("k", transport=transport) as api:
            with self.assertRaises(NotFoundError):
                await api.get_player_team("nobody")

    async def test_requires_key(self):
        with self.assertRaises(ValueError):
            AsyncMythicMC("")

    async def test_close_refuses_further_requests(self):
        _, transport = stub(httpx.Response(200, json={"ok": True}))
        api = AsyncMythicMC("k", transport=transport)
        await api.close()
        with self.assertRaises(RuntimeError):
            await api.health()


if __name__ == "__main__":
    unittest.main()
