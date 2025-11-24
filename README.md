![Static Badge](https://img.shields.io/badge/made_by_hand-not_ai-blue?style=for-the-badge)

# Pomelo (for Plex) 🐶

Pomelo is a tool that allows you to extend the functionality of your Plex server in almost any way imaginable. Pomelo runs proxy server that sits between your Plex server and your Plex client, 
allowing you to intercept & modify requests to, and responses from the Plex server. This allows you to do things like add custom hubs, change what buttons do, how metadata is displayed...or just about anything else.

## Installation 
Pomelo is built to run in a container, as part of a compose stack with Plex Media Server. If you're already running PMS inside a container, adding Pomelo is super easy - just update your `docker-compose.yml` to add Pomelo
to the stack:
```yml
version: "3"
services:
  plex:
    image: lscr.io/linuxserver/plex:latest
    container_name: plex
    environment:
      - PUID=1000
      - PGID=1000
      - TZ=Etc/UTC
      - VERSION=docker
    ports:
      - 5001:32400            # In case you need to reach the original server for some reason
    volumes:
      - /plex:/config
      - /media/music:/music
      - /media/movies:/movies
      - /media/tv:/tv
    restart: unless-stopped

  pomelo:
    image: oatmealmonster/pomelo:latest
    environment:
      - PYTHONUNBUFFERED=1    # Make `print` work
    ports:
      - 32400:5500
    volumes:
      - /plex:/config         # !!Make this the same as line 14!!
      - /plex/pomelo:/pomelo  # This can be anywhere - this is where Pomelo will store it's configuration files
    depends_on:
      - plex
```
### A couple things to note:
- Pomelo _requires_ a volume mapping from the directory on the host machine where the Plex libary is stored, to `/config`.
- Your Plex Media Server container must not be running networking in host mode; the Pomelo container needs to bind to port 32400.
- You may want enable the `Treat WAN IP As LAN Bandwidth` setting in the Network tab if you're having trouble with Plex throttling your streams.

## Config
Pomelo stores a `pomelo_config.toml` file in the `/pomelo` volume specified in your `docker-compose.yml`. Most of the options should be left at their defaults 99% of the time, with the exception
of plugin configuation (see below)

|Option name|What it does|Default value|
|-----------|------------|-------------|
|`caddy_admin_url`|Specifies the admin url for the [Caddy](https://caddyserver.com/) server that Pomelo runs. Should be left at default.|`http://localhost:2019`|
|`caddy_listen_port`|The port the Caddy server should listen on. Should be left at default.|`5500`|
|`plex_host`|The url to the Plex server. Should only be changed if you know what you're doing.|`plex`|
|`plex_port`|The port the Plex server is running on. Should only be changed if you know what you're doing.|`32400`|
|`plex_token`|An access token for requests to your Plex server. Pomelo should be able to populate this automatically; if you run into issues you can set it yourself: [Finding X-Plex-Token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/) |``|
|`pomelo_port`|The port (on the container) that Pomelo runs on. You shouldn't need to change this, but if you do, you'll need to update your `docker-compose.yml` accordingly.|`32400`|
|`enabled_plugins`|A list of plugins that Pomelo should load & run. Feel free to edit & update this as you wish.|`["pomelo.plugins.ExploreRadio", "pomelo.plugins.AnyRadios"]`|

## Plugins
Extensions to Plex functionality served by Pomelo are handled by plugins. Pomelo currently comes bundled with three plugins, and can load external plugins as well.

### External Plugins
External plugins can be placed in `/pomelo/plugins`, and added to the `enabled_plugins` list in `pomelo_config.toml`.

### Plugin Config
Some plugins offer their own config options. These can be specified under `[{Plugin Name}]` in `pomelo_config.toml`:
```toml
[ExploreRadio]
station_name = "Cool Radio"
```
Available options for each builtin plugin are listed in the documentation for each plugin.

## AnyRadios
Adds a new hub to music sections of your library where you can add custom "stations" that shuffle your music collection according to logic you define.

### Options
|Option name|What it does|Default value|
|-----------|------------|-------------|
|`length`|How many tracks should be added to the queue when a station is started. Larger numbers will make the station play for longer, but take longer to start up.|`100`|
|`enabled_sections`|Library sections where the Pomelo Stations should be shown. If empty, it will be shown in every music section in your library.|`[]`|
|`hub_title`|The title of the hub where your custom stations are show.|`Pomelo Stations`|
|`stations`|A list of station definitions. See below for more.|See below.|

### Station Configurations
The easiest way to understand station config is probably with an example:
```toml
[[AnyRadios.stations]]
name = "Smart Shuffle"                      # [Required] The name of the station shown in the UI.
key = "smart"                               # [Required] Used in the backend.

[[AnyRadios.stations.sources]]              # Each station can have as many sources as you want.
filters = { "track.addedAt>>" = "-90d" }    # Filters that restrict which tracks will be included in this source. Uses Plex's filter syntax; see below.
chance = 2                                  # [Required] The chance a track from this source will be picked relative to the other sources. In this example, this source is twice as likely as the second source below.
sort = "addedAt"                            # If a source has a `sort` defined, the first track will be more likely to be added to the queue than the last.
sort_reverse = true
sort_weight = 1                             # Determines how much more likely the first track will be than the last.

[[AnyRadios.stations.sources]]              # A source with no filters will pick a random assortment of tracks.
chance = 1
```

#### Sorting & Filtering
See [here](https://www.plexopedia.com/plex-media-server/api/filter/) for a guide to Plex's filtering syntax.

In this example, the most recently added track will be twice as likely than a random track (from the source below); the least recently added track will be equally as likely as a random track.
Other tracks in the list will be somewhere in between; for example, if there are three tracks in this source:
- Track 1: Chance 2
- Track 2: Change 1.5
- Track 3: Chance 1

## ExploreRadio
The Explore Radio Plugin adds a new Station to your Music library which tries to play a pretty even mix of songs you've rated highly and songs you've never heard before, while maintaining a vibe (using Plex's sonic similarity feature).

### Options
`ExploreRadio` offers one option - `station_name` - which determines what the Explore station will be named in the UI.
|Option name|What it does|Default value|
|-----------|------------|-------------|
|`station_name`|The name of the station in the Plex UI|`Explore Radio`|
|`enabled_sections`|Library sections where the Pomelo Stations should be shown. If empty, it will be shown in every music section in your library.|`[]`|

## BetterTrackRadio
BetterTrackRadio makes the radios started from a track (only possible on Plexamp) use similar logic to the ExploreRadio plugin.

## Thanks
Huge thanks [@cchaz003](https://github.com/cchaz003) for all the help testing this, and for the idea to use containers!

## Prior Art
- [Replex](https://github.com/lostb1t/replex): A similar project; where I originally got the idea of using a proxy to extend Plex.
- [Psueplex](https://github.com/lufinkey/pseuplex): Another similar project; written in TypeScript and doesn't use containers.


![IMG_5578](https://github.com/user-attachments/assets/4e7d842e-55a8-4bbc-a0a5-e0278b5de77b)

