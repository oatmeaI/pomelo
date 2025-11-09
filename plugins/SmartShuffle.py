import random
import copy
import json

from melon.config import Config
from melon import constants
from melon.store import store
from plexapi.server import PlexServer, PlayQueue
from melon.util import bail, forwardRequest, requestToServer

PLUGIN_NAME = "SmartShuffle"
STATION_KEY = "smart"
HIJACK = "hijack"
DEFAULT_CONFIG = {
    "station_name": "Smart Shuffle",
    "chance_unheard": 30,
    "chance_fave": 30,
    "chance_new": 30,
}

#######
# Shuffles your entire library with a slight preference for unheard tracks and favorite
# tracks. No sonic similarity used, so you get the eclectic experience of full library
# shuffle. Weights (out of 100) for favorites and unheards can be tweaked in config. Random is chosen
# if neither of the other two are - so if you have a 35% chance for Fave and 35% chance
# for unheard (the defaults), you'd have a %30 chance for random.
######


def probably(chance):
    return random.random() < chance


class Plugin:
    _server = None
    queues = {}
    tracksByQueue = {}
    inflight = False
    favorites = 1  # Unused
    pivot = 10

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
        return {
            "hubs/sections/1": self.addExploreStation,
            "playQueues": self.startStation,
            f"playQueues/{str(queueId)}": self.handleQueue,
        }

    def addExploreStation(self, _, __, response):
        print("Adding station...")
        return self.addStation(self.config["station_name"], STATION_KEY, response)

    def addStation(self, name, key, response):
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
            bail()

    def startStation(self, path, request, response):
        # TODO: instead of try/except, detect the case correctly
        try:
            if (
                constants.URI_KEY in request.args
                and STATION_KEY in request.args[constants.URI_KEY]
                and HIJACK in request.args[constants.URI_KEY]
            ):
                print("starting smart shuffle")
                section = self.server().library.section(Config.musicSection)
                firstTrack = section.searchTracks(maxresults=1, sort="random")[0]
                tracks = [firstTrack]
                server = self.server()
                queue = PlayQueue.create(server, tracks)
                self.tracksByQueue[queue.playQueueID] = tracks

                prevTrack = firstTrack
                while len(self.tracksByQueue[queue.playQueueID]) < 2:
                    print("adding starter track")
                    prevTrack = self.getNextTrack(server, prevTrack, queue)
                    self.addTrackToQueue(queue, prevTrack)

                deviceId = request.args[constants.DEVICE_NAME_KEY]
                self.setQueueIdForDevice(deviceId, queue.playQueueID)
                return requestToServer(
                    f"playQueues/{str(queue.playQueueID)}", request.headers
                )
        except Exception as e:
            print(e)
            return response
        return response

    def getNextTrack(self, server, track, queue):
        print(self.config)
        CHANCE_UNHEARD = self.config["chance_unheard"]
        CHANCE_FAVE = self.config["chance_fave"]
        CHANCE_NEW = self.config["chance_new"]

        # TODO: this probability logic is a little jacked up, I don't think the
        # probabilities are being picked correctly since the two randoms are sequential

        section = self.server().library.section(Config.musicSection)
        if probably(CHANCE_NEW / 100):
            track = section.searchTracks(
                maxresults=1, sort="random", filters={"track.addedAt>>": "-30d"}
            )[0]
            print("new", track)
            return track
        elif probably(CHANCE_UNHEARD / 100):
            # get unheard track
            track = section.searchTracks(
                maxresults=1, sort="random", filters={"track.viewCount<<": 1}
            )[0]
            print("Unheard", track)
            return track
        elif probably(CHANCE_FAVE / 100):
            print("Fave")
            # get fave track
            return section.searchTracks(
                maxresults=1, sort="random", filters={"track.userRating>>": 1}
            )[0]
        else:
            print("Random")
            # get random track
            return section.searchTracks(maxresults=1, sort="random")[0]

    def handleQueue(self, path, request, response):
        queueId = str(self.getQueueIdForRequest(request))
        print(queueId, path)
        if queueId in path and not self.inflight:
            try:
                print("checking if we should add to queue")
                self.inflight = True
                server = self.server()
                queueId = self.getQueueIdForRequest(request)
                queue = PlayQueue.get(server, queueId)
                pos = (
                    len(self.tracksByQueue[queueId]) - queue.playQueueSelectedItemOffset
                )
                while pos < 15:
                    print("pos", pos)
                    track = self.tracksByQueue[queueId][-1]
                    nextTrack = self.getNextTrack(server, track, queue)
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
            return forwardRequest(request, path)
        return response
