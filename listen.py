from sigm import sigm_connect, log_connect
from config import Config
from data import payload_handler


def listen():
    while 1:
        try:
            Config.SIGM_CONNECTION.poll()
        except:
            print('Database cannot be accessed, PostgreSQL service probably rebooting')
            try:
                Config.SIGM_CONNECTION.close()
                Config.SIGM_CONNECTION, sigm_db_cursor = sigm_connect(Config.LISTEN_CHANNEL)
                Config.LOG_CONNECTION.close()
                Config.LOG_CONNECTION, Config.log_db_cursor = log_connect()
            except:
                pass
        else:
            Config.SIGM_CONNECTION.commit()
            while Config.SIGM_CONNECTION.notifies:
                notify = Config.SIGM_CONNECTION.notifies.pop()
                raw_payload = notify.payload
                print(f'Alert Triggered : {raw_payload}')
                payload_handler(raw_payload)


if __name__ == "__main__":
    listen()
