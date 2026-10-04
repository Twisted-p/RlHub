import json
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from unittest.mock import patch
from requests import Response
from tracker_proxy import TrackerUnavailableError, check_tracker_response

from desktop_app import start_server


class DesktopServiceTests(unittest.TestCase):
    def setUp(self):
        self.server = start_server(0)
        self.origin = f"http://127.0.0.1:{self.server.server_port}"

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()

    def lookup(self, platform, gamertag="", origin=True):
        return urlopen(Request(self.origin + "/api/profile",
            data=json.dumps({"platform": platform, "gamertag": gamertag}).encode(),
            headers={"Content-Type": "application/json", **({"Origin": self.origin} if origin else {})}))

    def test_ui_and_tracker_share_origin(self):
        with urlopen(self.origin + "/") as response:
            html = response.read().decode()
            self.assertLess(html.index("desktop-runtime.js"), html.index("./script.js"))
            self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))
        for name in ["dashboard.html", "garage.html", "training.html", "profile.html", "performance.html", "performance.js", "styles.css", "script.js", "desktop-runtime.js", "App%20Logo.png"]:
            with urlopen(self.origin + "/" + name) as response:
                self.assertEqual(response.status, 200)
        with patch("desktop_app.fetch_rank_profile", return_value={"name": "Test Player"}) as fetch:
            with self.lookup("epic", "Test Player") as response:
                self.assertEqual(json.load(response)["profile"]["name"], "Test Player")
            fetch.assert_called_once_with("epic", "Test Player", "")

    def test_source_files_and_traversal_are_not_served(self):
        for name in ["desktop_app.py", "tracker_proxy.py", ".git/config", "../tracker_proxy.py", "%2e%2e%2ftracker_proxy.py", "overwolf/background.js"]:
            with self.assertRaises(HTTPError) as result:
                urlopen(self.origin + "/" + name)
            self.assertEqual(result.exception.code, 404)

    def test_dashboard_ranks_are_current_and_exclude_account_identifiers(self):
        from types import SimpleNamespace
        from threading import RLock
        with urlopen(self.origin + "/api/dashboard-ranks") as response:
            self.assertIsNone(json.load(response)["profile"])
        self.server.overlay = SimpleNamespace(lock=RLock(), profile={
            "name": "Test", "playerId": "private-id", "fetchedAt": "2026-10-03",
            "ranks": [{"playlist": "2v2", "rank": "Diamond I Division II", "mmr": 1000}]})
        with urlopen(self.origin + "/api/dashboard-ranks") as response:
            profile = json.load(response)["profile"]
            self.assertNotIn("playerId", profile)
            self.assertEqual(profile["ranks"][0]["mmr"], 1000)
        self.server.overlay.profile["ranks"][0]["mmr"] = 1009
        with urlopen(self.origin + "/api/dashboard-ranks") as response:
            self.assertEqual(json.load(response)["profile"]["ranks"][0]["mmr"], 1009)

    def test_runtime_session_changes_on_app_restart(self):
        with urlopen(self.origin + "/desktop-runtime.js") as response:
            first = response.read().decode()
        with urlopen(self.origin + "/desktop-runtime.js") as response:
            self.assertEqual(response.read().decode(), first)
        self.assertIn(f'window.RL_HUB_SESSION = "{self.server.session_id}"', first)
        second_server = start_server(0)
        try:
            self.assertNotEqual(self.server.session_id, second_server.session_id)
        finally:
            second_server.shutdown()
            second_server.server_close()

    def test_invalid_lookup_does_not_call_tracker(self):
        with patch("desktop_app.fetch_rank_profile") as fetch:
            for platform, gamertag in [("invalid", "Player"), ("epic", "")]:
                with self.assertRaises(HTTPError) as result:
                    self.lookup(platform, gamertag)
                self.assertEqual(result.exception.code, 400)
            fetch.assert_not_called()

    def test_tracker_denied_returns_actionable_error(self):
        response = Response()
        response.status_code = 403
        with self.assertRaises(TrackerUnavailableError) as result:
            check_tracker_response(response)
        self.assertEqual(result.exception.code, "tracker_access_denied")
        with patch("desktop_app.fetch_rank_profile", side_effect=result.exception):
            with self.assertRaises(HTTPError) as failure:
                self.lookup("epic", "Twisted_p")
            payload = json.load(failure.exception)
            self.assertEqual(failure.exception.code, 503)
            self.assertEqual(payload["code"], "tracker_access_denied")
            self.assertNotIn("403 Client Error", payload["error"])

    def test_get_profile_never_fetches_or_changes_state(self):
        from threading import RLock
        from types import SimpleNamespace
        profile = {"name": "Saved player", "ranks": []}
        self.server.overlay = SimpleNamespace(lock=RLock(), profile=profile)
        with patch("desktop_app.fetch_rank_profile") as fetch:
            with urlopen(self.origin + "/api/profile?platform=epic&gamertag=Other") as response:
                self.assertEqual(json.load(response)["profile"], profile)
            fetch.assert_not_called()
        self.assertEqual(self.server.overlay.profile, profile)

    def test_profile_mutation_requires_origin(self):
        with patch("desktop_app.fetch_rank_profile") as fetch:
            with self.assertRaises(HTTPError) as failure:
                self.lookup("epic", "Other", origin=False)
            self.assertEqual(failure.exception.code, 403)
            fetch.assert_not_called()

    def test_untrusted_host_rejected_for_reads_and_writes(self):
        for method in ("GET", "POST", "OPTIONS"):
            request = Request(self.origin + "/api/profile", method=method,
                headers={"Host": "attacker.example", "Origin": self.origin})
            with self.assertRaises(HTTPError) as failure:
                urlopen(request)
            self.assertEqual(failure.exception.code, 403)

    def test_tracker_rate_limit_is_distinct_from_access_denial(self):
        response = Response()
        response.status_code = 429
        with self.assertRaises(TrackerUnavailableError) as result:
            check_tracker_response(response)
        self.assertEqual(result.exception.code, "tracker_rate_limited")


if __name__ == "__main__":
    unittest.main()
