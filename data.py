import re
import datetime
from sql import *
from emails import *


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