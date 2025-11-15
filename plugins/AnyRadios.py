import json
import datetime
from random import choices, shuffle

from plexapi.server import PlayQueue

from melon.config import Config
from melon import constants
from melon.util import createServer, requestToServer

# Anything not listed here will default to 0
FIELD_MINIMUMS = {
    "addedAt": datetime.datetime.min,
    "lastViewedAt": datetime.datetime.min,
    "lastRatedAt": datetime.datetime.min,
}

PLUGIN_NAME = "AnyRadios"
DEFAULT_CONFIG = {
    "length": 100,
    "stations": [
        {
            "name": "Smart Shuffle",
            "key": "shuffle",
            "sources": [
                {
                    "name": "random",
                    "filters": {},
                    "sort": "userRating",
                    "sort_weight": 1,
                    "chance": 2,
                },
                {
                    "name": "new",
                    "filters": {"track.addedAt>>": "-30d"},
                    "chance": 2,
                },
            ],
        }
    ],
    "hub_title": "Pomelo Stations",
}


class Plugin:
    _server = None
    inflight = False

    @property
    def config(self):
        return DEFAULT_CONFIG | Config.getPluginSettings(PLUGIN_NAME)

    def server(self):
        if self._server is None:
            self._server = createServer()
        return self._server

    def paths(self):
        return {
            "/hubs/sections/1": self.addStations,
            "/anyradios": self.returnStations,
            "/playQueues": self.startStation,
        }

    def returnStations(self, path, request, response):
        items = self.buildStations()

        content = json.loads(response.content)
        content["MediaContainer"]["Metadata"] = items
        content["MediaContainer"]["size"] = len(items)
        content["MediaContainer"]["totalSize"] = len(items)

        response._content = json.dumps(content)
        return response

    def buildStations(self):
        stations = self.config["stations"]
        items = []
        for station in stations:
            key = station["key"]
            item = {
                "key": f"/hijack/stations/{key}",
                "guid": f"hijack://station/{key}",
                "type": "playlist",
                "title": station["name"],
                "smart": True,
                "playlistType": "audio",
                "leafCount": 0,
                "radio": "1",
                "icon": "playlist://image.smart",
            }
            items.append(item)
        return items

    def addStations(self, path, request, response):
        hub = {
            "title": self.config["hub_title"],
            "type": "album",
            "hubIdentifier": "anyradios",
            "context": "anyradios",
            "size": 0,
            "more": False,
            "style": "grid",
            "Metadata": [],
        }

        items = self.buildStations()
        hub["Metadata"] += items
        hub["size"] += len(items)

        content = json.loads(response.content)
        content["MediaContainer"]["Hub"].insert(0, hub)
        content["MediaContainer"]["size"] = content["MediaContainer"]["size"] + 1

        response._content = json.dumps(content)
        return response

    def startStation(self, _, request, response):
        if constants.URI_KEY not in request.args:
            return response

        station = next(
            (
                station
                for station in self.config["stations"]
                if station["key"] in request.args[constants.URI_KEY]
            ),
            None,
        )

        if station is None:
            return response

        length = self.config["length"]
        sources = station["sources"]
        section = self.server().library.section(Config.music_section_title)

        pool = []
        weights = []

        for source in sources:
            filters = source["filters"] if "filters" in source else {}
            tracks = section.searchTracks(
                maxresults=length, sort="random", filters=filters
            )

            if "sort" in source:
                sort_key = source["sort"]
                reverse = source["sort_reverse"]
                tracks.sort(
                    key=lambda track: getattr(track, sort_key)
                    or FIELD_MINIMUMS[sort_key]
                    or 0,
                    reverse=reverse,
                )

            sort_weight_max = source["sort_weight"] if "sort_weight" in source else 0.0
            sort_weight_start = sort_weight_max / len(tracks)
            sort_weight = 0.0

            for track in tracks:
                pool.append(track)
                weights.append(source["chance"] - sort_weight)
                sort_weight += sort_weight_start

        tracks = choices(pool, weights=weights, k=length)
        tracks = list(set(tracks))
        shuffle(tracks)  # set -> list changes the order, so we reshuffle

        server = self.server()
        queue = PlayQueue.create(server, tracks)

        return requestToServer(f"playQueues/{str(queue.playQueueID)}", request.headers)
