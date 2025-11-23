from waitress import serve
from flask import Flask
import logging

from pomelo.config import Config
from pomelo.caddy import init_caddy
from pomelo.plugin import init_plugins
from pomelo.routes import init_routes
from pomelo.wizard import wizard_app, wizard_init


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

    return app


def start():
    app = boot()
    serve(app, listen=f"*:{Config.pomelo_port}", url_scheme="https")


def start_dev():
    log = logging.getLogger("werkzeug")
    log.setLevel(logging.ERROR)
    app = boot()
    app.run(port=Config.pomelo_port, debug=True)
