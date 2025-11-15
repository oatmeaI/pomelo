import tomllib
import tomli_w
import os

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
from platformdirs import user_config_dir

from melon.constants import APP_NAME, CONFIG_FILE_NAME

DEFAULTS = {
    "plex_host": "127.0.0.1",
    "plex_port": 32400,
    "plex_token": None,
    "pomelo_port": 5200,
    "music_section_title": "Music",
    "enabled_plugins": ["ExploreRadio", "AnyRadios"],
    "caddy_url": "http://localhost:2019",
    "proxy_host": ":5500",
}


class _Config(FileSystemEventHandler):
    def __init__(self):
        self.config_dir = user_config_dir(APP_NAME, ensure_exists=True)
        self.config_file_path = f"{self.config_dir}/{CONFIG_FILE_NAME}"
        Path(self.config_dir).mkdir(parents=True, exist_ok=True)

        self.loadConfig()
        self.plex_host = self.data["plex_host"]
        self.plex_port = self.data["plex_port"]
        self.music_section_title = self.data["music_section_title"]
        self.enabled_plugins = self.data["enabled_plugins"]
        self.caddy_url = self.data["caddy_url"]

        self.proxy_host = self.data["proxy_host"]

        self.pomelo_port = self.data["pomelo_port"]
        self.plex_token = self.data["plex_token"]
        observer = Observer()
        observer.schedule(
            self,
            self.config_dir,
        )
        observer.start()

    def loadConfig(self):
        data = {}
        if os.path.exists(self.config_file_path):
            with open(self.config_file_path, "rb") as f:
                data = tomllib.load(f)

        self.data = DEFAULTS | data

    def on_modified(self, event):
        if event.src_path == self.config_file_path:
            self.loadConfig()

    def getPluginSettings(self, pluginName):
        return self.data[pluginName] if pluginName in self.data else {}

    def writeSetting(self, setting, value):
        self.data[setting] = value

        if os.path.exists(self.config_file_path):
            with open(self.config_file_path, "wb") as f:
                tomli_w.dump(self.data, f)
        else:
            with open(self.config_file_path, "xb") as f:
                tomli_w.dump(self.data, f)


Config = _Config()
