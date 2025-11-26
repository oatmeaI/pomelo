import requests
import os.path

from pomelo.certs import create_certs, cert_path, key_path
from pomelo.config import Config


def init_caddy():
    caddy_admin_url = Config.caddy_admin_url
    caddy_listen_port = Config.caddy_listen_port
    pomelo_port = Config.pomelo_port
    plex_host = Config.plex_host
    plex_port = Config.plex_port

    if not os.path.isfile(cert_path) or not os.path.isfile(key_path):
        create_certs()

    payload = f"""
:{caddy_listen_port} {{ 
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
        url=f"{caddy_admin_url}/load",
        data=payload,
    )

    response.raise_for_status()
