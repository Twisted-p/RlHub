from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from desktop_app import start_server
from overlay_service import OverlayService
from performance_service import PerformanceService
from test_performance import STATE, END, PLAYER


class OverlayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.performance = PerformanceService(self.path, root=self.path, local_player={"name": "Player A", "playerId": PLAYER})
        self.overlay = OverlayService(self.path, self.performance)
        self.overlay.set_profile({"name": "Player A", "playerId": PLAYER, "fetchedAt": "2026-10-01T12:00:00+00:00", "ranks": [{"playlist": "2v2", "mmr": 900, "rank": "Diamond I"}]})

    def tearDown(self):
        self.performance.stop()
        self.temp.cleanup()

    def test_active_match_toggle_and_real_player_stats(self):
        self.performance.ingest(STATE)
        self.assertEqual(self.overlay.view()["phase"], "hidden")
        self.overlay.configure({"showInMatch": True})
        view = self.overlay.view()
        self.assertEqual(view["phase"], "match")
        self.assertEqual(view["player"]["score"], 425)
        self.assertEqual(view["player"]["goals"], 2)
        self.assertEqual(view["teams"][0]["score"], 3)

    def test_finish_counts_once_and_abandon_does_not_count(self):
        self.performance.ingest(STATE)
        self.performance.ingest(END)
        self.performance.ingest(END)
        view = self.overlay.view()
        self.assertEqual(view["phase"], "post-match")
        self.assertEqual((view["wins"], view["losses"], view["result"]), (1, 0, "Seier"))
        self.overlay.reset_session()
        self.assertEqual(self.overlay.view()["wins"], 0)
        self.performance.ingest({"Event": "MatchDestroyed", "Data": {}})
        state = deepcopy(STATE)
        state["Data"]["MatchGuid"] = "abandoned"
        self.performance.ingest(state)
        self.performance.ingest({"Event": "MatchDestroyed", "Data": {}})
        self.assertEqual(self.overlay.view()["losses"], 0)

    def test_training_timer_without_saving_training_as_match(self):
        state = deepcopy(STATE)
        state["Data"]["Players"] = state["Data"]["Players"][:1]
        state["Data"]["Game"]["Teams"] = []
        self.performance.ingest(state)
        self.assertEqual(self.overlay.view(now=100)["phase"], "training")
        self.assertEqual(self.overlay.view(now=165)["trainingSeconds"], 65)
        self.assertEqual(self.performance.snapshot()["matches"], [])
        self.performance.ingest({"Event": "MatchDestroyed", "Data": {}})
        self.assertEqual(self.overlay.view(now=170)["phase"], "lobby")

    def test_old_matches_not_shown_and_unknown_player_not_guessed(self):
        self.performance.ingest(STATE)
        self.performance.ingest(END)
        self.performance.history[0]["endedAt"] = "2000-01-01T00:00:00+00:00"
        self.assertEqual(self.overlay.view()["phase"], "lobby")
        self.performance.local_player = {"playerId": "not-this-player"}
        self.overlay.profile = None
        self.assertIsNone(self.overlay.view()["player"])

    def test_mmr_baseline_and_stale_profile_cannot_revert_refresh(self):
        self.overlay.set_profile({"name": "Player A", "playerId": PLAYER, "fetchedAt": "2026-10-01T13:00:00+00:00", "ranks": [{"playlist": "2v2", "mmr": 909, "rank": "Diamond I"}]})
        view = self.overlay.view()
        self.assertEqual((view["startMmr"], view["mmr"], view["delta"]), (900, 909, 9))
        self.overlay.set_profile({"name": "Player A", "playerId": PLAYER, "fetchedAt": "2026-10-01T12:00:00+00:00", "ranks": [{"playlist": "2v2", "mmr": 900, "rank": "Diamond I"}]})
        self.assertEqual(self.overlay.view()["mmr"], 909)

    def test_private_matches_show_result_without_ranked_win_and_replays_hide(self):
        private = deepcopy(STATE)
        private["Data"]["Game"]["PlaylistId"] = 6
        self.performance.ingest(private)
        self.performance.ingest(END)
        view = self.overlay.view()
        self.assertEqual(view["result"], "Seier")
        self.assertEqual(view["wins"], 0)
        self.performance.ingest({"Event": "ReplayCreated", "Data": {}})
        self.assertEqual(self.overlay.view()["phase"], "hidden")

    def test_training_timer_survives_short_shot_transition(self):
        snapshot = {"connected": True, "liveAge": 0, "live": {"training": True, "players": []}}
        self.overlay.view(snapshot, now=100)
        self.overlay.view({"connected": True}, now=101)
        self.assertEqual(self.overlay.view(snapshot, now=102)["trainingSeconds"], 2)

    def test_disabling_also_hides_active_preview(self):
        self.overlay.preview()
        self.assertTrue(self.overlay.view()["preview"])
        self.overlay.configure({"enabled": False})
        self.assertFalse(self.overlay.view()["preview"])

    def test_settings_are_atomic_and_persisted(self):
        self.overlay.configure({"position": "bottom-right", "scale": 125, "showInMatch": True})
        with self.assertRaises(ValueError):
            self.overlay.configure({"enabled": False, "scale": 1000})
        self.assertTrue(self.overlay.settings["enabled"])
        restored = OverlayService(self.path, self.performance)
        self.assertEqual(restored.settings["position"], "bottom-right")
        self.assertTrue(restored.settings["showInMatch"])

    def test_api_requires_same_origin_and_rejects_invalid_settings(self):
        server = start_server(0, self.performance, self.overlay)
        origin = f"http://127.0.0.1:{server.server_port}"
        try:
            for headers, data, status in [({}, {}, 403), ({"Origin": "https://example.com"}, {}, 403), ({"Origin": origin}, {"scale": 500}, 400)]:
                request = Request(origin + "/api/overlay/settings", data=json.dumps(data).encode(), headers=headers)
                with self.assertRaises(HTTPError) as result:
                    urlopen(request)
                self.assertEqual(result.exception.code, status)
            request = Request(origin + "/api/overlay/settings", data=b'{"showInMatch":true}', headers={"Origin": origin})
            with urlopen(request) as response:
                self.assertTrue(json.load(response)["settings"]["showInMatch"])
            with urlopen(origin + "/overlay.html") as response:
                self.assertIn(b"desktop-runtime.js", response.read())
        finally:
            server.shutdown()
            server.server_close()
