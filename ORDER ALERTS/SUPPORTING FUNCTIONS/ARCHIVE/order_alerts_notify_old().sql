CREATE OR REPLACE FUNCTION order_alerts_notify()
  RETURNS trigger AS
$BODY$
DECLARE
sigm_str TEXT;
BEGIN
sigm_str := (
    SELECT application_name 
    FROM pg_stat_activity 
    WHERE pid IN (
        SELECT pg_backend_pid()
    )
);

IF tg_table_name = 'invoicing' THEN

    IF
        tg_op = 'INSERT'
        AND NEW.inv_orig_inv_no = 0 
        AND (
            SELECT ord_bo_accptd 
            FROM order_header 
            WHERE order_header.ord_no = NEW.ord_no
        )::text = 'false'
        AND (
            SELECT CASE WHEN EXISTS (
                SELECT orl_id
                FROM order_line 
                WHERE ord_no = NEW.ord_no
                AND (orl_quantity - orl_qty_ready) <> 0
            ) THEN 1 ELSE 0 END
        ) = 1
    THEN 
        PERFORM pg_notify(
            'alert', '' 
            || 'ord_no' || ', '
            || NEW.ord_no::text || ', '
            || 'BO NOT ALLOWED' || ', '
            || sigm_str || ''
        );
        
    ELSIF
        tg_op = 'UPDATE'
        AND NEW.inv_status = 'F'
        AND NEW.inv_ship_amnt = 0
        AND NEW.inv_ship_term = 0
        AND NEW.inv_no <> 0
    THEN 
        PERFORM pg_notify(
            'alert', '' 
            || 'inv_no' || ', '
            || NEW.inv_no::text || ', '
            || 'SHIPPING COST MISSING' || ', '
            || sigm_str || ''
        );
    END IF;
    
ELSIF tg_table_name = 'invoicing_line' THEN

    IF 
        tg_op = 'UPDATE'
        AND OLD.inl_status <> 'A'
        AND NEW.inl_status = 'A'
    THEN
        PERFORM pg_notify(
            'alert', '' 
            || 'inv_pckslp_no' || ', '
            || NEW.inv_pckslp_no::text || ', '
            || 'CANCELLED PACKING SLIP' || ', '
            || sigm_str || ''
        );
    END IF;
    
ELSIF tg_table_name = 'order_header' THEN

    IF tg_op = 'UPDATE' THEN
    
        IF
            NEW.ord_status NOT IN ('C', 'F', 'I')
            AND TRIM(NEW.ord_pmt_term_desc) = ''
            AND (
                SELECT CASE WHEN EXISTS (
                    SELECT orl_id
                    FROM order_line
                    WHERE ord_no = NEW.ord_no
                    AND orl_quantity = 0
                    AND prt_no <> ''
                ) THEN 1 ELSE 0 END
            ) = 1
        THEN
            PERFORM pg_notify(
                'alert', '' 
                || 'ord_no' || ', '
                || NEW.ord_no::text || ', '
                || 'ZERO QUANTITY' || ', '
                || sigm_str || ''
            );
            
        ELSIF
            NEW.ord_status <> 'E' 
            AND OLD.ord_status <> 'E'
            AND NEW.ord_type <> 9
            AND NEW.ord_type <> 10
            AND (
                SELECT CASE WHEN EXISTS (
                    SELECT orl_id
                    FROM order_line 
                    WHERE ord_no = NEW.ord_no
                    AND orl_quantity <> orl_reserved_qty
                    AND (
                        orl_quantity <> orl_ship_qty
                        OR orl_quantity <> orl_qty_ready + orl_ship_qty + orl_reserved_qty
                        OR orl_quantity <> orl_ship_qty + orl_reserved_qty
                    )
                ) THEN 1 ELSE 0 END
            ) = 1
            --blank "ord_pmt_term_desc" field implies the order has been closed in SIGM (X button, escape, arrows)
            --this prevents duplicate alerts (may stop working if we acquire the project module, or on SIGM update)
            AND TRIM(NEW.ord_pmt_term_desc) = ''
        THEN
            PERFORM pg_notify(
                'alert', '' 
                || 'ord_no' || ', '
                || NEW.ord_no::text || ', '
                || 'NOT RESERVED' || ', '
                || sigm_str || ''
            );
            
        ELSIF
            OLD.ord_status IN ('A', 'B') 
            AND NEW.ord_status = 'C'
        THEN
            PERFORM pg_notify(
                'alert', '' 
                || 'ord_no' || ', '
                || NEW.ord_no::text || ', '
                || 'ORDER CANCELLED' || ', '
                || sigm_str || ''
            );
            
        ELSIF
            OLD.ord_type <> 9 
            AND NEW.ord_type = 9
        THEN
            PERFORM pg_notify(
                'alert', '' 
                || 'ord_no' || ', '
                || NEW.ord_no::text || ', '
                || 'NEW BLANKET' || ', '
                || sigm_str || ''
            );
            
        ELSIF
            OLD.ord_type <> 10 
            AND NEW.ord_type = 10
        THEN
            PERFORM pg_notify(
                'alert', '' 
                || 'ord_no' || ', '
                || NEW.ord_no::text || ', '
                || 'NEW RELEASE' || ', '
                || sigm_str || ''
            );
        END IF;
    END IF;
    
ELSIF tg_table_name = 'client' THEN

    IF tg_op = 'UPDATE' THEN
    
        IF
            NEW.cli_bo_accptd::text = 'true' 
            AND (
                NEW.cli_creation_dt = current_date 
                OR OLD.cli_active <> NEW.cli_active
            )
        THEN
            PERFORM pg_notify(
                'alert', '' 
                || 'cli_no' || ', '
                || NEW.cli_no::text || ', '
                || 'BO ALLOWED' || ', '
                || sigm_str || ''
            );
        END IF;
    END IF;
END IF;

RETURN NULL;

END;
$BODY$
  LANGUAGE plpgsql VOLATILE
  COST 100;
ALTER FUNCTION order_alerts_notify()
  OWNER TO "SIGM";