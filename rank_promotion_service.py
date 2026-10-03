"""First observed rank-family milestones; independent of session and UI lifetime."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import logging
from pathlib import Path
from threading import RLock
from uuid import uuid4

from mmr_provider import TIERS
from progression_service import account_key, stamp

FAMILIES = ("Unranked", "Bronze", "Silver", "Gold", "Platinum", "Diamond",
            "Champion", "Grand Champion", "Supersonic Legend")
COLORS = ("#94a3b8", "#cd9161", "#c7d4e8", "#ffd366", "#62d6e8",
          "#559dff", "#b58aff", "#ff657e", "#edf2ff")
MODES = {10: "1v1", 11: "2v2", 13: "3v3"}


def rank_info(label):
    tier = str(label).split(" Division ")[0].strip()
    if tier not in TIERS:
        return None
    icon = TIERS.index(tier)
    family = 0 if icon == 0 else 8 if icon == 22 else (icon - 1) // 3 + 1
    return {"family": family, "name": FAMILIES[family], "color": COLORS[family], "icon": icon}


class RankPromotionService:
    def __init__(self, data_dir, history):
        self.file = Path(data_dir) / "rank-promotions.json"
        self.lock = RLock()
        self.accounts = {}
        try:
            saved = json.loads(self.file.read_text(encoding="utf-8"))
            for key, modes in saved.items():
                if not isinstance(modes, dict):
                    continue
                valid = {}
                for mode, state in modes.items():
                    if mode in MODES.values() and isinstance(state, dict) and type(state.get("highest")) is int and 0 <= state["highest"] <= 8 and stamp(state.get("at")):
                        valid[mode] = state
                self.accounts[key] = valid
        except (OSError, ValueError, TypeError, AttributeError):
            pass
        # Existing observations establish a baseline when upgrading the app.
        with history.lock:
            for key, modes in history.accounts.items():
                states = self.accounts.setdefault(key, {})
                for mode, rows in modes.items():
                    known = [(row, rank_info(row.get("rank"))) for row in rows]
                    known = [(row, info) for row, info in known if info and info["family"] > 0]
                    if known and mode not in states:
                        states[mode] = {"highest": max(info["family"] for _, info in known),
                                        "at": max(stamp(row["at"]) for row, _ in known).isoformat(), "pending": None}

    def _save(self):
        try:
            self.file.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.file.with_suffix(".tmp")
            temporary.write_text(json.dumps(self.accounts, ensure_ascii=False), encoding="utf-8")
            temporary.replace(self.file)
        except OSError:
            logging.exception("Could not save rank milestones")

    def observe(self, profile, matches=()):
        key = account_key(profile)
        at = stamp((profile or {}).get("fetchedAt"))
        if not key or not at or at > datetime.now(timezone.utc) + timedelta(minutes=5):
            return
        with self.lock:
            states = self.accounts.setdefault(key, {})
            changed = False
            for row in profile.get("ranks", []):
                mode, info = row.get("playlist"), rank_info(row.get("rank"))
                if mode not in MODES.values() or not info or info["family"] == 0:
                    continue
                previous = states.get(mode)
                if previous and at <= stamp(previous["at"]):
                    continue
                state = previous or {"highest": info["family"], "pending": None}
                if previous and info["family"] > previous["highest"]:
                    recent = []
                    for match in sorted(matches, key=lambda m: m.get("endedAt", ""), reverse=True):
                        ended = stamp(match.get("endedAt"))
                        me = next((p for p in match.get("players", []) if p.get("playerId") == profile["playerId"]), None)
                        if MODES.get(match.get("playlist")) == mode and ended and timedelta(0) <= at-ended <= timedelta(hours=24) and me and me.get("team") in (0, 1) and match.get("winnerTeam") in (0, 1):
                            recent.append(me["team"] == match["winnerTeam"])
                    state["pending"] = {"id": str(uuid4()), "name": profile.get("name", ""),
                        "playlist": mode, "rank": row["rank"], "family": info["name"],
                        "previousFamily": FAMILIES[previous["highest"]], "color": info["color"],
                        "icon": info["icon"], "mmr": row["mmr"], "observedAt": at.isoformat(),
                        "stats": {"matches24h": len(recent), "wins24h": sum(recent), "losses24h": len(recent)-sum(recent)}}
                    state["highest"] = info["family"]
                state["at"] = at.isoformat()
                states[mode] = state
                changed = True
            if changed:
                self._save()

    def pending(self, profile):
        with self.lock:
            return deepcopy([state["pending"] for state in self.accounts.get(account_key(profile), {}).values() if state.get("pending")])

    def acknowledge(self, profile, event_id):
        with self.lock:
            for state in self.accounts.get(account_key(profile), {}).values():
                if (state.get("pending") or {}).get("id") == event_id:
                    state["pending"] = None
                    self._save()
                    return True
            return False
