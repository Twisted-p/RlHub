"""Read ranked skill data from the public mmr-api-v2 service.

Service/schema: https://github.com/Kalilamodow/mmr-api-v2
Only public player identifiers are read from local game logs, never credentials.
"""
from __future__ import annotations

import ctypes
from datetime import datetime, timezone
from pathlib import Path
import re
import sys

import requests
from tracker_proxy import TrackerUnavailableError, avatar_text, estimate_next_rank_gap

MMR_BASE = "https://mmr.kmdw.dev"
PLATFORMS = {"epic": "Epic", "steam": "Steam", "xbl": "XboxOne", "psn": "PS4", "switch": "Switch"}
PLAYLISTS = {10: "1v1", 11: "2v2", 13: "3v3"}
TIERS = ["Unranked"] + [f"{family} {tier}" for family in
    ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Champion", "Grand Champion"]
    for tier in ["I", "II", "III"]] + ["Supersonic Legend"]
LOGIN_PATTERN = re.compile(
    r"HandleLocalPlayerLoginStatusChanged PlayerName=(.*?) PlayerID=((?:Epic|Steam|XboxOne|PS4|Switch)\|[A-Za-z0-9_-]+\|0) LoginStatus=LS_LoggedIn IsPrimary=True(?:\s|$)"
)


def documents_dir() -> Path:
    if sys.platform == "win32":
        buffer = ctypes.create_unicode_buffer(32768)
        if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buffer) == 0:
            return Path(buffer.value)
    return Path.home() / "Documents"


def normalize_player_id(platform: str, value: str) -> str:
    prefix = PLATFORMS.get(platform)
    if not prefix:
        raise ValueError("Ugyldig plattform.")
    value = value.strip()
    if "|" not in value:
        value = f"{prefix}|{value}|0"
    match = re.fullmatch(r"(Epic|Steam|XboxOne|PS4|Switch)\|([A-Za-z0-9_-]{1,128})\|0", value)
    if not match or match[1] != prefix:
        raise ValueError("Spiller-ID må stemme med valgt plattform.")
    if prefix == "Epic" and not re.fullmatch(r"[a-fA-F0-9]{32}", match[2]):
        raise ValueError("Epic Account ID må bestå av 32 tegn (tall og a–f).")
    if prefix == "Steam" and not re.fullmatch(r"\d{17}", match[2]):
        raise ValueError("Bruk SteamID64 på 17 siffer.")
    return value


def resolve_player_id(platform: str, gamertag: str, player_id: str = "", log_dir: Path | None = None) -> str:
    if player_id:
        return normalize_player_id(platform, player_id)
    if platform == "epic" and re.fullmatch(r"[a-fA-F0-9]{32}", gamertag):
        return normalize_player_id(platform, gamertag)
    if platform == "steam" and re.fullmatch(r"\d{17}", gamertag):
        return normalize_player_id(platform, gamertag)
    directory = log_dir if log_dir is not None else documents_dir() / "My Games/Rocket League/TAGame/Logs"
    try:
        logs = sorted(directory.glob("Launch*.log"), key=lambda p: p.stat().st_mtime, reverse=True)[:6]
        for path in logs:
            # Reading only login identity records prevents tokens from being used or exposed.
            found = None
            with path.open(encoding="utf-8", errors="replace") as stream:
                for line in stream:
                    match = LOGIN_PATTERN.search(line)
                    if match and match[1].casefold() == gamertag.casefold() and match[2].startswith(PLATFORMS[platform] + "|"):
                        found = match[2]
            if found:
                return normalize_player_id(platform, found)
    except OSError:
        pass
    raise TrackerUnavailableError(
        "Fant ikke kontoen på denne maskinen. Kontroller plattform og gamertag. Start Rocket League med kontoen din én gang, og prøv igjen.",
        "player_id_required",
    )


def rank_label(tier: int, division: int) -> str:
    if not 0 <= tier < len(TIERS) or not 0 <= division <= 3:
        raise ValueError("Ugyldig rank fra MMR-tjenesten.")
    if tier in (0, 22):
        return TIERS[tier]
    return f"{TIERS[tier]} Division {['I', 'II', 'III', 'IV'][division]}"


def build_rank_profile(platform: str, gamertag: str, player_id: str, data: dict, name: str | None = None) -> dict:
    rows = data.get("playlists")
    if not isinstance(rows, list):
        raise TrackerUnavailableError("MMR-tjenesten fant ingen ranked-data for denne spilleren.", "rank_data_unavailable")
    ranks = []
    for playlist_id, playlist_name in PLAYLISTS.items():
        item = next((row for row in rows if row.get("id") == playlist_id), None)
        if item is None:
            continue
        mmr = item.get("mmr")
        if isinstance(mmr, bool) or not isinstance(mmr, (int, float)) or not 0 <= mmr <= 10000:
            raise ValueError("Ugyldig MMR fra tjenesten.")
        label = rank_label(item["tier"], item["division"])
        ranks.append({"playlist": playlist_name, "rank": label, "mmr": int(mmr),
                      "trend": f"{int(mmr)} MMR", "matches": None,
                      "nextRank": estimate_next_rank_gap(int(mmr), label)})
    if not ranks:
        raise TrackerUnavailableError("Ingen 1v1-, 2v2- eller 3v3-data tilgjengelig for denne spilleren.", "rank_data_unavailable")
    doubles = next((row for row in ranks if row["playlist"] == "2v2"), ranks[0])
    fetched_at = datetime.now(timezone.utc).isoformat()
    handle = name or gamertag
    return {
        "name": handle, "avatarText": avatar_text(handle),
        "tagline": f"{doubles['playlist']}: {doubles['rank']} ({doubles['mmr']} MMR)",
        "sourceLabel": "Kilde: MMR API · kmdw.dev (tredjepart)",
        "provider": "kmdw", "playerId": player_id, "fetchedAt": fetched_at,
        "stats": [{"label": row["playlist"] + " MMR", "value": str(row["mmr"])} for row in ranks],
        "ranks": ranks,
        "session": {"playlist": doubles["playlist"], "startMmr": doubles["mmr"], "currentMmr": doubles["mmr"],
                    "delta": 0, "nextRank": doubles["nextRank"],
                    "streak": {"type": "neutral", "count": 0, "label": "Ingen games enda"}},
        "activity": [f"Hentet: {datetime.now().astimezone().strftime('%d.%m.%Y %H:%M')}",
                     "Rank og MMR hentes direkte i appen. Kampantall og lifetime-statistikk leveres ikke av denne kilden."],
    }


def fetch_rank_profile(platform: str, gamertag: str, player_id: str = "") -> dict:
    resolved = resolve_player_id(platform, gamertag, player_id)
    with requests.Session() as session:
        session.headers["User-Agent"] = "RLHub/0.3 (desktop rank lookup)"
        response = session.get(f"{MMR_BASE}/get-skills", params={"playerId": resolved}, timeout=15)
        if response.status_code == 429:
            raise TrackerUnavailableError("MMR-tjenesten har begrenset antall oppslag. Vent litt før du prøver igjen.", "rank_rate_limited")
        response.raise_for_status()
        payload = response.json()
        name = None
        try:
            profile = session.get(f"{MMR_BASE}/get-profile", params={"playerId": resolved}, timeout=8)
            profile.raise_for_status()
            identity = profile.json()
            if identity and identity.get("id") == resolved and isinstance(identity.get("name"), str):
                name = identity["name"]
        except (requests.RequestException, ValueError):
            pass  # Ranked data remains usable if the optional name lookup fails.
    return build_rank_profile(platform, gamertag, resolved, payload, name)
