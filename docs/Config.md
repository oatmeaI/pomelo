## Configuration
Pomelo stores a `pomelo_config.toml` file in the `/pomelo` volume specified in your `docker-compose.yml`. 
Most of the options should be left at their defaults 99% of the time, with the exception of [plugin configuation](/docs/plugings/README.md#plugin-config).

|Option name|What it does|Default value|
|-----------|------------|-------------|
|`caddy_admin_url`|Specifies the admin url for the [Caddy](https://caddyserver.com/) server that Pomelo runs. Should be left at default.|`http://localhost:2019`|
|`caddy_listen_port`|The port the Caddy server should listen on. Should be left at default.|`5500`|
|`plex_host`|The url to the Plex server. Should only be changed if you know what you're doing.|`plex`|
|`plex_port`|The port the Plex server is running on. Should only be changed if you know what you're doing.|`32400`|
|`plex_token`|An access token for requests to your Plex server. Pomelo should be able to populate this automatically; if you run into issues you can set it yourself: [Finding X-Plex-Token](https://support.plex.tv/articles/204059436-finding-an-authentication-token-x-plex-token/) |empty|
|`pomelo_port`|The port (on the container) that Pomelo runs on. You shouldn't need to change this, but if you do, you'll need to update your `docker-compose.yml` accordingly.|`32400`|
|`enabled_plugins`|A list of plugins that Pomelo should load & run. Feel free to edit & update this as you wish.|`["pomelo.plugins.ExploreRadio", "pomelo.plugins.AnyRadios"]`|
