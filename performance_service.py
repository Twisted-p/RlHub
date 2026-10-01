"""Local, read-only consumer of Rocket League's official Stats API."""
from __future__ import annotations

import configparser
from copy import deepcopy
from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re
import shutil
import uuid
from threading import Event, RLock, Thread

import websocket
from mmr_provider import documents_dir, LOGIN_PATTERN

SECTION = "TAGame.MatchStatsExporter_TA"
PLAYLISTS = {10: "Ranked 1v1", 11: "Ranked 2v2", 13: "Ranked 3v3", 1: "Casual 1v1", 2: "Casual 2v2", 3: "Casual 3v3", 6: "Privat kamp"}
STAT_KEYS = ["Score", "Goals", "Assists", "Saves", "Shots", "Touches", "CarTouches", "Demos"]


def game_info() -> tuple[Path | None, dict | None]:
    directory = documents_dir() / "My Games/Rocket League/TAGame/Logs"
    try:
        logs = sorted(directory.glob("Launch*.log"), key=lambda p: p.stat().st_mtime, reverse=True)[:3]
        root, player = None, None
        for path in logs:
            with path.open(encoding="utf-8", errors="replace") as stream:
                for line in stream:
                    base = re.search(r"Base directory:\s*(.+)", line)
                    if base and root is None:
                        binary_dir = Path(base[1].strip().rstrip("\\/"))
                        if binary_dir.parent.name.lower() == "binaries":
                            candidate = binary_dir.parent.parent
                            if (candidate / "TAGame/Config").is_dir():
                                root = candidate
                    match = LOGIN_PATTERN.search(line)
                    if match:
                        player = {"name": match[1], "playerId": match[2]}
            if root and player:
                break
        return root, player
    except OSError:
        return None, None


def config_path(root: Path | None) -> Path | None:
    if root is None:
        return None
    directory = root / "TAGame/Config"
    own = directory / "TAStatsAPI.ini"
    return own if own.exists() else directory / "DefaultStatsAPI.ini"


def read_settings(path: Path | None) -> dict:
    config = configparser.ConfigParser(strict=False)
    try:
        if path is not None:
            config.read(path, encoding="utf-8-sig")
        rate = config.getfloat(SECTION, "PacketSendRate", fallback=0)
        port = config.getint(SECTION, "WebPort", fallback=49124)
        return {"enabled": rate > 0 and 0 < port < 65536, "port": port, "found": bool(path and path.exists())}
    except (OSError, configparser.Error, ValueError):
        return {"enabled": False, "port": 49124, "found": bool(path and path.exists())}


def enable_stats_api(path: Path) -> None:
    """Preserve unrelated settings and comments, with a one-time backup."""
    text = path.read_text(encoding="utf-8-sig")
    settings = read_settings(path)
    port = settings["port"] if 0 < settings["port"] < 65536 else 49124
    parser = configparser.ConfigParser(strict=False)
    parser.read_string(text)
    if parser.getint(SECTION, "Port", fallback=49123) == port:
        port = 49124 if port != 49124 else 49125
    values = {"PacketSendRate": "2", "WebPort": str(port)}
    pattern = re.compile(r"(?ms)^\[" + re.escape(SECTION) + r"\][^\r\n]*\r?\n(.*?)(?=^\[|\Z)")
    match = pattern.search(text)
    if match:
        body = match[1]
        for key, value in values.items():
            key_pattern = re.compile(r"(?mi)^\s*" + key + r"\s*=.*$")
            if key_pattern.search(body):
                body = key_pattern.sub(key + "=" + value, body)
            else:
                body = body.rstrip() + "\n" + key + "=" + value + "\n"
        text = text[:match.start(1)] + body + text[match.end(1):]
    else:
        text = text.rstrip() + f"\n\n[{SECTION}]\nPacketSendRate=2\nWebPort={port}\n"
    backup = path.with_name(path.name + ".rlhub.bak")
    if not backup.exists():
        shutil.copy2(path, backup)
    temporary = path.with_name(path.name + ".rlhub.tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


class PerformanceService:
    def __init__(self, data_dir: Path, root: Path | None = None, local_player: dict | None = None):
        self.data_dir = data_dir
        self.history_file = data_dir / "performance.json"
        self.root, detected = game_info() if root is None else (root, None)
        self.local_player = local_player or detected
        self.lock = RLock()
        self.stop_event = Event()
        self.thread = None
        self.connection = None
        self.connected = False
        self.last_event = None
        self.last_event_name = None
        self.received_messages = 0
        self.parsed_events = 0
        self.ignored_messages = 0
        self.current = None
        self.replay = False
        self.history = []
        try:
            saved = json.loads(self.history_file.read_text(encoding="utf-8"))
            if isinstance(saved, list):
                self.history = [row for row in saved if isinstance(row, dict) and row.get("id") and isinstance(row.get("players"), list)][:100]
                for row in self.history:
                    row["mode"] = PLAYLISTS.get(row.get("playlist"), "Annen modus")
        except (OSError, ValueError):
            pass

    def start(self):
        self.thread = Thread(target=self._listen, name="rl-hub-stats-api", daemon=True)
        self.thread.start()

    def stop(self):
        self.stop_event.set()
        connection = self.connection
        if connection is not None:
            try:
                connection.shutdown()
            except (OSError, websocket.WebSocketException):
                pass
        if self.thread:
            self.thread.join(timeout=4)

    def setup(self) -> dict:
        if self.root is None:
            self.root, self.local_player = game_info()
        path = config_path(self.root)
        if path is None or not path.exists():
            raise ValueError("Fant ikke Rocket League. Start spillet én gang på denne maskinen, lukk det, og prøv igjen.")
        try:
            with self.lock:
                enable_stats_api(path)
        except configparser.Error as error:
            raise ValueError("Spillets innstillinger kunne ikke leses.") from error
        return {"message": "Kampoppsummeringer er aktivert. Start Rocket League på nytt, og spill en kamp med RL Hub åpen."}

    def snapshot(self) -> dict:
        with self.lock:
            settings = read_settings(config_path(self.root))
            return {"connected": self.connected, "enabled": settings["enabled"], "gameFound": settings["found"],
                    "lastEvent": self.last_event, "localPlayer": self.local_player,
                    "activeMatch": bool(self.current and self.current["players"] and not self.current.get("finished")),
                    "lastEventName": self.last_event_name, "receivedMessages": self.received_messages,
                    "parsedEvents": self.parsed_events, "ignoredMessages": self.ignored_messages,
                    "matches": deepcopy(self.history)}

    def _listen(self):
        while not self.stop_event.is_set():
            settings = read_settings(config_path(self.root))
            if not settings["enabled"]:
                self.stop_event.wait(3)
                continue
            connection = None
            try:
                connection = websocket.create_connection(f"ws://127.0.0.1:{settings['port']}/", timeout=2,
                                                         suppress_origin=True, http_no_proxy=["127.0.0.1", "localhost"])
                self.connection = connection
                with self.lock:
                    self.connected = True
                while not self.stop_event.is_set():
                    try:
                        message = connection.recv()
                        if not message:
                            break
                        if len(message) > 2_000_000:
                            continue
                        self.ingest(json.loads(message))
                    except websocket.WebSocketTimeoutException:
                        continue
                    except (ValueError, TypeError, KeyError):
                        logging.warning("Ignored malformed Rocket League stats event")
            except (OSError, websocket.WebSocketException):
                pass  # The game is commonly closed; reconnect quietly.
            finally:
                with self.lock:
                    self.connected = False
                    self.current = None  # Never mix snapshots across connections.
                self.connection = None
                if connection:
                    connection.close(timeout=0)
            self.stop_event.wait(3)

    def ingest(self, message: dict):
        with self.lock:
            self.received_messages += 1
            if not isinstance(message, dict):
                self.ignored_messages += 1
                return
            event, data = message.get("Event"), message.get("Data", {})
            if isinstance(data, str):
                try:
                    data = json.loads(data) if data.strip() else {}
                except ValueError:
                    self.ignored_messages += 1
                    return
            if not isinstance(data, dict) or not isinstance(event, str):
                self.ignored_messages += 1
                return
            self.parsed_events += 1
            self.last_event = datetime.now(timezone.utc).isoformat()
            self.last_event_name = event
            game = data.get("Game", {})
            if event == "ReplayCreated":
                self.current = None
                self.replay = True
                return
            if event == "MatchCreated":
                self.replay = False
            if self.replay or game.get("bReplay"):
                return
            match_id = data.get("MatchGuid")
            if event == "UpdateState" and (len(game.get("Teams", [])) < 2 or len(data.get("Players", [])) < 2):
                return  # A training snapshot is not a completed match.
            if event == "MatchCreated" and not match_id:
                self.current = None  # Private/local matches may omit their GUID.
            if not match_id:
                match_id = self.current["id"] if self.current else "local-" + uuid.uuid4().hex
            elif self.current and self.current["id"].startswith("local-") and event == "UpdateState":
                self.current["id"] = match_id  # An authoritative GUID can arrive after MatchCreated.
            if event in ("MatchCreated", "MatchInitialized", "UpdateState"):
                if self.current is None or self.current["id"] != match_id:
                    self.current = {"id": match_id, "players": [], "teams": [], "playlist": None,
                                    "startedAt": self.last_event, "partial": event == "UpdateState", "overtime": False}
            if self.current is None or self.current["id"] != match_id:
                return
            if event == "UpdateState":
                self.current["players"] = [self._player(row) for row in data.get("Players", []) if isinstance(row, dict)]
                self.current["teams"] = [{"name": row.get("Name", ""), "team": row.get("TeamNum"), "score": row.get("Score", 0)}
                                         for row in game.get("Teams", []) if isinstance(row, dict)]
                self.current["playlist"] = game.get("PlaylistId")
                self.current["arena"] = game.get("Arena", "")
                self.current["overtime"] = self.current["overtime"] or bool(game.get("bOvertime"))
                if game.get("bHasWinner"):
                    winner = next((row["team"] for row in self.current["teams"] if row["name"] == game.get("Winner")), None)
                    if winner is not None:
                        self.current["winnerTeam"] = winner
                        self.current["finished"] = True
                if self.current.get("finished"):
                    self._save_match()
            elif event == "MatchEnded":
                self.current["winnerTeam"] = data.get("WinnerTeamNum")
                self.current["finished"] = True
                self._save_match()
            elif event == "MatchDestroyed":
                self.current = None  # Leaving before MatchEnded does not fabricate a loss.

    @staticmethod
    def _player(row: dict) -> dict:
        result = {"name": row.get("Name", ""), "playerId": row.get("PrimaryId", ""), "team": row.get("TeamNum")}
        for key in STAT_KEYS:
            value = row.get(key)
            result[key.lower()] = max(0, value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None
        result["accuracy"] = round(100 * result["goals"] / result["shots"], 1) if result["shots"] and result["goals"] is not None else None
        return result

    def _save_match(self):
        if not self.current["players"] or self.current.get("winnerTeam") not in (0, 1):
            return
        row = deepcopy(self.current)
        row.setdefault("endedAt", self.last_event)
        row["mode"] = PLAYLISTS.get(row["playlist"], "Annen modus")
        existing = next((match for match in self.history if match["id"] == row["id"]), None)
        if existing:
            row["endedAt"] = existing["endedAt"]
            if row == existing:
                return
        self.history = [row] + [match for match in self.history if match["id"] != row["id"]]
        self.history = self.history[:100]
        try:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            temporary = self.history_file.with_suffix(".tmp")
            temporary.write_text(json.dumps(self.history, ensure_ascii=False), encoding="utf-8")
            temporary.replace(self.history_file)
        except OSError:
            logging.exception("Could not persist performance history")
