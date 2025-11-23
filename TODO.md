# MVP
- [ ] how to build for multi-platform? / push to dockerhub
- [ ] make sure addresses etc in logs are correct
- [ ] Setup instructions + general docs (incl. docker compose)
- [ ] Docs for AnyRadios
- [ ] Docs for how sort weighting works in AnyRadios
- [ ] Early alpha stage disclaimer
- [ ] mention charlie in readme

# Later
- [ ] notes on how to make work with plex outside docker
    - token, processed machineIdentifier out of plist, into fake prefs.xml
    - override plex host in config toml
        host.docker.internal
        turn off caddy inside container and just use main caddy
    - tls doesn't work
    - need to set allowLocalhostOnly
- [ ] look into user setting in dockerfile
- [ ] run locally for dev instead of constantly having to rebuild docker image
- [ ] shove music videos into extras for music / album / artists plugin
- [ ] cloud to butt plus plugin
- [ ] subprocess logs to files instead of devnull
- [ ] plugins from separate dir?
- [ ] setup customConnections (customConnections set)
- [ ] Verify config valid
- [ ] addHub helper method?
- [ ] better structure for boot log hooks
- [ ] prettier CLI output ([Rich](https://github.com/Textualize/rich))

## Plugins
- [ ] Can we add station descriptions, use different colors, etc?
- [ ] AnyRadios sort only works with datetimes

# Questions
- [ ] What does `hub.type` do / what are the options?
- [ ] What does `hub.hubIdentifer` do?
- [ ] What does `hub.context` do?
- [ ] What does the `smart` property do on a hub item?
- [ ] What does the `radio` property do on a hub item?
- [ ] What other icons exist?


add ip or whatever to custom server access urls, turn off GDM, and relay
