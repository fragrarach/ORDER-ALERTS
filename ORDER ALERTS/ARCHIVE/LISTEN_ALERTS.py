import smtplib
import psycopg2.extensions
import re
import datetime
import os
import time
from os.path import dirname, abspath
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

psycopg2.extensions.register_type(psycopg2.extensions.UNICODE)
psycopg2.extensions.register_type(psycopg2.extensions.UNICODEARRAY)

conn_sigm = psycopg2.connect("host='192.168.0.250' dbname='QuatroAir' user='SIGM' port='5493'")
conn_sigm.set_client_encoding("latin1")
conn_sigm.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

sigm_listen = conn_sigm.cursor()
sigm_listen.execute("LISTEN alert;")
sigm_query = conn_sigm.cursor()

conn_log = psycopg2.connect("host='192.168.0.57' dbname='LOG' user='SIGM' port='5493'")
conn_log.set_client_encoding("latin1")
conn_log.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)

log_query = conn_log.cursor()


def log_handler(timestamp, alert, ref_type, ref, user, station):
    sql_exp = f'INSERT INTO alerts (time_stamp, alert, ref_type, reference, user_name, station) ' \
              f'VALUES (\'{timestamp}\', \'{alert}\', \'{ref_type}\', \'{ref}\', \'{user}\', \'{station}\')'
    log_query.execute(sql_exp)


def duplicate_alert_check(timestamp, alert, ref_type, ref, user, station):
    sql_exp = f'SELECT CASE WHEN NOT EXISTS (' \
              f'        SELECT * ' \
              f'        FROM alerts ' \
              f'        WHERE alert = \'{alert}\' ' \
              f'        AND ref_type = \'{ref_type}\' ' \
              f'        AND reference = \'{ref}\' ' \
              f'        AND user_name = \'{user}\' ' \
              f'        AND time_stamp + 1 * interval \'1 hour\' > \'{timestamp}\'::timestamp ' \
              f'        AND time_stamp < \'{timestamp}\'::timestamp ' \
              f'        AND station = \'{station}\' ' \
              f') THEN 1 ELSE 0 END'
    log_query.execute(sql_exp)
    result_set = log_query.fetchall()
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


def payload_handler(payload):
    ref_type = payload.split(", ")[0]
    ref = payload.split(", ")[1]
    alert = payload.split(", ")[2]
    sigm_string = payload.split(", ")[3]
    user = re.findall(r'(?<=aSIGMWIN\.EXE u)(.*)(?= m)', sigm_string)[0]
    station = re.findall(r'(?<= w)(.*)$', sigm_string)[0]
    timestamp = datetime.datetime.now()

    duplicate_alert_check(timestamp, alert, ref_type, ref, user, station)


def order_cli_name1(ord_no):
    sql_exp = f'SELECT cli_id FROM order_header WHERE ord_no = {ord_no}'
    sigm_query.execute(sql_exp)
    result_set = sigm_query.fetchall()

    for row in result_set:
        for cell in row:
            cli_id = cell

    sql_exp = f'SELECT cli_name1 FROM client WHERE cli_id = {cli_id}'
    sigm_query.execute(sql_exp)
    result_set = sigm_query.fetchall()

    for row in result_set:
        for cell in row:
            cli_name1 = cell.strip()
            return cli_name1


def packing_slip_ord_no(inv_pckslp_no):
    sql_exp = f'SELECT ord_no FROM invoicing WHERE inv_pckslp_no = {inv_pckslp_no}'
    sigm_query.execute(sql_exp)
    result_set = sigm_query.fetchall()

    for row in result_set:
        for cell in row:
            ord_no = cell
            return ord_no


def invoice_ord_no(inv_no):
    sql_exp = f'SELECT ord_no FROM invoicing WHERE inv_no = {inv_no}'
    sigm_query.execute(sql_exp)
    result_set = sigm_query.fetchall()

    for row in result_set:
        for cell in row:
            ord_no = cell
            return ord_no


def transaction_prt_no(ptn_id):
    sql_exp = f'SELECT prt_no FROM part_transaction WHERE ptn_id = {ptn_id}'
    sigm_query.execute(sql_exp)
    result_set = sigm_query.fetchall()

    for row in result_set:
        for cell in row:
            prt_no = cell.strip()
            return prt_no


def transaction_ptn_desc(ptn_id):
    sql_exp = f'SELECT ptn_desc FROM part_transaction WHERE ptn_id = {ptn_id}'
    sigm_query.execute(sql_exp)
    result_set = sigm_query.fetchall()

    for row in result_set:
        for cell in row:
            ptn_desc = cell.strip()
            return ptn_desc


def planning_lot_prt_no(plq_lot_no):
    sql_exp = f'SELECT prt_no FROM planning_lot_quantity WHERE plq_lot_no = {plq_lot_no}'
    sigm_query.execute(sql_exp)
    result_set = sigm_query.fetchall()

    for row in result_set:
        for cell in row:
            prt_no = cell.strip()
            return prt_no


def order_existing_blankets(ord_no):
    sql_exp = f'SELECT prt_no, ord_no FROM blanket_orders WHERE cli_no IN ( ' \
              f'        SELECT c.cli_no ' \
              f'        FROM order_header oh ' \
              f'        JOIN client c on c.cli_id = oh.cli_id ' \
              f'        WHERE ord_no = {ord_no} ' \
              f') ' \
              f'AND prt_no IN ( ' \
              f'        SELECT ol.prt_no ' \
              f'        FROM order_header oh ' \
              f'        JOIN order_line ol ON ol.ord_no = oh.ord_no ' \
              f'        WHERE ol.ord_no = {ord_no} ' \
              f')'
    sigm_query.execute(sql_exp)
    result_set = sigm_query.fetchall()

    blankets = []
    for row in result_set:
        blanket = []
        for cell in row:
            if type(cell) == str:
                record = cell.strip()
            else:
                record = cell
            blanket.append(record)
        blankets.append(blanket)
    return blankets


def client_bo_allowed(ref):
    to_list = ['sales@quatroair.com']
    cc_list = ['']

    # to_list = ['jan.z@quatroair.com']
    # cc_list = ['jan.z@quatroair.com']

    subject_str = f"SIGM Client {ref} Issue"
    body = f"Our system has detected a potential issue with the record for client {ref}.\n\n" + \
           "This is due to a newly entered or reactivated client record having \"ALLOW B.O.\" turned on.\n\n" + \
           "If this was done intentionally, please ignore this message. \n\n" + \
           "Thank you"
    return body, to_list, cc_list, subject_str


def order_bo_not_allowed(ref, client):
    to_list = ['sales@quatroair.com']
    cc_list = ['']

    # to_list = ['jan.z@quatroair.com']
    # cc_list = ['jan.z@quatroair.com']

    subject_str = f"SIGM Order {ref} / Client {client} Issue"
    body = f"Our system has detected an issue with the record for order number {ref}.\n\n" + \
           "This is due to an incomplete packing slip being generated with \"ALLOW B.O.\" turned off in an order. " + \
           "This will cause the rest of the order to be cancelled. The packing slip must be cancelled " + \
           "and the \"ALLOW B.O.\" option turned on.\n\n" + \
           "Thank you"
    return body, to_list, cc_list, subject_str


def order_not_reserved(ref, client, user):
    if user != 'SANJAY':
        to_list = ['sales@quatroair.com']
        cc_list = ['carmy.m@quatroair.com']
    else:
        to_list = ['sanjay.m@quatroair.com']
        cc_list = ['']

    # to_list = ['jan.z@quatroair.com']
    # cc_list = ['jan.z@quatroair.com']

    subject_str = f"SIGM Order {ref} / Client {client} Issue"
    body = f"Our system has detected an issue with the record for order number {ref}. \n\n" + \
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


def order_zero_quantity(ref, client):
    to_list = ['sales@quatroair.com']
    cc_list = ['']

    # to_list = ['jan.z@quatroair.com']
    # cc_list = ['jan.z@quatroair.com']

    subject_str = f"SIGM Order {ref} / Client {client} Issue"
    body = f"Our system has detected an issue with the record for order number {ref}.\n\n" + \
           "This is due to the quantity of an ordered part being set to 0. " \
           "It is also possible that this is a blanket order not set to the correct type. Please review the order and" \
           " make the appropriate changes.\n\n" \
           "Thank you"
    return body, to_list, cc_list, subject_str


def order_cancelled(ref, user):
    to_list = ['sales@quatroair.com']
    cc_list = ['shipping@quatroair.com', 'jorge.g@quatroair.com']

    # to_list = ['jan.z@quatroair.com']
    # cc_list = ['jan.z@quatroair.com']

    subject_str = f"SIGM Order {ref} Issue"
    body = f'Please be advised order number {ref} has been cancelled. Please destroy the picking list ' + \
           f'and return the packing slip to {user}.\n\n' + \
           f'Thank you'
    return body, to_list, cc_list, subject_str


def order_new_blanket(ref, client, user):
    if user != 'SANJAY':
        to_list = ['sanjay.m@quatroair.com']
        cc_list = ['stephanie.l@quatroair.com']
    else:
        to_list = ['stephanie.l@quatroair.com']
        cc_list = ['']

    # to_list = ['jan.z@quatroair.com']
    # cc_list = ['jan.z@quatroair.com']

    subject_str = f"New Blanket Order {ref}"
    body = f"Our system has detected a newly generated blanket order (Order Number {ref}) for {client}.\n\n" + \
           "Thank you"
    return body, to_list, cc_list, subject_str


def order_new_release(ref, client, user):
    if user != 'SANJAY':
        to_list = ['sanjay.m@quatroair.com']
        cc_list = ['stephanie.l@quatroair.com']
    else:
        to_list = ['stephanie.l@quatroair.com']
        cc_list = ['']

    # to_list = ['jan.z@quatroair.com']
    # cc_list = ['jan.z@quatroair.com']

    subject_str = f"New Blanket Release {ref}"
    body = f"Our system has detected a newly generated blanket release (Order Number {ref}) for {client}.\n\n" + \
           "Thank you"
    return body, to_list, cc_list, subject_str


def order_cancelled_packing_slip(ref, user, order):
    to_list = ['sales@quatroair.com']
    cc_list = ['carmy.m@quatroair.com']

    # to_list = ['jan.z@quatroair.com']
    # cc_list = ['jan.z@quatroair.com']

    subject_str = f"SIGM Order {order} Issue"
    body = f'Please be advised packing slip {ref} has been cancelled by {user} (Order {order}).\n\n ' \
           f'Thank you'
    return body, to_list, cc_list, subject_str


def order_shipping_cost_missing(ref, order):
    to_list = ['sales@quatroair.com']
    cc_list = ['carmy.m@quatroair.com']

    # to_list = ['jan.z@quatroair.com']
    # cc_list = ['jan.z@quatroair.com']

    subject_str = f"SIGM Order {order} Issue"
    body = f'Please be advised invoice {ref} has been generated without shipping costs. ' \
           f'The shipping terms in order {order} require shipping costs be added. Please cancel the invoice ' \
           f'and add the shipping costs before generating a new packing slip and invoice.\n\n ' \
           f'Thank you'
    return body, to_list, cc_list, subject_str


def order_different_line_dates(ref, client):
    to_list = ['sales@quatroair.com']
    cc_list = ['carmy.m@quatroair.com']

    # to_list = ['jan.z@quatroair.com']
    # cc_list = ['jan.z@quatroair.com']

    subject_str = f"SIGM Order {ref} / Client {client} Issue"
    body = f'Our system has detected an issue with the record for order number {ref}. \n\n' \
           f'This order includes parts with different required dates. The potential issues are either: \n\n' \
           f'1) Status set to "COMPLETE SHIPMENT" \n' \
           f'2) Status set to "PARTIAL SHIPMENT" and "ALLOW B.O." is turned off. \n\n' \
           f'Please set the order status to "PARTIAL SHIPMENT" and enable "ALLOW B.O.". \n\n ' \
           f'Thank you'
    return body, to_list, cc_list, subject_str


def order_zero_bank_fees(ref, client):
    to_list = ['sales@quatroair.com']
    cc_list = ['carmy.m@quatroair.com']

    # to_list = ['jan.z@quatroair.com']
    # cc_list = ['jan.z@quatroair.com']

    subject_str = f"SIGM Order {ref} / Client {client} Issue"
    body = f'Our system has detected an issue with the record for order number {ref}. \n\n' \
           f'This is due to the order payment terms being set to "Wire Transfer" and "Bank Fees" being set to 0. ' \
           f'If this was done intentionally, please ignore this message.\n\n' \
           f'Thank you'
    return body, to_list, cc_list, subject_str


def transaction_negative_quantity(ref, part, desc):
    to_list = ['stephanie.l@quatroair.com']
    cc_list = ['']

    # to_list = ['jan.z@quatroair.com']
    # cc_list = ['jan.z@quatroair.com']

    subject_str = f"SIGM Part {part} Negative Quantity"
    body = f'Our system has detected a negative quantity for part number {part}. \n\n' \
           f'This is the result of the following transaction : {desc}. \n\n' \
           f'Transaction ID : {ref} \n\n' \
           f'Thank you'
    return body, to_list, cc_list, subject_str


def order_completed_blanket(ref, client):
    to_list = ['sales@quatroair.com']
    cc_list = ['']

    # to_list = ['jan.z@quatroair.com']
    # cc_list = ['jan.z@quatroair.com']

    subject_str = f"SIGM Order {ref} / Client {client} Issue"
    body = f"Our system has detected an issue with the record for order number {ref}.\n\n" + \
           "This is due to a blanket order having all quantities set to 0 and not being set to the cancelled status. " \
           "Completed blanket orders are to be set to the cancelled status. Please review the order and make the " \
           "appropriate changes.\n\n" \
           "Thank you"
    return body, to_list, cc_list, subject_str


def invoice_email_unsent(ref, order):
    to_list = ['carmy.m@quatroair.com']
    cc_list = ['']

    # to_list = ['jan.z@quatroair.com']
    # cc_list = ['jan.z@quatroair.com']

    subject_str = f"SIGM Order {order} / Invoice {ref} Issue"
    body = f'Please be advised invoice {ref} has been generated without an email being sent to the client.\n\n' \
           f'Thank you'
    return body, to_list, cc_list, subject_str


def transaction_invoiced_production(ref, part):
    to_list = ['stephanie.l@quatroair.com']
    cc_list = ['']

    # to_list = ['jan.z@quatroair.com']
    # cc_list = ['jan.z@quatroair.com']

    subject_str = f"SIGM Invoiced Production {part} / {ref}"
    body = f'Our system has detected a production has been run for an invoiced order. \n\n' \
           f'Produced Part : {part} \n' \
           f'Planning Lot # : {ref} \n\n' \
           f'Thank you'
    return body, to_list, cc_list, subject_str


def order_converted_date(ref, client):
    to_list = ['sales@quatroair.com']
    cc_list = ['']

    # to_list = ['jan.z@quatroair.com']
    # cc_list = ['jan.z@quatroair.com']

    subject_str = f"SIGM Order {ref} / Client {client} Issue"
    body = f"Our system has detected an incorrect order date (Order Number {ref}) for {client}. \n\n" \
           f"This is due to an order with status \"Quote\" or \"Pending Shipment\" being converted to a " \
           f"\"Complete Shipment\" or \"Partial Shipment\" status and the order date not being set to today's date. " \
           f"This alert can be avoided by changing the date to today's date before changing the status.\n\n" + \
           "Thank you"
    return body, to_list, cc_list, subject_str


def order_existing_blanket(ref, client, blankets):
    to_list = ['sales@quatroair.com']
    cc_list = ['']

    # to_list = ['jan.z@quatroair.com']
    # cc_list = ['jan.z@quatroair.com']

    subject_str = f"SIGM Order {ref} / Client {client} Issue"
    body = f"Our system has detected an issue with the record for order number {ref}.\n\n" \
           f"This is due to the order being set to set to the type \"Order\" instead of \"Blanket Release\". " \
           f"The following parts from this order exist on the following blankets : \n\n"
    for blanket in blankets:
        body += f'   Part Number {blanket[0]} in Blanket Order {blanket[1]}\n'
    body += '\n' \
            'If this was done intentionally, please ignore this message.\n\n' \
            'Thank you.'
    return body, to_list, cc_list, subject_str


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


def alert_handler(alert, ref, user):
    if alert == 'BO ALLOWED':
        body, to_list, cc_list, subject_str = client_bo_allowed(ref)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'BO NOT ALLOWED':
        client = order_cli_name1(ref)
        body, to_list, cc_list, subject_str = order_bo_not_allowed(ref, client)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'NOT RESERVED':
        client = order_cli_name1(ref)
        body, to_list, cc_list, subject_str = order_not_reserved(ref, client, user)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'ZERO QUANTITY':
        client = order_cli_name1(ref)
        body, to_list, cc_list, subject_str = order_zero_quantity(ref, client)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'ORDER CANCELLED':
        body, to_list, cc_list, subject_str = order_cancelled(ref, user)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'NEW BLANKET':
        client = order_cli_name1(ref)
        body, to_list, cc_list, subject_str = order_new_blanket(ref, client, user)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'NEW RELEASE':
        client = order_cli_name1(ref)
        body, to_list, cc_list, subject_str = order_new_release(ref, client, user)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'CANCELLED PACKING SLIP':
        order = packing_slip_ord_no(ref)
        body, to_list, cc_list, subject_str = order_cancelled_packing_slip(ref, user, order)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'SHIPPING COST MISSING':
        order = invoice_ord_no(ref)
        body, to_list, cc_list, subject_str = order_shipping_cost_missing(ref, order)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'LINE DATES':
        client = order_cli_name1(ref)
        body, to_list, cc_list, subject_str = order_different_line_dates(ref, client)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'ZERO BANK FEES':
        client = order_cli_name1(ref)
        body, to_list, cc_list, subject_str = order_zero_bank_fees(ref, client)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'NEGATIVE QUANTITY':
        part = transaction_prt_no(ref)
        desc = transaction_ptn_desc(ref)
        body, to_list, cc_list, subject_str = transaction_negative_quantity(ref, part, desc)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'COMPLETED BLANKET':
        client = order_cli_name1(ref)
        body, to_list, cc_list, subject_str = order_completed_blanket(ref, client)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'UNSENT INVOICE EMAIL':
        order = invoice_ord_no(ref)
        body, to_list, cc_list, subject_str = invoice_email_unsent(ref, order)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'INVOICED PRODUCTION':
        part = planning_lot_prt_no(ref)
        body, to_list, cc_list, subject_str = transaction_invoiced_production(ref, part)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'CONVERTED DATE':
        client = order_cli_name1(ref)
        body, to_list, cc_list, subject_str = order_converted_date(ref, client)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'EXISTING BLANKET':
        client = order_cli_name1(ref)
        blankets = order_existing_blankets(ref)
        body, to_list, cc_list, subject_str = order_existing_blanket(ref, client, blankets)
        email_handler(body, to_list, cc_list, subject_str)


while 1:
    conn_sigm.poll()
    conn_sigm.commit()
    while conn_sigm.notifies:
        notify = conn_sigm.notifies.pop()
        raw_payload = notify.payload
        print(f'Alert Triggered : {raw_payload}')
        payload_handler(raw_payload)
