from melon.config import Config


class Store:
    token = Config.plex_token

    def setToken(self, token):
        self.token = token
        Config.write_setting("token", token)


store = Store()
