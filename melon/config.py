import tomllib
import tomli_w
import os
from platformdirs import user_config_dir
from melon.constants import APP_NAME, CONFIG_FILE_NAME

DEFAULTS = {
    "serverAddress": "http://127.0.0.1",
    "serverPort": "32400",
    "musicSection": "Music",
    "debug": False,
    "enabled_plugins": ["ExploreRadio", "BetterTrackRadio", "SmartShuffle"],
    "port": 5200,
    "plugin_config": {},
    "token": None,
}


class _Config:
    def __init__(self):
        self.config_dir = user_config_dir(APP_NAME, ensure_exists=True)
        self.config_file_path = f"{self.config_dir}/{CONFIG_FILE_NAME}"

        if os.path.exists(self.config_file_path):
            with open(self.config_file_path, "rb") as f:
                self.data = tomllib.load(f)
        else:
            self.data = DEFAULTS

        self.serverAddress = self.loadSetting("serverAddress")
        self.serverPort = self.loadSetting("serverPort")
        self.musicSection = self.loadSetting("musicSection")
        self.debug = self.loadSetting("debug")
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


Config = _Config()
