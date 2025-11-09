from melon.config import Config


class Store:
    token = Config.token

    def setToken(self, token):
        self.token = token
        Config.writeSetting("token", token)


store = Store()
