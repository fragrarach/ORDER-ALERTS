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

    IF tg_op = 'INSERT' THEN
    
        IF
            NEW.inv_orig_inv_no = 0 
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
        END IF;
        
    ELSIF tg_op = 'UPDATE' THEN
        
        IF
            NEW.inv_status = 'F'
            AND NEW.inv_ship_amnt = 0
            AND NEW.inv_ship_term = 0
            AND NEW.inv_no <> 0
            AND NEW.inv_subtotal >= 0
        THEN 
            PERFORM pg_notify(
                'alert', '' 
                || 'inv_no' || ', '
                || NEW.inv_no::text || ', '
                || 'SHIPPING COST MISSING' || ', '
                || sigm_str || ''
            );
        END IF;
        
        IF
            NEW.inv_inv_sendmail = 'T'
            AND NEW.inv_inv_email_sent = 'F'
            AND NEW.inv_no <> 0
            AND NEW.inv_subtotal >= 0
        THEN 
            PERFORM pg_notify(
                'alert', '' 
                || 'inv_no' || ', '
                || NEW.inv_no::text || ', '
                || 'UNSENT INVOICE EMAIL' || ', '
                || sigm_str || ''
            );
        END IF;
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
    
        IF NEW.prj_no IS NULL THEN
        
            IF
                NEW.ord_status NOT IN ('C', 'F', 'I')
                AND NEW.ord_type <> 9
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
            END IF;
            
            IF
                NEW.ord_status NOT IN ('C', 'F', 'I')
                AND NEW.ord_type = 9
                AND (
                    SELECT CASE WHEN EXISTS (
                        SELECT ord_no
                        FROM order_line
                        WHERE ord_no = NEW.ord_no
                        AND prt_no <> ''
                        GROUP BY ord_no
                        HAVING COUNT(orl_id) = (
                            SELECT COUNT(orl_id)
                            FROM order_line
                            WHERE orl_quantity = 0
                            AND order_line.ord_no = NEW.ord_no
                            AND prt_no <> ''
                        )
                    ) THEN 1 ELSE 0 END
                ) = 1
            THEN
                PERFORM pg_notify(
                    'alert', '' 
                    || 'ord_no' || ', '
                    || NEW.ord_no::text || ', '
                    || 'COMPLETED BLANKET' || ', '
                    || sigm_str || ''
                );
            END IF;
            
            IF
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
            THEN
                PERFORM pg_notify(
                    'alert', '' 
                    || 'ord_no' || ', '
                    || NEW.ord_no::text || ', '
                    || 'NOT RESERVED' || ', '
                    || sigm_str || ''
                );
            END IF;
                
            IF
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
            END IF;
                
            IF
                (
                    (NEW.ord_status = 'A')
                    OR (NEW.ord_status = 'B' AND NEW.ord_bo_accptd <> 'true')
                )
                AND (
                    SELECT CASE WHEN EXISTS (
                        WITH orl_dates AS (
                            SELECT ord_no, orl_req_dt 
                            FROM order_line
                            WHERE orl_req_dt IS NOT NULL
                            AND ord_no IN (
                                SELECT ord_no
                                FROM order_line
                                WHERE orl_req_dt IS NOT NULL
                                GROUP BY ord_no
                                HAVING COUNT(*) > 1
                            )
                            GROUP BY ord_no, orl_req_dt
                            ORDER BY ord_no
                        )
                        SELECT ord_no
                        FROM orl_dates
                        WHERE NEW.ord_no = ord_no
                        GROUP BY ord_no
                        HAVING COUNT(*) > 1
                        ORDER BY ord_no
                    ) THEN 1 ELSE 0 END
                ) = 1
            THEN
                PERFORM pg_notify(
                    'alert', '' 
                    || 'ord_no' || ', '
                    || NEW.ord_no::text || ', '
                    || 'LINE DATES' || ', '
                    || sigm_str || ''
                );
            END IF;
            
            IF
                (
                    SELECT CASE WHEN EXISTS (
                        select orl_id
                        FROM order_line
                        WHERE order_line.ord_no = NEW.ord_no
                        AND prt_no IN (
                            select prt_no
                            from part
                            where prt_sort ILIKE 'ASV%'
                            AND prt_sort <> 'ASV Tabl'
                            and prt_type = 'F'
                            order by prt_no
                        )
                    ) THEN 1 ELSE 0 END
                ) = 1
                AND (
                    SELECT CASE WHEN NOT EXISTS (
                        select orl_id
                        FROM order_line
                        WHERE order_line.ord_no = NEW.ord_no
                        AND prt_no = 'AE750'
                    ) THEN 1 ELSE 0 END
                ) = 1
            THEN
                PERFORM pg_notify(
                    'alert', '' 
                    || 'ord_no' || ', '
                    || NEW.ord_no::text || ', '
                    || 'MISSING AE750' || ', '
                    || sigm_str || ''
                );
            END IF;
                
            IF
                NEW.ord_pmt_term = 4
                and NEW.ord_status IN ('A', 'B')
                and NEW.ord_type = 1
                and NEW.ord_pkg_cost = 0
            THEN
                PERFORM pg_notify(
                    'alert', '' 
                    || 'ord_no' || ', '
                    || NEW.ord_no::text || ', '
                    || 'ZERO BANK FEES' || ', '
                    || sigm_str || ''
                );
            END IF;
            
            IF
                NEW.ord_status NOT IN ('C', 'F', 'I')
                AND EXISTS (
                    SELECT ol.ord_no
                    FROM order_line ol
                    JOIN order_header oh ON oh.ord_no = ol.ord_no
                    WHERE oh.ord_type = 1
                    AND oh.ord_no = NEW.ord_no
                    AND oh.cli_id = NEW.cli_id
                    AND prt_no <> ''
                    AND prt_no IN (
                        SELECT prt_no
                        FROM order_line ol_2
                        JOIN order_header oh_2 ON oh_2.ord_no = ol_2.ord_no
                        WHERE ol_2.ord_no <> ol.ord_no
                        AND oh_2.ord_type = 9
                        AND oh.cli_id = oh_2.cli_id
                        AND prt_no <> ''
                    )
                )
            THEN
                PERFORM pg_notify(
                    'alert', '' 
                    || 'ord_no' || ', '
                    || NEW.ord_no::text || ', '
                    || 'EXISTING BLANKET' || ', '
                    || sigm_str || ''
                );
            END IF;
        END IF;
        
        IF
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
        END IF;
            
        IF
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

        IF
            OLD.ord_status IN ('D', 'E') 
            AND NEW.ord_status IN ('A', 'B') 
            AND NEW.ord_date <> NOW()::DATE
        THEN
            PERFORM pg_notify(
                'alert', '' 
                || 'ord_no' || ', '
                || NEW.ord_no::text || ', '
                || 'CONVERTED DATE' || ', '
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
    
ELSIF tg_table_name = 'part_transaction' THEN

    IF tg_op = 'INSERT' THEN
    
        IF
            NEW.prt_type = 'A'
            AND NEW.ptn_qty_after < 0
        THEN
            PERFORM pg_notify(
                'alert', '' 
                || 'ptn_id' || ', '
                || NEW.ptn_id::text || ', '
                || 'NEGATIVE QUANTITY' || ', '
                || sigm_str || ''
            );
        END IF;
        
        IF
            EXISTS (
                SELECT *
                FROM invoicing_line 
                WHERE inv_id IN (
                    SELECT inv_id
                    FROM invoicing
                    WHERE ord_no IN (
                        SELECT ord_no 
                        FROM planning_lot_detailed 
                        WHERE plq_lot_no = NEW.plq_lot_no
                        AND ord_no <> 0
                    )
                )
            )
        THEN
            PERFORM pg_notify(
                'alert', '' 
                || 'plq_lot_no' || ', '
                || NEW.plq_lot_no::text || ', '
                || 'INVOICED PRODUCTION' || ', '
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