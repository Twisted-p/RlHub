"""Persistent local coaching session driven by Stats API, never by UI timers."""
from copy import deepcopy
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from threading import Event, RLock, Thread
import time

from overlay_service import own_player, RANKED

FOCUS_SECONDS = 90 * 60
PLAYLISTS = {1, 2, 3, 4, 10, 11, 13, 27, 28, 29, 30}


def timestamp(value):
    try:
        parsed = datetime.fromisoformat(value)
        return parsed.timestamp() if parsed.tzinfo else 0
    except (ValueError, TypeError):
        return 0


class ReadinessService:
    def __init__(self, data_dir, performance, overlay, clock=time.monotonic, wall=lambda: datetime.now(timezone.utc)):
        self.file = Path(data_dir) / "readiness.json"
        self.performance, self.overlay = performance, overlay
        self.clock, self.wall = clock, wall
        self.lock, self.stop_event = RLock(), Event()
        self.thread = None
        self.previous = None
        self.last_save = 0
        self.state = self._empty()
        try:
            saved = json.loads(self.file.read_text(encoding="utf-8"))
            if saved.get("version") == 1 and saved.get("day") == self._day():
                # Saved monotonic timestamps are deliberately never reused.
                for key in self.state:
                    if key in saved and type(saved[key]) is type(self.state[key]):
                        self.state[key] = saved[key]
        except (OSError, ValueError, TypeError):
            pass

    def _day(self):
        return self.wall().astimezone().date().isoformat()

    def _empty(self):
        return dict(version=1, day=self._day(), startedAt="", identity="", trainingSeconds=0.0,
                    focusSeconds=0.0, matches=[], knownIds=[], bases={}, processed=0,
                    advice={}, resting=False, restSeconds=0.0, warmupSeconds=0.0)

    def _save(self):
        try:
            self.file.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.file.with_suffix(".tmp")
            temporary.write_text(json.dumps(self.state, ensure_ascii=False), encoding="utf-8")
            temporary.replace(self.file)
        except OSError:
            logging.exception("Could not save coaching session")

    def reset(self):
        with self.lock:
            self.state = self._empty()
            self.previous = None
            self.overlay.reset_session()
            self._save()

    def start_break(self):
        with self.lock:
            self.tick()
            if not self.state["startedAt"]:
                raise ValueError("Start trening eller en kamp først.")
            if not self.state["advice"]:
                self.state["advice"] = {"kind": "manual", "rest": 900, "warmup": 0, "bracket": 0}
            if self.state["advice"].get("stage", "rest") != "warmup":
                self.state["resting"] = True
            self._save()

    def start(self):
        self.thread = Thread(target=self._run, name="rl-hub-readiness", daemon=True)
        self.thread.start()

    def _run(self):
        while not self.stop_event.wait(1):
            try:
                self.tick()
            except Exception:
                logging.exception("Coaching session update failed")

    def stop(self):
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=3)
        with self.lock:
            self._save()

    def tick(self, snapshot=None):
        snapshot = snapshot if snapshot is not None else self.performance.snapshot()
        now = self.clock()
        with self.lock:
            with self.overlay.lock:
                profile = deepcopy(self.overlay.profile or {})
                playlist = self.overlay.settings["playlist"]
                rank_status = self.overlay.refresh_status
            identity = snapshot.get("localPlayer") or profile
            identity_key = str(identity.get("playerId") or identity.get("name", "")).casefold()
            s = self.state
            if s["day"] != self._day() or (identity_key and s["identity"] and identity_key != s["identity"]):
                self.state = s = self._empty()
                self.previous = None
            live = snapshot.get("live") or {}
            fresh = snapshot.get("connected") and snapshot.get("liveAge") is not None and snapshot["liveAge"] <= 5 and not snapshot.get("replay")
            training = bool(fresh and live.get("training") and not snapshot.get("activeMatch"))
            playing = bool(fresh and (training or snapshot.get("activeMatch")))
            busy = bool(snapshot.get("activeMatch") or snapshot.get("replay") or live.get("training"))
            if not s["startedAt"] and playing and identity_key:
                s["startedAt"] = self.wall().isoformat()
                s["identity"] = identity_key
                s["knownIds"] = [m.get("id") for m in snapshot.get("matches", [])]
                self.overlay.reset_session()
            if s["startedAt"]:
                # Only rank data for the actual player can influence coaching.
                if str(profile.get("playerId") or profile.get("name", "")).casefold() == s["identity"]:
                    for row in profile.get("ranks", []):
                        s["bases"].setdefault(row["playlist"], row["mmr"])
                # Bound gaps: suspended/closed apps and stale feeds never add training/rest time.
                elapsed = now - self.previous["at"] if self.previous else 0
                dt = elapsed if 0 <= elapsed <= 3 else 0
                prev = self.previous or {}
                if training and prev.get("training"):
                    s["trainingSeconds"] += dt
                advice = s["advice"]
                if s["resting"]:
                    if playing or busy:
                        s["restSeconds"] = 0.0
                    elif prev.get("idle"):
                        s["restSeconds"] += dt
                    if s["restSeconds"] >= advice.get("rest", 900):
                        s["resting"] = False
                        if advice.get("warmup"):
                            advice["stage"] = "warmup"
                        else:
                            s["advice"] = {}
                elif advice.get("stage") == "warmup":
                    if training and prev.get("training"):
                        s["warmupSeconds"] += dt
                    if s["warmupSeconds"] >= advice["warmup"]:
                        s["advice"] = {}
                if (not s["resting"] or playing or busy) and prev.get("connected") and snapshot.get("connected"):
                    s["focusSeconds"] += dt
                known = set(s["knownIds"])
                new = sorted(snapshot.get("matches", []), key=lambda m: timestamp(m.get("endedAt")))
                for match in new:
                    if match.get("id") in known or timestamp(match.get("endedAt")) < timestamp(s["startedAt"]):
                        continue
                    me = own_player(match.get("players", []), identity)
                    if match.get("playlist") not in PLAYLISTS or not me or me.get("team") not in (0, 1) or match.get("winnerTeam") not in (0, 1):
                        continue
                    s["knownIds"].append(match["id"])
                    known.add(match["id"])
                    s["matches"].append({"id": match["id"], "win": me["team"] == match["winnerTeam"],
                                         "playlist": match["playlist"], "endedAt": match["endedAt"],
                                         "partial": bool(match.get("partial")),
                                         "stats": {k: me.get(k) for k in ("goals", "shots", "saves", "assists", "score")}})
                completed = len(s["matches"]) // 5
                if completed > s["processed"]:
                    block = s["matches"][(completed - 1) * 5:completed * 5]
                    wins = sum(m["win"] for m in block)
                    s["advice"] = {"kind": "loss" if wins < 3 else "win", "rest": 900 if wins < 3 else 300,
                                   "warmup": 0 if wins < 3 else 300, "bracket": completed, "wins": wins}
                    s["processed"] = completed
                    s["resting"] = False
                    s["restSeconds"] = s["warmupSeconds"] = 0.0
                    self._save()
            self.previous = {"at": now, "training": training, "connected": bool(snapshot.get("connected")),
                             "idle": not playing and not busy}
            if now - self.last_save >= 10:
                self._save()
                self.last_save = now
            playlist = RANKED.get(live.get("playlist"), next((RANKED[m["playlist"]] for m in reversed(s["matches"]) if m["playlist"] in RANKED), playlist))
            return self._view(profile, playlist, rank_status, training, playing, snapshot)

    def _view(self, profile, playlist, rank_status, training, playing, snapshot):
        s = self.state
        recent = s["matches"][-5:]
        wins = sum(m["win"] for m in recent)
        averages = {}
        for key in ("goals", "shots", "saves", "assists", "score"):
            values = [m["stats"][key] for m in recent if type(m["stats"].get(key)) in (int, float) and m["stats"][key] >= 0]
            averages[key] = round(sum(values) / len(values), 1) if values else None
        mmr = []
        same_account = str(profile.get("playerId") or profile.get("name", "")).casefold() == s["identity"]
        for row in profile.get("ranks", []) if same_account else []:
            base = s["bases"].get(row["playlist"])
            mmr.append({"playlist": row["playlist"], "current": row["mmr"], "start": base,
                        "delta": row["mmr"] - base if base is not None else None})
        selected = next((r for r in mmr if r["playlist"] == playlist), None)
        delta = selected["delta"] if selected else None
        form = (wins / len(recent) - .5) * 40 if recent else 0
        contribution = min(10, sum(averages[k] or 0 for k in ("goals", "saves", "assists")) * 2)
        fatigue = min(45, s["focusSeconds"] / FOCUS_SECONDS * 35)
        components = {"base": 50, "training": round(min(20, s["trainingSeconds"] / 600 * 20)),
                      "results": round(form), "performance": round(contribution),
                      "mmr": round(max(-10, min(10, (delta or 0) / 3))), "fatigue": round(fatigue)}
        score = round(max(0, min(100, sum(v for k, v in components.items() if k != "fatigue") - fatigue))) if s["startedAt"] else None
        return {"startedAt": s["startedAt"], "trainingSeconds": int(s["trainingSeconds"]),
                "focusSeconds": int(s["focusSeconds"]), "focusRemaining": max(0, FOCUS_SECONDS - int(s["focusSeconds"])),
                "focusLimit": FOCUS_SECONDS, "readiness": score, "components": components,
                "recent": deepcopy(recent), "wins": wins, "losses": len(recent) - wins, "averages": averages,
                "matchCount": len(s["matches"]), "bracketProgress": len(s["matches"]) % 5,
                "advice": deepcopy(s["advice"]), "resting": s["resting"],
                "restSeconds": int(s["restSeconds"]), "warmupSeconds": int(s["warmupSeconds"]),
                "mmr": mmr, "playlist": playlist, "rankStatus": rank_status,
                "training": training, "playing": playing, "connected": bool(snapshot.get("connected"))}
