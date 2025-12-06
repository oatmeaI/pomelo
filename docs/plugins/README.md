# Plugins
Extensions to Plex functionality served by Pomelo are handled by plugins. 
Pomelo bundles some builtin plugins, and can load external plugins.

## Plugin Config
Some plugins offer their own config options.
These can be specified under `[{Plugin Name}]` in `pomelo_config.toml`:
```toml
[ExploreRadio]
station_name = "Cool Radio"
```
Available options for each builtin plugin are listed in the documentation for each plugin (see below).

## Built-In Plugins
|Plugin Name|What it does|Plugin Id|Plugin Documentation|
|-----------|------------|----------|---------------------|
|ExploreRadio|Adds a new Station to your Music library.|`pomelo.plugins.ExploreRadio`|[Documentation](docs/plugins/ExploreRadio.md)|
|AnyRadios|Lets you create custom "stations" that shuffle your music collection according to logic you define.|`pomelo.plugins.AnyRadios`|[Documentation](docs/plugins/AnyRadios.md)|
|BetterTrackRadio|Makes stations started from a track use similar logic to the Explore Radio plugin.|`pomelo.plugins.BetterTrackRadio`|[in progress...]|
|YouTubeVideos|Searches YouTube for videos related to library items and adds them to the "Extras" section.|`pomelo.plugins.YoutubeVideos`|[in progress...]|

## External Plugins
External plugins can be placed in `/pomelo/plugins`, and added to the `enabled_plugins` list in `pomelo_config.toml`.
