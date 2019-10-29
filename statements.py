from quatro import sql_query, scalar_data, tabular_data, log, configuration as c
import data


# Pull 'cli_id' record from 'order_header' table based on 'ord_no' record
def ord_no_cli_id(ord_no):
    sql_exp = f'SELECT cli_id FROM order_header WHERE ord_no = {ord_no}'
    result_set = sql_query(sql_exp, c.config.sigm_db_cursor)
    cli_id = scalar_data(result_set)
    return cli_id


# Pull 'cli_id' record from 'order_header' table based on 'ord_no' record
def orl_id_ord_no(orl_id):
    sql_exp = f'SELECT ord_no FROM order_line WHERE orl_id = {orl_id}'
    result_set = sql_query(sql_exp, c.config.sigm_db_cursor)
    ord_no = scalar_data(result_set)
    return ord_no


# Pull 'cli_name1' record from 'client' table based on 'cli_id' record
def cli_id_cli_name1(cli_id):
    sql_exp = f'SELECT cli_name1 FROM client WHERE cli_id = {cli_id}'
    result_set = sql_query(sql_exp, c.config.sigm_db_cursor)
    cli_name1 = scalar_data(result_set)
    return cli_name1


# Pull 'ord_no' record from 'invoicing' table based on 'inv_pckslp_no' record
def packing_slip_ord_no(inv_pckslp_no):
    sql_exp = f'SELECT ord_no FROM invoicing WHERE inv_pckslp_no = {inv_pckslp_no}'
    result_set = sql_query(sql_exp, c.config.sigm_db_cursor)
    ord_no = scalar_data(result_set)
    return ord_no


# Pull 'ord_no' record from 'invoicing' table based on 'inv_no' record
def invoice_ord_no(inv_no):
    sql_exp = f'SELECT ord_no FROM invoicing WHERE inv_no = {inv_no}'
    result_set = sql_query(sql_exp, c.config.sigm_db_cursor)
    ord_no = scalar_data(result_set)
    return ord_no


# Pull 'prt_no' record from 'part_transaction' table based on 'ptn_id' record
def transaction_prt_no(ptn_id):
    sql_exp = f'SELECT prt_no FROM part_transaction WHERE ptn_id = {ptn_id}'
    result_set = sql_query(sql_exp, c.config.sigm_db_cursor)
    prt_no = scalar_data(result_set)
    return prt_no


# Pull 'ptn_desc' record from 'part_transaction' table based on 'ptn_id' record
def transaction_ptn_desc(ptn_id):
    sql_exp = f'SELECT ptn_desc FROM part_transaction WHERE ptn_id = {ptn_id}'
    result_set = sql_query(sql_exp, c.config.sigm_db_cursor)
    ptn_desc = scalar_data(result_set)
    return ptn_desc


# Pull 'prt_no' record from 'planning_lot_quantity' table based on 'plq_lot_no' record
def planning_lot_prt_no(plq_lot_no):
    sql_exp = f'SELECT prt_no FROM planning_lot_quantity WHERE plq_lot_no = {plq_lot_no}'
    result_set = sql_query(sql_exp, c.config.sigm_db_cursor)
    prt_no = scalar_data(result_set)
    return prt_no


# Pass 'ord_no' to 'order_existing_blankets' stored procedure
# Checks if any existing blanket orders include parts on 'ord_no' reference
def order_existing_blankets(ord_no):
    sql_exp = f'SELECT * FROM order_existing_blankets({ord_no})'
    result_set = sql_query(sql_exp, c.config.sigm_db_cursor)
    blankets = tabular_data(result_set)
    return blankets


# Pass 'ord_no' to 'order_component_parents' stored procedure
# Pass 'ord_no', 'orl_kitmaster_id' to 'order_missing_components' stored procedure
# Checks if any parts on the order are "parents", check if any of their "children" are missing from the order
def order_missing_component_prt_no(ord_no):
    sql_exp = f'SELECT * FROM order_component_parents({ord_no})'
    result_set = sql_query(sql_exp, c.config.sigm_db_cursor)

    kits = []
    for row in result_set:
        parent = []
        index = row[0]
        prt_no = row[1].strip()
        orl_kitmaster_id = row[2]

        parent.append(index)
        parent.append(prt_no)
        sql_exp = f'SELECT * FROM order_missing_components({ord_no}, {orl_kitmaster_id})'
        c.config.sigm_db_cursor.execute(sql_exp)
        result_set = c.config.sigm_db_cursor.fetchall()

        lines = tabular_data(result_set)

        parent.append(lines)
        kits.append(parent)
    return kits


# Pass 'ord_no' to 'order_component_parents' stored procedure
# Pass 'ord_no', 'orl_kitmaster_id' to 'order_component_quantities' stored procedure
# Checks if any parts on the order are "parents", check if any of their "children" have incorrect quantities
def order_component_multiplier_prt_no(ord_no):
    sql_exp = f'SELECT * FROM order_component_parents({ord_no})'
    c.config.sigm_db_cursor.execute(sql_exp)
    result_set = c.config.sigm_db_cursor.fetchall()

    kits = []
    for row in result_set:
        parent = []
        index = row[0]
        prt_no = row[1].strip()
        orl_kitmaster_id = row[2]

        parent.append(index)
        parent.append(prt_no)
        sql_exp = f'SELECT * FROM order_component_quantities({ord_no}, {orl_kitmaster_id})'
        c.config.sigm_db_cursor.execute(sql_exp)
        result_set = c.config.sigm_db_cursor.fetchall()

        lines = tabular_data(result_set)

        parent.append(lines)
        kits.append(parent)
    return kits


# Log triggered alerts to LOG DB
def log_handler(timestamp, alert, ref_type, ref, user, station):
    sql_exp = f'INSERT INTO alerts (time_stamp, alert, ref_type, reference, user_name, station) ' \
              f'VALUES (\'{timestamp}\', \'{alert}\', \'{ref_type}\', \'{ref}\', \'{user}\', \'{station}\')'
    c.config.log_db_cursor.execute(sql_exp)


# Check if alert has been triggered recently
def duplicate_alert_check(timestamp, alert, ref_type, ref, user, station):
    sql_exp = f'SELECT * FROM duplicate_alert_check(' \
              f'\'{timestamp}\', \'{alert}\', \'{ref_type}\', \'{ref}\', \'{user}\', \'{station}\')'
    c.config.log_db_cursor.execute(sql_exp)
    result_set = c.config.log_db_cursor.fetchall()
    log_message = f'{alert} on {ref_type} {ref} by {user} on workstation {station} at {timestamp}\n'

    for row in result_set:
        for cell in row:
            check = cell
            if check == 1:
                log(f'Error Logged : {log_message}')
                log_handler(timestamp, alert, ref_type, ref, user, station)
                data.alert_handler(alert, ref, user)
            else:
                log(f'Duplicate Error : {log_message}')
