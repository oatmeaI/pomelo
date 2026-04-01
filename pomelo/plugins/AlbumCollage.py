from datetime import date, datetime, timedelta, timezone
import concurrent.futures
import requests
from PIL import Image, ImageFont, ImageDraw, ImageFilter
from io import BytesIO
from urllib.parse import urlencode
from pomelo.BasePlugin import BasePlugin
from flask import Response
from pomelo.config import Config

# ROADMAP:
# - cache things somehow
# - Configure font via query params
# - configure text rendering (position, color, size, etc) via query params


MAX_PIXELS = 2000
MAX_DAYS = 365


class Plugin(BasePlugin):
    PLUGIN_NAME = "AlbumCollage"
    DEFAULT_CONFIG = {}

    def paths(self):
        return {"/collage": self.make_collage}

    def make_collage(self, path, request, response):
        # date to start looking for history
        start = request.args.get("start")

        # font for text overlays
        font = request.args.get("font")

        # days back from start to look for history
        background = request.args.get("background") or "FFFFFF"

        # days back from start to look for history
        days = max(int(request.args.get("days") or 7), 0)

        # rows in the collage
        rows = max(int(request.args.get("rows") or 3), 1)

        # columns in the collage
        cols = max(int(request.args.get("cols") or 3), 1)

        # when an album is played start to finish, count that as one play for the album
        aggregate_albums = bool(request.args.get("aggregate_albums") or False)

        # render playcounts on top of album art
        show_playcount = bool(request.args.get("show_playcount") or False)

        # spacing between album covers
        spacing = max(int(request.args.get("spacing") or 0), 0)

        # max square dimension for each album cover; the final image will be max_size * rows tall and max_size * cols wide
        max_size = max(int(request.args.get("max_size") or 200), 1)

        # library section to look at for history
        library_section = int(request.args.get("library_section") or 1)
        print(request.args)

        if days > MAX_DAYS:
            raise Exception("Too many days")

        albums = self.get_albums(
            library_section, start, days, rows * cols, aggregate_albums
        )
        self.load_all_images(albums)
        collage = self.make_grid(
            albums, cols, rows, spacing, max_size, background, show_playcount, font
        )

        collage = collage.resize((800, 800))
        img_io = BytesIO()
        collage.save(img_io, format="JPEG")
        img_io.seek(0)
        return Response(img_io, mimetype="image/jpeg")

    def make_grid(
        self,
        albums,
        cols=3,
        rows=3,
        spacing=0,
        max_size=200,
        background="FFFFFF",
        show_playcount=False,
        font_name=None,
    ):
        img_width = min(album["image"].width for album in albums)
        img_height = min(album["image"].height for album in albums)
        size = min([img_width, img_height, max_size])

        width = (size * cols) + (spacing * (cols + 1))
        height = (size * rows) + (spacing * (rows + 1))

        if width > MAX_PIXELS or height > MAX_PIXELS:
            raise Exception("Too big")

        collage = Image.new("RGB", (width, height), color=f"#{background}")
        draw = ImageDraw.Draw(collage)
        for i, album in enumerate(albums):
            img = album["image"]
            img = img.resize((size, size), Image.Resampling.LANCZOS)
            row = i // rows
            col = i % cols
            x = (col * (size + spacing)) + spacing
            y = (row * (size + spacing)) + spacing

            if show_playcount:
                height = 50
                cropped_img = img.crop((0, img.height - height, img.width, img.height))
                blurred_img = cropped_img.filter(
                    ImageFilter.GaussianBlur(4),
                ).convert("RGB")
                draw = ImageDraw.Draw(blurred_img, "RGBA")
                draw.fontmode = "L"  # SECRET LORE THAT MAKES fonts look good
                draw.rectangle(
                    xy=(0, 0, blurred_img.width, blurred_img.height),
                    fill=(0, 0, 0, 127),
                    outline=(0, 0, 0, 127),
                    width=5,
                )
                font = ImageFont.truetype(font_name or "Arial.ttf", 20)
                offset = font.getlength(f"{album["count"]}")
                draw.text((18, 18), f"{album['title']}", (255, 255, 255), font=font)
                draw.text(
                    (blurred_img.width - offset - 18, 18),
                    f"{album['count']}",
                    (255, 255, 255),
                    font=font,
                )
                img.paste(blurred_img, (0, img.height - height))
            collage.paste(img, (x, y))

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

    def get_albums(
        self, library_section, start=None, days=7, length=9, aggregate_albums=False
    ):
        start = date.fromisoformat(start) if start is not None else datetime.today()

        start_date = datetime.combine(start, datetime.max.time())
        end_date = datetime.combine(start - timedelta(days=days), datetime.min.time())

        args = {
            "librarySectionID": library_section,
            "viewedAt>": int(end_date.timestamp()),
            "viewedAt<": int(start_date.timestamp()),
        }
        key = f"/status/sessions/history/all?{urlencode(args)}"
        section = self.server.library.sectionByID(library_section)
        history = section.fetchItems(key)
        albums = {}

        last = None
        for track in history:
            album_id = track.parentKey
            if (
                last is not None
                and aggregate_albums
                and last.parentKey == track.parentKey
            ):
                continue
            if album_id is None:
                continue
            if album_id in albums:
                albums[album_id]["count"] += 1
            else:
                albums[album_id] = {
                    "count": 1,
                    "art": track.parentThumb,
                    "title": track.parentTitle,
                }
            last = track

        sorted_albums = sorted(
            [
                {
                    "id": id,
                    "count": album["count"],
                    "art": album["art"],
                    "title": album["title"],
                }
                for id, album in albums.items()
            ],
            key=lambda album: albums[album["id"]]["count"],
            reverse=True,
        )[0:length]

        return sorted_albums
