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
                AND NEW.ord_type NOT IN (9, 10)
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
                and NEW.ord_status IN ('A', 'B', 'E')
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
            
            IF
                NEW.ord_status NOT IN ('C', 'F', 'I')
                AND EXISTS (
                    WITH children AS (
                        SELECT pkt_master_prt_id, prt_id 
                        FROM part_kit
                        WHERE pkt_master_prt_id IN (
                            SELECT DISTINCT ol.prt_id
                            FROM order_line ol
                            LEFT JOIN part_kit pk ON pk.prt_id = ol.prt_id
                            LEFT JOIN part_kit pk2 ON pk2.pkt_master_prt_id = ol.prt_id
                            WHERE ord_no = NEW.ord_no
                            AND orl_kitmaster_id = 0
                        )
                    )
                    SELECT DISTINCT ord_no
                    FROM order_line ol
                    LEFT JOIN part_kit pk ON pk.prt_id = ol.prt_id
                    LEFT JOIN part_kit pk2 ON pk2.pkt_master_prt_id = ol.prt_id
                    WHERE ord_no = NEW.ord_no
                    AND orl_kitmaster_id = 0
                    AND EXISTS (
                        SELECT prt_id
                        FROM children
                        WHERE pkt_master_prt_id = ol.prt_id
                        AND prt_id NOT IN (
                            SELECT prt_id
                            FROM order_line
                            WHERE orl_kitmaster_id = ol.orl_id
                        )
                    )
                )
            THEN
                PERFORM pg_notify(
                    'alert', '' 
                    || 'ord_no' || ', '
                    || NEW.ord_no::text || ', '
                    || 'MISSING COMPONENT' || ', '
                    || sigm_str || ''
                );
            END IF;
            
            IF
                NEW.ord_status NOT IN ('C', 'F', 'I')
                AND EXISTS (
                    SELECT DISTINCT ord_no
                    FROM order_line ol
                    LEFT JOIN part_kit pk ON pk.prt_id = ol.prt_id
                    LEFT JOIN part_kit pk2 ON pk2.pkt_master_prt_id = ol.prt_id
                    WHERE ord_no = NEW.ord_no
                    AND pk.pkt_qty * (
                        SELECT orl_quantity 
                        FROM order_line ol2 
                        WHERE ord_no = NEW.ord_no 
                        AND ol2.orl_id = ol.orl_kitmaster_id
                    ) <> ol.orl_quantity
                    AND pk.pkt_master_prt_id IN (
                        SELECT prt_id 
                        FROM order_line 
                        WHERE ord_no = NEW.ord_no 
                    )
                )
            THEN
                PERFORM pg_notify(
                    'alert', '' 
                    || 'ord_no' || ', '
                    || NEW.ord_no::text || ', '
                    || 'COMPONENT MULTIPLIER' || ', '
                    || sigm_str || ''
                );
            END IF;
        END IF;
        
        IF
            NEW.ord_id <> OLD.ord_id OR  
            NEW.orl_first_id <> OLD.orl_first_id OR  
            NEW.ord_line_nb <> OLD.ord_line_nb OR  
            NEW.ord_date <> OLD.ord_date OR  
            NEW.cli_id <> OLD.cli_id OR  
            NEW.ord_no <> OLD.ord_no OR  
            NEW.inv_cli_id <> OLD.inv_cli_id OR  
            NEW.ord_finv_to_cli <> OLD.ord_finv_to_cli OR  
            NEW.ord_notes_stat <> OLD.ord_notes_stat OR  
            NEW.ord_note1 <> OLD.ord_note1 OR  
            NEW.ord_note2 <> OLD.ord_note2 OR  
            NEW.ord_note3 <> OLD.ord_note3 OR  
            NEW.ord_note4 <> OLD.ord_note4 OR  
            NEW.cli_inv_note1 <> OLD.cli_inv_note1 OR  
            NEW.cli_inv_note2 <> OLD.cli_inv_note2 OR  
            NEW.ord_pckslp_no1 <> OLD.ord_pckslp_no1 OR  
            NEW.ord_pckslp_no2 <> OLD.ord_pckslp_no2 OR  
            NEW.ord_pckslp_no3 <> OLD.ord_pckslp_no3 OR  
            NEW.ord_pckslp_no4 <> OLD.ord_pckslp_no4 OR  
            NEW.ord_ship_dt1 <> OLD.ord_ship_dt1 OR  
            NEW.ord_ship_dt2 <> OLD.ord_ship_dt2 OR  
            NEW.ord_ship_dt3 <> OLD.ord_ship_dt3 OR  
            NEW.ord_ship_dt4 <> OLD.ord_ship_dt4 OR  
            NEW.ord_inv_no1 <> OLD.ord_inv_no1 OR  
            NEW.ord_inv_no2 <> OLD.ord_inv_no2 OR  
            NEW.ord_inv_no3 <> OLD.ord_inv_no3 OR  
            NEW.ord_inv_no4 <> OLD.ord_inv_no4 OR  
            NEW.ord_status <> OLD.ord_status OR  
            NEW.ord_req_dt <> OLD.ord_req_dt OR  
            NEW.ord_cancel_dt <> OLD.ord_cancel_dt OR  
            NEW.ord_pmt_term <> OLD.ord_pmt_term OR  
            NEW.ord_fpmt_term <> OLD.ord_fpmt_term OR  
            NEW.ord_fcli_dscnt <> OLD.ord_fcli_dscnt OR  
            NEW.ord_ship_term <> OLD.ord_ship_term OR  
            NEW.ord_fship_term <> OLD.ord_fship_term OR  
            NEW.car_name <> OLD.car_name OR  
            NEW.car_fname <> OLD.car_fname OR  
            NEW.ter_id <> OLD.ter_id OR  
            NEW.ord_fter_id <> OLD.ord_fter_id OR  
            NEW.ord_fship <> OLD.ord_fship OR  
            NEW.sal_id <> OLD.sal_id OR  
            NEW.ord_fsal_id <> OLD.ord_fsal_id OR  
            NEW.ord_fsal_comm <> OLD.ord_fsal_comm OR  
            NEW.cli_del_name1 <> OLD.cli_del_name1 OR  
            NEW.cli_del_name2 <> OLD.cli_del_name2 OR  
            NEW.cli_del_addr <> OLD.cli_del_addr OR  
            NEW.cli_del_city <> OLD.cli_del_city OR  
            NEW.cli_del_pc <> OLD.cli_del_pc OR  
            NEW.cli_phone1 <> OLD.cli_phone1 OR  
            NEW.ord_fdel <> OLD.ord_fdel OR  
            NEW.inv_name1 <> OLD.inv_name1 OR  
            NEW.inv_name2 <> OLD.inv_name2 OR  
            NEW.inv_addr <> OLD.inv_addr OR  
            NEW.inv_city <> OLD.inv_city OR  
            NEW.inv_pc <> OLD.inv_pc OR  
            NEW.inv_phone <> OLD.inv_phone OR  
            NEW.ord_bo_accptd <> OLD.ord_bo_accptd OR  
            NEW.ord_pckslp_stat1 <> OLD.ord_pckslp_stat1 OR  
            NEW.ord_pckslp_stat2 <> OLD.ord_pckslp_stat2 OR  
            NEW.ord_pckslp_stat3 <> OLD.ord_pckslp_stat3 OR  
            NEW.ord_pckslp_stat4 <> OLD.ord_pckslp_stat4 OR  
            NEW.cli_dscnt_fixed <> OLD.cli_dscnt_fixed OR  
            NEW.sal_comm_fixed <> OLD.sal_comm_fixed OR  
            NEW.ord_cli_ord_no <> OLD.ord_cli_ord_no OR  
            NEW.ord_use_ship_amnt <> OLD.ord_use_ship_amnt OR  
            NEW.inv_pckslp_prnfmt <> OLD.inv_pckslp_prnfmt OR  
            NEW.inv_prnfmt <> OLD.inv_prnfmt OR  
            NEW.ord_export <> OLD.ord_export OR  
            -- NEW.prj_no <> OLD.prj_no OR  
            NEW.cod_no <> OLD.cod_no OR  
            NEW.ord_ftax <> OLD.ord_ftax OR  
            NEW.ord_finv_addr <> OLD.ord_finv_addr OR  
            NEW.ord_inv_onhold <> OLD.ord_inv_onhold OR  
            NEW.ord_prj_add_class <> OLD.ord_prj_add_class OR  
            -- NEW.ord_prj_add_no <> OLD.ord_prj_add_no OR  
            NEW.ord_prnfmt <> OLD.ord_prnfmt OR  
            NEW.acm_id <> OLD.acm_id OR  
            NEW.inv_del_fax <> OLD.inv_del_fax OR  
            NEW.inv_fax <> OLD.inv_fax OR  
            NEW.ord_imported <> OLD.ord_imported OR  
            NEW.whs_no <> OLD.whs_no OR  
            NEW.ord_expir_dt <> OLD.ord_expir_dt OR  
            NEW.ord_orig_req_dt <> OLD.ord_orig_req_dt OR  
            NEW.ord_req_time <> OLD.ord_req_time OR  
            NEW.ord_oreq_time <> OLD.ord_oreq_time OR  
            NEW.cli_taxe_group_no <> OLD.cli_taxe_group_no OR  
            NEW.ord_taxe_1_no <> OLD.ord_taxe_1_no OR  
            NEW.cli_exempt1_no <> OLD.cli_exempt1_no OR  
            NEW.ord_taxe_2_no <> OLD.ord_taxe_2_no OR  
            NEW.cli_exempt2_no <> OLD.cli_exempt2_no OR  
            NEW.ord_taxe_3_no <> OLD.ord_taxe_3_no OR  
            NEW.cli_exempt3_no <> OLD.cli_exempt3_no OR  
            NEW.ord_taxe_4_no <> OLD.ord_taxe_4_no OR  
            NEW.cli_exempt4_no <> OLD.cli_exempt4_no OR  
            NEW.ord_taxe_5_no <> OLD.ord_taxe_5_no OR  
            NEW.cli_exempt5_no <> OLD.cli_exempt5_no OR  
            NEW.cli_dscnt <> OLD.cli_dscnt OR  
            NEW.ord_ship_rate <> OLD.ord_ship_rate OR  
            NEW.sal_comm <> OLD.sal_comm OR  
            NEW.ord_pship_rate <> OLD.ord_pship_rate OR  
            NEW.ord_tship_rate <> OLD.ord_tship_rate OR  
            NEW.ord_ship_amnt <> OLD.ord_ship_amnt OR  
            NEW.ord_pkg_cost <> OLD.ord_pkg_cost OR  
            NEW.inv_pmt_dscnt <> OLD.inv_pmt_dscnt OR  
            NEW.ord_use_edi <> OLD.ord_use_edi OR  
            NEW.cli_scac <> OLD.cli_scac OR  
            NEW.ord_sb_authorized <> OLD.ord_sb_authorized OR  
            NEW.ord_sb_assigned <> OLD.ord_sb_assigned OR  
            NEW.ord_sb_truck_no <> OLD.ord_sb_truck_no OR  
            NEW.ord_sb_load_order <> OLD.ord_sb_load_order OR  
            NEW.ord_edi_invrpt <> OLD.ord_edi_invrpt OR  
            NEW.ord_edi_invext <> OLD.ord_edi_invext OR  
            NEW.ord_ptax1_amnt <> OLD.ord_ptax1_amnt OR  
            NEW.ord_ptax2_amnt <> OLD.ord_ptax2_amnt OR  
            NEW.ord_ptax3_amnt <> OLD.ord_ptax3_amnt OR  
            NEW.ord_ptax4_amnt <> OLD.ord_ptax4_amnt OR  
            NEW.ord_ptax5_amnt <> OLD.ord_ptax5_amnt OR  
            NEW.ord_ttax1_amnt <> OLD.ord_ttax1_amnt OR  
            NEW.ord_ttax2_amnt <> OLD.ord_ttax2_amnt OR  
            NEW.ord_ttax3_amnt <> OLD.ord_ttax3_amnt OR  
            NEW.ord_ttax4_amnt <> OLD.ord_ttax4_amnt OR  
            NEW.ord_ttax5_amnt <> OLD.ord_ttax5_amnt OR  
            NEW.ord_type <> OLD.ord_type OR  
            NEW.mot_id <> OLD.mot_id OR  
            NEW.ord_inv_method <> OLD.ord_inv_method OR  
            NEW.ord_print_pckslp <> OLD.ord_print_pckslp OR  
            NEW.ord_print_invoice <> OLD.ord_print_invoice OR  
            -- NEW.ord_pmt_term_desc <> OLD.ord_pmt_term_desc OR  
            NEW.ord_ship_term_desc <> OLD.ord_ship_term_desc OR  
            NEW.en_creation <> OLD.en_creation OR  
            NEW.ord_ord_sendmail <> OLD.ord_ord_sendmail OR  
            NEW.ord_psc_sendmail <> OLD.ord_psc_sendmail OR  
            NEW.ord_inv_sendmail <> OLD.ord_inv_sendmail OR  
            NEW.ord_res_sendmail <> OLD.ord_res_sendmail OR  
            NEW.ord_ord_email_fmt <> OLD.ord_ord_email_fmt OR  
            NEW.ord_psc_email_fmt <> OLD.ord_psc_email_fmt OR  
            NEW.ord_inv_email_fmt <> OLD.ord_inv_email_fmt OR  
            NEW.ord_res_email_fmt <> OLD.ord_res_email_fmt OR  
            NEW.ord_ord_email_subj <> OLD.ord_ord_email_subj OR  
            NEW.ord_psc_email_subj <> OLD.ord_psc_email_subj OR  
            NEW.ord_inv_email_subj <> OLD.ord_inv_email_subj OR  
            NEW.ord_res_email_subj <> OLD.ord_res_email_subj OR  
            NEW.ord_ord_email_to <> OLD.ord_ord_email_to OR  
            NEW.ord_psc_email_to <> OLD.ord_psc_email_to OR  
            NEW.ord_inv_email_to <> OLD.ord_inv_email_to OR  
            NEW.ord_res_email_to <> OLD.ord_res_email_to OR  
            NEW.ord_ord_email_cc <> OLD.ord_ord_email_cc OR  
            NEW.ord_psc_email_cc <> OLD.ord_psc_email_cc OR  
            NEW.ord_inv_email_cc <> OLD.ord_inv_email_cc OR  
            NEW.ord_res_email_cc <> OLD.ord_res_email_cc OR  
            NEW.ord_ord_email_bcc <> OLD.ord_ord_email_bcc OR  
            NEW.ord_psc_email_bcc <> OLD.ord_psc_email_bcc OR  
            NEW.ord_inv_email_bcc <> OLD.ord_inv_email_bcc OR  
            NEW.ord_res_email_bcc <> OLD.ord_res_email_bcc OR  
            NEW.ord_ord_email_sent <> OLD.ord_ord_email_sent OR  
            NEW.ord_res_email_sent <> OLD.ord_res_email_sent OR  
            NEW.ord_printed <> OLD.ord_printed OR  
            NEW.ord_pkl_prnfmt <> OLD.ord_pkl_prnfmt OR  
            NEW.ord_pkl_printed <> OLD.ord_pkl_printed OR  
            NEW.ord_lbl_prnfmt <> OLD.ord_lbl_prnfmt OR  
            NEW.ord_deposit <> OLD.ord_deposit OR  
            NEW.ord_psl_sendmail <> OLD.ord_psl_sendmail OR  
            NEW.ord_psl_email_fmt <> OLD.ord_psl_email_fmt OR  
            NEW.ord_psl_email_subj <> OLD.ord_psl_email_subj OR  
            NEW.ord_psl_email_to <> OLD.ord_psl_email_to OR  
            NEW.ord_psl_email_cc <> OLD.ord_psl_email_cc OR  
            NEW.ord_psl_email_bcc <> OLD.ord_psl_email_bcc OR  
            NEW.ord_fpkg_cost <> OLD.ord_fpkg_cost OR  
            NEW.ord_sb_pallet_nb <> OLD.ord_sb_pallet_nb OR  
            NEW.ord_sb_load_note <> OLD.ord_sb_load_note OR  
            NEW.ord_use_asn_edi <> OLD.ord_use_asn_edi OR  
            NEW.ord_edi_asnrpt <> OLD.ord_edi_asnrpt OR  
            NEW.ord_edi_asnext <> OLD.ord_edi_asnext OR  
            NEW.ord_pnb_package <> OLD.ord_pnb_package OR  
            NEW.ord_fpnb_package <> OLD.ord_fpnb_package OR  
            NEW.ord_tnb_package <> OLD.ord_tnb_package OR  
            NEW.ord_ftnb_package <> OLD.ord_ftnb_package OR  
            NEW.ord_package_price <> OLD.ord_package_price OR  
            NEW.ord_pqty <> OLD.ord_pqty OR  
            NEW.ord_tqty <> OLD.ord_tqty OR  
            NEW.ord_pweight <> OLD.ord_pweight OR  
            NEW.ord_tweight <> OLD.ord_tweight OR  
            NEW.ord_pvolume <> OLD.ord_pvolume OR  
            NEW.ord_tvolume <> OLD.ord_tvolume OR  
            NEW.cli_del_email <> OLD.cli_del_email OR  
            NEW.inv_email <> OLD.inv_email OR  
            NEW.ord_sync_to_web <> OLD.ord_sync_to_web OR  
            NEW.ord_web_ord_no <> OLD.ord_web_ord_no OR  
            NEW.ord_websync_id <> OLD.ord_websync_id
        THEN
            PERFORM pg_notify(
                'alert', '' 
                || 'ord_no' || ', '
                || NEW.ord_no::text || ', '
                || 'CHANGE MADE' || ', '
                || sigm_str || ''
            );
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
    
ELSIF tg_table_name = 'planning_lot_detailed' THEN

    IF tg_op = 'UPDATE' THEN
        IF 
            NEW.pld_lvl <> 0
            AND NEW.prt_id IN (
                SELECT prt_master_id
                FROM bill_of_materials_mat
            )
            AND NEW.pld_qty_res = 0
            AND (
                SELECT pqt_real_qty 
                FROM part_quantity pq 
                WHERE pq.prt_id = NEW.prt_id
            ) >= (
                (
                    SELECT SUM(pld_qty_res)
                    FROM planning_lot_detailed 
                    WHERE prt_id = NEW.prt_id
                    AND pld_adj_flag = 'f'
                ) + NEW.pld_qty_for
            )
            AND (NEW.pld_adj_flag = 'f' OR OLD.pld_adj_flag = 'f')
        THEN
            PERFORM pg_notify(
                'alert', '' 
                || 'plq_lot_no' || ', '
                || NEW.plq_lot_no::text || ', '
                || 'UNCHECKED NEED CALCULATION' || ', '
                || sigm_str || ''
            );
        END IF;
    ELSIF tg_op = 'INSERT' THEN
        IF 
            NEW.pld_lvl <> 0
            AND NEW.prt_id IN (
                SELECT prt_master_id
                FROM bill_of_materials_mat
            )
            AND NEW.pld_qty_res = 0
            AND (
                SELECT pqt_real_qty 
                FROM part_quantity pq 
                WHERE pq.prt_id = NEW.prt_id
            ) >= (
                (
                    SELECT SUM(pld_qty_res)
                    FROM planning_lot_detailed 
                    WHERE prt_id = NEW.prt_id
                    AND pld_adj_flag = 'f'
                ) + NEW.pld_qty_for
            )
            AND NEW.pld_adj_flag = 'f'
        THEN
            PERFORM pg_notify(
                'alert', '' 
                || 'plq_lot_no' || ', '
                || NEW.plq_lot_no::text || ', '
                || 'UNCHECKED NEED CALCULATION' || ', '
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