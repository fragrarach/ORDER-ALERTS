import re
import datetime
import statements
from emails import *
from quatro import log


# Split payload string, store as named variables, send to duplicate alert checker
def payload_handler(payload):
    ref_type = payload.split(", ")[0]
    ref = payload.split(", ")[1]
    alert = payload.split(", ")[2]
    sigm_string = payload.split(", ")[3]
    user = re.findall(r'(?<=aSIGMWIN\.EXE u)(.*)(?= m)', sigm_string)[0]
    station = re.findall(r'(?<= w)(.*)$', sigm_string)[0]
    timestamp = datetime.datetime.now()

    return timestamp, alert, ref_type, ref, user, station


# Calls appropriate email body formatting function based on triggered alert
def alert_handler(alert, ref, user):
    if alert == 'BO ALLOWED':
        body, to_list, cc_list, subject_str = client_bo_allowed(ref)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'BO NOT ALLOWED':
        ord_no = ref
        cli_id = statements.ord_no_cli_id(ord_no)
        cli_name1 = statements.cli_id_cli_name1(cli_id)
        body, to_list, cc_list, subject_str = order_bo_not_allowed(ref, cli_name1)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'NOT RESERVED':
        ord_no = ref
        cli_id = statements.ord_no_cli_id(ord_no)
        cli_name1 = statements.cli_id_cli_name1(cli_id)
        body, to_list, cc_list, subject_str = order_not_reserved(ref, cli_name1, user)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'ZERO QUANTITY':
        ord_no = ref
        cli_id = statements.ord_no_cli_id(ord_no)
        cli_name1 = statements.cli_id_cli_name1(cli_id)
        body, to_list, cc_list, subject_str = order_zero_quantity(ref, cli_name1)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'ORDER CANCELLED':
        body, to_list, cc_list, subject_str = order_cancelled(ref, user)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'NEW BLANKET':
        ord_no = ref
        cli_id = statements.ord_no_cli_id(ord_no)
        cli_name1 = statements.cli_id_cli_name1(cli_id)
        body, to_list, cc_list, subject_str = order_new_blanket(ref, cli_name1, user)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'NEW RELEASE':
        ord_no = ref
        cli_id = statements.ord_no_cli_id(ord_no)
        cli_name1 = statements.cli_id_cli_name1(cli_id)
        body, to_list, cc_list, subject_str = order_new_release(ref, cli_name1, user)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'CANCELLED PACKING SLIP':
        ord_no = statements.packing_slip_ord_no(ref)
        body, to_list, cc_list, subject_str = order_cancelled_packing_slip(ref, user, ord_no)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'SHIPPING COST MISSING':
        ord_no = statements.invoice_ord_no(ref)
        body, to_list, cc_list, subject_str = order_shipping_cost_missing(ref, ord_no)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'LINE DATES':
        ord_no = ref
        cli_id = statements.ord_no_cli_id(ord_no)
        cli_name1 = statements.cli_id_cli_name1(cli_id)
        body, to_list, cc_list, subject_str = order_different_line_dates(ref, cli_name1)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'ZERO BANK FEES':
        ord_no = ref
        cli_id = statements.ord_no_cli_id(ord_no)
        cli_name1 = statements.cli_id_cli_name1(cli_id)
        body, to_list, cc_list, subject_str = order_zero_bank_fees(ref, cli_name1)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'NEGATIVE QUANTITY':
        prt_no = statements.transaction_prt_no(ref)
        ptn_desc = statements.transaction_ptn_desc(ref)
        body, to_list, cc_list, subject_str = transaction_negative_quantity(ref, prt_no, ptn_desc)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'COMPLETED BLANKET':
        ord_no = ref
        cli_id = statements.ord_no_cli_id(ord_no)
        cli_name1 = statements.cli_id_cli_name1(cli_id)
        body, to_list, cc_list, subject_str = order_completed_blanket(ref, cli_name1)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'UNSENT INVOICE EMAIL':
        ord_no = statements.invoice_ord_no(ref)
        body, to_list, cc_list, subject_str = invoice_email_unsent(ref, ord_no)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'INVOICED PRODUCTION':
        ord_no = statements.orl_id_ord_no(ref)
        body, to_list, cc_list, subject_str = invoiced_unrun_production(ord_no)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'CONVERTED DATE':
        ord_no = ref
        cli_id = statements.ord_no_cli_id(ord_no)
        cli_name1 = statements.cli_id_cli_name1(cli_id)
        body, to_list, cc_list, subject_str = order_converted_date(ref, cli_name1)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'EXISTING BLANKET':
        ord_no = ref
        cli_id = statements.ord_no_cli_id(ord_no)
        cli_name1 = statements.cli_id_cli_name1(cli_id)
        blankets = statements.order_existing_blankets(ref)
        body, to_list, cc_list, subject_str = order_existing_blanket(ref, cli_name1, blankets)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'MISSING COMPONENT':
        ord_no = ref
        cli_id = statements.ord_no_cli_id(ord_no)
        cli_name1 = statements.cli_id_cli_name1(cli_id)
        missing_components = statements.order_missing_component_prt_no(ref)
        body, to_list, cc_list, subject_str = order_missing_component(ref, cli_name1, missing_components)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'COMPONENT MULTIPLIER':
        ord_no = ref
        cli_id = statements.ord_no_cli_id(ord_no)
        cli_name1 = statements.cli_id_cli_name1(cli_id)
        component_multiplier = statements.order_component_multiplier_prt_no(ref)
        if component_multiplier[0][2]:
            body, to_list, cc_list, subject_str = order_component_multiplier(ref, cli_name1, component_multiplier)
            email_handler(body, to_list, cc_list, subject_str)
        else:
            log(f'FALSE POSITIVE COMPONENT MULTIPLIER')

    elif alert == 'UNCHECKED NEED CALCULATION':
        body, to_list, cc_list, subject_str = planning_lot_calculation(ref, user)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'UNIT DATES':
        ord_no = ref
        cli_id = statements.ord_no_cli_id(ord_no)
        cli_name1 = statements.cli_id_cli_name1(cli_id)
        body, to_list, cc_list, subject_str = order_unit_date(ord_no, cli_name1)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'DUPLICATE PO':
        ord_no = ref
        cli_id = statements.ord_no_cli_id(ord_no)
        cli_name1 = statements.cli_id_cli_name1(cli_id)
        body, to_list, cc_list, subject_str = order_duplicate_po(ord_no, cli_name1)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'MISSING TAX ID':
        ord_no = ref
        cli_id = statements.ord_no_cli_id(ord_no)
        cli_name1 = statements.cli_id_cli_name1(cli_id)
        body, to_list, cc_list, subject_str = order_missing_tax_id(ord_no, cli_name1)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'TRUCK SHIPMENT':
        ord_no = ref
        cli_id = statements.ord_no_cli_id(ord_no)
        cli_name1 = statements.cli_id_cli_name1(cli_id)
        body, to_list, cc_list, subject_str = order_truck_shipment(ord_no, cli_name1)
        email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'RECEPTION':
        pul_id = ref
        puh_no = statements.pul_id_puh_no(pul_id)
        puh_reference = statements.puh_no_puh_reference(puh_no)
        if 'ALERT' in puh_reference:
            usr_no = statements.puh_no_usr_no(puh_no)
            sup_name1 = statements.puh_no_sup_name1(puh_no)
            body, to_list, cc_list, subject_str = purchase_order_reception(usr_no, puh_reference, puh_no, sup_name1)
            email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'MISSING SUPPLIER':
        pul_id = ref
        puh_no = statements.pul_id_puh_no(pul_id)
        prt_no = statements.pul_id_prt_no(pul_id)
        if prt_no != 'SPECIAL':
            body, to_list, cc_list, subject_str = purchase_order_missing_supplier(user, puh_no, prt_no)
            email_handler(body, to_list, cc_list, subject_str)

    elif alert == 'OVER RECEPTION':
        pul_id = ref
        puh_no = statements.pul_id_puh_no(pul_id)
        body, to_list, cc_list, subject_str = purchase_order_over_reception(user, puh_no)
        email_handler(body, to_list, cc_list, subject_str)
