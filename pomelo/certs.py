import subprocess
import xmltodict
import hashlib

prefs_path = "/config/Library/Application Support/Plex Media Server/Preferences.xml"
p12_path = "/config/Library/Application Support/Plex Media Server/Cache/cert-v2.p12"
cert_path = "/config/pomelo/cert.pem"
key_pem_path = "/config/pomelo/key.pem"
key_path = "/config/pomelo/server.key"


def read_prefs():
    with open(prefs_path, "r") as f:
        my_xml = f.read()
        prefs = xmltodict.parse(my_xml)
        return prefs["Preferences"]


def p12_password():
    prefs = read_prefs()
    id = prefs["@ProcessedMachineIdentifier"]
    return hashlib.sha512(f"plex{id}".encode("utf-8")).hexdigest()


def create_cert_pem(password):
    subprocess.run(
        [
            "openssl",
            "pkcs12",
            "-in",
            p12_path,
            "-clcerts",
            "-nokeys",
            "-out",
            cert_path,
            "-password",
            f"pass:{password}",
        ],
    )


def create_key_pem(password):
    subprocess.run(
        [
            "openssl",
            "pkcs12",
            "-in",
            p12_path,
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
