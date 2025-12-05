from flask import request
import json
from pomelo.util import bail, buildResponse, forwardRequest
from pomelo.config import Config


def routeHandler(handlers, route):
    def inner(*args, **kwargs):
        try:
            # We can't watch filesystem events from inside a container, so
            # we just refresh the config at every request. Not super efficient,
            # but it's good enough for now.
            Config.load_config()
            response = forwardRequest(request, route)
            interceptedResponse = response

            for handler in handlers:
                interceptedResponse = handler(
                    *args, route, request, interceptedResponse, **kwargs
                )

            return buildResponse(interceptedResponse)
        except Exception as e:
            print("Hit error:", e, route, request, interceptedResponse)
            bail()

    inner.__name__ = route
    return inner


def config():
    return json.dumps(Config.data)


def init_routes(app, plugins):
    routes = {}
    for plugin in plugins:
        for k, v in plugin.paths().items():
            if k in routes:
                routes[k].append(v)
            else:
                routes[k] = [v]

    for route, handlers in routes.items():
        app.add_url_rule(
            route,
            view_func=routeHandler(handlers, route),
            methods=["POST", "GET", "PUT", "PATCH", "DELETE"],
        )

    app.add_url_rule(
        "/config",
        view_func=config,
        methods=["GET"],
    )
