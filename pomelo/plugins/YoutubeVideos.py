import json
import urllib.parse
import requests
import yt_dlp

from pomelo.config import Config
from pomelo.BasePlugin import BasePlugin
from youtube_search import YoutubeSearch

# LATER
# - get correct title
# - pick higher quality streams if when available
# - make it work on other clients (and safari)
# - can I make it so search results don't change after a video is stopped?

# Desktop client throws FFMpeg errors when we try to use HTTPS, so serve this one over http Problem is serviing "localhost" isn't gonna work in the long run when we're running on a
# different machine than the server...need to find a workaround TODO
# It also doesn't work to serve HTTP on app.plex.tv because CORS disallows fetching HTTP
# resources from an HTTPS origin

STREAM_ENDPOINT = "/stream"
METADATA_ENDPOINT = "/library/metadata/youtube"


class Plugin(BasePlugin):
    PLUGIN_NAME = "YoutubeVideos"
    DEFAULT_CONFIG = {
        "artist": [
            {
                "query": "%title% band music video",
                "kind": "musicVideo",
                "max_results": 5,
            },
            {
                "query": "%title% band interview",
                "kind": "behindTheScenes",
                "max_results": 5,
            },
        ],
        "movie": [
            {
                "query": "%title% making of",
                "kind": "behindTheScenes",
                "max_results": 5,
            },
        ],
    }

    def paths(self):
        routes = {
            "/library/metadata/<id>": self.add_extras,
            METADATA_ENDPOINT: self.return_stream,
            "/playQueues": self.play_video,
            STREAM_ENDPOINT: self.stream,
            "/library/metadata/<id>/extras": self.extras_endpoint,
        }
        return routes

    def stream(self, path, request, response):
        url = urllib.parse.unquote(request.args["url"])
        res = requests.get(url)
        excluded_headers = ["connection", "expires"]
        headers = [
            (k, v) for k, v in res.headers.items() if k.lower() not in excluded_headers
        ]
        headers.append(("access-control-allow-origin", "*"))
        return (res.content, res.status_code, headers)

    def play_video(self, path, request, response):
        if "youtube" not in request.args["uri"]:
            return response

        # TODO: this is silly
        id = request.args["uri"].split("/")[-1].replace("youtube?id=", "")

        content = json.loads(response.content)
        content["MediaContainer"] = {
            "playQueueID": 999,
            "playQueueSelectedItemID": 1,
            "playQueueSelectedItemOffset": 0,
            "Metadata": [
                {
                    "playQueueItemID": 1,
                    "key": self.build_metadata_key(id),
                    # TODO: getting the video title here is a pain.
                    # "title": "The Lord Of The Rings: The Fellowship Of The Ring",
                    "type": "clip",
                    "Media": [
                        {
                            "id": 1,
                        }
                    ],
                }
            ],
        }

        response._content = json.dumps(content)
        return response

    def build_metadata_key(self, id):
        return f"{METADATA_ENDPOINT}?id={id}"

    def return_stream(self, path, request, response):
        with yt_dlp.YoutubeDL({}) as ydl:
            id = request.args["id"]
            info = ydl.extract_info(
                "https://www.youtube.com/watch?v=" + id, download=False
            )
            streams = [
                format
                for format in info["formats"][::-1]
                if format["vcodec"] != "none"
                and format["acodec"] != "none"
                and format["ext"] == "mp4"
                and format["protocol"] == "https"
            ]
            stream_url = streams[0]["url"]
            stream_url = (
                f"{STREAM_ENDPOINT}?url={urllib.parse.quote(stream_url, safe='')}"
            )
            container = "mp4"

            return {
                "size": 1,
                "Metadata": [
                    {
                        "key": self.build_metadata_key(id),
                        "ratingKey": id,
                        "guid": stream_url,
                        "title": info["title"],
                        "index": 1,
                        "Media": [
                            {
                                "id": 999,
                                "container": container,
                                "Part": [
                                    {
                                        "id": 999,
                                        "file": stream_url,
                                        "key": stream_url,
                                        "container": container,
                                        "optimizedForStreaming": True,
                                    }
                                ],
                            },
                        ],
                    }
                ],
            }

    def build_extras(self, entityType, title):
        searches = self.config[entityType] if entityType in self.config else []
        extras = []
        for search in searches:
            term = search["query"].replace("%title%", title)
            results = YoutubeSearch(term, max_results=search["max_results"]).to_dict()
            for result in results:
                extras.append(
                    {
                        "key": self.build_metadata_key(result["id"]),
                        "type": "clip",
                        "title": result["title"],
                        "index": 1,
                        "thumb": result["thumbnails"][0],
                        "subtype": search["kind"],
                        "extraType": 4,
                    }
                )
        return extras

    def prep_content(self, extras_container, extras_list):
        if "Metadata" not in extras_container:
            extras_container["Metadata"] = []
            extras_container["size"] = 0

        for extra in extras_list:
            extras_container["Metadata"].append(extra)
            extras_container["size"] += 1

        return extras_container

    def add_extras(self, path, request, response, id):
        content = json.loads(response.content)
        title = content["MediaContainer"]["Metadata"][0]["title"]
        entityType = content["MediaContainer"]["Metadata"][0]["type"]
        extras = self.build_extras(entityType, title)

        self.prep_content(content["MediaContainer"]["Metadata"][0]["Extras"], extras)

        response._content = json.dumps(content)
        return response

    def extras_endpoint(self, path, request, response, id):
        remote_url = f"http://{Config.plex_host}:{Config.plex_port}{request.full_path.replace('/extras', '')}"
        req = requests.Request(
            method=request.method,
            url=remote_url,
            headers=request.headers,
            data=request.data,
        )
        with requests.Session() as s:
            resp = s.send(req.prepare(), stream=True)
            c = json.loads(resp.content)
            title = c["MediaContainer"]["Metadata"][0]["title"]
            entityType = c["MediaContainer"]["Metadata"][0]["type"]

            content = json.loads(response.content)
            extras = self.build_extras(entityType, title)

            self.prep_content(content["MediaContainer"], extras)

            response._content = json.dumps(content)
            return response
