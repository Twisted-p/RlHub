import base64
from copy import deepcopy
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import struct
import tempfile
from threading import Thread
import time
import unittest
from unittest.mock import patch
from urllib.request import Request, urlopen
from urllib.error import HTTPError

from desktop_app import start_server
from performance_service import PerformanceService, enable_stats_api, read_settings

PLAYER = "Epic|" + "a" * 32 + "|0"
STATE = {"Event": "UpdateState", "Data": {"MatchGuid": "test-match", "Players": [
    {"Name": "Player A", "PrimaryId": PLAYER, "TeamNum": 0, "Score": 425, "Goals": 2,
     "Assists": 1, "Saves": 3, "Shots": 5, "Touches": 20, "Demos": 1},
    {"Name": "Player B", "PrimaryId": "Steam|123|0", "TeamNum": 1, "Score": 210,
     "Goals": 1, "Assists": 0, "Saves": 1, "Shots": 3}],
    "Game": {"PlaylistId": 11, "Teams": [{"Name": "Blue", "TeamNum": 0, "Score": 3},
             {"Name": "Orange", "TeamNum": 1, "Score": 1}], "bReplay": False, "bOvertime": False}}}
END = {"Event": "MatchEnded", "Data": {"MatchGuid": "test-match", "WinnerTeamNum": 0}}


class PerformanceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.path = Path(self.temporary.name)
        self.service = PerformanceService(self.path / "data", root=self.path, local_player={"name": "Player A", "playerId": PLAYER})

    def tearDown(self):
        self.service.stop()
        self.temporary.cleanup()

    def test_end_snapshot_persists_and_deduplicates(self):
        self.service.ingest(STATE)
        self.service.ingest(END)
        self.service.ingest(END)
        final = deepcopy(STATE)
        final["Data"]["Players"][0]["Score"] = 450
        self.service.ingest(final)
        matches = self.service.snapshot()["matches"]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]["players"][0]["score"], 450)
        self.assertEqual(matches[0]["players"][0]["accuracy"], 40)
        self.assertEqual(matches[0]["winnerTeam"], 0)
        self.assertEqual(matches[0]["mode"], "Ranked 2v2")
        restored = PerformanceService(self.path / "data", root=self.path)
        self.assertEqual(restored.snapshot()["matches"], matches)

    def test_goal_replay_does_not_erase_active_match(self):
        self.service.ingest(STATE)
        replay = deepcopy(STATE)
        replay["Data"]["Game"]["bReplay"] = True
        self.service.ingest(replay)
        self.service.ingest(END)
        self.assertEqual(len(self.service.snapshot()["matches"]), 1)

    def test_history_replays_and_abandoned_matches_are_not_saved(self):
        self.service.ingest({"Event": "ReplayCreated", "Data": {"MatchGuid": "test-match"}})
        self.service.ingest(STATE)
        self.service.ingest(END)
        self.assertEqual(self.service.snapshot()["matches"], [])
        self.service.ingest({"Event": "MatchCreated", "Data": {"MatchGuid": "test-match"}})
        self.service.ingest(STATE)
        self.service.ingest({"Event": "MatchDestroyed", "Data": {"MatchGuid": "test-match"}})
        self.service.ingest(END)
        self.assertEqual(self.service.snapshot()["matches"], [])

    def test_late_join_flag_and_missing_stats(self):
        state = deepcopy(STATE)
        state["Data"]["Players"][0].pop("Shots")
        self.service.ingest(state)
        self.service.ingest(END)
        match = self.service.snapshot()["matches"][0]
        self.assertTrue(match["partial"])
        self.assertIsNone(match["players"][0]["accuracy"])

    def test_config_activation_preserves_settings_and_backup(self):
        config = self.path / "TAGame/Config/DefaultStatsAPI.ini"
        config.parent.mkdir(parents=True)
        original = "[TAGame.MatchStatsExporter_TA]\n; keep comment\nPort=49123\nWebPort=49124\nPacketSendRate=0\n[Other]\nValue=123\n"
        config.write_text(original)
        self.service.setup()
        self.assertTrue(read_settings(config)["enabled"])
        self.assertIn("; keep comment", config.read_text())
        self.assertIn("Value=123", config.read_text())
        self.assertEqual(config.with_name(config.name + ".rlhub.bak").read_text(), original)
        self.service.setup()
        self.assertEqual(config.with_name(config.name + ".rlhub.bak").read_text(), original)

    def test_start_automatically_activates_stats_api(self):
        config = self.path / "TAGame/Config/DefaultStatsAPI.ini"
        config.parent.mkdir(parents=True)
        original = "[TAGame.MatchStatsExporter_TA]\nPacketSendRate=0\nWebPort=49124\n"
        config.write_text(original)
        self.service.start()
        deadline = time.monotonic() + 3
        while not self.service.snapshot()["enabled"] and time.monotonic() < deadline:
            time.sleep(.02)
        self.assertTrue(self.service.snapshot()["enabled"])
        self.assertEqual(config.with_name(config.name + ".rlhub.bak").read_text(), original)
        self.assertIn("automatisk", self.service.snapshot()["setupMessage"])

    def test_auto_setup_preserves_already_enabled_settings(self):
        config = self.path / "TAGame/Config/TAStatsAPI.ini"
        config.parent.mkdir(parents=True)
        original = "[TAGame.MatchStatsExporter_TA]\nPacketSendRate=7\nWebPort=49126\n"
        config.write_text(original)
        with patch("performance_service.enable_stats_api") as enable:
            self.service._ensure_setup()
            self.service._ensure_setup()
        enable.assert_not_called()
        self.assertEqual(config.read_text(), original)
        self.assertEqual(self.service.snapshot()["setupMessage"], "")

    def test_auto_setup_retries_when_game_is_discovered_later(self):
        config = self.path / "TAGame/Config/DefaultStatsAPI.ini"
        config.parent.mkdir(parents=True)
        config.write_text("[TAGame.MatchStatsExporter_TA]\nPacketSendRate=0\n")
        self.service.root = None
        with patch("performance_service.game_info", side_effect=[(None, None), (self.path, None)]):
            self.service._ensure_setup()
            self.assertFalse(self.service.snapshot()["enabled"])
            self.assertTrue(self.service.snapshot()["setupError"])
            self.service._ensure_setup()
        self.assertTrue(self.service.snapshot()["enabled"])
        self.assertEqual(self.service.snapshot()["setupError"], "")

    def test_auto_setup_permission_error_keeps_app_available(self):
        config = self.path / "TAGame/Config/DefaultStatsAPI.ini"
        config.parent.mkdir(parents=True)
        original = "[TAGame.MatchStatsExporter_TA]\nPacketSendRate=0\n"
        config.write_text(original)
        with patch("performance_service.enable_stats_api", side_effect=PermissionError):
            self.service._ensure_setup()
        self.assertIn("administrator", self.service.snapshot()["setupError"])
        self.assertFalse(self.service.snapshot()["enabled"])
        self.assertEqual(config.read_text(), original)

    def test_auto_setup_uses_override_and_keeps_original_backup(self):
        config = self.path / "TAGame/Config/TAStatsAPI.ini"
        config.parent.mkdir(parents=True)
        default = config.with_name("DefaultStatsAPI.ini")
        original = "[TAGame.MatchStatsExporter_TA]\nPacketSendRate=0\nWebPort=49124\n"
        config.write_text(original)
        default.write_text(original)
        self.service._ensure_setup()
        config.write_text(original + "; reset by game update\n")
        self.service._ensure_setup()
        self.assertTrue(self.service.snapshot()["enabled"])
        self.assertEqual(default.read_text(), original)
        self.assertEqual(config.with_name(config.name + ".rlhub.bak").read_text(), original)

    def test_history_endpoint_and_activation_origin(self):
        server = start_server(0, performance=self.service)
        origin = f"http://127.0.0.1:{server.server_port}"
        try:
            self.service.ingest(STATE)
            self.service.ingest(END)
            with urlopen(origin + "/api/performance") as response:
                self.assertEqual(len(json.load(response)["matches"]), 1)
            with self.assertRaises(HTTPError) as result:
                urlopen(Request(origin + "/api/performance/setup", method="POST"))
            self.assertEqual(result.exception.code, 403)
        finally:
            server.shutdown()
            server.server_close()

    def test_local_websocket_transport(self):
        class GameSocket(BaseHTTPRequestHandler):
            def do_GET(handler):
                key = handler.headers["Sec-WebSocket-Key"]
                accept = base64.b64encode(hashlib.sha1((key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11").encode()).digest()).decode()
                handler.send_response(101)
                handler.send_header("Upgrade", "websocket")
                handler.send_header("Connection", "Upgrade")
                handler.send_header("Sec-WebSocket-Accept", accept)
                handler.end_headers()
                for event in [STATE, END]:
                    wire_event = dict(event, Data=json.dumps(event["Data"]))
                    payload = json.dumps(wire_event).encode()
                    header = bytes([0x81, 126]) + struct.pack("!H", len(payload)) if len(payload) >= 126 else bytes([0x81, len(payload)])
                    handler.wfile.write(header + payload)
                    handler.wfile.flush()
                time.sleep(.3)
            def log_message(self, *args):
                pass
        game = ThreadingHTTPServer(("127.0.0.1", 0), GameSocket)
        config = self.path / "TAGame/Config/DefaultStatsAPI.ini"
        config.parent.mkdir(parents=True)
        config.write_text(f"[TAGame.MatchStatsExporter_TA]\nPacketSendRate=2\nWebPort={game.server_port}\n")
        Thread(target=game.serve_forever, daemon=True).start()
        try:
            self.service.start()
            deadline = time.monotonic() + 5
            while not self.service.snapshot()["matches"] and time.monotonic() < deadline:
                time.sleep(.05)
            self.assertEqual(len(self.service.snapshot()["matches"]), 1)
        finally:
            self.service.stop()
            game.shutdown()
            game.server_close()

    def test_actual_wire_envelope_decodes_inner_json(self):
        for event in [STATE, END]:
            self.service.ingest(dict(event, Data=json.dumps(event["Data"])))
        result = self.service.snapshot()
        self.assertEqual(len(result["matches"]), 1)
        self.assertEqual(result["parsedEvents"], 2)
        self.assertEqual(result["ignoredMessages"], 0)
        self.assertEqual(result["lastEventName"], "MatchEnded")

    def test_invalid_inner_json_is_reported_without_stopping_collector(self):
        self.service.ingest({"Event": "UpdateState", "Data": "not json"})
        self.service.ingest(dict(STATE, Data=json.dumps(STATE["Data"])))
        self.service.ingest(dict(END, Data=json.dumps(END["Data"])))
        result = self.service.snapshot()
        self.assertEqual(result["ignoredMessages"], 1)
        self.assertEqual(result["parsedEvents"], 2)
        self.assertEqual(len(result["matches"]), 1)

    def test_match_end_without_guid_uses_current_match(self):
        self.service.ingest(dict(STATE, Data=json.dumps(STATE["Data"])))
        self.service.ingest({"Event": "MatchEnded", "Data": '{"WinnerTeamNum":0}'})
        self.assertEqual(len(self.service.snapshot()["matches"]), 1)

    def test_private_match_without_guid_gets_stable_local_id(self):
        self.service.ingest({"Event": "MatchCreated", "Data": "{}"})
        state = deepcopy(STATE)
        state["Data"].pop("MatchGuid")
        self.service.ingest(dict(state, Data=json.dumps(state["Data"])))
        self.service.ingest({"Event": "MatchEnded", "Data": '{"WinnerTeamNum":0}'})
        self.service.ingest({"Event": "MatchEnded", "Data": '{"WinnerTeamNum":0}'})
        matches = self.service.snapshot()["matches"]
        self.assertEqual(len(matches), 1)
        self.assertTrue(matches[0]["id"].startswith("local-"))


if __name__ == "__main__":
    unittest.main()
