from melon.config import Config


def logRequest(path, request):
    if False and Config.debug:
        print("New request")
        print("Path: ", path)
        print("Query: ", request.args)
        print("------\n")
