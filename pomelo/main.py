import logging

from waitress import serve
from flask import Flask
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask.logging import default_handler

from pomelo.config import Config
from pomelo.caddy import init_caddy
from pomelo.plugin import init_plugins
from pomelo.routes import init_routes
from pomelo.wizard import wizard_app, wizard_init


def init_app():
    app = Flask(__name__)
    return app


def init_limiter(app):
    limiter = Limiter(
        get_remote_address,
        app=app,
        default_limits=["1/second"],
        storage_uri="memory://",
    )
    limiter_logger = logging.getLogger("flask-limiter")
    limiter_logger.setLevel(logging.DEBUG)
    limiter_logger.addHandler(default_handler)

    return limiter


def boot():
    wizard_init()

    app = init_app()
    limiter = init_limiter(app)
    plugins = init_plugins()

    if Config.use_caddy:
        init_caddy()

    init_routes(app, plugins, limiter)

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
