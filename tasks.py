from data import payload_handler
import statements
from quatro import log


def listen_task(notify):
    raw_payload = notify.payload
    log(f'Alert Triggered : {raw_payload}')
    timestamp, alert, ref_type, ref, user, station = payload_handler(raw_payload)
    statements.duplicate_alert_check(timestamp, alert, ref_type, ref, user, station)
