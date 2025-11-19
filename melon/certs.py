import subprocess
from melon.config import Config
import xmltojson
import json
import hashlib
import platform
from pathlib import Path

home = Path.home()
system = platform.system()

PATHS = {
    "Darwin": {
        "prefs": f"{home}/Library/Preferences/com.plexapp.plexmediaserver.plist",
        "certs": f"{home}/Library/Caches/PlexMediaServer/certificate.p12",
    },
    "Linux": {
        "prefs": "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Preferences.xml".replace(
            " ", "\\ "
        ),
        "certs": "/var/lib/plexmediaserver/Library/Application Support/Plex Media Server/Cache/cert-v2.p12".replace(
            " ", "\\ "
        ),
    },
}

cert_path = f"{Config.config_dir}/cert.pem"
key_pem_path = f"{Config.config_dir}/key.pem"
key_path = f"{Config.config_dir}/server.key"


def read_prefs_darwin():
    path = PATHS["Darwin"]["prefs"]
    r = subprocess.run(
        ["plutil", "-convert", "json", "-o", "-", path],
        capture_output=True,
    )
    prefs = json.loads(r.stdout.decode("utf-8"))
    return prefs


def read_prefs_linux():
    path = PATHS["Linux"]["prefs"]
    with open(path, "r") as f:
        my_xml = f.read()
        prefs = xmltojson.parse(my_xml)
        return prefs["Preferences"]


read_prefs = {"Darwin": read_prefs_darwin, "Linux": read_prefs_linux}


def p12_password():
    prefs = read_prefs[system]()
    id = (
        prefs["ProcessedMachineIdentifier"]
        if "ProcessedMachineIdentifier"
        else prefs["@ProcessedMachineIdentifier"]
    )
    return hashlib.sha512(f"plex{id}".encode("utf-8")).hexdigest()


def create_cert_pem(password):
    path = PATHS[system]["certs"]
    subprocess.run(
        [
            "openssl",
            "pkcs12",
            "-in",
            path,
            "-clcerts",
            "-nokeys",
            "-out",
            cert_path,
            "-password",
            f"pass:{password}",
        ],
    )


def create_key_pem(password):
    path = PATHS[system]["certs"]
    subprocess.run(
        [
            "openssl",
            "pkcs12",
            "-in",
            path,
            "-nocerts",
            "-out",
            key_pem_path,
            "-password",
            f"pass:{password}",
            "-passout",
            "pass:pomelo",
        ],
    )


def create_server_key():
    subprocess.run(
        [
            "openssl",
            "rsa",
            "-in",
            key_pem_path,
            "-out",
            key_path,
            "-passin",
            "pass:pomelo",
        ],
    )


def create_certs():
    password = p12_password()
    create_cert_pem(password)
    create_key_pem(password)
    create_server_key()
