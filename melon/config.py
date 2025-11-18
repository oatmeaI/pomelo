import tomllib
import tomli_w
import os

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pathlib import Path
from platformdirs import user_config_dir

from melon.constants import APP_NAME, CONFIG_FILE_NAME
from melon.strings import (
    confirm,
    error,
    log,
    no_config_file,
    plex_token_explainer,
    advanced_settings,
    ask,
)

SETTING_NAMES = {
    "plex_host": "Plex server address",
    "plex_port": "Plex server port",
    "plex_token": "Plex token",
    "pomelo_port": "Pomelo port",
    "music_section_id": "Music section ID",
    "caddy_url": "Caddy URL",
    "proxy_host": "Proxy host",
    "auto_firewall": "Automatically try to enable firewall",
}

DEFAULTS = {
    "plex_host": "127.0.0.1",
    "plex_port": 32400,
    "plex_token": "",
    "pomelo_port": 5200,
    "music_section_id": 1,
    "enabled_plugins": ["ExploreRadio", "AnyRadios"],
    "caddy_url": "http://localhost:2019",
    "proxy_host": ":5500",
    "auto_firewall": False,
}


class _Config(FileSystemEventHandler):
    def __init__(self):
        self.data = DEFAULTS
        self.config_dir = user_config_dir(APP_NAME, ensure_exists=True)
        self.config_file_path = f"{self.config_dir}/{CONFIG_FILE_NAME}"
        Path(self.config_dir).mkdir(parents=True, exist_ok=True)

        self.load_config()
        self.plex_host = self.data["plex_host"]
        self.plex_port = self.data["plex_port"]
        self.music_section_id = self.data["music_section_id"]
        self.enabled_plugins = self.data["enabled_plugins"]
        self.caddy_url = self.data["caddy_url"]

        self.proxy_host = self.data["proxy_host"]

        self.pomelo_port = self.data["pomelo_port"]
        self.plex_token = self.data["plex_token"]

        if self.plex_token == "":
            error("No Plex token found in config; exiting.")
            exit()

        observer = Observer()
        observer.schedule(
            self,
            self.config_dir,
        )
        observer.start()

    def setup(self):
        log(no_config_file.format(path=self.config_file_path), highlight=False)
        log(plex_token_explainer)
        self.prompt_setting("plex_token")
        self.prompt_setting("plex_host")
        self.prompt_setting("plex_port")
        if confirm(advanced_settings, default=False):
            self.prompt_setting("pomelo_port")
            self.prompt_setting("caddy_url")
            self.prompt_setting("proxy_host")
        self.write_config()

    def prompt_setting(self, setting):
        default = str(self.data[setting])
        if default != "":
            self.data[setting] = ask(f"{SETTING_NAMES[setting]}", default=default)
        else:
            self.data[setting] = ask(f"{SETTING_NAMES[setting]}")

    def load_config(self):
        if os.path.exists(self.config_file_path):
            with open(self.config_file_path, "rb") as f:
                self.data = DEFAULTS | tomllib.load(f)
        else:
            self.setup()

    def on_modified(self, event):
        if event.src_path == self.config_file_path:
            self.load_config()

    def getPluginSettings(self, pluginName):
        return self.data[pluginName] if pluginName in self.data else {}

    def write_config(self):
        if os.path.exists(self.config_file_path):
            with open(self.config_file_path, "wb") as f:
                tomli_w.dump(self.data, f)
        else:
            with open(self.config_file_path, "xb") as f:
                tomli_w.dump(self.data, f)

    def write_setting(self, setting, value):
        self.data[setting] = value
        self.write_config()


Config = _Config()
