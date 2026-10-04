"""Pause decorative UI and minimize only on authoritative game transitions."""
import json
import logging
import time
from threading import Event, Thread


class GameWindowController:
    def __init__(self, window, performance, clock=time.monotonic):
        self.window = window
        self.performance = performance
        self.busy = False
        self.auto_minimized = False
        self.page_dirty = Event()
        self.ready = Event()
        self.stopped = Event()
        self.thread = None
        self.clock = clock
        self.lobby_since = None
        window.events.loaded += self.loaded

    def loaded(self):
        self.ready.set()
        self.page_dirty.set()

    def start(self):
        self.thread = Thread(target=self.run, name="rl-hub-game-window", daemon=True)
        self.thread.start()

    def stop(self):
        self.stopped.set()
        if self.thread:
            self.thread.join(timeout=2)

    def tick(self):
        if not self.ready.is_set():
            return
        state = self.performance.activity_snapshot()
        target = self.busy
        if state["connected"]:
            if state["phase"] in ("training", "match", "post-match", "replay"):
                target = True
                self.lobby_since = None
            elif state["phase"] == "lobby":
                if self.lobby_since is None:
                    self.lobby_since = self.clock()
                if self.clock() - self.lobby_since >= 1.5:
                    target = False
            else:
                self.lobby_since = None
        else:
            self.lobby_since = None
        changed = target != self.busy
        self.busy = target
        if changed or self.page_dirty.is_set():
            self.page_dirty.clear()
            self.window.evaluate_js(
                "window.RL_HUB_SET_GAME_ACTIVITY && window.RL_HUB_SET_GAME_ACTIVITY(" + json.dumps(self.busy) + ")")
        if self.busy and not self.auto_minimized:
            self.window.minimize()
            self.auto_minimized = True
        elif not self.busy and self.auto_minimized:
            self.window.restore()
            self.auto_minimized = False

    def run(self):
        while not self.stopped.wait(.5):
            try:
                self.tick()
            except Exception:
                self.page_dirty.set()
                logging.exception("Could not update RL Hub game window")
