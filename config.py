from os.path import dirname, abspath
from quatro import sigm_connect, log_connect


class Config:
    def __init__(self, main_file_path):
        self.main_file_path = main_file_path
        self.parent_dir = dirname(abspath(main_file_path))
        self.sigm_connection = None
        self.sigm_db_cursor = None
        self.log_connection = None
        self.log_db_cursor = None
        self.LISTEN_CHANNEL = 'alert'
        self.user_emails = {
            'JAN': 'jan.z@quatroair.com',
            'SANJAY': 'sanjay.m@quatroair.com',
            'ERICK': 'erick.h@quatroair.com',
            'MARK': 'mark.s@quatroair.com',
            'RECEPTION': 'service@aerofil.ca',
            'STEPHEN': 'stephen.f@quatroair.com'
        }

    def sql_connections(self):
        self.sigm_connection, self.sigm_db_cursor = sigm_connect(self.LISTEN_CHANNEL)
        self.log_connection, self.log_db_cursor = log_connect()
