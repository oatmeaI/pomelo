# MVP
- [ ] separate steps for exposing externally
- [ ] make sure addresses etc in logs are correct
- [ ] Setup instructions + general docs
- [ ] Docs for AnyRadios
- [ ] Docs for how sort weighting works in AnyRadios
- [ ] Early alpha stage disclaimer
- [ ] don't bother trying to add to caddy setup if already running, just ask whether to start proxy server or not; if not it's up to you to config

# Later
- [ ] subprocess logs to files instead of devnull
- [ ] setup customConnections
- [ ] Verify config valid
- [ ] figure out why start_dev boots everything twice
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


customConnections set

- make config.toml work (or pull from docker env?)
- make docker build correct
- dunno how to existing plex migrate to docker correctly

podman-compose up
podman-compose exec pomelo /bin/bash
poetry install
source .venv/bin/activate
poetry run start
p4uEJfzuwK3Sy2VWx_Hy
add ip or whatever to custom server access urls, turn off GDM, remote access and relay
