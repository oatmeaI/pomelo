import tomllib
import tomli_w
import os

from pomelo.certs import read_prefs
from pomelo.constants import CONFIG_FILE_NAME

SETTING_NAMES = {
    "plex_host": "Plex server address",
    "plex_port": "Plex server port",
    "plex_token": "Plex token",
    "pomelo_port": "Pomelo port",
    "music_section_id": "Music section ID",
    "caddy_url": "Caddy admin URL",
    "caddy_listen_port": "Port for Caddy to listen on",
}

DEFAULTS = {
    "caddy_admin_url": "http://localhost:2019",
    "caddy_listen_port": 5500,
    "plex_host": "plex",
    "plex_port": 32400,
    "plex_token": "",
    "pomelo_port": 5200,
    "music_section_id": 1,
    "enabled_plugins": ["ExploreRadio", "AnyRadios"],
}


class _Config:
    def __init__(self):
        self.data = DEFAULTS

        self.config_dir = "/pomelo"
        self.config_file_path = f"{self.config_dir}/{CONFIG_FILE_NAME}"

        self.load_config()

        self.set_config()

        if self.plex_token == "":
            prefs = read_prefs()
            self.plex_token = prefs["@PlexOnlineToken"]
            self.write_config()

        if not os.path.exists(self.config_file_path):
            self.write_config()

    # TODO: deprecate
    def set_config(self):
        self.plex_host = self.data["plex_host"]
        self.plex_port = self.data["plex_port"]
        self.music_section_id = self.data["music_section_id"]
        self.enabled_plugins = self.data["enabled_plugins"]
        self.caddy_admin_url = self.data["caddy_admin_url"]
        self.caddy_listen_port = self.data["caddy_listen_port"]
        self.pomelo_port = self.data["pomelo_port"]
        self.plex_token = self.data["plex_token"]

    def load_config(self):
        print("load config")
        if os.path.exists(self.config_file_path):
            with open(self.config_file_path, "rb") as f:
                self.data = DEFAULTS | tomllib.load(f)
                print(self.data)
        else:
            print("file no exist")

    def getPluginSettings(self, pluginName):
        return self.data[pluginName] if pluginName in self.data else {}

    def write_config(self):
        mode = "wb" if os.path.exists(self.config_file_path) else "xb"
        with open(self.config_file_path, mode) as f:
            tomli_w.dump(self.data, f)


Config = _Config()
