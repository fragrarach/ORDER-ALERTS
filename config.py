import quatro


class Config:
    LISTEN_CHANNEL = 'alert'

    def __init__(self):
        self.sigm_connection, self.sigm_db_cursor = quatro.sigm_connect(Config.LISTEN_CHANNEL)
        self.log_connection, self.log_db_cursor = quatro.log_connect()
