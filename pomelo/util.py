import time
import requests
from flask import abort
from plexapi.server import PlexServer
from pomelo.constants import TOKEN_KEY
from pomelo.config import Config

excluded_headers = [
    "content-encoding",
    "content-length",
    "transfer-encoding",
    "connection",
    "keep-alive",
]


def buildResponse(response):
    headers = [
        (k, v) for k, v in response.headers.items() if k.lower() not in excluded_headers
    ]

    return (
        response.content,
        response.status_code,
        headers,
    )


def createServer():
    s = None
    while s is None:
        try:
            s = PlexServer(
                f"http://{Config.plex_host}:{Config.plex_port}", Config.plex_token
            )
        except Exception as e:
            time.sleep(1)
    return s


def bail():
    return abort(501)


def requestToServer(endpoint, _headers):
    remote_url = f"http://{Config.plex_host}:{Config.plex_port}/{endpoint}"

    # Create a new headers obj since sometimes what we get passed in is immutable
    headers = {}
    headers[TOKEN_KEY] = Config.plex_token
    for k, v in _headers.items():
        if k in excluded_headers:
            continue
        headers[k] = v

    esreq = requests.Request(
        method="get",
        url=remote_url,
        headers=headers,
    )
    with requests.Session() as s:
        resp = s.send(esreq.prepare(), stream=True)
        return resp


def forwardRequest(request, path):
    query_string = request.query_string.decode()
    remote_url = f"http://{Config.plex_host}:{Config.plex_port}/{path}?{query_string}"
    req = requests.Request(
        method=request.method,
        url=remote_url,
        headers=request.headers,
        data=request.data,
    )
    with requests.Session() as s:
        resp = s.send(req.prepare(), stream=True)
        return resp
