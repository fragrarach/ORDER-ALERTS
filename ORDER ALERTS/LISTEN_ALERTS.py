import smtplib
import re
import datetime
from sigm import *
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# PostgreSQL DB connection configs
psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)


# Log triggered alerts to LOG DB
def log_handler(timestamp, alert, ref_type, ref, user, station):
    sql_exp = f'INSERT INTO alerts (time_stamp, alert, ref_type, reference, user_name, station) ' \
              f'VALUES (\'{timestamp}\', \'{alert}\', \'{ref_type}\', \'{ref}\', \'{user}\', \'{station}\')'
    log_db_cursor.execute(sql_exp)


# Check if alert has been triggered recently
def duplicate_alert_check(timestamp, alert, ref_type, ref, user, station):
    sql_exp = f'SELECT * FROM duplicate_alert_check(' \
              f'\'{timestamp}\', \'{alert}\', \'{ref_type}\', \'{ref}\', \'{user}\', \'{station}\')'
    log_db_cursor.execute(sql_exp)
    result_set = log_db_cursor.fetchall()
    log_message = f'{alert} on {ref_type} {ref} by {user} on workstation {station} at {timestamp}\n'

    for row in result_set:
        for cell in row:
            check = cell
            if check == 1:
                print(f'Error Logged : {log_message}')
                log_handler(timestamp, alert, ref_type, ref, user, station)
                alert_handler(alert, ref, user)
            else:
                print(f'Duplicate Error : {log_message}')


# Split payload string, store as named variables, send to duplicate alert checker
def payload_handler(payload):
    ref_type = payload.split(", ")[0]
    ref = payload.split(", ")[1]
    alert = payload.split(", ")[2]
    sigm_string = payload.split(", ")[3]
    user = re.findall(r'(?<=aSIGMWIN\.EXE u)(.*)(?= m)', sigm_string)[0]
    station = re.findall(r'(?<= w)(.*)$', sigm_string)[0]
    timestamp = datetime.datetime.now()

    duplicate_alert_check(timestamp, alert, ref_type, ref, user, station)


# Pull 'cli_id' record from 'order_header' table based on 'ord_no' record
def ord_no_cli_id(ord_no):
    sql_exp = f'SELECT cli_id FROM order_header WHERE ord_no = {ord_no}'
    result_set = sql_query(sql_exp, sigm_db_cursor)
    cli_id = scalar_data(result_set)
    return cli_id


# Pull 'cli_name1' record from 'client' table based on 'cli_id' record
def cli_id_cli_name1(cli_id):
    sql_exp = f'SELECT cli_name1 FROM client WHERE cli_id = {cli_id}'
    result_set = sql_query(sql_exp, sigm_db_cursor)
    cli_name1 = scalar_data(result_set)
    return cli_name1


# Pull 'ord_no' record from 'invoicing' table based on 'inv_pckslp_no' record
def packing_slip_ord_no(inv_pckslp_no):
    sql_exp = f'SELECT ord_no FROM invoicing WHERE inv_pckslp_no = {inv_pckslp_no}'
    result_set = sql_query(sql_exp, sigm_db_cursor)
    ord_no = scalar_data(result_set)
    return ord_no


# Pull 'ord_no' record from 'invoicing' table based on 'inv_no' record
def invoice_ord_no(inv_no):
    sql_exp = f'SELECT ord_no FROM invoicing WHERE inv_no = {inv_no}'
    result_set = sql_query(sql_exp, sigm_db_cursor)
    ord_no = scalar_data(result_set)
    return ord_no


# Pull 'prt_no' record from 'part_transaction' table based on 'ptn_id' record
def transaction_prt_no(ptn_id):
    sql_exp = f'SELECT prt_no FROM part_transaction WHERE ptn_id = {ptn_id}'
    result_set = sql_query(sql_exp, sigm_db_cursor)
    prt_no = scalar_data(result_set)
    return prt_no


# Pull 'ptn_desc' record from 'part_transaction' table based on 'ptn_id' record
def transaction_ptn_desc(ptn_id):
    sql_exp = f'SELECT ptn_desc FROM part_transaction WHERE ptn_id = {ptn_id}'
    result_set = sql_query(sql_exp, sigm_db_cursor)
    ptn_desc = scalar_data(result_set)
    return ptn_desc


# Pull 'prt_no' record from 'planning_lot_quantity' table based on 'plq_lot_no' record
def planning_lot_prt_no(plq_lot_no):
    sql_exp = f'SELECT prt_no FROM planning_lot_quantity WHERE plq_lot_no = {plq_lot_no}'
    result_set = sql_query(sql_exp, sigm_db_cursor)
    prt_no = scalar_data(result_set)
    return prt_no


# Pass 'ord_no' to 'order_existing_blankets' stored procedure
# Checks if any existing blanket orders include parts on 'ord_no' reference
def order_existing_blankets(ord_no):
    sql_exp = f'SELECT * FROM order_existing_blankets({ord_no})'
    result_set = sql_query(sql_exp, sigm_db_cursor)
    blankets = tabular_data(result_set)
    return blankets


# Pass 'ord_no' to 'order_component_parents' stored procedure
# Pass 'ord_no', 'orl_kitmaster_id' to 'order_missing_components' stored procedure
# Checks if any parts on the order are "parents", check if any of their "children" are missing from the order
def order_missing_component_prt_no(ord_no):
    sql_exp = f'SELECT * FROM order_component_parents({ord_no})'
    result_set = sql_query(sql_exp, sigm_db_cursor)

    kits = []
    for row in result_set:
        parent = []
        index = row[0]
        prt_no = row[1].strip()
        orl_kitmaster_id = row[2]

        parent.append(index)
        parent.append(prt_no)
        sql_exp = f'SELECT * FROM order_missing_components({ord_no}, {orl_kitmaster_id})'
        sigm_db_cursor.execute(sql_exp)
        result_set = sigm_db_cursor.fetchall()

        lines = tabular_data(result_set)

        parent.append(lines)
        kits.append(parent)
    return kits


# Pass 'ord_no' to 'order_component_parents' stored procedure
# Pass 'ord_no', 'orl_kitmaster_id' to 'order_component_quantities' stored procedure
# Checks if any parts on the order are "parents", check if any of their "children" have incorrect quantities
def order_component_multiplier_prt_no(ord_no):
    sql_exp = f'SELECT * FROM order_component_parents({ord_no})'
    sigm_db_cursor.execute(sql_exp)
    result_set = sigm_db_cursor.fetchall()

    kits = []
    for row in result_set:
        parent = []
        index = row[0]
        prt_no = row[1].strip()
        orl_kitmaster_id = row[2]

        parent.append(index)
        parent.append(prt_no)
        sql_exp = f'SELECT * FROM order_component_quantities({ord_no}, {orl_kitmaster_id})'
        sigm_db_cursor.execute(sql_exp)
        result_set = sigm_db_cursor.fetchall()

        lines = tabular_data(result_set)

        parent.append(lines)
        kits.append(parent)
    return kits


# Email body formatting functions, called by the alert handler based on triggered alert
def client_bo_allowed(ref):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        to_list = ['sales@quatroair.com']
        cc_list = ['']

    cli_name1 = ref
    subject_str = f"SIGM Client {cli_name1} Issue"
    body = f"Our system has detected a potential issue with the record for client {cli_name1}.\n\n" + \
           "This is due to a newly entered or reactivated client record having \"ALLOW B.O.\" turned on.\n\n" + \
           "If this was done intentionally, please ignore this message. \n\n" + \
           "Thank you"
    return body, to_list, cc_list, subject_str


def order_bo_not_allowed(ref, cli_name1):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        to_list = ['sales@quatroair.com']
        cc_list = ['']

    ord_no = ref
    subject_str = f"SIGM Order {ord_no} / Client {cli_name1} Issue"
    body = f"Our system has detected an issue with the record for order number {ord_no}.\n\n" + \
           "This is due to an incomplete packing slip being generated with \"ALLOW B.O.\" turned off in an order. " + \
           "This will cause the rest of the order to be cancelled. The packing slip must be cancelled " + \
           "and the \"ALLOW B.O.\" option turned on.\n\n" + \
           "Thank you"
    return body, to_list, cc_list, subject_str


def order_not_reserved(ref, cli_name1, user):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        if user != 'SANJAY':
            to_list = ['sales@quatroair.com']
            cc_list = ['carmy.m@quatroair.com']
        else:
            to_list = ['sanjay.m@quatroair.com']
            cc_list = ['']

    ord_no = ref
    subject_str = f"SIGM Order {ord_no} / Client {cli_name1} Issue"
    body = f"Our system has detected an issue with the record for order number {ord_no}. \n\n" + \
           "This is due to a reserved quantity not matching the ordered quantity for a part. \n\n" + \
           "If this order is set to \"Complete Shipment\", " + \
           "this will prevent shipping from printing a packing slip. \n\n" + \
           "If this order is set to \"Partial Shipment\", " \
           "this will back order remaining unreserved quantities. " + \
           "If it is also set to not \"Allow B.O.\", " + \
           "the remaining unreserved quantities will be cancelled. \n\n" + \
           "If this was done intentionally, please ignore this message. " + \
           "If not, please ensure the reserved quantity matches the ordered quantity. \n\n" + \
           "Thank you"
    return body, to_list, cc_list, subject_str


def order_zero_quantity(ref, cli_name1):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        to_list = ['sales@quatroair.com']
        cc_list = ['']

    ord_no = ref
    subject_str = f"SIGM Order {ord_no} / Client {cli_name1} Issue"
    body = f"Our system has detected an issue with the record for order number {ord_no}.\n\n" + \
           "This is due to the quantity of an ordered part being set to 0. " \
           "It is also possible that this is a blanket order not set to the correct type. Please review the order and" \
           " make the appropriate changes.\n\n" \
           "Thank you"
    return body, to_list, cc_list, subject_str


def order_cancelled(ref, user):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        to_list = ['sales@quatroair.com']
        cc_list = ['shipping@quatroair.com', 'jorge.g@quatroair.com']

    ord_no = ref
    subject_str = f"SIGM Order {ord_no} Issue"
    body = f'Please be advised order number {ord_no} has been cancelled. Please destroy the picking list ' + \
           f'and return the packing slip to {user}.\n\n' + \
           f'Thank you'
    return body, to_list, cc_list, subject_str


def order_new_blanket(ref, cli_name1, user):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        if user != 'SANJAY':
            to_list = ['sanjay.m@quatroair.com']
            cc_list = ['stephanie.l@quatroair.com']
        else:
            to_list = ['stephanie.l@quatroair.com']
            cc_list = ['']

    ord_no = ref
    subject_str = f"New Blanket Order {ord_no}"
    body = f"Our system has detected a newly generated blanket order (Order Number {ord_no}) for {cli_name1}.\n\n" + \
           "Thank you"
    return body, to_list, cc_list, subject_str


def order_new_release(ref, cli_name1, user):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        if user != 'SANJAY':
            to_list = ['sanjay.m@quatroair.com']
            cc_list = ['stephanie.l@quatroair.com']
        else:
            to_list = ['stephanie.l@quatroair.com']
            cc_list = ['']

    ord_no = ref
    subject_str = f"New Blanket Release {ord_no}"
    body = f"Our system has detected a newly generated blanket release (Order Number {ord_no}) for {cli_name1}.\n\n" + \
           "Thank you"
    return body, to_list, cc_list, subject_str


def order_cancelled_packing_slip(ref, user, ord_no):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        to_list = ['sales@quatroair.com']
        cc_list = ['carmy.m@quatroair.com']

    inv_pckslp_no = ref
    subject_str = f"SIGM Order {ord_no} Issue"
    body = f'Please be advised packing slip {inv_pckslp_no} has been cancelled by {user} (Order {ord_no}).\n\n ' \
           f'Thank you'
    return body, to_list, cc_list, subject_str


def order_shipping_cost_missing(ref, ord_no):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        to_list = ['sales@quatroair.com']
        cc_list = ['carmy.m@quatroair.com']

    inv_no = ref
    subject_str = f"SIGM Order {ord_no} Issue"
    body = f'Please be advised invoice {inv_no} has been generated without shipping costs. ' \
           f'The shipping terms in order {ord_no} require shipping costs be added. Please cancel the invoice ' \
           f'and add the shipping costs before generating a new packing slip and invoice.\n\n ' \
           f'Thank you'
    return body, to_list, cc_list, subject_str


def order_different_line_dates(ref, cli_name1):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        to_list = ['sales@quatroair.com']
        cc_list = ['carmy.m@quatroair.com']

    ord_no = ref
    subject_str = f"SIGM Order {ord_no} / Client {cli_name1} Issue"
    body = f'Our system has detected an issue with the record for order number {ord_no}. \n\n' \
           f'This order includes parts with different required dates. The potential issues are either: \n\n' \
           f'1) Status set to "COMPLETE SHIPMENT" \n' \
           f'2) Status set to "PARTIAL SHIPMENT" and "ALLOW B.O." is turned off. \n\n' \
           f'Please set the order status to "PARTIAL SHIPMENT" and enable "ALLOW B.O.". \n\n ' \
           f'Thank you'
    return body, to_list, cc_list, subject_str


def order_zero_bank_fees(ref, cli_name1):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        to_list = ['sales@quatroair.com']
        cc_list = ['carmy.m@quatroair.com']

    ord_no = ref
    subject_str = f"SIGM Order {ord_no} / Client {cli_name1} Issue"
    body = f'Our system has detected an issue with the record for order number {ord_no}. \n\n' \
           f'This is due to the order payment terms being set to "Wire Transfer" and "Bank Fees" being set to 0. ' \
           f'If this was done intentionally, please ignore this message.\n\n' \
           f'Thank you'
    return body, to_list, cc_list, subject_str


def transaction_negative_quantity(ref, prt_no, ptn_desc):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        to_list = ['stephanie.l@quatroair.com']
        cc_list = ['']

    ptn_id = ref
    subject_str = f"SIGM Part {prt_no} Negative Quantity"
    body = f'Our system has detected a negative quantity for part number {prt_no}. \n\n' \
           f'This is the result of the following transaction : {ptn_desc}. \n\n' \
           f'Transaction ID : {ptn_id} \n\n' \
           f'Thank you'
    return body, to_list, cc_list, subject_str


def order_completed_blanket(ref, cli_name1):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        to_list = ['sales@quatroair.com']
        cc_list = ['stephanie.l@quatroair.com']

    ord_no = ref
    subject_str = f"SIGM Order {ord_no} / Client {cli_name1} Issue"
    body = f"Our system has detected an issue with the record for order number {ord_no}.\n\n" + \
           "This is due to a blanket order having all quantities set to 0 and not being set to the cancelled status. " \
           "Completed blanket orders are to be set to the cancelled status. Please review the order and make the " \
           "appropriate changes.\n\n" \
           "Thank you"
    return body, to_list, cc_list, subject_str


def invoice_email_unsent(ref, ord_no):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        to_list = ['carmy.m@quatroair.com']
        cc_list = ['']

    inv_no = ref
    subject_str = f"SIGM Order {ord_no} / Invoice {inv_no} Issue"
    body = f'Please be advised invoice {inv_no} has been generated without an email being sent to the client.\n\n' \
           f'Thank you'
    return body, to_list, cc_list, subject_str


def transaction_invoiced_production(ref, prt_no):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        to_list = ['stephanie.l@quatroair.com']
        cc_list = ['']

    plq_lot_no = ref
    subject_str = f"SIGM Invoiced Production {prt_no} / {plq_lot_no}"
    body = f'Our system has detected a production has been run for an invoiced order. \n\n' \
           f'Produced Part : {prt_no} \n' \
           f'Planning Lot # : {plq_lot_no} \n\n' \
           f'Thank you'
    return body, to_list, cc_list, subject_str


def order_converted_date(ref, cli_name1):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        to_list = ['sales@quatroair.com']
        cc_list = ['']

    ord_no = ref
    subject_str = f"SIGM Order {ord_no} / Client {cli_name1} Issue"
    body = f"Our system has detected an incorrect order date (Order Number {ord_no}) for {cli_name1}. \n\n" \
           f"This is due to an order with status \"Quote\" or \"Pending Shipment\" being converted to a " \
           f"\"Complete Shipment\" or \"Partial Shipment\" status and the order date not being set to today's date. " \
           f"This alert can be avoided by changing the date to today's date before changing the status.\n\n" + \
           "Thank you"
    return body, to_list, cc_list, subject_str


def order_existing_blanket(ref, cli_name1, blankets):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        to_list = ['sales@quatroair.com']
        cc_list = ['']

    ord_no = ref
    subject_str = f"SIGM Order {ord_no} / Client {cli_name1} Issue"
    body = f"Our system has detected an issue with the record for order number {ord_no}.\n\n" \
           f"This is due to the order being set to set to the type \"Order\" instead of \"Blanket Release\". " \
           f"The following parts from this order exist on the following blankets : \n\n"
    for blanket in blankets:
        prt_no = blanket[0]
        ord_no = blanket[1]
        body += f'   Part Number {prt_no} in Blanket Order {ord_no}\n'
    body += '\n' \
            'If this was done intentionally, please ignore this message.\n\n' \
            'Thank you.'
    return body, to_list, cc_list, subject_str


def order_missing_component(ref, cli_name1, missing_components):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        to_list = ['sales@quatroair.com']
        cc_list = ['stephanie.l@quatroair.com']

    ord_no = ref
    subject_str = f"SIGM Order {ord_no} / Client {cli_name1} Issue"
    body = f"Our system has detected (a) missing component(s) (Order Number {ord_no}) for {cli_name1}. \n\n"
    body += f"The following parent part(s) is/are missing component(s): \n\n"

    for parent in missing_components:
        orl_sort_idx = parent[0]
        prt_no = parent[1]
        body += f'Parent Line #: {orl_sort_idx}, Parent Part #: {prt_no}\n\n'
        for components in parent[2]:
            orl_sort_idx = components[0]
            prt_no = components[1]
            body += f'Line #: {orl_sort_idx}, Part #: {prt_no}\n'
        body += '\n'

    body += 'Please delete these lines and re-enter the parent(s) to the order. '
    body += 'This will allow the system to pull the appropriate component(s).\n\n'
    body += 'Thank you'
    return body, to_list, cc_list, subject_str


def order_component_multiplier(ref, cli_name1, component_multiplier):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        to_list = ['sales@quatroair.com']
        cc_list = ['stephanie.l@quatroair.com']

    ord_no = ref
    subject_str = f"SIGM Order {ord_no} / Client {cli_name1} Issue"
    body = f"Our system has detected an incorrect component quantity (Order Number {ord_no}) for {cli_name1}. \n\n"

    if len(component_multiplier) == 1:
        body += f"The following part has an incorrect quantity: \n\n"
    else:
        body += f"The following parts have incorrect quantities: \n\n"

    for parent in component_multiplier:
        orl_sort_idx = parent[0]
        prt_no = parent[1]
        body += f'Parent Line #: {orl_sort_idx}, Parent Part #: {prt_no}\n\n'
        for components in parent[2]:
            orl_sort_idx = components[0]
            prt_no = components[1]
            fixed_qty = components[2]
            body += f'Line #: {orl_sort_idx}, Part #: {prt_no}\n'
            body += f'Suggested Quantity: {fixed_qty}\n\n'

    if len(component_multiplier) == 1:
        body += 'The suggested quantity is based on the parent part quantity being correct. '
        body += 'If the parent part quantity is also incorrect, you can delete that line and the component. '
        body += 'Re-entering the parent part with the correct quantity will pull the correct component quantity. \n\n'
    else:
        body += 'The suggested quantities are based on the parent part quantity being correct. '
        body += 'If the parent part quantity is also incorrect, you can delete that line and its components. '
        body += 'Re-entering the parent part with the correct quantity will pull the correct component quantities. \n\n'
    body += 'Thank you'
    return body, to_list, cc_list, subject_str


def planning_lot_calculation(ref):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        to_list = ['stephanie.l@quatroair.com']
        cc_list = ['']

    plq_lot_no = ref
    subject_str = f"SIGM Uncheck Lot Calculation {plq_lot_no}"
    body = f'Our system has detected a planning lot ({plq_lot_no}) has been calculated without using' \
           f' manufactured inventory. \n\n'
    body += 'Thank you'
    return body, to_list, cc_list, subject_str


# Send formatted email body to defined recipients
def email_handler(body, to_list, cc_list, subject_str):
    from_str = 'noreply@quatroair.com'
    bcc_list = ['jan.z@quatroair.com']
    to_str = ', '.join(to_list)
    cc_str = ', '.join(cc_list)

    msg = MIMEMultipart()
    msg['From'] = from_str
    msg['To'] = to_str
    msg['CC'] = cc_str
    msg['Subject'] = subject_str
    msg.attach(MIMEText(body, 'plain'))
    text = msg.as_string()

    s = smtplib.SMTP('aerofil-ca.mail.protection.outlook.com')
    s.starttls()

    s.sendmail(from_str, to_list + cc_list + bcc_list, text)
    s.quit()
    print('Email Sent')


# Calls appropriate email body formatting function based on triggered alert
def alert_handler(alert, ref, user):
    if alert == 'BO ALLOWED':
        body, to_list, cc_list, subject_str = client_bo_allowed(ref)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'BO NOT ALLOWED':
        ord_no = ref
        cli_id = ord_no_cli_id(ord_no)
        cli_name1 = cli_id_cli_name1(cli_id)
        body, to_list, cc_list, subject_str = order_bo_not_allowed(ref, cli_name1)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'NOT RESERVED':
        ord_no = ref
        cli_id = ord_no_cli_id(ord_no)
        cli_name1 = cli_id_cli_name1(cli_id)
        body, to_list, cc_list, subject_str = order_not_reserved(ref, cli_name1, user)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'ZERO QUANTITY':
        ord_no = ref
        cli_id = ord_no_cli_id(ord_no)
        cli_name1 = cli_id_cli_name1(cli_id)
        body, to_list, cc_list, subject_str = order_zero_quantity(ref, cli_name1)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'ORDER CANCELLED':
        body, to_list, cc_list, subject_str = order_cancelled(ref, user)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'NEW BLANKET':
        ord_no = ref
        cli_id = ord_no_cli_id(ord_no)
        cli_name1 = cli_id_cli_name1(cli_id)
        body, to_list, cc_list, subject_str = order_new_blanket(ref, cli_name1, user)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'NEW RELEASE':
        ord_no = ref
        cli_id = ord_no_cli_id(ord_no)
        cli_name1 = cli_id_cli_name1(cli_id)
        body, to_list, cc_list, subject_str = order_new_release(ref, cli_name1, user)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'CANCELLED PACKING SLIP':
        ord_no = packing_slip_ord_no(ref)
        body, to_list, cc_list, subject_str = order_cancelled_packing_slip(ref, user, ord_no)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'SHIPPING COST MISSING':
        ord_no = invoice_ord_no(ref)
        body, to_list, cc_list, subject_str = order_shipping_cost_missing(ref, ord_no)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'LINE DATES':
        ord_no = ref
        cli_id = ord_no_cli_id(ord_no)
        cli_name1 = cli_id_cli_name1(cli_id)
        body, to_list, cc_list, subject_str = order_different_line_dates(ref, cli_name1)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'ZERO BANK FEES':
        ord_no = ref
        cli_id = ord_no_cli_id(ord_no)
        cli_name1 = cli_id_cli_name1(cli_id)
        body, to_list, cc_list, subject_str = order_zero_bank_fees(ref, cli_name1)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'NEGATIVE QUANTITY':
        prt_no = transaction_prt_no(ref)
        ptn_desc = transaction_ptn_desc(ref)
        body, to_list, cc_list, subject_str = transaction_negative_quantity(ref, prt_no, ptn_desc)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'COMPLETED BLANKET':
        ord_no = ref
        cli_id = ord_no_cli_id(ord_no)
        cli_name1 = cli_id_cli_name1(cli_id)
        body, to_list, cc_list, subject_str = order_completed_blanket(ref, cli_name1)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'UNSENT INVOICE EMAIL':
        ord_no = invoice_ord_no(ref)
        body, to_list, cc_list, subject_str = invoice_email_unsent(ref, ord_no)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'INVOICED PRODUCTION':
        prt_no = planning_lot_prt_no(ref)
        body, to_list, cc_list, subject_str = transaction_invoiced_production(ref, prt_no)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'CONVERTED DATE':
        ord_no = ref
        cli_id = ord_no_cli_id(ord_no)
        cli_name1 = cli_id_cli_name1(cli_id)
        body, to_list, cc_list, subject_str = order_converted_date(ref, cli_name1)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'EXISTING BLANKET':
        ord_no = ref
        cli_id = ord_no_cli_id(ord_no)
        cli_name1 = cli_id_cli_name1(cli_id)
        blankets = order_existing_blankets(ref)
        body, to_list, cc_list, subject_str = order_existing_blanket(ref, cli_name1, blankets)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'MISSING COMPONENT':
        ord_no = ref
        cli_id = ord_no_cli_id(ord_no)
        cli_name1 = cli_id_cli_name1(cli_id)
        missing_components = order_missing_component_prt_no(ref)
        body, to_list, cc_list, subject_str = order_missing_component(ref, cli_name1, missing_components)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'COMPONENT MULTIPLIER':
        ord_no = ref
        cli_id = ord_no_cli_id(ord_no)
        cli_name1 = cli_id_cli_name1(cli_id)
        component_multiplier = order_component_multiplier_prt_no(ref)
        if component_multiplier[0][2]:
            body, to_list, cc_list, subject_str = order_component_multiplier(ref, cli_name1, component_multiplier)
            email_handler(body, to_list, cc_list, subject_str)
        else:
            print(f'FALSE POSITIVE COMPONENT MULTIPLIER')

    elif alert == 'UNCHECKED NEED CALCULATION':
        body, to_list, cc_list, subject_str = planning_lot_calculation(ref)
        email_handler(body, to_list, cc_list, subject_str)


def main():
    channel = 'alert'
    global sigm_connection, sigm_db_cursor, log_connection, log_db_cursor
    sigm_connection, sigm_db_cursor = sigm_connect(channel)
    log_connection, log_db_cursor = log_connect()

    add_sql_files()

    while 1:
        try:
            sigm_connection.poll()
        except:
            print('Database cannot be accessed, PostgreSQL service probably rebooting')
            try:
                sigm_connection.close()
                sigm_connection, sigm_db_cursor = sigm_connect(channel)
                log_connection.close()
                log_connection, log_db_cursor = log_connect()
            except:
                pass
        else:
            sigm_connection.commit()
            while sigm_connection.notifies:
                notify = sigm_connection.notifies.pop()
                raw_payload = notify.payload
                print(f'Alert Triggered : {raw_payload}')
                payload_handler(raw_payload)


main()
