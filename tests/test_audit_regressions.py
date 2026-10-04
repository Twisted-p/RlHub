from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from desktop_app import start_server, UI_FILES
from overlay_service import OverlayService
from performance_service import PerformanceService
from readiness_service import ReadinessService
from test_performance import STATE, END, PLAYER


class AuditRegressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.performance = PerformanceService(self.root, root=self.root)
        self.overlay = OverlayService(self.root, self.performance)

    def tearDown(self):
        self.performance.stop()
        self.temp.cleanup()

    def profile(self, rank, seconds=0, account=PLAYER):
        return {"playerId": account, "name": "Tester", "fetchedAt":
            (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat(),
            "ranks": [{"playlist": "2v2", "rank": rank, "mmr": 1100}]}

    def test_malformed_nested_events_do_not_change_lifecycle(self):
        self.performance.ingest(STATE)
        before = self.performance.activity_snapshot()
        for fields in ({"Game": None}, {"Game": "wrong"}, {"Game": {"Teams": None}},
                       {"Players": None}, {"Players": [None]}, {"Game": {"Teams": [42]}}):
            event = deepcopy(STATE)
            event["Data"].update(fields)
            self.performance.ingest(event)
            self.assertEqual(self.performance.activity_snapshot(), before)
        self.performance.ingest(END)
        self.assertEqual(len(self.performance.snapshot()["matches"]), 1)
        self.assertEqual(self.performance.snapshot()["ignoredMessages"], 6)

    def test_identity_refresh_switches_accounts_without_changing_root(self):
        a = {"playerId": PLAYER, "name": "A"}
        b = {"playerId": "Steam|123|0", "name": "B"}
        with patch("performance_service.game_info", side_effect=[(self.root, a), (self.root, b), (None, None), (self.root, a)]):
            for expected in (a, b, b, a):
                self.performance.refresh_identity(force=True)
                self.assertEqual(self.performance.snapshot()["localPlayer"], expected)
                self.assertEqual(self.performance.root, self.root)

    def test_coaching_does_not_mix_rank_profile_with_game_account(self):
        self.overlay.set_profile(self.profile("Diamond III Division IV"))
        self.performance.local_player = {"playerId": "Steam|123|0", "name": "B"}
        self.performance.connected = True
        self.performance.ingest(STATE)
        service = ReadinessService(self.root, self.performance, self.overlay)
        view = service.tick()
        self.assertTrue(view["accountMismatch"])
        self.assertEqual(view["mmr"], [])
        self.overlay.set_profile(self.profile("Champion I Division I", account="Steam|123|0"))
        view = service.tick()
        self.assertFalse(view["accountMismatch"])
        self.assertEqual(view["mmr"][0]["current"], 1100)
        self.performance.local_player = None
        self.assertFalse(service.tick()["accountMismatch"])

    def test_failed_acknowledgement_remains_pending_and_retry_persists(self):
        self.overlay.set_profile(self.profile("Diamond III Division IV", -20))
        self.overlay.set_profile(self.profile("Champion I Division I", -10))
        event = self.overlay.promotions.pending(self.overlay.profile)[0]
        with patch.object(Path, "replace", side_effect=PermissionError("Test disk failure")):
            with self.assertRaises(OSError):
                self.overlay.promotions.acknowledge(self.overlay.profile, event["id"])
        self.assertEqual(self.overlay.promotions.pending(self.overlay.profile)[0]["id"], event["id"])
        restored = OverlayService(self.root, self.performance)
        self.assertEqual(restored.promotions.pending(restored.profile)[0]["id"], event["id"])
        self.assertTrue(self.overlay.promotions.acknowledge(self.overlay.profile, event["id"]))
        self.assertEqual(OverlayService(self.root, self.performance).promotions.pending(self.overlay.profile), [])

    def test_overlay_failed_save_rolls_back_and_api_reports_failure(self):
        self.overlay.configure({"scale": 100})
        server = start_server(0, overlay=self.overlay)
        origin = f"http://127.0.0.1:{server.server_port}"
        def change():
            return urlopen(Request(origin + "/api/overlay/settings", data=b'{"scale":125}', headers={"Origin": origin}))
        try:
            with patch.object(Path, "replace", side_effect=PermissionError("Test disk failure")):
                with self.assertRaises(HTTPError) as error:
                    change()
                self.assertEqual(error.exception.code, 500)
                self.assertIn("Prøv igjen", json.load(error.exception)["error"])
            self.assertEqual(self.overlay.settings["scale"], 100)
            self.assertEqual(OverlayService(self.root, self.performance).settings["scale"], 100)
            with change() as response:
                self.assertEqual(response.status, 200)
            self.assertEqual(OverlayService(self.root, self.performance).settings["scale"], 125)
        finally:
            server.shutdown()
            server.server_close()

    def test_runtime_assets_exist_and_are_in_packaged_manifest(self):
        import ast
        repo = Path(__file__).resolve().parents[1]
        tree = ast.parse((repo / "RL Hub.spec").read_text(encoding="utf-8"))
        assets = next(ast.literal_eval(node.value) for node in tree.body if isinstance(node, ast.Assign)
                      and any(isinstance(target, ast.Name) and target.id == "assets" for target in node.targets))
        assets.extend(f"assets/ranks/{i}.png" for i in range(23))
        for name in UI_FILES:
            self.assertTrue((repo / name).is_file(), name)
            self.assertIn(name, assets)


if __name__ == "__main__":
    unittest.main()
