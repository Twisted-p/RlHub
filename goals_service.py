"""Saved per-player ranked goals and transparent +9 MMR win estimates."""
from copy import deepcopy
import json
import logging
import math
from pathlib import Path
from threading import RLock

from mmr_provider import TIERS

# Approximate, rounded promotion targets, NOT the lower edge of a retention range.
# References checked 2026-10-01:
# https://earlygame.com/rocket-league/mmr-guide-match-making-rank
# https://rocketleague.tracker.network/rocket-league/distribution?playlist=10
# Rank boundaries can change; no live TRN request is needed by the app.
TARGETS = {
    "1v1": [0,155,215,275,335,395,455,515,575,635,695,755,815,875,935,995,1055,1115,1175,1235,1295,1355],
    "2v2": [0,175,235,295,355,415,475,535,595,655,715,775,835,915,995,1075,1195,1315,1435,1575,1715,1875],
    "3v3": [0,175,235,295,355,415,475,535,595,655,715,775,835,915,995,1075,1195,1315,1435,1575,1715,1875],
}


def estimate(current, target):
    if type(current) not in (int, float) or not math.isfinite(current) or not 0 <= current <= 10000:
        return {"remaining": None, "wins": None, "reached": False}
    gap = max(0, target - current)
    return {"remaining": math.ceil(gap), "wins": math.ceil(gap / 9), "reached": gap == 0}


class GoalsService:
    def __init__(self, data_dir, overlay):
        self.file = Path(data_dir) / "goals.json"
        self.overlay = overlay
        self.lock = RLock()
        self.accounts = {}
        try:
            saved = json.loads(self.file.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                for account, goals in saved.items():
                    if isinstance(goals, dict):
                        self.accounts[account] = {mode: tier for mode, tier in goals.items() if mode in TARGETS and type(tier) is int and 1 <= tier <= 22}
        except (OSError, ValueError, TypeError):
            pass

    def _profile(self):
        with self.overlay.lock:
            return deepcopy(self.overlay.profile or {})

    def _save(self):
        self.file.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.file.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.accounts, ensure_ascii=False), encoding="utf-8")
        temporary.replace(self.file)

    def set_goal(self, payload):
        if not isinstance(payload, dict) or payload.get("playlist") not in TARGETS:
            raise ValueError("Velg 1v1, 2v2 eller 3v3.")
        tier = payload.get("tier")
        if tier is not None and (type(tier) is not int or not 1 <= tier <= 22):
            raise ValueError("Velg en gyldig rank.")
        profile = self._profile()
        account = profile.get("playerId") or "draft"
        with self.lock:
            goals = self.accounts.setdefault(account, {})
            if tier is None:
                goals.pop(payload["playlist"], None)
            else:
                goals[payload["playlist"]] = tier
            self._save()
        return self.view()

    def view(self):
        profile = self._profile()
        account = profile.get("playerId") or "draft"
        with self.lock:
            # A goal can be chosen before Profile is connected, then assigned once.
            if account != "draft" and self.accounts.get("draft"):
                goals = self.accounts.setdefault(account, {})
                for mode, tier in self.accounts["draft"].items():
                    goals.setdefault(mode, tier)
                self.accounts.pop("draft")
                try:
                    self._save()
                except OSError:
                    logging.exception("Could not assign draft goals")
            goals = self.accounts.get(account, {})
            rows = []
            for mode, thresholds in TARGETS.items():
                rank = next((row for row in profile.get("ranks", []) if row["playlist"] == mode), {})
                tier = goals.get(mode)
                target = thresholds[tier - 1] if tier else None
                rows.append({"playlist": mode, "tier": tier, "targetRank": TIERS[tier] if tier else None,
                             "targetMmr": target, "currentMmr": rank.get("mmr"), "currentRank": rank.get("rank"),
                             **(estimate(rank.get("mmr"), target) if target is not None else {"remaining": None, "wins": None, "reached": False})})
            return {"name": profile.get("name"), "fetchedAt": profile.get("fetchedAt"), "mmrPerWin": 9,
                    "catalog": [{"tier": i, "rank": label} for i, label in enumerate(TIERS) if i], "goals": rows}
