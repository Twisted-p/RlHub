from copy import deepcopy
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock

from game_window import GameWindowController
from performance_service import PerformanceService
from test_performance import STATE, END


class LoadedEvent(list):
    def __iadd__(self, handler):
        self.append(handler)
        return self


class GameWindowTests(unittest.TestCase):
    def setUp(self):
        self.storage = tempfile.TemporaryDirectory()
        self.addCleanup(self.storage.cleanup)
        self.performance = PerformanceService(Path(self.storage.name), root=Path(self.storage.name))
        self.performance.connected = True
        self.window = Mock()
        self.window.events = SimpleNamespace(loaded=LoadedEvent())
        self.now = 0
        self.controller = GameWindowController(self.window, self.performance, clock=lambda:self.now)
        self.controller.loaded()

    def test_training_results_and_lobby_transition(self):
        training = deepcopy(STATE)
        training['Data']['Players'] = training['Data']['Players'][:1]
        training['Data']['Game']['Teams'] = []
        self.performance.ingest(training)
        self.controller.tick()
        self.assertEqual(self.performance.activity_snapshot()['phase'], 'training')
        self.window.minimize.assert_called_once()
        self.assertTrue(self.controller.busy)
        self.performance.ingest({'Event':'MatchCreated','Data':{}})
        self.performance.ingest(STATE)
        self.performance.ingest(END)
        self.controller.tick()
        self.assertEqual(self.performance.activity_snapshot()['phase'], 'post-match')
        self.window.restore.assert_not_called()
        self.performance.ingest({'Event':'MatchDestroyed','Data':{}})
        self.controller.tick()
        self.window.restore.assert_not_called()
        self.now = 2
        self.controller.tick()
        self.window.restore.assert_called_once()
        self.assertFalse(self.controller.busy)
        self.controller.tick()
        self.window.restore.assert_called_once()

    def test_connection_loss_does_not_fake_lobby_or_restore(self):
        self.performance.ingest(STATE)
        self.controller.tick()
        self.performance.connected = False
        self.performance.activity = 'unknown'
        self.now = 30
        self.controller.tick()
        self.assertTrue(self.controller.busy)
        self.window.restore.assert_not_called()

    def test_navigation_preserves_pause_and_quick_queue_does_not_restore(self):
        self.performance.ingest(STATE)
        self.controller.tick()
        self.controller.loaded()
        self.controller.tick()
        self.assertIn('(true)', self.window.evaluate_js.call_args.args[0])
        self.window.minimize.assert_called_once()
        self.performance.ingest({'Event':'MatchDestroyed','Data':{}})
        self.controller.tick()
        self.now = .5
        self.performance.ingest({'Event':'MatchCreated','Data':{}})
        self.controller.tick()
        self.now = 2
        self.controller.tick()
        self.window.restore.assert_not_called()

    def test_startup_unknown_state_does_not_minimize(self):
        self.controller.tick()
        self.window.minimize.assert_not_called()
        self.window.restore.assert_not_called()
