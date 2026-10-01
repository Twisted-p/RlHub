from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import json

from desktop_app import start_server
from overlay_service import OverlayService
from readiness_service import ReadinessService


class Feed:
    def __init__(self):
        self.data = dict(connected=True, liveAge=0, localPlayer={"name": "A", "playerId": "public-a"},
                         activeMatch=False, live={"training": True}, matches=[])

    def snapshot(self):
        return deepcopy(self.data)


class CoachingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name)
        self.now = 100.0
        self.wall = datetime(2026, 10, 1, 10, tzinfo=timezone.utc)
        self.feed = Feed()
        self.overlay = OverlayService(self.path, self.feed)
        self.profile(900)
        self.service = self.create()

    def create(self):
        return ReadinessService(self.path, self.feed, self.overlay, clock=lambda: self.now, wall=lambda: self.wall)

    def profile(self, mmr):
        self.overlay.set_profile({"playerId": "public-a", "name": "A", "ranks": [{"playlist": "2v2", "mmr": mmr}]})

    def step(self, seconds=1):
        result = None
        for _ in range(seconds):
            self.now += 1
            self.wall += timedelta(seconds=1)
            result = self.service.tick()
        return result

    def add_match(self, win, playlist=11, player="public-a", **stats):
        self.wall += timedelta(seconds=1)
        self.feed.data["matches"].insert(0, {"id": str(len(self.feed.data["matches"])), "playlist": playlist,
             "endedAt": self.wall.isoformat(), "winnerTeam": 0 if win else 1,
             "players": [{"playerId": player, "team": 0, "goals": 1, "shots": 4, "saves": 2, "assists": 0, "score": 300, **stats}]})
        return self.service.tick()

    def lobby(self):
        self.feed.data.update(live=None, liveAge=None, activeMatch=False)
        self.step()

    def tearDown(self):
        self.temporary.cleanup()

    def test_starts_on_play_not_lobby_and_actual_training_only(self):
        self.lobby()
        self.assertEqual(self.step(20)["startedAt"], "")
        self.feed.data.update(live={"training": True}, liveAge=0)
        self.service.tick()
        view = self.step(600)
        self.assertEqual(view["trainingSeconds"], 600)
        self.assertEqual(view["components"]["training"], 20)
        self.lobby()
        self.assertEqual(self.step(10)["trainingSeconds"], 600)
        self.assertGreater(view["readiness"], 50)

    def test_stale_replay_disconnected_sleep_do_not_count_training(self):
        self.service.tick()
        self.step(3)
        self.feed.data["liveAge"] = 99
        self.assertEqual(self.step(5)["trainingSeconds"], 3)
        self.feed.data.update(liveAge=0, replay=True)
        self.assertEqual(self.step(5)["trainingSeconds"], 3)
        self.feed.data.update(replay=False, connected=False)
        self.assertEqual(self.step(5)["trainingSeconds"], 3)
        self.feed.data["connected"] = True
        self.now += 900
        self.assertEqual(self.service.tick()["trainingSeconds"], 3)

    def test_last_five_own_public_matches_and_missing_stats(self):
        self.service.tick()
        self.add_match(True, playlist=6)
        self.add_match(True, player="someone-else")
        for result in (False, True, False, True, True, False):
            view = self.add_match(result, shots=None)
        self.assertEqual(view["matchCount"], 6)
        self.assertEqual((view["wins"], view["losses"]), (3, 2))
        self.assertIsNone(view["averages"]["shots"])
        self.assertEqual(view["averages"]["goals"], 1)
        self.assertEqual(self.service.tick()["matchCount"], 6)
        self.assertEqual(view["bracketProgress"], 1)

    def test_three_losses_require_15_continuous_minutes_rest(self):
        self.service.tick()
        for win in (True, False, False, True, False):
            view = self.add_match(win)
        self.assertEqual(view["advice"]["rest"], 900)
        self.assertFalse(view["resting"])
        self.lobby()
        self.service.start_break()
        self.step(120)
        self.feed.data.update(activeMatch=True)
        self.assertEqual(self.step()["restSeconds"], 0)
        self.lobby()
        focus = self.service.tick()["focusSeconds"]
        view = self.step(900)
        self.assertEqual(view["advice"], {})
        self.assertFalse(view["resting"])
        self.assertLessEqual(view["focusSeconds"] - focus, 1)
        self.assertEqual(self.service.tick()["advice"], {})  # Same bracket never retriggers.

    def test_three_wins_require_rest_then_new_training_and_next_bracket(self):
        self.service.tick()
        self.step(600)  # Earlier training cannot satisfy post-break warmup.
        for win in (True, True, False, True, False):
            self.add_match(win)
        self.lobby()
        self.service.start_break()
        view = self.step(300)
        self.assertEqual(view["advice"]["stage"], "warmup")
        self.assertEqual(view["warmupSeconds"], 0)
        self.step(100)
        self.feed.data.update(live={"training": True}, liveAge=0)
        self.step()
        self.assertEqual(self.step(299)["advice"]["stage"], "warmup")
        self.assertEqual(self.step()["advice"], {})
        for win in (False, False, False, True, True):
            view = self.add_match(win)
        self.assertEqual(view["advice"]["bracket"], 2)
        self.assertEqual(view["advice"]["rest"], 900)

    def test_playing_during_pause_still_reduces_focus_and_stale_training_is_not_rest(self):
        self.service.tick()
        self.service.start_break()
        view = self.step(60)
        self.assertEqual(view["restSeconds"], 0)
        self.assertEqual(view["focusSeconds"], 60)
        self.feed.data["liveAge"] = 99
        self.assertEqual(self.step(60)["restSeconds"], 0)

    def test_focus_progressive_90_min_not_app_open_and_pause_does_not_reset(self):
        start = self.service.tick()
        self.lobby()
        middle = self.step(2700)
        end = self.step(2700)
        self.assertGreater(start["readiness"], middle["readiness"])
        self.assertGreater(middle["readiness"], end["readiness"])
        self.assertEqual(end["focusRemaining"], 0)
        self.assertEqual(end["components"]["fatigue"], 35)
        self.service.start_break()
        self.assertEqual(self.step(900)["focusRemaining"], 0)

    def test_mmr_sources_baselines_and_wrong_account(self):
        self.service.tick()
        self.profile(912)
        view = self.step()
        self.assertEqual(view["mmr"][0]["delta"], 12)
        self.assertEqual(view["components"]["mmr"], 4)
        self.profile(882)
        self.assertEqual(self.step()["mmr"][0]["delta"], -18)
        self.overlay.profile["playerId"] = "other"
        self.assertEqual(self.step()["mmr"], [])
        self.assertEqual(self.step()["components"]["mmr"], 0)

    def test_persist_restart_excludes_offline_time_and_day_rollover(self):
        self.service.tick()
        self.step(10)
        for win in (False, False, False, True, True):
            self.add_match(win)
        self.service.stop()
        self.now += 999
        self.wall += timedelta(seconds=999)
        self.service = self.create()
        view = self.service.tick()
        self.assertEqual((view["trainingSeconds"], view["matchCount"]), (10, 5))
        self.assertEqual(view["advice"]["bracket"], 1)
        self.wall += timedelta(days=1)
        view = self.service.tick()
        self.assertEqual((view["trainingSeconds"], view["matchCount"]), (0, 0))

    def test_api_same_origin_and_reset_mmr_baseline(self):
        self.service.tick()
        self.profile(915)
        self.lobby()
        server = start_server(0, performance=self.feed, overlay=self.overlay, readiness=self.service)
        origin = f"http://127.0.0.1:{server.server_port}"
        try:
            with self.assertRaises(HTTPError) as raised:
                urlopen(Request(origin + "/api/readiness/reset", method="POST"))
            self.assertEqual(raised.exception.code, 403)
            with urlopen(Request(origin + "/api/readiness/reset", method="POST", headers={"Origin": origin})) as response:
                self.assertEqual(json.load(response)["startedAt"], "")
            self.assertEqual(self.overlay.bases["2v2"], 915)
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
