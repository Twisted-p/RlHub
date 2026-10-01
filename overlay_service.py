"""Standalone overlay state; rendering and game focus are handled by Windows."""
from copy import deepcopy
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from threading import RLock, Thread
import time

from mmr_provider import fetch_rank_profile

RANKED = {10: "1v1", 11: "2v2", 13: "3v3"}
DEFAULTS = {"enabled": True, "showInMatch": False, "position": "top-left", "scale": 100, "playlist": "2v2"}


def own_player(players, identity):
    if not identity:
        return None
    if identity.get("playerId"):
        return next((p for p in players if p.get("playerId") == identity["playerId"]), None)
    name = str(identity.get("name", "")).casefold()
    return next((p for p in players if name and str(p.get("name", "")).casefold() == name), None)


class OverlayService:
    def __init__(self, data_dir, performance):
        self.file = Path(data_dir) / "overlay.json"
        self.performance = performance
        self.lock = RLock()
        self.settings = dict(DEFAULTS)
        self.profile = None
        self.lookup = None
        self.bases = {}
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.preview_until = 0
        self.training_since = None
        self.last_training = 0
        self.last_seen_end = None
        self.refresh_at = 0
        self.refreshing = False
        self.refresh_status = "idle"
        self.native_ready = False
        self.native_error = ""
        self.hotkey = False
        self.visible = False
        try:
            saved = json.loads(self.file.read_text(encoding="utf-8"))
            self.configure(saved.get("settings", {}), persist=False)
            self.set_profile(saved.get("profile"), saved.get("lookup"), persist=False)
            started = saved.get("startedAt")
            if started and datetime.fromisoformat(started).tzinfo:
                self.started_at = started
            bases = saved.get("bases", {})
            if isinstance(bases, dict):
                self.bases.update({k: int(v) for k, v in bases.items() if k in ("1v1", "2v2", "3v3") and type(v) in (int, float) and 0 <= v <= 10000})
        except (OSError, ValueError, TypeError):
            pass

    def _save(self):
        try:
            self.file.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.file.with_suffix(".tmp")
            temporary.write_text(json.dumps({"settings": self.settings, "profile": self.profile, "lookup": self.lookup, "startedAt": self.started_at, "bases": self.bases}, ensure_ascii=False), encoding="utf-8")
            temporary.replace(self.file)
        except OSError:
            logging.exception("Could not save overlay settings")

    def configure(self, changes, persist=True):
        if not isinstance(changes, dict):
            raise ValueError("Ugyldige overlay-innstillinger.")
        with self.lock:
            settings = dict(self.settings)
            for key in ("enabled", "showInMatch"):
                if key in changes:
                    if not isinstance(changes[key], bool):
                        raise ValueError("Ugyldig bryter.")
                    settings[key] = changes[key]
            if "position" in changes:
                if changes["position"] not in ("top-left", "top-right", "bottom-left", "bottom-right"):
                    raise ValueError("Ugyldig plassering.")
                settings["position"] = changes["position"]
            if "scale" in changes:
                if type(changes["scale"]) is not int or not 75 <= changes["scale"] <= 125:
                    raise ValueError("Størrelse må være mellom 75 og 125 prosent.")
                settings["scale"] = changes["scale"]
            if "playlist" in changes:
                if changes["playlist"] not in ("1v1", "2v2", "3v3"):
                    raise ValueError("Ugyldig spilleliste.")
                settings["playlist"] = changes["playlist"]
            self.settings = settings
            if not settings["enabled"]:
                self.preview_until = 0
            if persist:
                self._save()
            return dict(settings)

    def set_profile(self, profile, lookup=None, persist=True):
        if profile is None:
            return
        if not isinstance(profile, dict) or not isinstance(profile.get("ranks"), list):
            raise ValueError("Ugyldig rank-profil.")
        ranks = []
        for row in profile["ranks"][:3]:
            if not isinstance(row, dict) or row.get("playlist") not in ("1v1", "2v2", "3v3"):
                continue
            if type(row.get("mmr")) not in (int, float) or not 0 <= row["mmr"] <= 10000:
                continue
            next_rank = row.get("nextRank") if isinstance(row.get("nextRank"), dict) else {}
            next_label = next_rank.get("label", "") if next_rank else row.get("nextRank", "") if isinstance(row.get("nextRank"), str) else ""
            ranks.append({"playlist": row["playlist"], "mmr": int(row["mmr"]), "rank": str(row.get("rank", ""))[:80],
                          "nextRank": str(next_label)[:80]})
        if not ranks:
            return
        value = {"playerId": str(profile.get("playerId", ""))[:160], "name": str(profile.get("name", ""))[:80],
                 "ranks": ranks, "fetchedAt": str(profile.get("fetchedAt", ""))[:50]}
        with self.lock:
            if self.profile and self.profile["playerId"] == value["playerId"] and self.profile["fetchedAt"] > value["fetchedAt"]:
                return
            if self.profile and self.profile["playerId"] != value["playerId"]:
                self.bases = {}
                self.started_at = datetime.now(timezone.utc).isoformat()
            for row in ranks:
                self.bases.setdefault(row["playlist"], row["mmr"])
            self.profile = value
            if isinstance(lookup, dict) and lookup.get("platform") in ("epic", "steam", "psn", "xbl"):
                self.lookup = {"platform": lookup["platform"], "gamertag": str(lookup.get("gamertag", ""))[:160], "playerId": value["playerId"]}
            if persist:
                self._save()

    def preview(self):
        with self.lock:
            self.preview_until = time.monotonic() + 20

    def reset_session(self):
        with self.lock:
            self.started_at = datetime.now(timezone.utc).isoformat()
            self.bases = {r["playlist"]: r["mmr"] for r in (self.profile or {}).get("ranks", [])}
            self._save()

    def _refresh(self):
        with self.lock:
            lookup = deepcopy(self.lookup)
            account = (self.profile or {}).get("playerId")
        try:
            if lookup:
                profile = fetch_rank_profile(**lookup)
                with self.lock:
                    if (self.profile or {}).get("playerId") == account:
                        self.set_profile(profile, lookup)
                        self.refresh_status = "updated"
        except Exception:
            with self.lock:
                self.refresh_status = "unavailable"
        finally:
            with self.lock:
                self.refreshing = False

    def view(self, snapshot=None, now=None):
        snapshot = snapshot if snapshot is not None else self.performance.snapshot()
        now = time.monotonic() if now is None else now
        with self.lock:
            live = snapshot.get("live")
            if snapshot.get("liveAge") is None or snapshot.get("liveAge", 99) > 5:
                live = None
            identity = self.profile or snapshot.get("localPlayer")
            matches = [m for m in snapshot.get("matches", []) if m.get("endedAt", "") >= self.started_at and (own_player(m.get("players", []), identity) or {}).get("team") in (0, 1)]
            latest = matches[0] if matches else None
            if latest and latest["id"] != self.last_seen_end:
                self.last_seen_end = latest["id"]
                try:
                    ended_age = (datetime.now(timezone.utc) - datetime.fromisoformat(latest["endedAt"])).total_seconds()
                except (ValueError, TypeError):
                    ended_age = 999
                if 0 <= ended_age < 35 and latest.get("playlist") in RANKED and self.lookup:
                    self.refresh_at = now + 8
            if self.refresh_at and now >= self.refresh_at and not self.refreshing:
                self.refresh_at = 0
                self.refreshing = True
                self.refresh_status = "updating"
                Thread(target=self._refresh, name="rl-hub-overlay-rank", daemon=True).start()
            playlist = RANKED.get((live or {}).get("playlist"), self.settings["playlist"])
            if latest and not live:
                playlist = RANKED.get(latest.get("playlist"), playlist)
            row = next((r for r in (self.profile or {}).get("ranks", []) if r["playlist"] == playlist), None)
            base = self.bases.get(playlist)
            ranked = [m for m in matches if RANKED.get(m.get("playlist")) == playlist]
            results = [own_player(m["players"], identity).get("team") == m.get("winnerTeam") for m in ranked]
            streak = 0
            for result in results:
                if result != results[0]:
                    break
                streak += 1
            phase = "lobby"
            if snapshot.get("replay"):
                phase = "hidden"
            elif snapshot.get("activeMatch"):
                phase = "match" if self.settings["showInMatch"] else "hidden"
            elif live and live.get("training"):
                phase = "training"
            elif latest:
                try:
                    age = (datetime.now(timezone.utc) - datetime.fromisoformat(latest["endedAt"])).total_seconds()
                    if 0 <= age < 35:
                        phase = "post-match"
                except (ValueError, TypeError):
                    pass
            if phase == "training":
                if self.training_since is None:
                    self.training_since = now
                self.last_training = now
            elif snapshot.get("activeMatch") or snapshot.get("replay") or not snapshot.get("connected") or now - self.last_training > 3:
                self.training_since = None
            match = latest if phase == "post-match" else live
            me = own_player((match or {}).get("players", []), identity)
            return {"settings": dict(self.settings), "phase": phase, "preview": now < self.preview_until,
                    "nativeReady": self.native_ready, "nativeError": self.native_error,
                    "hotkey": self.hotkey, "visible": self.visible, "connected": snapshot.get("connected", False),
                    "name": (identity or {}).get("name", "Koble spiller i Profile"), "playlist": playlist,
                    "rank": row["rank"] if row else "Ingen rank hentet", "mmr": row["mmr"] if row else None,
                    "nextRank": row.get("nextRank", "") if row else "",
                    "startMmr": base, "delta": row["mmr"] - base if row and base is not None else None,
                    "wins": sum(results), "losses": len(results) - sum(results),
                    "streak": f"{streak}{'W' if results[0] else 'L'}" if results else "Ny økt",
                    "player": me, "teams": (match or {}).get("teams", []),
                    "result": ("Seier" if me and me.get("team") == match.get("winnerTeam") else "Tap" if me else "Kamp ferdig") if phase == "post-match" else None,
                    "trainingSeconds": int(now - self.training_since) if self.training_since is not None else 0,
                    "rankStatus": self.refresh_status}
