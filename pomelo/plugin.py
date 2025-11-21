import importlib
from pomelo.constants import PLUGIN_NAMESPACE
from pomelo.config import Config
from pomelo.wizard import wizard_plugins


def init_plugins():
    plugins = []
    wizard_plugins()
    for plugin_name in Config.enabled_plugins:
        pluginModule = importlib.import_module(f"{PLUGIN_NAMESPACE}.{plugin_name}")
        plugin = pluginModule.Plugin()
        plugins.append(plugin)

    return plugins
