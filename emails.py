import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from quatro import dev_check, log


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
        to_list = ['sales@quatroair.com']
        cc_list = ['carmy.m@quatroair.com']

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
        to_list = ['sanjay.m@quatroair.com']
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
        to_list = ['sanjay.m@quatroair.com']
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
        to_list = ['sanjay.m@quatroair.com']
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
        cc_list = ['']

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


def invoiced_unrun_production(ord_no):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        to_list = ['sanjay.m@quatroair.com']
        cc_list = ['']

    subject_str = f"SIGM Invoiced Production (Order # {ord_no})"
    body = f'Our system has detected an invoice has been generated ' \
           f'for an existing production linked to order {ord_no}. \n\n' \
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
        cc_list = ['']

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
        cc_list = ['']

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
        to_list = ['sanjay.m@quatroair.com']
        cc_list = ['']

    plq_lot_no = ref
    subject_str = f"SIGM Uncheck Lot Calculation {plq_lot_no}"
    body = f'Our system has detected a planning lot ({plq_lot_no}) has been calculated without using' \
           f' manufactured inventory. \n\n'
    body += 'Thank you'
    return body, to_list, cc_list, subject_str


def order_unit_date(ref, cli_name1):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        to_list = ['sales@quatroair.com']
        cc_list = ['']

    ord_no = ref
    subject_str = f"SIGM Order {ord_no} / Client {cli_name1} Issue"
    body = f"Our system has detected an incorrect order line date (Order Number {ord_no}) for {cli_name1}. \n\n" \
           f"This is due to the order line required date being less than 14 days from the order date for a unit. " \
           f"This is possible for expedited orders, otherwise order line required dates should be at least 14 days " \
           f"from the order date. \n"
    body += '\n' \
            'If this was done intentionally, please ignore this message.\n\n' \
            'Thank you.'

    return body, to_list, cc_list, subject_str


def order_duplicate_po(ord_no, cli_name1):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        to_list = ['sales@quatroair.com']
        cc_list = ['']

    subject_str = f"SIGM Order {ord_no} / Client {cli_name1} Issue"
    body = f"Our system has detected a duplicate client order number (Order Number {ord_no}) for {cli_name1}. \n\n" \
           f"This is due to two orders with the same invoice-to client having the same client order number. \n"
    body += '\n' \
            'If this was done intentionally, please ignore this message.\n\n' \
            'Thank you.'

    return body, to_list, cc_list, subject_str


def order_missing_tax_id(ord_no, cli_name1):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        to_list = ['sales@quatroair.com']
        cc_list = ['']

    subject_str = f"SIGM Order {ord_no} / Client {cli_name1} Issue"
    body = f"Our system has detected a missing tax ID for a US client (Order Number {ord_no}) for {cli_name1}. \n\n" \
           f"Printing a picking list will be impossible until the tax ID number is entered for the client. \n"
    body += '\n' \
            'If this was done intentionally, please ignore this message.\n\n' \
            'Thank you.'

    return body, to_list, cc_list, subject_str


def order_truck_shipment(ord_no, cli_name1):
    if dev_check():
        to_list = ['jan.z@quatroair.com']
        cc_list = ['jan.z@quatroair.com']
    else:
        to_list = ['sales@quatroair.com']
        cc_list = ['']

    subject_str = f"SIGM Order {ord_no} / Client {cli_name1} Issue"
    body = f"Our system has detected an order including (a) 'PALLET ONLY' part(s) with carrier set to UPS. \n"
    body += f"Orders including such parts can only ship by truck. \n\n"
    body += f"Thank you."

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
    log('Email Sent')
