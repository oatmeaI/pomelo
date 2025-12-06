# Pomelo (for Plex) 🐶

<!--toc:start-->
- [Pomelo (for Plex) 🐶](#pomelo-for-plex-🐶)
  - [Contents](#contents)
  - [Quickstart](#quickstart)
      - [A couple things to note:](#a-couple-things-to-note)
  - [Configuration](#configuration)
  - [Plugins](#plugins)
  - [Builtin Plugins](#builtin-plugins)
  - [Thanks](#thanks)
  - [Prior Art](#prior-art)
<!--toc:end-->

Pomelo is a tool that lets you use Plugins extend or modify your Plex server's functionality, by intercepting and modifying communication between Plex players and your server.

Pomelo lets you do all kinds of stuff to your sever - like **create custom Stations**:
<p align="center">
  <img width="476" height="537" alt="image" src="https://github.com/user-attachments/assets/591e79c0-971d-4f41-98c8-8abe609324c3" />
</p>

Or show related videos from **YouTube in the Extras section**:
<p align="center">
<img width="1301" height="797" alt="Screenshot 2025-12-05 at 12 25 33 AM" src="https://github.com/user-attachments/assets/aff5e4d9-2420-46a9-9d5c-d821604926b4" />
<img width="1301" height="797" alt="Screenshot 2025-12-05 at 12 36 45 AM" src="https://github.com/user-attachments/assets/d0ffe17e-2d35-447e-98c1-e996f9dfa8e4" />
</p>

<p align="center">
[more examples to come, as I build them!]
</p>

## Quickstart 
Pomelo is built to run in a container, as part of a compose stack with Plex Media Server. 
If you're already running PMS inside a container, adding Pomelo is super easy - just update your `docker-compose.yml` to add Pomelo to the stack:
```yml
services:
  plex:
    image: lscr.io/linuxserver/plex:latest
    container_name: plex
    # NOTE: You MUST remove `network_mode: host` from the plex service in order for Pomelo to work.
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Etc/UTC
      - VERSION=docker
    ports:
      - 5001:32400            # Not required; just here in case you need to reach the original server for some reason
    volumes:
      - /plex:/config
      - /media/music:/music
      - /media/movies:/movies
      - /media/tv:/tv
    restart: unless-stopped

  pomelo:
    image: oatmealmonster/pomelo:latest
    environment:
      - PYTHONUNBUFFERED=1    # Make `print` work; not required
    ports:
      - 32400:5500
    volumes:
      - /plex:/config         # REQUIRED !!Make this the same as the /config volume in the plex service!!
      - /plex/pomelo:/pomelo  # REQUIRED This can be anywhere - this is where Pomelo will store it's configuration files
    depends_on:
      - plex
```
### A couple things to note:
- Your Plex Media Server container must _not_ use `network_mode: host`; the Pomelo container needs to bind to port 32400.
- Pomelo _requires_ a volume mapping from the directory on the host machine where the Plex libary is stored to `/config`.
- You may want enable the `Treat WAN IP As LAN Bandwidth` setting in the Network tab of the Plex Media Server settings if you're having trouble with Plex throttling streams.

## Configuration
Pomelo stores a `pomelo_config.toml` file in the `/pomelo` volume specified in your `docker-compose.yml`.
Most of the options should be left at their defaults 99% of the time, with the exception
of plugin configuation (see below).
- [Config Option Documentation](docs/Config.md)

## Plugins
Extensions to Plex functionality served by Pomelo are handled by plugins. 
Pomelo bundles some builtin plugins, and can load external plugins.
- [Plugin Documentation](docs/Plugins.md)

## Builtin Plugins
|Plugin Name|What it does|Plugin Id|Plugin Documentation|
|-----------|------------|----------|---------------------|
|ExploreRadio|Adds a new Station to your Music library.|`pomelo.plugins.ExploreRadio`|[Documentation](docs/plugins/ExploreRadio.md)|
|AnyRadios|Lets you create custom "stations" that shuffle your music collection according to logic you define.|`pomelo.plugins.AnyRadios`|[Documentation](docs/plugins/AnyRadios.md)|
|BetterTrackRadio|Makes stations started from a track use similar logic to the Explore Radio plugin.|`pomelo.plugins.BetterTrackRadio`|[in progress...]|
|YouTubeVideos|Searches YouTube for videos related to library items and adds them to the "Extras" section.|`pomelo.plugins.YoutubeVideos`|[in progress...]|

## Thanks
Huge thanks [@cchaz003](https://github.com/cchaz003) for all the help testing this, and for the idea to use containers!

## Prior Art
- [Replex](https://github.com/lostb1t/replex): A similar project; where I originally got the idea of using a proxy to extend Plex.
- [Psueplex](https://github.com/lufinkey/pseuplex): Another similar project; written in TypeScript and doesn't use containers.
- [Python-PlexAPI](https://python-plexapi.readthedocs.io/en/latest/): Pomelo uses this library for communication with the Plex server; this project would be impossible without it!


![IMG_5578](https://github.com/user-attachments/assets/4e7d842e-55a8-4bbc-a0a5-e0278b5de77b)

![Static Badge](https://img.shields.io/badge/made_by_hand-not_ai-blue?style=for-the-badge)
