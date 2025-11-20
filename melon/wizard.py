from melon.config import Config
from melon.util import createServer


def wizard_init():
    print("===> Welcome to Pomelo! <===")


def wizard_config():
    print(f"\t ->> Loaded config from {Config.config_file_path}")


def wizard_plugins():
    print("\t ->> Enabled plugins: ", Config.enabled_plugins)


def wizard_caddy():
    proxy_host = Config.caddy_listen_port
    print(f"\t ->> Reverse proxy configured at {proxy_host}")


def wizard_app():
    pomelo_port = Config.pomelo_port
    print(f"\t ->> Starting Pomelo on port {pomelo_port}")


def wizard_proxy():
    caddy_listen_port = Config.caddy_listen_port
    plex_host = Config.plex_host
    plex_port = Config.plex_port

    server = createServer()
    id = server.machineIdentifier

    print(f"\nGo to http://localhost:{caddy_listen_port}")
    print("\n===> First Time Setup <===")
    print("\t (If you've already done this, you can safely ignore these steps)")
    print(
        f"\t 1. Go to http://{plex_host}:{plex_port}/web/index.html#!/settings/server/{id}/settings/network"
    )
    print("\t 2. Click 'Show advanced' at the top of the page")
    print("\t 3. Scroll down until you find the 'Custom server access URLs'")
    print(
        f"\t 4. Enter http://{caddy_listen_port} in the text box, and click Save Changes."
    )

    #     f"\t\t Note: http://{caddy_listen_port} should be accessible from the internet. You may need to forward port {proxy_port if proxy_port else '443'} to this machine on your router."
    # )
    print(
        f"\t 5. Go to http://{caddy_listen_port}. If everything worked, you should see your Plex server!"
    )
    print("\n")
