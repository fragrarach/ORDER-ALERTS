DROP FUNCTION order_existing_blankets(integer);
CREATE OR REPLACE FUNCTION order_existing_blankets(IN INTEGER)
  RETURNS TABLE(prt_no CHAR(15), ord_no INTEGER) AS
$BODY$ 
BEGIN
RETURN QUERY
    SELECT blanket_orders.prt_no, blanket_orders.ord_no 
    FROM blanket_orders 
    WHERE cli_no IN (
        SELECT c.cli_no
        FROM order_header oh
        JOIN client c ON c.cli_id = oh.cli_id
        WHERE oh.ord_no = $1
    )
    AND blanket_orders.prt_no IN (
        SELECT ol.prt_no
        FROM order_header oh
        JOIN order_line ol ON ol.ord_no = oh.ord_no
        WHERE ol.ord_no = $1
    )
;
END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100
  ROWS 1000;
ALTER FUNCTION order_existing_blankets(INTEGER)
  OWNER TO "SIGM";