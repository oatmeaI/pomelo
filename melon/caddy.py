import requests
import subprocess
import atexit
import time
import platform

from melon.config import Config
from melon.wizard import wizard_caddy
from melon.strings import warn, log, confirm


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
        try:
            update_config(jsonConfig)
        except Exception as e:
            # TODO:
            print(
                "Caddy problem, could be nothing - add better logs here and try to fix it"
            )

    log(
        "In order to force Plex to connect through Pomelo, we usually need to set up a firewall to block port 32400 for all origins except localhost."
    )
    log(
        "If you have pfctl or iptables installed (on macOS and most Linux distros, you will have one), Pomelo can try to configure this for you. (If you're not sure if you have one of these tools installed, Pomelo will check for you)."
    )
    try_firewall = confirm(
        "Would you like Pomelo to try to configure the firewall? It will be turned off when Pomelo quits. (This will require root privileges)"
    )
    if try_firewall:
        try:
            system = platform.system()
            if system == "Darwin":
                add_firewall_pfctl()
            elif system == "Linux":
                add_firewall_iptables()
            else:
                warn(
                    "Unable to configure firewall on Windows yet - please block port 32400 for all origins except localhost manually"
                )
        except Exception as e:
            warn(
                "Pomelo was unable to configure the firewall automatically, please set it up manually."
            )

    wizard_caddy()


def del_firewall_iptables():
    subprocess.run(
        [
            "sudo",
            "iptables",
            "-D",
            "OUTPUT",
            "-p",
            "tcp",
            "--dport",
            "32400",
            "-j",
            "DROP",
        ]
    )
    subprocess.run(
        [
            "sudo",
            "iptables",
            "-D",
            "INPUT",
            "-i",
            "lo",
            "-p",
            "tcp",
            "--sport",
            "32400",
            "-j",
            "ACCEPT",
        ]
    )


def add_firewall_iptables():
    subprocess.run(
        [
            "sudo",
            "iptables",
            "-A",
            "OUTPUT",
            "-p",
            "tcp",
            "--dport",
            "32400",
            "-j",
            "DROP",
        ]
    )
    subprocess.run(
        [
            "sudo",
            "iptables",
            "-A",
            "INPUT",
            "-i",
            "lo",
            "-p",
            "tcp",
            "--sport",
            "32400",
            "-j",
            "ACCEPT",
        ]
    )
    atexit.register(del_firewall_iptables)


# iptables -A OUTPUT -p tcp --dport 32400 -j DROP
# iptables -A INPUT -i lo -p tcp --sport 32400 -j ACCEPT


def add_firewall_pfctl():
    rules = """
block drop out proto tcp from any to any port 32400
pass out proto tcp from 127.0.0.1 to any port 32400
"""
    payload = subprocess.run(
        ["cat", "/etc/pf.conf", "-"], input=rules.encode("utf-8"), capture_output=True
    ).stdout
    subprocess.run(["sudo", "pfctl", "-f", "-"], input=payload)
    atexit.register(del_firewall_pfctl)


def del_firewall_pfctl():
    subprocess.run(["sudo", "pfctl", "-f", "/etc/pf.conf"])


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
