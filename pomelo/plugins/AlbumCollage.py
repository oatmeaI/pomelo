from datetime import date, datetime, timedelta
import concurrent.futures
import requests
from PIL import Image, ImageFont, ImageDraw
from io import BytesIO
from urllib.parse import urlencode
from pomelo.BasePlugin import BasePlugin
from flask import Response
from pomelo.config import Config


class Plugin(BasePlugin):
    PLUGIN_NAME = "AlbumCollage"
    DEFAULT_CONFIG = {}

    def paths(self):
        return {"/collage": self.make_collage}

    def make_collage(self, path, request, response):
        # date to start looking for history
        start = request.args.get("start")

        # days back from start to look for history
        background = request.args.get("background") or "FFFFFF"

        # days back from start to look for history
        days = int(request.args.get("days") or 7)

        # rows in the collage
        rows = int(request.args.get("rows") or 3)

        # columns in the collage
        cols = int(request.args.get("cols") or 3)

        # spacing between album covers
        spacing = int(request.args.get("spacing") or 0)

        # max square dimension for each album cover; the final image will be max_size * rows tall and max_size * cols wide
        max_size = int(request.args.get("max_size") or 200)

        # library section to look at for history
        library_section = request.args.get("library_section") or 1

        albums = self.get_albums(library_section, start, days, rows * cols)
        self.load_all_images(albums)
        collage = self.make_grid(albums, cols, rows, spacing, max_size, background)

        img_io = BytesIO()
        collage.save(img_io, "PNG", quality=70)
        img_io.seek(0)
        return Response(img_io, mimetype="image/jpeg")

    def make_grid(
        self, albums, cols=3, rows=3, spacing=0, max_size=200, background="FFFFFF"
    ):
        img_width = min(album["image"].width for album in albums)
        img_height = min(album["image"].height for album in albums)
        size = min([img_width, img_height, max_size])

        width = (size * cols) + (spacing * (cols + 1))
        height = (size * rows) + (spacing * (rows + 1))

        collage = Image.new("RGB", (width, height), color=f"#{background}")
        draw = ImageDraw.Draw(collage)
        for i, album in enumerate(albums):
            img = album["image"]
            img = img.resize((size, size), Image.Resampling.LANCZOS)
            row = i // rows
            col = i % cols
            x = (col * (size + spacing)) + spacing
            y = (row * (size + spacing)) + spacing
            collage.paste(img, (x, y))
            # draw.text((x, y), f"{album['count']}", (255, 255, 255))

        return collage

    def load_image(self, album):
        url = f"http://{Config.plex_url}{album['art']}?X-Plex-Token={Config.plex_token}"
        image = Image.open(requests.get(url, stream=True).raw)
        album["image"] = image
        return album

    def do_concurrent(self, collection, cb):
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            future_to_source = {executor.submit(cb, item): item for item in collection}
            for future in concurrent.futures.as_completed(future_to_source):
                result = future.result()
                results.append(result)
        return results

    def load_all_images(self, albums):
        return self.do_concurrent(albums, self.load_image)

    def get_albums(self, library_section, start=None, days=7, length=9):
        start = date.fromisoformat(start) if start is not None else datetime.today()

        start_date = datetime.combine(
            start,
            datetime.max.time(),
        )

        end_date = datetime.combine(
            start - timedelta(days=days),
            datetime.min.time(),
        )

        args = {
            "librarySectionID": library_section,
            "viewedAt>": int(end_date.timestamp()),
            "viewedAt<": int(start_date.timestamp()),
        }
        key = f"/status/sessions/history/all?{urlencode(args)}"
        section = self.server.library.sectionByID(library_section)
        history = section.fetchItems(key)
        albums = {}

        for track in history:
            album_id = track.parentKey
            if album_id is None:
                continue
            if album_id in albums:
                albums[album_id]["count"] += 1
            else:
                albums[album_id] = {"count": 1, "art": track.parentThumb}

        sorted_albums = sorted(
            [
                {"id": id, "count": album["count"], "art": album["art"]}
                for id, album in albums.items()
            ],
            key=lambda album: albums[album["id"]]["count"],
            reverse=True,
        )[0:length]

        return sorted_albums
