import socket
from requests import get
from melon.config import Config
from melon.util import createServer


def wizard_init():
    print("===> Welcome to Pomelo! <===")


def wizard_config():
    print(f"\t ->> Loaded config from {Config.config_file_path}")


def wizard_plugins():
    print("\t ->> Enabled plugins: ", Config.enabled_plugins)


def wizard_caddy():
    proxy_host = Config.proxy_host
    print(f"\t ->> Reverse proxy configured at {proxy_host}")


def wizard_app():
    pomelo_port = Config.pomelo_port
    print(f"\t ->> Starting Pomelo on port {pomelo_port}")


def wizard_proxy():
    proxy_host = Config.proxy_host
    plex_host = Config.plex_host
    plex_port = Config.plex_port

    [proxy_host, proxy_port] = (
        proxy_host.split(":") if ":" in proxy_host else [proxy_host, ""]
    )

    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)

    if proxy_host == "":
        proxy_host = get("https://api.ipify.org").content.decode("utf8")

    if proxy_port != "":
        proxy_host = f"{proxy_host}:{proxy_port}"

    server = createServer()
    id = server.machineIdentifier
    # id = "asdf"
    print(f"\nGo to http://{local_ip}:{proxy_port}")
    print("\n===> First Time Setup <===")
    print("\t (If you've already done this, you can safely ignore these steps)")
    print(
        f"\t 1. Go to http://{plex_host}:{plex_port}/web/index.html#!/settings/server/{id}/settings/network"
    )
    print("\t 2. Click 'Show advanced' at the top of the page")
    print("\t 3. Scroll down until you find the 'Custom server access URLs'")
    print(f"\t 4. Enter http://{proxy_host} in the text box, and click Save Changes.")
    print(
        f"\t\t Note: http://{proxy_host} should be accessible from the internet. You may need to forward port {proxy_port if proxy_port else '443'} to this machine on your router."
    )
    print(
        f"\t 5. Go to http://{proxy_host}. If everything worked, you should see your Plex server!"
    )
    print("\n")
