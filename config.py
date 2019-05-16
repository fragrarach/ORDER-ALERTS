from quatro import sigm_connect, log_connect


class Config:
    LISTEN_CHANNEL = 'alert'

    def __init__(self):
        self.sigm_connection, self.sigm_db_cursor = sigm_connect(Config.LISTEN_CHANNEL)
        self.log_connection, self.log_db_cursor = log_connect()
