import datetime
import concurrent.futures
import json
from time import time
from urllib.parse import urlencode
from pomelo.BasePlugin import BasePlugin


class Plugin(BasePlugin):
    PLUGIN_NAME = "AnyHubs"
    DEFAULT_CONFIG = {
        "hubs": [
            {
                "section": 1,
                "title": "Past year",
                "type": "album",
                "source": "history",
                "history_length": 365,
                "history_start": 0,
                "hub_max_length": 6,
                "sort": "desc",
            }
        ]
    }

    def paths(self):
        sections = [hub["section"] for hub in self.config["hubs"]]

        routes = {}
        for section in sections:
            key = f"/hubs/sections/{section}"
            routes[key] = self.add_hubs

        return routes

    def create_hub(self, hub_config):
        hub = {
            "title": hub_config["title"],
            "type": hub_config["type"],  # album, what else?
            "hubIdentifier": hub_config["title"],
            "context": hub_config["title"],
            "size": 0,
            "more": False,
            "style": "shelf",
            "Metadata": [],
        }
        items = self.populate_hub(hub_config)
        hub["Metadata"] += items
        hub["size"] += len(items)
        return hub

    def populate_hub(self, hub_config):
        section = self.server.library.sectionByID(hub_config["section"])
        if hub_config["source"] == "history":
            today = datetime.date.today()
            end = datetime.datetime.combine(
                today
                - datetime.timedelta(
                    days=hub_config["history_length"]
                    + (
                        hub_config["history_start"]
                        if "history_start" in hub_config
                        else 0
                    )
                ),
                datetime.datetime.min.time(),
            )
            start = (
                datetime.datetime.combine(
                    today - datetime.timedelta(days=hub_config["history_start"]),
                    datetime.datetime.min.time(),
                )
                if "history_start" in hub_config
                else None
            )
            args = {
                "librarySectionID": hub_config["section"],
                "viewedAt>": int(end.timestamp()),
            }
            if start is not None:
                args["viewedAt<"] = int(start.timestamp())
            key = f"/status/sessions/history/all?{urlencode(args)}"
            print(hub_config["title"], key)
            ts = time()
            history = section.fetchItems(key)
            te = time()
            print("hub:%r took: %2.4f sec" % (hub_config["title"], te - ts))
            albums = {}
            for track in history:
                if start and track.viewedAt > start:
                    # print(start, track.viewedAt, end)
                    # break
                    continue
                album_id = track.parentKey
                if album_id is None:
                    # unclear why this happens sometimes
                    continue
                if album_id in albums:
                    albums[album_id] += 1
                else:
                    albums[album_id] = 1
            # TODO: sort prop comes from hub config
            sorted_albums = sorted(
                [{"id": id, "count": count} for id, count in albums.items()],
                key=lambda album: albums[album["id"]],
                reverse=True,
            )[0 : hub_config["hub_max_length"]]
            if "sort" in hub_config and hub_config["sort"] == "asc":
                sorted_albums.reverse()
            hydrated_albums = [section.fetchItem(x["id"]) for x in sorted_albums]
            items = [
                {
                    "ratingKey": album.ratingKey,
                    "key": album.key,
                    "thumb": album.thumb,
                    "type": "album",
                    "title": f"{album.title}",
                    "parentKey": album.parentKey,
                    "parentTitle": album.parentTitle,
                }
                for album in hydrated_albums
            ]
            return items
        else:
            return []

    def add_hubs(self, path, request, response):
        content = json.loads(response.content)

        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            future_to_source = {
                executor.submit(self.create_hub, hub): hub
                for hub in self.config["hubs"]
            }
            for future in concurrent.futures.as_completed(future_to_source):
                hub = future.result()
                content["MediaContainer"]["Hub"].insert(0, hub)
                content["MediaContainer"]["size"] = (
                    content["MediaContainer"]["size"] + 1
                )

        response._content = json.dumps(content)
        return response
