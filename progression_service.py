"""Persist actual rank observations, independently of session resets."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import hashlib
import json
import logging
from pathlib import Path
from threading import RLock

from goals_service import TARGETS
from mmr_provider import TIERS


def stamp(value):
    try:
        result = datetime.fromisoformat(value)
        return result.astimezone(timezone.utc) if result.tzinfo else None
    except (TypeError, ValueError):
        return None


def account_key(profile):
    identity = (profile or {}).get("playerId")
    return hashlib.sha256(identity.encode()).hexdigest() if isinstance(identity, str) and identity else None


class ProgressionService:
    def __init__(self, data_dir):
        self.file = Path(data_dir) / "rank-history.json"
        self.lock = RLock()
        self.accounts = {}
        try:
            data = json.loads(self.file.read_text(encoding="utf-8"))
            for key, modes in data.items():
                if not isinstance(modes, dict):
                    continue
                self.accounts[key] = {}
                for mode, rows in modes.items():
                    if mode in TARGETS and isinstance(rows, list):
                        valid = [r for r in rows if isinstance(r, dict) and stamp(r.get("at")) and type(r.get("mmr")) is int and 0 <= r["mmr"] <= 10000 and isinstance(r.get("rank"), str)]
                        self.accounts[key][mode] = sorted(valid, key=lambda r: stamp(r["at"]))[-10000:]
        except (OSError, ValueError, TypeError, AttributeError):
            pass

    def record(self, profile):
        key = account_key(profile)
        at = stamp((profile or {}).get("fetchedAt"))
        if not key or not at or at > datetime.now(timezone.utc) + timedelta(minutes=5):
            return
        with self.lock:
            modes = self.accounts.setdefault(key, {})
            changed = False
            for row in profile.get("ranks", []):
                mode = row.get("playlist")
                if mode not in TARGETS or type(row.get("mmr")) is not int or not 0 <= row["mmr"] <= 10000:
                    continue
                rows = modes.setdefault(mode, [])
                normalized = at.isoformat()
                if any(r["at"] == normalized for r in rows):
                    continue
                rows.append({"at": normalized, "mmr": row["mmr"], "rank": str(row.get("rank", ""))[:80]})
                rows.sort(key=lambda r: stamp(r["at"]))
                del rows[:-10000]
                changed = True
            if changed:
                try:
                    self.file.parent.mkdir(parents=True, exist_ok=True)
                    temporary = self.file.with_suffix(".tmp")
                    temporary.write_text(json.dumps(self.accounts), encoding="utf-8")
                    temporary.replace(self.file)
                except OSError:
                    logging.exception("Could not save rank history")

    def view(self, profile, mode="2v2", days=90, matches=None, now=None):
        now = now or datetime.now(timezone.utc)
        with self.lock:
            all_points = deepcopy(self.accounts.get(account_key(profile), {}).get(mode, []))
        cutoff = now - timedelta(days=days) if days else None
        points = [r for r in all_points if not cutoff or stamp(r["at"]) >= cutoff]
        current = next((r for r in (profile or {}).get("ranks", []) if r["playlist"] == mode), None)
        recent = []
        for match in sorted(matches or [], key=lambda m: m.get("endedAt", ""), reverse=True):
            if {10:"1v1",11:"2v2",13:"3v3"}.get(match.get("playlist")) != mode:
                continue
            me = next((p for p in match.get("players", []) if profile and p.get("playerId") == profile.get("playerId") and profile.get("playerId")), None)
            if me and me.get("team") in (0,1) and match.get("winnerTeam") in (0,1):
                recent.append({"at":match.get("endedAt"), "win":me["team"] == match["winnerTeam"]})
        recent = recent[:5]
        week = [r for r in all_points if stamp(r["at"]) >= now-timedelta(days=7)]
        return {"playlist":mode, "days":days, "name":(profile or {}).get("name", ""),
            "weekDelta":week[-1]["mmr"]-week[0]["mmr"] if len(week)>1 else None,
            "current":deepcopy(current), "points":points, "firstObserved":all_points[0]["at"] if all_points else None,
            "delta":points[-1]["mmr"]-points[0]["mmr"] if len(points)>1 else None,
            "recent":recent, "wins":sum(r["win"] for r in recent),
            "bands":[{"rank":TIERS[i+1], "low":low, "high":TARGETS[mode][i+1] if i+1<len(TARGETS[mode]) else 10000} for i,low in enumerate(TARGETS[mode])],
            "boundsApproximate":True}
