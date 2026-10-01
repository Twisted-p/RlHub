import json
import unittest
from urllib.error import HTTPError
from urllib.request import urlopen
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

    def test_ui_and_tracker_share_origin(self):
        with urlopen(self.origin + "/") as response:
            html = response.read().decode()
            self.assertLess(html.index("desktop-runtime.js"), html.index("./script.js"))
            self.assertIsNone(response.headers.get("Access-Control-Allow-Origin"))
        for name in ["dashboard.html", "garage.html", "training.html", "profile.html", "performance.html", "performance.js", "styles.css", "script.js", "desktop-runtime.js", "App%20Logo.png"]:
            with urlopen(self.origin + "/" + name) as response:
                self.assertEqual(response.status, 200)
        with patch("desktop_app.fetch_rank_profile", return_value={"name": "Test Player"}) as fetch:
            with urlopen(self.origin + "/api/profile?platform=epic&gamertag=Test%20Player") as response:
                self.assertEqual(json.load(response)["profile"]["name"], "Test Player")
            fetch.assert_called_once_with("epic", "Test Player", "")

    def test_source_files_and_traversal_are_not_served(self):
        for name in ["desktop_app.py", "tracker_proxy.py", ".git/config", "../tracker_proxy.py", "%2e%2e%2ftracker_proxy.py", "overwolf/background.js"]:
            with self.assertRaises(HTTPError) as result:
                urlopen(self.origin + "/" + name)
            self.assertEqual(result.exception.code, 404)

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
            for query in ["platform=invalid&gamertag=Player", "platform=epic"]:
                with self.assertRaises(HTTPError) as result:
                    urlopen(self.origin + "/api/profile?" + query)
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
                urlopen(self.origin + "/api/profile?platform=epic&gamertag=Twisted_p")
            payload = json.load(failure.exception)
            self.assertEqual(failure.exception.code, 503)
            self.assertEqual(payload["code"], "tracker_access_denied")
            self.assertTrue(payload["profileUrl"].endswith("/epic/Twisted_p/overview"))
            self.assertNotIn("403 Client Error", payload["error"])

    def test_tracker_rate_limit_is_distinct_from_access_denial(self):
        response = Response()
        response.status_code = 429
        with self.assertRaises(TrackerUnavailableError) as result:
            check_tracker_response(response)
        self.assertEqual(result.exception.code, "tracker_rate_limited")


if __name__ == "__main__":
    unittest.main()
