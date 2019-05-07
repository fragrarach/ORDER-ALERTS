CREATE TABLE IF NOT EXISTS alerts (
    time_stamp      TIMESTAMP WITHOUT TIME ZONE,
    alert           TEXT,
    ref_type        TEXT,
    reference       TEXT,
    user_name       TEXT,
    station         TEXT
);