# Pomelo (for Plex) 🐶
`pomelo` is a tool that allows you to extend the functionality of your Plex server in almost any way imaginable.

## How?
`pomelo` is a proxy server that sits between your Plex server and your Plex client, allowing you to intercept & modify requests to, and responses from the Plex server. This allows you to do things like add custom Stations, change what buttons do or how metadata is displayed...or just about anything else.

## Usage
Setting up `pomelo` takes a little bit of work, because we need to trick Plex into always connecting via `pomelo` instead of connecting directly to the Plex server. There are 3 main steps:

### 1. Start Pomelo
0. Ensure [Poetry](https://python-poetry.org/) is installed
1. `git clone` this repo
2. Run `poetry install` in the project root
3. Run `poetry start`
(In the future, we'll distribute an actual binary and you won't need to clone the repo or use Poetry...but for now...)

### 2. Configure your Plex server
1. **Add Pomelo's URL to Plex:** In the Network tab, click "Show Advanced", find the "Custom server access URLs" field, and `http://<Your IP>:5200`. (`pomelo` runs on port 5200 by default; you can change this in the config). 
2. **Disable Remote Access:** In your Plex server settings, disable Remote Access (don't worry, you'll still be able to access your server remotely)
3. **Force Plex to use Pomelo:** Following the [Plex documentation on changing hidden settings](https://support.plex.tv/articles/201105343-advanced-hidden-server-settings/) to set `allowLocalhostOnly 1` (on my Mac, I ran `defaults write com.plexapp.plexmediaserver allowLocalhostOnly 1`). This tells Plex not to allow LAN connections, forcing your clients to to connect via Pomelo. Alternately, you can make a firewall rule to block the port that Plex runs on - usually 32400.

## Plugins
Extensions to Plex functionality served by pomelo are handled by plugins. Currently there is only one plugin - Explore Radio - and all plugins must be bundled with Pomelo. In the future, there will be more plugins which over more functionlality, and a way to install plugins not bundled with Pomelo (see the Roadmap below).

### ExploreRadio
`ExploreRadio` is the reason I created pomelo. The Explore Radio Plugin adds a new Station to your Music library which tries to play a pretty even mix of songs you've rated highly and songs you've never heard before, while maintaining a vibe (using Plex's sonic similarity feature).

#### Options
`ExploreRadio` offers one option - `station_name` - which determines what the Explore station will be named in the UI.

## Config
Pomelo's config file lives at the `user_config_dir` specified by [platformdirs](https://pypi.org/project/platformdirs/) - on macOS, it's `~/Library/Application Support/pomelo/config.toml`.
The available options and their defaults are:
|Option name|What it does|Default value|
|-----------|------------|-------------|
|`server_address`|The address of your Plex server.|`http://127.0.0.`|
|`server_port`|The port your Plex server is listening on.|`32400`|
|`music_section`|The name of your Music library on your Plex server|`Music`|
|`port`|The port that `pomelo` should listen on|`5200`|
|`token`|The token for accessing your Plex server. Pomelo will try to populate this automatically, but you can override it if you need to for some reason.|`None`|
|`enabled_plugins`|A list of bundled plugins to that should be enabled|`["ExploreRadio"]`|

### Plugin Config
Some plugins offer their own config options. These can be specified under `[plugin_config.{Plugin Name}]` in the `config.toml`

### Example config.toml:
(This is the config that I use)
```toml
server_address = "http://127.0.0.1"
server_port = 32400
music_section = "Music"
port = 5200
token = "<Plex token here>"
enabled_plugins = [
    "ExploreRadio",
    "BetterTrackRadio",
    "SmartShuffle",
    "AnyRadios",
]

[plugin_config.ExploreRadio]
station_name = "Cool Guys Radio"
```

## Roadmap
- [ ] Plugin developer documentation
- [ ] An actual build process & binary distribution
- [ ] Better & prettier documentation

![IMG_5578](https://github.com/user-attachments/assets/4e7d842e-55a8-4bbc-a0a5-e0278b5de77b)

