from pomelo.config import Config


def wizard_init():
    print("===> Welcome to Pomelo! <===")


def wizard_config():
    print(f"->> Loaded config from {Config.config_file_path}")


def wizard_plugins():
    print("->> Enabled plugins: ", Config.enabled_plugins)


def wizard_caddy():
    proxy_host = Config.caddy_listen_port
    print(f"->> Reverse proxy configured at {proxy_host}")


def wizard_app():
    pomelo_port = Config.pomelo_port
    print(f"->> Starting Pomelo on port {pomelo_port}")
