import json
from pathlib import Path
import tempfile
import unittest
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from desktop_app import start_server
from goals_service import GoalsService, TARGETS, estimate
from overlay_service import OverlayService


class GoalsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name)
        self.overlay = OverlayService(self.path, None)
        self.profile('a', 900)
        self.goals = GoalsService(self.path, self.overlay)

    def profile(self, account, mmr):
        self.overlay.set_profile({'name': 'Test Player', 'playerId': account, 'ranks': [
            {'playlist': mode, 'mmr': mmr, 'rank': 'Diamond I'} for mode in TARGETS]})

    def tearDown(self):
        self.temp.cleanup()

    def test_ceiling_boundary_missing_and_reached(self):
        self.assertEqual(estimate(1000, 1075)['wins'], 9)
        self.assertEqual(estimate(1066, 1075)['wins'], 1)
        self.assertEqual(estimate(1065, 1075)['wins'], 2)
        self.assertEqual(estimate(1075, 1075), {'remaining': 0, 'wins': 0, 'reached': True})
        self.assertEqual(estimate(1080, 1075)['remaining'], 0)
        self.assertIsNone(estimate(None, 1075)['wins'])
        self.assertIsNone(estimate(True, 1075)['wins'])
        self.assertIsNone(estimate(float('nan'), 1075)['wins'])

    def test_per_mode_targets_fresh_mmr_and_persistence(self):
        for mode in TARGETS:
            self.goals.set_goal({'playlist': mode, 'tier': 16})  # Champion I
        rows = self.goals.view()['goals']
        self.assertEqual([r['targetMmr'] for r in rows], [995, 1075, 1075])
        self.assertEqual([r['wins'] for r in rows], [11, 20, 20])
        self.profile('a', 1000)
        self.assertEqual([r['wins'] for r in self.goals.view()['goals']], [0, 9, 9])
        restarted = GoalsService(self.path, self.overlay)
        self.assertEqual(restarted.view()['goals'], self.goals.view()['goals'])
        self.assertEqual(len(restarted.view()['catalog']), 22)

    def test_accounts_independent_and_draft_assigned_once(self):
        self.goals.set_goal({'playlist': '2v2', 'tier': 16})
        self.profile('b', 1200)
        self.assertIsNone(self.goals.view()['goals'][1]['tier'])
        self.goals.set_goal({'playlist': '2v2', 'tier': 19})
        self.profile('a', 900)
        self.assertEqual(self.goals.view()['goals'][1]['tier'], 16)
        self.overlay.profile = None
        self.goals.set_goal({'playlist': '1v1', 'tier': 22})
        self.profile('c', 1300)
        self.assertEqual(self.goals.view()['goals'][0]['tier'], 22)
        self.profile('d', 1300)
        self.assertIsNone(self.goals.view()['goals'][0]['tier'])

    def test_validation_clear_and_corrupted_storage(self):
        for payload in ({'playlist': '4v4', 'tier': 16}, {'playlist': '1v1', 'tier': True},
                        {'playlist': '1v1', 'tier': 23}, {'playlist': '1v1', 'tier': '16'}, []):
            with self.assertRaises(ValueError):
                self.goals.set_goal(payload)
        self.goals.set_goal({'playlist': '2v2', 'tier': 16})
        self.goals.set_goal({'playlist': '2v2', 'tier': None})
        self.assertIsNone(self.goals.view()['goals'][1]['targetMmr'])
        self.goals.file.write_text('broken', encoding='utf-8')
        self.assertEqual(GoalsService(self.path, self.overlay).accounts, {})

    def test_api_origin_and_invalid_goal(self):
        server = start_server(0, overlay=self.overlay, goals=self.goals)
        origin = f'http://127.0.0.1:{server.server_port}'
        try:
            with self.assertRaises(HTTPError) as raised:
                urlopen(Request(origin + '/api/goals', data=b'{}', method='POST'))
            self.assertEqual(raised.exception.code, 403)
            request = Request(origin + '/api/goals', data=json.dumps({'playlist':'2v2','tier':16}).encode(),
                              headers={'Origin':origin, 'Content-Type':'application/json'})
            with urlopen(request) as response:
                self.assertEqual(json.load(response)['goals'][1]['wins'], 20)
        finally:
            server.shutdown()
            server.server_close()
