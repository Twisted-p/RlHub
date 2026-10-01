from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

from mmr_provider import build_rank_profile, fetch_rank_profile, normalize_player_id, resolve_player_id
from tracker_proxy import TrackerUnavailableError

EPIC_ID = "Epic|" + "a" * 32 + "|0"


class MmrProviderTests(unittest.TestCase):
    def test_local_login_resolves_only_the_requested_name(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)
            (path / "Launch.log").write_text(
                f"[0018.08] Party: HandleLocalPlayerLoginStatusChanged PlayerName=twisted_p PlayerID={EPIC_ID} LoginStatus=LS_LoggedIn IsPrimary=True IsInParty=False\n",
                encoding="utf-8",
            )
            self.assertEqual(resolve_player_id("epic", "Twisted_p", log_dir=path), EPIC_ID)
            with self.assertRaises(TrackerUnavailableError):
                resolve_player_id("epic", "SomeoneElse", log_dir=path)

    def test_explicit_id_validation(self):
        self.assertEqual(normalize_player_id("epic", "a" * 32), EPIC_ID)
        with self.assertRaises(ValueError):
            normalize_player_id("steam", EPIC_ID)
        with self.assertRaises(ValueError):
            normalize_player_id("epic", "twisted_p")

    def test_ranks_come_from_tiers_and_zero_based_divisions(self):
        profile = build_rank_profile("epic", "twisted_p", EPIC_ID, {"playlists": [
            {"id": 10, "mmr": 638, "tier": 10, "division": 0},
            {"id": 11, "mmr": 911, "tier": 14, "division": 0},
            {"id": 13, "mmr": 904, "tier": 14, "division": 3},
            {"id": 0, "mmr": 1175, "tier": 0, "division": 0},
        ]})
        self.assertEqual([row["playlist"] for row in profile["ranks"]], ["1v1", "2v2", "3v3"])
        self.assertEqual(profile["ranks"][0]["rank"], "Platinum I Division I")
        self.assertEqual(profile["ranks"][1]["rank"], "Diamond II Division I")
        self.assertEqual(profile["ranks"][2]["rank"], "Diamond II Division IV")
        self.assertEqual(profile["session"]["currentMmr"], 911)
        self.assertNotIn("Wins", [stat["label"] for stat in profile["stats"]])

    def test_name_failure_does_not_discard_successful_mmr(self):
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"playlists": [{"id": 11, "mmr": 911, "tier": 14, "division": 0}]}
        session = Mock()
        session.headers = {}
        session.get.side_effect = [response, ValueError("invalid optional name payload")]
        with patch("mmr_provider.requests.Session") as factory:
            factory.return_value.__enter__.return_value = session
            result = fetch_rank_profile("epic", "twisted_p", EPIC_ID)
        self.assertEqual(result["ranks"][0]["mmr"], 911)

    def test_empty_data_does_not_invent_rank(self):
        for rows in [None, []]:
            with self.assertRaises(TrackerUnavailableError):
                build_rank_profile("epic", "twisted_p", EPIC_ID, {"playlists": rows})


if __name__ == "__main__":
    unittest.main()
