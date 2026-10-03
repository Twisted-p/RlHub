from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from progression_service import ProgressionService


class ProgressionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.service = ProgressionService(self.temp.name)
        self.now = datetime.now(timezone.utc)

    def tearDown(self):
        self.temp.cleanup()

    def profile(self, mmr=950, age=0, account="test"):
        return {"playerId":account,"name":"Test","fetchedAt":(self.now-timedelta(days=age)).isoformat(),"ranks":[{"playlist":"2v2","rank":"Diamond II Division III","mmr":mmr}]}

    def test_observations_dedup_persist_and_account_isolation(self):
        old, new = self.profile(900,10), self.profile(950)
        self.service.record(old);self.service.record(new);self.service.record(new)
        loaded = ProgressionService(self.temp.name)
        view = loaded.view(new, now=self.now)
        self.assertEqual(len(view["points"]),2)
        self.assertEqual(view["delta"],50)
        self.assertEqual(loaded.view(self.profile(account="other"),now=self.now)["points"],[])
        self.assertEqual(loaded.view(new,"1v1",now=self.now)["points"],[])
        self.assertNotIn('"test"',Path(self.temp.name,"rank-history.json").read_text())

    def test_periods_missing_rank_and_invalid_samples(self):
        old,new=self.profile(900,40),self.profile(940)
        self.service.record(old);self.service.record(new)
        self.assertEqual(len(self.service.view(new,days=30,now=self.now)["points"]),1)
        self.assertIsNone(self.service.view(new,days=30,now=self.now)["delta"])
        self.assertEqual(len(self.service.view(new,days=0,now=self.now)["points"]),2)
        invalid=self.profile();invalid["fetchedAt"]="invalid";self.service.record(invalid)
        future=self.profile(age=-1);self.service.record(future)
        self.assertEqual(len(self.service.view(new,now=self.now)["points"]),2)
        self.assertIsNone(self.service.view(new,"3v3",now=self.now)["current"])

    def test_ranked_results_use_correct_account_and_mode(self):
        profile=self.profile()
        rows=[{"playlist":11,"endedAt":self.now.isoformat(),"winnerTeam":0,"players":[{"playerId":"test","team":0}]},
              {"playlist":10,"endedAt":self.now.isoformat(),"winnerTeam":0,"players":[{"playerId":"test","team":1}]},
              {"playlist":11,"endedAt":self.now.isoformat(),"winnerTeam":0,"players":[{"playerId":"other","team":1}]},
              {"playlist":24,"endedAt":self.now.isoformat(),"winnerTeam":0,"players":[{"playerId":"test","team":1}]}]
        self.assertEqual(self.service.view(profile,matches=rows,now=self.now)["wins"],1)
        self.assertEqual(len(self.service.view(profile,matches=rows,now=self.now)["recent"]),1)

    def test_overlay_updates_and_restart_keep_history_after_session_reset(self):
        from types import SimpleNamespace
        from overlay_service import OverlayService
        performance = SimpleNamespace(snapshot=lambda: {"matches":[]})
        overlay = OverlayService(self.temp.name, performance)
        overlay.set_profile(self.profile(930,2))
        overlay.set_profile(self.profile(960))
        overlay.set_profile(self.profile(900,3))  # A stale fetch cannot replace current rank.
        overlay.reset_session()
        restarted = OverlayService(self.temp.name, performance)
        self.assertEqual(restarted.profile["ranks"][0]["mmr"],960)
        self.assertEqual(len(restarted.progression.view(restarted.profile,now=self.now)["points"]),2)
