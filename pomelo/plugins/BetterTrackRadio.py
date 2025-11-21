import random

from pomelo.config import Config
from pomelo import constants
from plexapi.server import PlayQueue
from pomelo.util import createServer, forwardRequest, requestToServer

DEFAULT_CONFIG = {}
PLUGIN_NAME = "BetterTrackRadio"
PIVOT_CHANGE = 5  # Higher this is, the less likely you are to get two unheard or two favorites in a row


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
        _config = Config.getPluginSettings(PLUGIN_NAME)
        self.config = _config if _config else DEFAULT_CONFIG

    def server(self):
        if self._server is None:
            self._server = createServer()
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

    # TODO: fixme
    def paths(self):
        # queueId = self.getQueueIdForRequest(request)
        return {
            "/playQueues": self.startStation,
            # f"playQueues/{str(queueId)}": self.handleQueue,
        }

    def startStation(self, path, request, response):
        # TODO: instead of try/except, detect the case correctly
        try:
            if constants.URI_KEY in request.args:
                uri = request.args[constants.URI_KEY]
                a = uri.find("library/metadata/") + 17
                b = uri.find("/station/")
                if a < 0 or b < 0:
                    return response
                print("starting track station")
                ekey = int(uri[a:b])
                firstTrack = self.server().library.fetchItem(ekey)
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
        tracks = track.sonicallySimilar(maxDistance=0.35)
        # make an unheard song more likely the more favorites in a row
        rand = random.randint(0, 3)
        queueItems = self.tracksByQueue[queue.playQueueID]
        # print(rand, self.pivot)
        unheard = probably(60 / 100)
        type = "unheard" if unheard else "favorited"

        # TODO: super dumb
        filtered = list(
            filter(
                lambda t: t not in queueItems
                and (
                    t.viewCount < 1
                    if unheard
                    else t.userRating is not None and t.userRating > 0
                )
                and queue[-1].parentTitle
                != t.parentTitle,  # don't add two tracks from the same album back to back
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
                    and queue[-1].parentTitle
                    != t.parentTitle,  # don't add two tracks from the same album back to back
                    tracks,
                )
            )

        if len(filtered) < 1:
            type = "fell through to rando"
            section = server.library.section(Config.music_section_title)
            filtered = [section.searchTracks(maxresults=1, sort="random")[0]]

        print(type + ": ", filtered[0])
        if unheard:
            self.pivot = self.pivot - PIVOT_CHANGE
        else:
            self.pivot = self.pivot + PIVOT_CHANGE
        return filtered[0]

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
