from datetime import datetime, timedelta, timezone
import tempfile
from types import SimpleNamespace
import unittest

from overlay_service import OverlayService
from rank_promotion_service import rank_info


class RankPromotionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.now = datetime.now(timezone.utc) - timedelta(minutes=1)
        self.matches = []
        self.performance = SimpleNamespace(snapshot=lambda: {"matches": self.matches})
        self.overlay = OverlayService(self.temp.name, self.performance)

    def tearDown(self):
        self.temp.cleanup()

    def update(self, rank, seconds=0, account="test", mode="2v2"):
        self.overlay.set_profile({"playerId": account, "name": "Tester", "fetchedAt": (self.now+timedelta(seconds=seconds)).isoformat(),
            "ranks": [{"playlist": mode, "rank": rank, "mmr": 1100}]})

    def pending(self):
        return self.overlay.promotions.pending(self.overlay.profile)

    def test_first_lookup_subtiers_and_divisions_do_not_celebrate(self):
        for seconds, rank in enumerate(("Diamond I Division IV", "Diamond II Division I", "Diamond III Division IV")):
            self.update(rank, seconds)
        self.assertEqual(self.pending(), [])

    def test_new_family_persists_and_ack_prevents_regain_repeat(self):
        self.update("Diamond III Division IV")
        self.update("Champion I Division I", 1)
        event = self.pending()[0]
        self.assertEqual((event["family"], event["previousFamily"], event["icon"]), ("Champion", "Diamond", 16))
        self.overlay = OverlayService(self.temp.name, self.performance)
        self.assertEqual(self.pending()[0]["id"], event["id"])
        self.assertFalse(self.overlay.promotions.acknowledge(self.overlay.profile, "unknown"))
        self.assertTrue(self.overlay.promotions.acknowledge(self.overlay.profile, event["id"]))
        self.update("Diamond III Division IV", 2)
        self.update("Champion II Division I", 3)
        self.overlay.reset_session()
        self.overlay = OverlayService(self.temp.name, self.performance)
        self.assertEqual(self.pending(), [])

    def test_accounts_modes_and_stale_samples_are_isolated(self):
        self.update("Diamond III Division IV")
        self.update("Champion I Division I", -1)
        self.update("Champion I Division I", 1, mode="1v1")
        self.assertEqual(self.pending(), [])
        self.update("Champion I Division I", 2)
        self.assertEqual(len(self.pending()), 1)
        self.update("Grand Champion I Division I", 3, account="other")
        self.assertEqual(self.pending(), [])

    def test_stats_count_only_own_completed_ranked_matches_in_last_day(self):
        self.update("Diamond III Division IV")
        def match(account="test", mode=11, age=0, winner=0):
            return {"playlist": mode, "endedAt": (self.now-timedelta(hours=age)).isoformat(),
                    "winnerTeam": winner, "players": [{"playerId": account, "team": 0}]}
        self.matches = [match(), match(winner=1), match(account="other"), match(mode=10), match(age=25), match(winner=None)]
        self.update("Champion I Division I", 1)
        self.assertEqual(self.pending()[0]["stats"], {"matches24h": 2, "wins24h": 1, "losses24h": 1})

    def test_existing_history_is_baseline_on_upgrade(self):
        self.update("Champion I Division I")
        self.overlay.promotions.file.unlink()
        self.overlay = OverlayService(self.temp.name, self.performance)
        self.update("Diamond III Division IV", 1)
        self.update("Champion II Division I", 2)
        self.assertEqual(self.pending(), [])

    def test_unranked_and_unknown_are_not_milestones(self):
        self.update("Unranked")
        self.update("Champion I Division I", 1)
        self.assertEqual(self.pending(), [])
        self.assertIsNone(rank_info("Something else"))
        self.assertEqual(rank_info("Supersonic Legend")["family"], 8)

    def test_api_requires_same_origin_and_ack_is_account_scoped(self):
        import json
        from urllib.error import HTTPError
        from urllib.request import Request, urlopen
        from desktop_app import start_server
        self.update("Diamond III Division IV")
        self.update("Champion I Division I", 1)
        server = start_server(0, overlay=self.overlay)
        origin = f"http://127.0.0.1:{server.server_port}"
        try:
            with urlopen(origin+"/api/rank-promotions") as response:
                event = json.load(response)["events"][0]
            data = json.dumps({"id":event["id"]}).encode()
            with self.assertRaises(HTTPError) as raised:
                urlopen(Request(origin+"/api/rank-promotions/ack", data=data))
            self.assertEqual(raised.exception.code, 403)
            self.update("Champion I Division I", 2, account="other")
            with urlopen(Request(origin+"/api/rank-promotions/ack", data=data, headers={"Origin":origin})) as response:
                self.assertFalse(json.load(response)["acknowledged"])
            self.update("Champion I Division I", 3)
            with urlopen(Request(origin+"/api/rank-promotions/ack", data=data, headers={"Origin":origin})) as response:
                self.assertTrue(json.load(response)["acknowledged"])
        finally:
            server.shutdown();server.server_close()


if __name__ == "__main__":
    unittest.main()
