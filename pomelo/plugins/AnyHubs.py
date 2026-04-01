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
            "hubIdentifier": getattr(hub_config, "key", hub_config["title"]),
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
            ts = time()
            history = section.fetchItems(key)
            te = time()
            print("hub:%r took: %2.4f sec" % (hub_config["title"], te - ts))
            last = None
            repeat = "repeat_plays" in hub_config and hub_config["repeat_plays"]
            show_count = "show_count" in hub_config and hub_config["show_count"]

            if hub_config["type"] == "album":
                artists = {}
                for track in history:
                    # If repeat_plays is true, we don't count consecutive plays from the
                    # same album (unless it's the same track on repeat)
                    # This is so that we can get a more accurate view of which albums
                    # you're REALLY into, vs a long album you listened to start to finish once
                    if (
                        last is not None
                        and repeat
                        and last.parentKey == track.parentKey
                    ):
                        continue
                    if start and track.viewedAt > start:
                        continue
                    artist_id = track.parentKey
                    if artist_id is None:
                        # unclear why this happens sometimes
                        continue
                    if artist_id in artists:
                        artists[artist_id] += 1
                    else:
                        artists[artist_id] = 1
                    last = track

                # TODO: sort prop comes from hub config
                sorted_artists = sorted(
                    [{"id": id, "count": count} for id, count in artists.items()],
                    key=lambda album: artists[album["id"]],
                    reverse=True,
                )[0 : hub_config["hub_max_length"]]

                if "sort" in hub_config and hub_config["sort"] == "asc":
                    sorted_artists.reverse()

                hydrated_artists = [section.fetchItem(x["id"]) for x in sorted_artists]
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
                    for album in hydrated_artists
                ]
                return items
            elif hub_config["type"] == "track":
                tracks = {}
                for track in history:
                    if start and track.viewedAt > start:
                        continue
                    track_id = track.key
                    if track_id is None or track_id == "":
                        continue
                    if track_id in tracks:
                        tracks[track_id] += 1
                    else:
                        tracks[track_id] = 1

                # TODO: sort prop comes from hub config
                sorted_artists = sorted(
                    [{"id": id, "count": count} for id, count in tracks.items()],
                    key=lambda track: tracks[track["id"]],
                    reverse=True,
                )[0 : hub_config["hub_max_length"]]

                if "sort" in hub_config and hub_config["sort"] == "asc":
                    sorted_artists.reverse()

                hydrated_artists = [section.fetchItem(x["id"]) for x in sorted_artists]

                items = [
                    {
                        "ratingKey": getattr(track, "ratingKey", ""),
                        "key": track.key,
                        "thumb": track.thumb,
                        "type": "track",
                        "title": f"{track.title}",
                        "parentKey": track.parentKey,
                        "parentTitle": track.parentTitle,
                        "grandparentKey": track.grandparentKey,
                        "grandparentTitle": f"[{tracks[track.key]}] {track.grandparentTitle}"
                        if show_count
                        else track.grandparentTitle,
                    }
                    for track in hydrated_artists
                ]
                return items

            elif hub_config["type"] == "artist":
                artists = {}
                for track in history:
                    # If repeat_plays is true, we don't count consecutive plays from the
                    # same album (unless it's the same track on repeat)
                    # This is so that we can get a more accurate view of which albums
                    # you're REALLY into, vs a long album you listened to start to finish once
                    if (
                        last is not None
                        and repeat
                        and last.parentKey == track.parentKey
                    ):
                        continue
                    if start and track.viewedAt > start:
                        continue
                    artist_id = track.grandparentKey
                    if artist_id is None:
                        # unclear why this happens sometimes
                        continue
                    if artist_id in artists:
                        artists[artist_id] += 1
                    else:
                        artists[artist_id] = 1
                    last = track

                # TODO: sort prop comes from hub config
                sorted_artists = sorted(
                    [{"id": id, "count": count} for id, count in artists.items()],
                    key=lambda artist: artists[artist["id"]],
                    reverse=True,
                )[0 : hub_config["hub_max_length"]]

                if "sort" in hub_config and hub_config["sort"] == "asc":
                    sorted_artists.reverse()

                hydrated_artists = [section.fetchItem(x["id"]) for x in sorted_artists]
                items = [
                    {
                        "ratingKey": artist.ratingKey,
                        "key": artist.key,
                        "thumb": artist.thumb,
                        "type": "artist",
                        "title": f"[{artists[artist.key]}] {artist.title}"
                        if show_count
                        else artist.title,
                        # "parentKey": artist.parentKey,
                        # "parentTitle": artist.parentTitle,
                    }
                    for artist in hydrated_artists
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
