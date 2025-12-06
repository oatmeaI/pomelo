# AnyRadios
Adds a new hub to music sections of your library where you can add custom "stations" that shuffle your music collection according to logic you define.
- `pomelo.plugins.AnyRadios`

## Options
|Option name|What it does|Default value|
|-----------|------------|-------------|
|`length`|How many tracks should be added to the queue when a station is started. Larger numbers will make the station play for longer, but take longer to start up.|`100`|
|`enabled_sections`|Library sections where the Pomelo Stations should be shown. If empty, it will be shown in every music section in your library.|`[]`|
|`hub_title`|The title of the hub where your custom stations are show.|`Pomelo Stations`|
|`stations`|A list of station definitions. See below for more.|See below.|

## Station Configurations
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

## Sorting
See [here](https://www.plexopedia.com/plex-media-server/api/filter/) for a guide to Plex's filtering syntax.

## Filtering
In this example, the most recently added track will be twice as likely than a random track (from the source below); the least recently added track will be equally as likely as a random track.
Other tracks in the list will be somewhere in between; for example, if there are three tracks in this source:
- Track 1: Chance 2
- Track 2: Chance 1.5
- Track 3: Chance 1
