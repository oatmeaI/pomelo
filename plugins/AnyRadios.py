import random
import copy
import json
from random import choices

from melon.config import Config
from melon import constants
from melon.store import store
from plexapi.server import PlexServer, PlayQueue
from melon.util import bail, forwardRequest, requestToServer

PLUGIN_NAME = "AnyRadios"
HIJACK = "hijack"
FILTERS = {"recentlyFaved": {"track.lastRatedAt>>": "-30d", "track.userRating>>": 1}}
DEFAULT_CONFIG = {
    "length": 50,
    "stations": [
        {
            "station_name": "test station",
            "key": "test",
            "sources": [
                {
                    "name": "recent release faves",
                    "filters": {
                        "track.userRating>>": 1,
                    },
                    "sort": "album.originallyAvailableAt:asc",
                    "aux_weight": 0.01,
                    "chance": 0.5,
                },
            ],
        },
        {
            "station_name": "Recent Releases (30d, prefer fave or unplayed)",
            "key": "recentreleases",
            "description": "Tracks from albums released in the past month",
            "sources": [
                {
                    "name": "recent release faves",
                    "filters": {
                        "album.originallyAvailableAt>>": "-30d",
                        "track.userRating>>": 1,
                    },
                    "chance": 0.35,
                },
                {
                    "name": "recent release new",
                    "filters": {
                        "album.originallyAvailableAt>>": "-30d",
                        "track.viewCount<<": 1,
                    },
                    "chance": 0.35,
                },
                {
                    "name": "recent release rand",
                    "filters": {
                        "album.originallyAvailableAt>>": "-30d",
                    },
                    "chance": 0.3,
                },
            ],
        },
        {
            "station_name": "New Faves (Faved in the 30d, weighted toward newly added)",
            "key": "newfaves",
            "description": "Favorited in the past month, prefer recently added",
            "sources": [
                {
                    "name": "freshlove",
                    "filters": {"track.addedAt>>": "-30d", "track.userRating>>": 1},
                    "chance": 0.5,
                },
                {
                    "name": "newlove",
                    "filters": FILTERS["recentlyFaved"],
                    "chance": 0.5,
                },
            ],
        },
        {
            "station_name": "Fresh Tracks (60d + unplayed or faved, or random)",
            "key": "freshtracks",
            "description": "Added in the past two monthes, and unplayed or favorited",
            "sources": [
                {
                    "name": "random",
                    "filters": {},
                    "chance": 0.10,
                },
                {
                    "name": "newunplayed",
                    "filters": {"track.addedAt>>": "-30d", "track.viewCount<<": 1},
                    "chance": 0.50,
                },
                {
                    "name": "newloved",
                    "filters": {"track.addedAt>>": "-30d", "track.userRating>>": 1},
                    "chance": 0.40,
                },
            ],
        },
        {
            "station_name": "Smart Shuffle (New, unplayed, faved & random)",
            "key": "smartshuffle",
            "sources": [
                # TODO: this is still a little jacked up - relies on the fact that we
                # iterate in order - each of these sources has a 30% chance of being
                # picked except for the last one, which is the remainder.
                # Surely there is a better way to do this
                {
                    "name": "newadd",
                    "filters": {"track.addedAt>>": "-90d"},
                    "chance": 0.31,
                },
                {
                    "name": "unplayed",
                    "filters": {"track.viewCount<<": 1},
                    "chance": 0.29,
                },
                {
                    "name": "faves",
                    "filters": {"track.userRating>>": 1},
                    "chance": 0.32,
                    "sort": "track.lastViewedAt:asc",
                    "aux_weight": 0.005,
                },
                # TODO: Enforce a default like this
                {"name": "random", "filters": {}, "chance": 0.08},
            ],
        },
    ],
}

# TODO: create a "sonicallySimilar" source
# TODO: fallback if no track matches filters


def pick(sources):
    weights = [s["chance"] for s in sources]
    source = choices(sources, weights=weights)[0]
    return source


class Plugin:
    _server = None
    queues = {}
    tracksByQueue = {}
    stationsByQueue = {}
    inflight = False
    totals = {}

    def __init__(self):
        _config = Config.getPluginSettins(PLUGIN_NAME)
        self.config = _config if _config else DEFAULT_CONFIG

    def server(self):
        if self._server is None:
            self._server = PlexServer(
                f"{Config.serverAddress}:{Config.serverPort}", store.token
            )
        return self._server

    def setQueueIdForDevice(self, device, queueId):
        self.queues[device] = queueId

    def getQueueIdForRequest(self, request):
        deviceId = (
            request.args[constants.DEVICE_NAME_KEY]
            if constants.DEVICE_NAME_KEY in request.args
            else None
        )
        if deviceId and deviceId in self.queues:
            return self.queues[deviceId]
        return ""

    def addTrackToQueue(self, queue, track):
        self.tracksByQueue[queue.playQueueID].append(track)
        queue.addItem(track)

    def paths(self, request):
        queueId = self.getQueueIdForRequest(request)
        # print(request)
        return {
            "hubs/sections/1": self.addStations,
            "playQueues": self.startStation,
            f"playQueues/{str(queueId)}": self.handleQueue,
        }

    def addStations(self, _, __, response):
        print("Adding stations...")
        try:
            stations = self.config["stations"]
            j = json.loads(response.content)
            # TODO: janky & slow
            # Completely hijacks Mixes For You section
            # Stations section does this annoying thing where Plexamp adds stuff at the
            # front every time, so we're taking over a different hub that we can control
            # more fully
            # TODO: might be possible to fully add our own hub, not sure
            example = None
            for hub in j["MediaContainer"]["Hub"]:
                if hub["title"] == "Stations":
                    example = copy.deepcopy(hub["Metadata"][0])
            if example is None:
                return
            for hub in j["MediaContainer"]["Hub"]:
                if hub["title"] == "Mixes For You":
                    hub["title"] = "Your Stations"
                    hub["size"] = 0
                    hub["Metadata"] = []
                    for station in stations:
                        hub["size"] += 1
                        key = station["key"]
                        first = copy.deepcopy(example)
                        first["title"] = station["station_name"]
                        first["guid"] = "hijack://station/" + key
                        first["key"] = "/hijack/stations/" + key
                        first["summary"] = (
                            station["description"] if "description" in station else ""
                        )

                        hub["Metadata"].insert(0, first)
                        print("Adding station to mixes hub")

            response._content = json.dumps(j)
            return response
        except Exception as e:
            print(e)
            bail()

    def startStation(self, path, request, response):
        try:
            if (
                constants.URI_KEY not in request.args
                or HIJACK not in request.args[constants.URI_KEY]
            ):
                return response

            for station in self.config["stations"]:
                if station["key"] not in request.args[constants.URI_KEY]:
                    continue

                self.totals = {}

                length = self.config["length"]
                sources = station["sources"]
                section = self.server().library.section(Config.musicSection)

                pool = []
                weights = []

                for source in sources:
                    sort = source["sort"] if "sort" in source else "random"
                    aux_weight_start = (
                        source["aux_weight"] if "aux_weight" in source else 0.0
                    )
                    aux_weight = aux_weight_start
                    filters = source["filters"]
                    tracks = section.searchTracks(
                        maxresults=length, sort=sort, filters=filters
                    )
                    for track in tracks:
                        pool.append(track)
                        weights.append(source["chance"] + aux_weight)
                        aux_weight += aux_weight_start

                tracks = list(set(choices(pool, weights=weights, k=length)))

                server = self.server()
                queue = PlayQueue.create(server, tracks)
                self.tracksByQueue[queue.playQueueID] = tracks

                deviceId = request.args[constants.DEVICE_NAME_KEY]
                self.setQueueIdForDevice(deviceId, queue.playQueueID)
                self.stationsByQueue[queue.playQueueID] = station

                return requestToServer(
                    f"playQueues/{str(queue.playQueueID)}", request.headers
                )
        except Exception as e:
            print(e)
            return response
        return response

    def getNextTrack(self, station):
        sources = station["sources"]
        section = self.server().library.section(Config.musicSection)
        source = pick(sources)
        filters = source["filters"]
        sort = source["sort"] if "sort" in source else "random"
        track = section.searchTracks(maxresults=1, sort=sort, filters=filters)[0]

        name = source["name"]
        if name not in self.totals:
            self.totals[name] = 0

        self.totals[name] += 1
        return track

    def handleQueue(self, path, request, response):
        queueId = str(self.getQueueIdForRequest(request))
        if queueId in path and not self.inflight:
            try:
                self.inflight = True
                server = self.server()
                queueId = self.getQueueIdForRequest(request)
                queue = PlayQueue.get(server, queueId)
                pos = (
                    len(self.tracksByQueue[queueId]) - queue.playQueueSelectedItemOffset
                )
                while pos < 15:
                    station = self.stationsByQueue[queueId]
                    nextTrack = self.getNextTrack(station)
                    self.addTrackToQueue(queue, nextTrack)
                    pos = (
                        len(self.tracksByQueue[queueId])
                        - queue.playQueueSelectedItemOffset
                    )
            except Exception as e:
                print(e)
                self.inflight = False
                raise e
            self.inflight = False
            # refresh the response since we changed the queue
            return response
            return forwardRequest(request, path)
        return response
