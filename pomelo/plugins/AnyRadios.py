import concurrent.futures
import json

from random import choices
from rich.table import Table
from rich.console import Console
from plexapi.server import PlayQueue

from pomelo.BasePlugin import BasePlugin
from pomelo import constants
from pomelo.util import requestToServer


class Plugin(BasePlugin):
    PLUGIN_NAME = "AnyRadios"
    DEFAULT_CONFIG = {
        "length": 100,
        "enabled_sections": [],
        "stations": [
            {
                "name": "Smart Shuffle",
                "key": "shuffle",
                "sources": [
                    {
                        "name": "random",  # Not used except in logging; required
                        "filters": {},
                        "weight": "track.userRating:desc",  # Weights tracks in source from most likely to least likely, based on key defined
                        "weight_factor": 2,  # How much more likely the first track is than the last
                        "chance": 50,  # How likely this source is to be chosen. No requirements, but it is easier to think about if they add up to 100
                    },
                    {
                        "name": "new",
                        "filters": {"track.addedAt>>": "-30d"},
                        "sort": "track.addedAt:desc",  # Sort: sorts query from plexapi, instead of random order
                        "length": 50,  # Overrides top-level length setting. Should equal at least percentage chance x top level length to ensure there are enough tracks. In this case .5 x 100.
                        "chance": 50,
                    },
                ],
            }
        ],
        "hub_title": "Pomelo Stations",
    }
    inflight = False

    def paths(self):
        sections = self.config["enabled_sections"]
        if len(sections) < 1:
            all_sections = self.server.library.sections()
            sections = [s.key for s in all_sections if s.TYPE == "artist"]

        routes = {
            "/anyradios": self.returnStations,
            "/playQueues": self.startStation,
        }
        for section in sections:
            key = f"/hubs/sections/{section}"
            routes[key] = self.addStations

        return routes

    def returnStations(self, path, request, response):
        sections = self.config["enabled_sections"]
        if len(sections) < 1:
            all_sections = self.server.library.sections()
            sections = [s.key for s in all_sections if s.TYPE == "artist"]

        items = []
        for section in sections:
            items += self.buildStations(section)

        content = json.loads(response.content)
        content["MediaContainer"]["Metadata"] = items
        content["MediaContainer"]["size"] = len(items)
        content["MediaContainer"]["totalSize"] = len(items)

        response._content = json.dumps(content)
        return response

    def buildStations(self, section):
        stations = self.config["stations"]
        items = []

        for station in stations:
            key = station["key"]
            item = {
                "key": f"/hijack/stations/{key}/{section}",
                "guid": f"hijack://station/{key}/{section}",
                "type": "playlist",
                # "summary": station["desc"] if "desc" in station else "",
                "parentTitle": station["desc"] if "desc" in station else "",
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
            "style": "shelf",
            "Metadata": [],
        }

        section = path.split("/")[-1]
        items = self.buildStations(section)
        hub["Metadata"] += items
        hub["size"] += len(items)

        content = json.loads(response.content)
        content["MediaContainer"]["Hub"].insert(0, hub)
        content["MediaContainer"]["size"] = content["MediaContainer"]["size"] + 1

        response._content = json.dumps(content)
        return response

    def load_source(self, source, section, length):
        filters = source["filters"] if "filters" in source else {}
        sort = source["sort"] if "sort" in source else "random"
        length = source["length"] if "length" in source else length
        tracks = section.searchTracks(maxresults=length, sort=sort, filters=filters)
        return tracks

    def console(self, thing):
        with open("report.txt", "at") as report_file:
            console = Console(file=report_file)
            console.print(thing)
        console = Console()
        console.print(thing)

    def get_key(self, track, obj, prop):
        map = {
            "track": lambda track: track,
            "album": lambda track: track.album(),
            "artist": lambda track: track.artist(),
        }
        return getattr(map[obj](track), prop)

    def startStation(self, path, request, response):
        if self.inflight:
            return response

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

        self.inflight = True
        try:
            length = self.config["length"]
            sources = station["sources"]
            section_id = request.args[constants.URI_KEY].split("/")[-1].split("?")[0]
            section = self.server.library.sectionByID(int(section_id))

            pool = {}

            self.console(f"Starting {station["name"]}")
            with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
                future_to_source = {
                    executor.submit(self.load_source, source, section, length): source
                    for source in sources
                }
                self.console("Started fetching tracks")
                for future in concurrent.futures.as_completed(future_to_source):
                    source = future_to_source[future]
                    tracks = future.result()
                    self.console(f"Fetched {source["name"]}")
                    source_name = source["name"]
                    pool[source_name] = {}
                    pool[source["name"]]["tracks"] = tracks
                    pool[source["name"]]["weights"] = [1 for _ in tracks]

                    if "weight" in source:
                        pool[source["name"]]["weights"] = []
                        weight_factor = (
                            source["weight_factor"] if "weight_factor" in source else 2
                        )
                        # If sort_weight is 2, the first track is 2x more likely than the last
                        weight = weight_factor
                        factor = (weight - 1) / len(tracks)
                        [key, dir] = source["weight"].split(":")
                        reverse = dir == "desc"
                        [obj, prop] = key.split(".")
                        tracks = sorted(
                            tracks,
                            key=lambda track: self.get_key(track, obj, prop),
                            reverse=reverse,
                        )
                        for track in tracks:
                            pool[source["name"]]["weights"].append(weight)
                            weight -= factor

            tracks = []
            options = [source["name"] for source in sources]
            option_weights = [source["chance"] for source in sources]

            totals = {}
            rows = []
            while len(tracks) < length:
                source_name = choices(options, weights=option_weights, k=1)[0]
                source = pool[source_name]

                if len(source["tracks"]) < 1:
                    self.console(f"Out of tracks for {source_name}, skipping...")
                    continue

                track = choices(source["tracks"], weights=source["weights"], k=1)[0]

                # Pick again if that track is already in the queue
                while track in tracks:
                    track = choices(source["tracks"], weights=source["weights"], k=1)[0]

                tracks.append(track)

                del source["weights"][source["tracks"].index(track)]
                source["tracks"].remove(track)

                totals[source_name] = (
                    0 if source_name not in totals else totals[source_name] + 1
                )
                rows.append({"track": track, "source": source_name})

            table = Table(title="Tracks", show_lines=True, width=55)
            table.add_column("Artist", style="cyan", justify="right")
            table.add_column("Track", style="green")
            table.add_column("Source", style="magenta")

            for row in reversed(rows):
                table.add_row(
                    row["track"].grandparentTitle, row["track"].title, row["source"]
                )
            self.console(table)

            table = Table(title="Sources")
            table.add_column("Source", justify="right", style="cyan", no_wrap=True)
            table.add_column("Count", style="magenta")
            table.add_column("Percentage", justify="left", style="green")

            for key, value in totals.items():
                table.add_row(f"{key}", f"{value}", f"{value/length:.0%}")

            self.console(table)

            server = self.server
            queue = PlayQueue.create(server, tracks)
            return requestToServer(
                f"playQueues/{str(queue.playQueueID)}", request.headers
            )
        finally:
            self.inflight = False
