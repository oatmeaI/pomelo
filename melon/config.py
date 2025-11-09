import tomllib
import tomli_w
import os
from pathlib import Path
from platformdirs import user_config_dir
from melon.constants import APP_NAME, CONFIG_FILE_NAME

DEFAULTS = {
    "server_address": "http://127.0.0.1",
    "server_port": 32400,
    "token": None,
    "port": 5200,
    "music_section": "Music",
    "enabled_plugins": [
        "ExploreRadio",
    ],
    "plugin_config": {},
}


class _Config:
    def __init__(self):
        self.config_dir = user_config_dir(APP_NAME, ensure_exists=True)
        self.config_file_path = f"{self.config_dir}/{CONFIG_FILE_NAME}"
        Path(self.config_dir).mkdir(parents=True, exist_ok=True)

        if os.path.exists(self.config_file_path):
            with open(self.config_file_path, "rb") as f:
                self.data = tomllib.load(f)
        else:
            self.data = DEFAULTS

        self.serverAddress = self.loadSetting("server_address")
        self.serverPort = self.loadSetting("server_port")
        self.musicSection = self.loadSetting("music_section")
        self.enabled_plugins = self.loadSetting("enabled_plugins")
        self.port = self.loadSetting("port")
        self.pluginConfig = self.loadSetting("plugin_config")
        self.token = self.loadSetting("token")

    def getPluginSettins(self, pluginName):
        if pluginName in self.pluginConfig:
            return self.pluginConfig[pluginName]
        return None

    def loadSetting(self, setting):
        return self.data[setting] if setting in self.data else DEFAULTS[setting]

    def writeSetting(self, setting, value):
        self.data[setting] = value

        if os.path.exists(self.config_file_path):
            with open(self.config_file_path, "wb") as f:
                tomli_w.dump(self.data, f)
        else:
            with open(self.config_file_path, "xb") as f:
                tomli_w.dump(self.data, f)


Config = _Config()
