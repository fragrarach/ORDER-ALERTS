CREATE OR REPLACE FUNCTION duplicate_alert_check(
        IN TIMESTAMP WITHOUT TIME ZONE,
        TEXT,
        TEXT,
        TEXT,
        TEXT,
        TEXT
)
RETURNS TABLE(
        duplicate_check INTEGER
) AS
$BODY$
BEGIN
RETURN QUERY

SELECT CASE WHEN NOT EXISTS (
        SELECT *
        FROM alerts
        WHERE time_stamp + 1 * interval '1 hour' > $1::timestamp
        AND time_stamp < $1::timestamp
        AND alert = $2
        AND ref_type = $3
        AND reference = $4
        AND user_name = $5
        AND station = $6
) THEN 1 ELSE 0 END AS duplicate_check
;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;
ALTER FUNCTION duplicate_alert_check(
        IN TIMESTAMP WITHOUT TIME ZONE,
        TEXT,
        TEXT,
        TEXT,
        TEXT,
        TEXT
)
  OWNER TO "SIGM";