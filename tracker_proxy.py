from __future__ import annotations

import json
import logging
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlparse

import cloudscraper
from requests.exceptions import RequestException, Timeout


HOST = "127.0.0.1"
PORT = 8765
TITLE_SLUG = "rocket-league"
API_BASE = "https://api.tracker.gg/api/v2/rocket-league/standard/profile"
PLATFORM_LABELS = {
    "epic": "Epic Games",
    "steam": "Steam",
    "xbl": "Xbox Live",
    "psn": "PlayStation Network",
    "switch": "Nintendo Switch",
}
PLAYLIST_LABELS = {
    "Ranked Duel 1v1": "1v1",
    "Ranked Doubles 2v2": "2v2",
    "Ranked Standard 3v3": "3v3",
}
PLAYLIST_ORDER = ["1v1", "2v2", "3v3"]
RANK_FAMILIES = ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Champion", "Grand Champion"]
ROMAN_TO_NUMBER = {"I": 1, "II": 2, "III": 3, "IV": 4}
NUMBER_TO_ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV"}
ESTIMATED_MMR_PER_DIVISION = 20


def create_scraper() -> cloudscraper.CloudScraper:
    return cloudscraper.create_scraper(
        browser={"browser": "chrome", "platform": "windows", "mobile": False}
    )


def tracker_profile_url(platform: str, gamertag: str) -> str:
    return f"https://rocketleague.tracker.network/{TITLE_SLUG}/profile/{platform}/{quote(gamertag, safe='')}/overview"


class TrackerUnavailableError(Exception):
    def __init__(self, message: str, code: str):
        super().__init__(message)
        self.code = code


def check_tracker_response(response) -> None:
    if response.status_code in (401, 403):
        raise TrackerUnavailableError(
            "Tracker avviser automatisk oppslag. Rocket League-data er ikke tilgjengelig via et offentlig Tracker-API. Åpne profilen på Tracker for å se statistikken.",
            "tracker_access_denied",
        )
    if response.status_code == 429:
        raise TrackerUnavailableError("Tracker har begrenset antall oppslag. Vent litt før du prøver igjen.", "tracker_rate_limited")
    if response.status_code == 404:
        raise LookupError("Fant ingen Rocket League-profil for denne gamertagen på valgt plattform.")
    response.raise_for_status()


def format_updated(value: str | None) -> str:
    if not value:
        return "ukjent"

    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value

    return stamp.strftime("%d.%m.%Y %H:%M UTC")


def avatar_text(name: str) -> str:
    letters = "".join(char for char in name if char.isalnum()).upper()
    return (letters[:2] or "RL").ljust(2, "L")


def compact_playlist_name(name: str) -> str:
    return PLAYLIST_LABELS.get(name, name)


def is_competitive_standard_playlist(segment: dict) -> bool:
    playlist_name = segment.get("metadata", {}).get("name", "")
    return playlist_name in PLAYLIST_LABELS


def build_rank_label(segment: dict) -> str:
    rating = segment["stats"].get("rating", {})
    tier = rating.get("metadata", {}).get("tierName") or segment["stats"].get("tier", {}).get(
        "metadata", {}
    ).get("name")
    division = segment["stats"].get("division", {}).get("metadata", {}).get("name")

    if tier and division:
        return f"{tier} {division}"
    return tier or "Ingen rank"


def parse_int(value) -> int | None:
    try:
        return int(float(str(value).replace(",", "").strip()))
    except (TypeError, ValueError):
        return None


def parse_rank_parts(rank_label: str) -> tuple[str, int, int | None] | None:
    if not rank_label or rank_label == "Ingen rank":
        return None

    if rank_label == "Supersonic Legend":
        return ("Supersonic Legend", 1, None)

    tier_part, _, division_part = rank_label.partition(" Division ")
    tier_tokens = tier_part.split()

    if not tier_tokens:
        return None

    tier_roman = tier_tokens[-1]
    family = " ".join(tier_tokens[:-1])
    tier_number = ROMAN_TO_NUMBER.get(tier_roman)
    division_number = ROMAN_TO_NUMBER.get(division_part.strip()) if division_part else None

    if family not in RANK_FAMILIES or tier_number is None:
        return None

    return (family, tier_number, division_number)


def next_rank_label(rank_label: str) -> str:
    parts = parse_rank_parts(rank_label)
    if not parts:
        return "Ukjent"

    family, tier_number, _division_number = parts

    if family == "Supersonic Legend":
        return "Top rank"

    if tier_number < 3:
        return f"{family} {NUMBER_TO_ROMAN[tier_number + 1]}"

    family_index = RANK_FAMILIES.index(family)
    if family_index + 1 >= len(RANK_FAMILIES):
        return "Supersonic Legend"

    return f"{RANK_FAMILIES[family_index + 1]} I"


def estimate_missing_to_next_rank(rank_label: str) -> int | None:
    parts = parse_rank_parts(rank_label)
    if not parts:
        return None

    _family, _tier_number, division_number = parts
    if division_number is None:
        return ESTIMATED_MMR_PER_DIVISION * 4

    return max(ESTIMATED_MMR_PER_DIVISION, (5 - division_number) * ESTIMATED_MMR_PER_DIVISION)


def estimate_next_rank_gap(mmr: int | None, rank_label: str | None = None) -> dict:
    if mmr is None or not rank_label:
        return {"label": "Ukjent", "target": None, "missing": None, "estimated": True}

    label = next_rank_label(rank_label)
    missing = estimate_missing_to_next_rank(rank_label)

    return {
        "label": label,
        "target": None,
        "missing": missing,
        "estimated": True,
    }


def build_rank_tiles(profile_data: dict) -> list[dict]:
    ranks = []

    for segment in profile_data.get("segments", []):
        if segment.get("type") != "playlist" or not is_competitive_standard_playlist(segment):
            continue

        name = compact_playlist_name(segment.get("metadata", {}).get("name", "Ukjent"))
        rating = segment["stats"].get("rating", {})
        matches = segment["stats"].get("matchesPlayed", {})
        mmr = rating.get("displayValue") or "-"
        mmr_value = parse_int(rating.get("value") or mmr)
        match_count = matches.get("displayValue") or "0"

        rank_label = build_rank_label(segment)

        ranks.append(
            {
                "playlist": name,
                "rank": rank_label,
                "trend": f"{mmr} MMR | {match_count} kamper",
                "mmr": mmr_value,
                "matches": parse_int(matches.get("value") or match_count),
                "nextRank": estimate_next_rank_gap(mmr_value, rank_label),
            }
        )

    ranks.sort(
        key=lambda item: PLAYLIST_ORDER.index(item["playlist"])
        if item["playlist"] in PLAYLIST_ORDER
        else len(PLAYLIST_ORDER)
    )
    return ranks[:3]


def choose_feature_rank(ranks: list[dict]) -> dict | None:
    valid_ranks = [rank for rank in ranks if rank.get("mmr") is not None]
    if not valid_ranks:
        return ranks[0] if ranks else None

    return max(valid_ranks, key=lambda rank: rank["mmr"])


def build_profile_payload(platform: str, gamertag: str, profile_data: dict, summary_data: dict) -> dict:
    platform_info = profile_data["platformInfo"]
    metadata = profile_data.get("metadata", {})
    summary_stats = summary_data.get("stats", {})
    handle = platform_info.get("platformUserHandle") or gamertag
    last_updated = metadata.get("lastUpdated", {}).get("value")
    wins = summary_stats.get("wins", {}).get("displayValue", "-")
    goals = summary_stats.get("goals", {}).get("displayValue", "-")
    shot_ratio = summary_stats.get("goalShotRatio", {}).get("displayValue")
    shot_ratio_display = f"{shot_ratio}%" if shot_ratio else "-"
    tracker_url = tracker_profile_url(platform, gamertag)
    ranks = build_rank_tiles(profile_data)
    feature_rank_item = choose_feature_rank(ranks)
    feature_queue = feature_rank_item["playlist"] if feature_rank_item else "Ranked"
    feature_rank = feature_rank_item["rank"] if feature_rank_item else "Ingen rank"
    feature_mmr = str(feature_rank_item["mmr"]) if feature_rank_item and feature_rank_item["mmr"] is not None else "-"
    doubles = next((rank for rank in ranks if rank["playlist"] == "2v2"), None)

    return {
        "name": handle,
        "tagline": f"{PLATFORM_LABELS[platform]} | {feature_queue}: {feature_rank} ({feature_mmr} MMR)",
        "avatarText": avatar_text(handle),
        "sourceLabel": f"Kilde: Tracker Network | {PLATFORM_LABELS[platform]}",
        "profileUrl": tracker_url,
        "stats": [
            {"label": "Best queue", "value": feature_queue},
            {"label": "Sesong", "value": str(metadata.get("currentSeason", "-"))},
            {"label": "Wins", "value": wins},
            {"label": "Goals", "value": goals},
            {"label": "Shot ratio", "value": shot_ratio_display},
            {"label": "MMR", "value": feature_mmr},
        ],
        "ranks": ranks,
        "session": {
            "playlist": "2v2",
            "startMmr": doubles["mmr"] if doubles else None,
            "currentMmr": doubles["mmr"] if doubles else None,
            "delta": 0,
            "streak": {"type": "neutral", "count": 0, "label": "Ingen games enda"},
            "nextRank": doubles["nextRank"] if doubles else estimate_next_rank_gap(None, None),
        },
        "activity": [
            f"Tracker sist oppdatert: {format_updated(last_updated)}",
            f"Høyeste competitive playlist akkurat nå: {feature_queue} - {feature_rank}",
            f"Lifetime totals: {wins} wins, {goals} goals og {shot_ratio_display} shot ratio",
        ],
    }


def fetch_tracker_profile(platform: str, gamertag: str) -> dict:
    scraper = create_scraper()
    encoded_tag = quote(gamertag, safe="")
    profile_url = f"{API_BASE}/{platform}/{encoded_tag}"
    summary_url = f"{profile_url}/summary"

    profile_response = scraper.get(profile_url, timeout=20)
    check_tracker_response(profile_response)

    summary_response = scraper.get(summary_url, timeout=20)
    check_tracker_response(summary_response)

    profile_data = profile_response.json()["data"]
    summary_data = summary_response.json()["data"]
    return build_profile_payload(platform, gamertag, profile_data, summary_data)


class TrackerProxyHandler(BaseHTTPRequestHandler):
    server_version = "RLHubTrackerProxy/1.0"
    source_name = "Tracker"

    def fetch_profile(self, platform: str, gamertag: str, player_id: str = "") -> dict:
        return fetch_tracker_profile(platform, gamertag)

    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)

        if parsed.path == "/health":
            self.respond_json(200, {"status": "ok"})
            return

        if parsed.path != "/api/profile":
            self.respond_json(404, {"error": "Fant ikke endepunktet."})
            return

        query = parse_qs(parsed.query)
        platform = (query.get("platform", ["epic"])[0] or "epic").strip().lower()
        gamertag = (query.get("gamertag", [""])[0] or "").strip()
        player_id = (query.get("playerId", [""])[0] or "").strip()

        if platform not in PLATFORM_LABELS:
            self.respond_json(400, {"error": "Ugyldig plattform."})
            return

        if not gamertag:
            self.respond_json(400, {"error": "Gamertag mangler."})
            return

        try:
            payload = self.fetch_profile(platform, gamertag, player_id)
        except ValueError:
            self.respond_json(400, {"error": "Spiller-ID eller svaret fra datakilden er ugyldig. Kontroller valgt plattform og ID."})
            return
        except TrackerUnavailableError as error:
            self.respond_json(503, {
                "error": str(error), "code": error.code,
                "profileUrl": tracker_profile_url(platform, gamertag),
            })
            return
        except LookupError as error:
            self.respond_json(404, {"error": str(error)})
            return
        except (Timeout, RequestException) as error:
            logging.warning("%s request failed: %s", self.source_name, error)
            self.respond_json(502, {
                "error": f"Klarte ikke kontakte {self.source_name}. Prøv igjen senere.",
                "code": "tracker_connection_failed",
                "profileUrl": tracker_profile_url(platform, gamertag),
            })
            return
        except Exception:  # pragma: no cover
            logging.exception("Unexpected %s response", self.source_name)
            self.respond_json(
                502,
                {"error": f"Klarte ikke lese statistikken fra {self.source_name} akkurat nå.", "code": "tracker_invalid_response"},
            )
            return

        self.respond_json(200, {"profile": payload})

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        return

    def respond_json(self, status: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), TrackerProxyHandler)
    print(f"RL Hub Tracker proxy running on http://{HOST}:{PORT}")
    server.serve_forever()


if __name__ == "__main__":
    main()
