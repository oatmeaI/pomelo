## Plugins
Extensions to Plex functionality served by Pomelo are handled by plugins. 
Pomelo bundles some builtin plugins, and can load external plugins.

### External Plugins
External plugins can be placed in `/pomelo/plugins`, and added to the `enabled_plugins` list in `pomelo_config.toml`.

### Plugin Config
Some plugins offer their own config options.
These can be specified under `[{Plugin Name}]` in `pomelo_config.toml`:
```toml
[ExploreRadio]
station_name = "Cool Radio"
```
Available options for each builtin plugin are listed in the documentation for each plugin.
- [Plugin Documentation](/docs/plugins/README.md)
