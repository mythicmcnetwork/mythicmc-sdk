import asyncio
import unittest
import httpx
from mythicmc import MythicMC, AsyncMythicMC, models


class Release110(unittest.TestCase):
    def test_new_routes_sync_and_async(self):
        cases = [('get_survival_shop', '/v1/survival/shop', None), ('get_player_shop_bundles', '/v1/players/{id}/shop-bundles', 'id'), ('list_bounty_claims', '/v1/survival/bounty-claims', 'page'), ('get_bounty_claim', '/v1/survival/bounty-claims/{claimId}', 'claimId'), ('get_event_details', '/v1/survival/events/{eventId}/details', 'eventId'), ('list_event_schedules', '/v1/survival/event-schedules', 'page'), ('get_event_schedule', '/v1/survival/event-schedules/{scheduleId}', 'scheduleId'), ('list_stalls', '/v1/survival/stalls', 'page'), ('get_stall', '/v1/survival/stalls/{stallId}', 'stallId'), ('list_bounties', '/v1/survival/bounties', 'page'), ('get_bounty', '/v1/survival/bounties/{id}', 'id')]
        for client_cls in (MythicMC, AsyncMythicMC):
            calls = []
            def handle(request):
                calls.append(request)
                return httpx.Response(200, json={})
            client = client_cls('k', transport=httpx.MockTransport(handle))
            async def run():
                for method, path, arg in cases:
                    args = ['a/b'] if arg and arg != 'page' else []
                    kwargs = {'limit': 2, 'cursor': 'a+/='} if arg == 'page' else {}
                    reply = getattr(client, method)(*args, **kwargs)
                    if client_cls is AsyncMythicMC:
                        await reply
                    expected = path.replace('{' + str(arg) + '}', 'a%2Fb')
                    if arg == 'page':
                        expected += '?limit=2&cursor=a%2B%2F%3D'
                    self.assertEqual(calls[-1].url.raw_path.decode(), expected)
                result = client.close()
                if client_cls is AsyncMythicMC:
                    await result
            asyncio.run(run())

    def test_conditional_shop_sync_and_async(self):
        for client_cls in (MythicMC, AsyncMythicMC):
            def handle(request):
                if request.headers.get('if-none-match') == '"abc"':
                    return httpx.Response(304)
                return httpx.Response(200, json={'revision': 'abc'}, headers={'ETag': '"abc"'})
            client = client_cls('k', transport=httpx.MockTransport(handle))
            async def run():
                shop = client.get_survival_shop()
                if client_cls is AsyncMythicMC:
                    shop = await shop
                self.assertEqual(shop.meta.etag, '"abc"')
                result = client.get_survival_shop(shop.meta.etag)
                if client_cls is AsyncMythicMC:
                    result = await result
                self.assertIsNone(result)
                close = client.close()
                if client_cls is AsyncMythicMC:
                    await close
            asyncio.run(run())

    def test_baskets_keep_null_slots_and_unknown_totals(self):
        reply = models.parse(models.PlayerShopBundles, {'bundles': [{'products': [None, {'material': 'minecraft:stone', 'quantity': 2, 'unitPrice': None, 'available': False}, None, None, None], 'totalPrice': None, 'available': False}]})
        basket = reply.bundles[0]
        self.assertEqual(len(basket.products), 5)
        self.assertIsNone(basket.products[0])
        self.assertEqual(basket.products[1].material, 'minecraft:stone')
        self.assertIsNone(basket.total_price)

    def test_event_variants_and_nested_prize_variants(self):
        raffle = models.parse(models.EventDetails, {'id': 'raffle', 'entryCost': 5, 'maxTicketsPerPlayer': 2})
        self.assertIsInstance(raffle, models.RaffleDetails)
        self.assertEqual(raffle.entry_cost, 5)
        bingo = models.parse(models.EventDetails, {'id': 'bingo', 'mode': 'full', 'prizes': [{'rank': 1, 'items': [{'spawner': 'cow', 'quantity': 1}]}]})
        self.assertIsInstance(bingo, models.BingoDetails)
        self.assertIsInstance(bingo.prizes[0].items[0], models.SpawnerPrize)
        self.assertEqual(bingo.prizes[0].items[0].spawner, 'cow')

    def test_removed_fields_are_not_models(self):
        self.assertFalse(hasattr(models, 'WorldStats'))
        self.assertFalse(hasattr(models.parse(models.SurvivalStats, {'combat': {}, 'world': {}}), 'world'))
        self.assertFalse(hasattr(models.parse(models.SelectedCosmetic, {'preview': 'old'}), 'preview'))
