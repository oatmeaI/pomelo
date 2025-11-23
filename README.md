# Pomelo (for Plex) 🐶
![Static Badge](https://img.shields.io/badge/made_by_hand-not_ai-blue?style=for-the-badge)
`pomelo` is a tool that allows you to extend the functionality of your Plex server in almost any way imaginable. `pomelo` runs proxy server that sits between your Plex server and your Plex client, 
allowing you to intercept & modify requests to, and responses from the Plex server. This allows you to do things like add custom hubs, change what buttons do, how metadata is displayed...or just about anything else.

## How?
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
    ports:
      - 32400:5500
    volumes:
      - /plex:/config         # !!Make this the same as line 14!!
      - /plex/pomelo:/pomelo  # This can be anywhere - this is where Pomelo will store it's configuration files
    depends_on:
      - plex
```
A couple things to note:
- Pomelo _requires_ a volume mapping from the directory on the host machine where the Plex libary is stored, to `/config`
- Your Plex Media Server container must not be running networking in host mode; the Pomelo container needs to bind to port 32400

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

### Builtin Plugins

#### ExploreRadio
`ExploreRadio` is the reason I created pomelo. The Explore Radio Plugin adds a new Station to your Music library which tries to play a pretty even mix of songs you've rated highly and songs you've never heard before, while maintaining a vibe (using Plex's sonic similarity feature).

##### Options
`ExploreRadio` offers one option - `station_name` - which determines what the Explore station will be named in the UI.



## How does it work?
TODO

## Thanks

## Prior Art

## Roadmap
- [ ] Plugin developer documentation
- [ ] An actual build process & binary distribution
- [ ] Better & prettier documentation

![IMG_5578](https://github.com/user-attachments/assets/4e7d842e-55a8-4bbc-a0a5-e0278b5de77b)

