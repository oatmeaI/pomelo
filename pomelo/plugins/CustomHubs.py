from pomelo.BasePlugin import BasePlugin


class Plugin(BasePlugin):
    DEFAULT_CONFIG = {"hubs": []}

    def paths(self):
        sections = []
        self.config["hubs"]
