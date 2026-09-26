import asyncio
import unittest
import httpx
from mythicmc import MythicMC, AsyncMythicMC, AuthenticationError, models


class DuelsTests(unittest.TestCase):
    def test_routes_and_anonymous_headers_sync_and_async(self):
        cases = [
            ('get_player_duels_stats', ['a/b'], {}, '/v1/players/a%2Fb/stats/duels'),
            ('get_duels', [], {}, '/v1/duels'),
            ('get_duels_ladder', [], {}, '/v1/duels/ladder'),
            ('list_duels_kits', [], {'limit': 2, 'cursor': 'a+/='}, '/v1/duels/kits?limit=2&cursor=a%2B%2F%3D'),
            ('get_duels_kit', ['a/b'], {}, '/v1/duels/kits/a%2Fb'),
            ('list_duels_matches', [], {'limit': 2, 'cursor': 'a+/=', 'player': 'A B'}, '/v1/duels/matches?limit=2&cursor=a%2B%2F%3D&player=A+B'),
            ('get_duels_match', ['a/b'], {}, '/v1/duels/matches/a%2Fb'),
            ('list_duels_leaderboards', [], {}, '/v1/gamemodes/duels/leaderboards'),
            ('get_duels_leaderboard', ['rating', 'all_time'], {'kit': 'a/b', 'limit': 2, 'cursor': 'a+/='}, '/v1/gamemodes/duels/leaderboards/rating/all_time?limit=2&cursor=a%2B%2F%3D&kit=a%2Fb'),
        ]
        for cls in (MythicMC, AsyncMythicMC):
            calls = []
            def handle(request):
                calls.append(request)
                return httpx.Response(200, json={})
            async def run():
                client = cls(transport=httpx.MockTransport(handle))
                for method, args, kwargs, expected in cases:
                    reply = getattr(client, method)(*args, **kwargs)
                    if cls is AsyncMythicMC:
                        await reply
                    self.assertEqual(calls[-1].url.raw_path.decode(), expected)
                    self.assertNotIn('authorization', calls[-1].headers)
                result = client.close()
                if cls is AsyncMythicMC:
                    await result
            asyncio.run(run())

    def test_nested_stats_keep_all_time_and_null_ratings(self):
        stats = models.parse(models.PlayerDuelsStats, {
            'uuid': 'a', 'name': 'Alpha', 'duels': {
                'rankedWins': {'daily': 1, 'weekly': 2, 'monthly': 3, 'all_time': 4},
                'kits': [{'kit': 'sword', 'rating': None, 'wins': {'all_time': 4}}], 'best': None,
            },
        })
        self.assertEqual(stats.duels.ranked_wins.all_time, 4)
        self.assertEqual(stats.duels.kits[0].wins.all_time, 4)
        self.assertIsNone(stats.duels.kits[0].rating)
        self.assertIsNone(stats.duels.best)

    def test_match_and_board_models(self):
        matches = models.parse(models.DuelsMatchPage, {'rows': [{'id': 'm1', 'players': [{'name': 'Alpha', 'remainingHealth': None}], 'winner': None, 'startedAt': None}], 'nextCursor': 'next'})
        self.assertEqual(matches.rows[0].players[0].name, 'Alpha')
        self.assertIsNone(matches.rows[0].players[0].remaining_health)
        self.assertEqual(matches.next_cursor, 'next')
        board = models.parse(models.DuelsLeaderboard, {'rows': [{'value': 120, 'displayValue': '120 points'}], 'kit': None, 'stale': False})
        self.assertEqual(board.rows[0].display_value, '120 points')
        self.assertFalse(board.stale)
        self.assertIsNone(board.kit)

    def test_keyed_endpoint_still_reports_authentication_error(self):
        with MythicMC(transport=httpx.MockTransport(lambda _: httpx.Response(401, json={'error': 'missing key'}))) as api:
            with self.assertRaises(AuthenticationError):
                api.get_duels()
