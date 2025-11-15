from flask import request, abort
from melon.util import bail, buildResponse, forwardRequest
from melon.store import store
from melon.constants import TOKEN_KEY


def routeHandler(handlers, route):
    def inner(*args):
        try:
            if store.token is None and TOKEN_KEY in request.args:
                store.setToken(request.args[TOKEN_KEY])

            response = forwardRequest(request, route)
            interceptedResponse = response

            for handler in handlers:
                interceptedResponse = handler(
                    *args, route, request, interceptedResponse
                )

            return buildResponse(interceptedResponse)
        except Exception as e:
            print(e)
            bail()

    inner.__name__ = route
    return inner


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
