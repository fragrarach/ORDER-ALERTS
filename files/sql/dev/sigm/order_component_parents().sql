CREATE OR REPLACE FUNCTION order_component_parents(IN INTEGER)
  RETURNS TABLE(orl_sort_idx BIGINT, prt_no CHAR(15), orl_id BIGINT) AS
$BODY$ 
BEGIN
RETURN QUERY
    SELECT DISTINCT 
        (SELECT order_line.orl_sort_idx FROM order_line WHERE order_line.orl_id  = ol.orl_id) orl_sort_idx,
        (SELECT order_line.prt_no FROM order_line WHERE order_line.orl_id  = ol.orl_id) prt_no,
        ol.orl_id
    FROM order_line ol
    LEFT JOIN part_kit pk ON pk.prt_id = ol.prt_id
    LEFT JOIN part_kit pk2 ON pk2.pkt_master_prt_id = ol.prt_id
    WHERE ord_no = $1
AND ol.prt_id = pk2.pkt_master_prt_id
    ORDER BY orl_sort_idx
;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;
ALTER FUNCTION order_component_parents(INTEGER)
  OWNER TO "SIGM";