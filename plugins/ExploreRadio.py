import random
import json
import copy

from plexapi.server import PlayQueue, PlexServer
from melon import constants
from melon.config import Config
from melon.store import store
from melon.util import bail, forwardRequest, requestToServer


PLUGIN_NAME = "ExploreRadio"
HIJACK = "hijack"
STATION_KEY = "explore"
DEFAULT_CONFIG = {"station_name": "Explore Radio"}


def probably(chance):
    return random.random() < chance


class Plugin:
    _server = None
    queues = {}
    tracksByQueue = {}
    inflight = False
    favorites = 1

    def __init__(self):
        _config = Config.getPluginSettins(PLUGIN_NAME)
        self.config = _config if _config else DEFAULT_CONFIG

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

    def server(self):
        if self._server is None:
            self._server = PlexServer(
                f"{Config.serverAddress}:{Config.serverPort}", store.token
            )
        return self._server

    def paths(self, request):
        queueId = self.getQueueIdForRequest(request)
        return {
            "hubs/sections/1": self.addExploreStation,
            "playQueues": self.startStation,
            f"playQueues/{str(queueId)}": self.playQueues,
        }

    def addExploreStation(self, path, request, response):
        print("Adding station...")
        return self.addStation(
            self.config["station_name"], STATION_KEY, path, request, response
        )

    def playQueues(self, path, request, response):
        queueId = str(self.getQueueIdForRequest(request))
        print("checking queue", queueId, path, self.inflight)
        if queueId in path and not self.inflight:
            print("checking if we should add to queue")
            self.inflight = True
            try:
                self.handleQueue(request)
            except Exception as e:
                print(e)
                self.inflight = False
                raise e
            self.inflight = False
            # refresh the response since we changed the queue
            return forwardRequest(request, path)

        return response

    def startStation(self, path, request, response):
        if (
            constants.URI_KEY in request.args
            and STATION_KEY in request.args[constants.URI_KEY]
            and HIJACK in request.args[constants.URI_KEY]
        ):
            print("Starting cool station...")
            print(store.token)
            section = self.server().library.section(Config.musicSection)

            # TODO: pick this in a smarter way
            firstTrack = section.searchTracks(maxresults=1, sort="random")[0]
            tracks = [firstTrack]
            server = self.server()
            queue = PlayQueue.create(server, tracks)
            self.tracksByQueue[queue.playQueueID] = tracks

            prevTrack = firstTrack
            while len(queue.items) < 3:
                prevTrack = self.getNextTrack(server, prevTrack, queue)
                self.addTrackToQueue(queue, prevTrack)

            deviceId = request.args[constants.DEVICE_NAME_KEY]
            self.setQueueIdForDevice(deviceId, queue.playQueueID)
            return requestToServer(
                f"playQueues/{str(queue.playQueueID)}", request.headers
            )
        return response

    def handleQueue(self, request):
        print("adding cool track")
        server = self.server()
        queueId = self.getQueueIdForRequest(request)
        queue = PlayQueue.get(server, queueId)
        pos = len(self.tracksByQueue[queueId]) - queue.playQueueSelectedItemOffset
        print("pos", pos)
        while pos < 15:
            print("pos", pos)
            track = self.tracksByQueue[queueId][-1]
            nextTrack = self.getNextTrack(server, track, queue)
            self.addTrackToQueue(queue, nextTrack)
            pos = len(self.tracksByQueue[queueId]) - queue.playQueueSelectedItemOffset

    # TODO: from here down is a real mess
    def addStation(self, name, key, path, request, response):
        try:
            j = json.loads(response.content)
            for hub in j["MediaContainer"]["Hub"]:
                if hub["title"] == "Stations":
                    hub["size"] = 5
                    first = copy.deepcopy(hub["Metadata"][0])
                    first["title"] = name
                    first["guid"] = "hijack://station/" + key
                    first["key"] = "/hijack/stations/" + key

                    hub["Metadata"].insert(0, first)

            response._content = json.dumps(j)
            return response
        except Exception as e:
            bail(request, path)

    def addTrackToQueue(self, queue, track):
        self.tracksByQueue[queue.playQueueID].append(track)
        queue.addItem(track)

    def getNextTrack(self, server, track, queue):
        tracks = track.sonicallySimilar(maxDistance=0.4)
        # make an unheard song more likely the more favorites in a row
        rand = random.randint(0, self.favorites)
        print(queue)
        queueItems = self.tracksByQueue[queue.playQueueID]
        unheard = True if self.favorites else probably(50 / 100)

        if not unheard:
            self.favorites = True
        else:
            self.favorites = False

        type = "unheard" if unheard else "favorited"
        # TODO: super dumb

        lastThreeAlbums = [track.grandparentTitle for track in queueItems[-3:]]
        print(lastThreeAlbums)

        filtered = list(
            filter(
                lambda t: t not in queueItems
                and (
                    t.viewCount < 1
                    if unheard
                    else t.userRating is not None and t.userRating > 0
                )
                and t.grandparentTitle
                not in lastThreeAlbums,  # Avoid adding two tracks by the same artist in three songs
                tracks,
            )
        )

        if len(filtered) < 1:
            unheard = not unheard
            type = "fell thru to unheard" if unheard else "fell thru to favorited"
            filtered = list(
                filter(
                    lambda t: t not in queueItems
                    and (
                        t.viewCount < 1
                        if unheard
                        else t.userRating is not None and t.userRating > 0
                    )
                    and t.grandparentTitle
                    not in lastThreeAlbums,  # Avoid adding two tracks by the same artist in three songs
                    tracks,
                )
            )

        if len(filtered) < 1:
            type = "fell through to rando"
            section = server.library.section(Config.musicSection)
            filtered = [section.searchTracks(maxresults=1, sort="random")[0]]

        print(type + ": ", filtered[0])
        return filtered[0]
