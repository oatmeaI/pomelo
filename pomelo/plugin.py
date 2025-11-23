import importlib
import sys
from pomelo.config import Config
from pomelo.wizard import wizard_plugins


def init_plugins():
    sys.path.append("/pomelo/plugins")
    plugins = []
    wizard_plugins()
    for plugin_name in Config.enabled_plugins:
        pluginModule = importlib.import_module(f"{plugin_name}")
        plugin = pluginModule.Plugin()
        plugins.append(plugin)

    return plugins
