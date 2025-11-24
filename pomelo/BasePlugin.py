from pomelo.config import Config
from pomelo.util import createServer


class BasePlugin:
    _server = None
    DEFAULT_CONFIG = {}
    PLUGIN_NAME = "BasePlugin"

    @property
    def config(self):
        return self.DEFAULT_CONFIG | Config.getPluginSettings(self.PLUGIN_NAME)

    @property
    def server(self):
        if self._server is None:
            self._server = createServer()
        return self._server
