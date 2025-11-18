from waitress import serve
from flask import Flask
import logging

from melon.config import Config
from melon.caddy import init_caddy
from melon.plugins import init_plugins
from melon.routes import init_routes
from melon.wizard import wizard_app, wizard_proxy, wizard_init


def init_app():
    app = Flask(__name__)
    return app


def boot():
    wizard_init()

    app = init_app()
    plugins = init_plugins()
    init_caddy()
    init_routes(app, plugins)

    wizard_app()
    wizard_proxy()

    return app


def start():
    app = boot()
    serve(app, listen=f"*:{Config.pomelo_port}", url_scheme="https")


def start_dev():
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)
    app = boot()
    app.run(port=Config.pomelo_port, debug=True)


def config():
    Config.setup()
