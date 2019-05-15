from data import payload_handler
import statements


def listen_task(config, notify):
    raw_payload = notify.payload
    print(f'Alert Triggered : {raw_payload}')
    timestamp, alert, ref_type, ref, user, station = payload_handler(raw_payload)
    statements.duplicate_alert_check(config, timestamp, alert, ref_type, ref, user, station)
