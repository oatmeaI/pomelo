import requests
import subprocess
import atexit
import time

from melon.config import Config
from melon.wizard import wizard_caddy


def quit_caddy():
    subprocess.run(["caddy", "stop"])


def init_caddy():
    caddy_url = Config.caddy_url

    config_url = f"{caddy_url}/config/"

    try:
        config = requests.request(method="GET", url=config_url)
    except Exception as e:
        # TODO log to a file instead of dev null
        subprocess.run(["caddy", "start"], stderr=subprocess.DEVNULL)
        atexit.register(quit_caddy)
        time.sleep(2)  # Wait for Caddy to boot
        config = requests.request(method="GET", url=config_url)

    jsonConfig = config.json()

    if jsonConfig is None:
        init_config()
    else:
        update_config(jsonConfig)

    wizard_caddy()


def init_config():
    caddy_url = Config.caddy_url
    proxy_host = Config.proxy_host
    pomelo_port = Config.pomelo_port
    plex_host = Config.plex_host
    plex_port = Config.plex_port

    payload = f"""
{proxy_host} {{ 
    reverse_proxy localhost:{pomelo_port} {{
        @error status 501 500 502 404
        handle_response @error {{
            reverse_proxy {plex_host}:{plex_port} 
        }}
    }}
}}
"""

    response = requests.request(
        method="POST",
        headers={"Content-Type": "text/caddyfile"},
        url=f"{caddy_url}/load",
        data=payload,
    )
    response.raise_for_status()


def update_config(config):
    proxy_host = Config.proxy_host
    server_name = None
    for sname, server_config in config["apps"]["http"]["servers"].items():
        if ":443" in server_config["listen"]:
            server_name = sname

    if server_name is None and proxy_host is not None:
        add_server(":443")
        pass
    if proxy_host is None:
        add_server(proxy_host)
    else:
        add_route(server_name)


def route():
    proxy_host = Config.proxy_host
    plex_host = Config.plex_host
    plex_port = Config.plex_port
    pomelo_port = Config.pomelo_port
    return {
        "match": [{"host": [proxy_host]}],
        "handle": [
            {
                "handler": "subroute",
                "routes": [
                    {
                        "handle": [
                            {
                                "handle_response": [
                                    {
                                        "match": {"status_code": [501, 500, 502, 404]},
                                        "routes": [
                                            {
                                                "handle": [
                                                    {
                                                        "handler": "reverse_proxy",
                                                        "upstreams": [
                                                            {
                                                                "dial": f"{plex_host}:{plex_port}"
                                                            }
                                                        ],
                                                    }
                                                ]
                                            }
                                        ],
                                    }
                                ],
                                "handler": "reverse_proxy",
                                "upstreams": [{"dial": f"localhost:{pomelo_port}"}],
                            }
                        ]
                    }
                ],
            }
        ],
        "terminal": True,
    }


def add_server(listen):
    caddy_url = Config.caddy_url
    payload = {
        "listen": [listen],
        "routes": [
            {
                "handle": [
                    {
                        "handler": "subroute",
                        "routes": [{"handle": [{"handle_response": [route()]}]}],
                    }
                ]
            }
        ],
    }
    response = requests.request(
        method="PUT",
        headers={"Content-Type": "application/json"},
        url=f"{caddy_url}/config/apps/http/servers/pomelo",
        json=payload,
    )
    response.raise_for_status()


def add_route(server_name):
    caddy_url = Config.caddy_url

    payload = route()
    response = requests.request(
        method="PUT",
        headers={"Content-Type": "application/json"},
        url=f"{caddy_url}/config/apps/http/servers/{server_name}/routes/0",
        json=payload,
    )
    response.raise_for_status()
