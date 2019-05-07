CREATE OR REPLACE FUNCTION order_missing_components(IN INTEGER, IN INTEGER)
  RETURNS TABLE(orl_sort_idx BIGINT, prt_no CHAR(15)) AS
$BODY$ 
BEGIN
RETURN QUERY
    WITH children AS (
        SELECT pkt_master_prt_id, prt_id 
        FROM part_kit pk
        WHERE pkt_master_prt_id IN (
            SELECT DISTINCT ol.prt_id
            FROM order_line ol
            LEFT JOIN part_kit pk ON pk.prt_id = ol.prt_id
            LEFT JOIN part_kit pk2 ON pk2.pkt_master_prt_id = ol.prt_id
            WHERE ord_no = $1
            AND orl_kitmaster_id = 0
        )
    )
    SELECT DISTINCT ol.orl_sort_idx, ol.prt_no
    FROM order_line ol
    LEFT JOIN part_kit pk ON pk.prt_id = ol.prt_id
    LEFT JOIN part_kit pk2 ON pk2.pkt_master_prt_id = ol.prt_id
    WHERE ord_no = $1
    AND orl_kitmaster_id = $2
    ORDER BY ol.orl_sort_idx
;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;
ALTER FUNCTION order_missing_components(INTEGER, INTEGER)
  OWNER TO "SIGM";