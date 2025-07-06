#!/usr/bin/env uv run --with watchdog --with requests>=2
from dataclasses import dataclass
from pathlib import Path
from watchfiles import watch
import requests
import tomllib
import logging
import typing as t

logger = logging.getLogger("now-playing")
logger.propagate = False
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter(
        "\x1b[1m%(levelname)s\x1b[0m \x1b[2m%(asctime)s [%(name)s]\x1b[0m  %(message)s"
    )
)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


CONFIG_FILE_PATH = "./config.toml"


class Config(t.TypedDict):
    song_file: str
    api_key: str
    api_url: str


def get_config(file_path: str) -> Config:
    with open(file_path, "rb") as f:
        return t.cast(Config, tomllib.load(f))


@dataclass
class Song:
    game: str
    title: str
    system: str

    def format_game(self) -> str:
        system = self.system if self.system == "?" else f"[{self.system}]"
        return f"{self.game} - {system}"

    def format_title(self) -> str:
        return self.title

    def is_error(self) -> bool:
        return self.game == "FOOBAR CLOSED" or self.game == "" or self.title == ""


def get_song_error_reason(song: Song) -> str | None:
    if song.game == "FOOBAR CLOSED":
        return "Foobar reported that it closed."
    elif song.title == "":
        return "No title was written"
    elif song.game == "":
        return "No game name was written."


def get_song(path: Path) -> Song | None:
    try:
        lines = path.read_bytes().splitlines()
        game = lines[0]
        title = lines[1]
        system = lines[2]
        return Song(
            game.decode("utf-8", "ignore").strip(),
            title.decode("utf-8", "ignore").strip(),
            system.decode("utf-8", "ignore").strip(),
        )
    except Exception as e:
        logger.error("Failed to read song file", e)


def update_remote_song_data(config: Config, song: Song):
    try:
        request = requests.post(
            config["api_url"],
            json={
                "game": song.format_game(),
                "title": song.format_title(),
                "key": config["api_key"],
            },
            verify=False,
            headers={"charset": "utf-8"},
        )
        request.raise_for_status()
        logger.info("Song successfully updated")
    except Exception as e:
        logger.error("Failed to submit song to target")
        logger.error(f"Song data: {song.format_game()} - {song.format_title()}")
        logger.error("Request error: %s", e)


def loop(config: Config):
    path = Path(config["song_file"])
    current_song = get_song(path)
    for changes in watch(path, debounce=250):
        logger.debug("Change events received", changes)

        if not path.exists():
            logger.warning("Foobar file no longer exists")
            continue

        new_song = get_song(path)
        if new_song is None:
            logging.warning("Unable to parse song file")
            continue

        if new_song == current_song:
            logging.debug("Song did not change in this update")
            continue

        if new_song.is_error():
            logging.warning(
                "Failed to read current song: ", get_song_error_reason(new_song)
            )
            continue

        logging.info(
            f"New song playing: {new_song.format_game()} - {new_song.format_title}"
        )

        current_song = new_song
        update_remote_song_data(config, current_song)


logger.info("Now Playing Monitor started")
loop(config=get_config(CONFIG_FILE_PATH))
