CREATE OR REPLACE FUNCTION order_component_quantities(IN INTEGER, IN INTEGER)
  RETURNS TABLE(orl_sort_idx BIGINT, prt_no CHAR(15), fixed_qty BIGINT) AS
$BODY$ 
BEGIN
RETURN QUERY
    SELECT DISTINCT
        ol.orl_sort_idx, 
        ol.prt_no,
        (pk.pkt_qty * (
            SELECT orl_quantity 
            FROM order_line 
            WHERE ord_no = $1
            AND orl_id = $2
            )
        )::BIGINT fixed_qty
    FROM order_line ol
    LEFT JOIN part_kit pk ON pk.prt_id = ol.prt_id
    LEFT JOIN part_kit pk2 ON pk2.pkt_master_prt_id = ol.prt_id
    WHERE ord_no = $1
    AND pk.pkt_qty * (
        SELECT orl_quantity 
        FROM order_line ol2 
        WHERE ord_no = $1
        AND ol2.orl_id = $2
    ) <> ol.orl_quantity
AND pk.pkt_master_prt_id = (SELECT prt_id FROM order_line WHERE order_line.orl_id = ol.orl_kitmaster_id)
    AND ol.orl_kitmaster_id = $2
    ORDER BY orl_sort_idx
;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;
ALTER FUNCTION order_component_quantities(INTEGER, INTEGER)
  OWNER TO "SIGM";