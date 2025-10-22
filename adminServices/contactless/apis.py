"""contact less module APIs"""

#  File details-
#   Author      - Manish Pawar
#   Description - This file contains APIs for Contactless module.
#   Name        - contact less module APIs
#   Modified by - Vismay Raul

# These are all the imports that we are exporting from
# different module's from project or library.
import json
import math
from queue import Queue
import traceback
import pandas as pd
import base64
import threading
import json
import traceback
import concurrent.futures
from datetime import datetime, timedelta
from decimal import Decimal
from dateutil import parser

import pandas as pd
from dateutil.relativedelta import relativedelta
import pytz

# pylint: disable-msg=W0622
from requests.exceptions import ConnectionError
from passlib.hash import django_pbkdf2_sha256 as handler
from decouple import config

from django.db.models import Q
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.shortcuts import render
from django.http import JsonResponse

from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response

# pylint:disable=import-error
from sharedServices.decorators import authenticated_user, allowed_users
from .api_v2 import FetchReceiptData, get_all_stations, get_charge_points, get_object_by, group_driivz, bulk_upsert_driivz_cache, bulk_upsert_driivz_database
# pylint: disable-msg=C0412
from sharedServices.constants import (
    NO,
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    POST_METHOD_ALLOWED,
    GET_METHOD_ALLOWED,
    VALETING_KEY_WORDS,
    VALETING_TAX_RATE,
    DEFAULT_VALETING_TAX_RATE,
    SECRET_KEY_IN_VALID,
    SECRET_KEY_NOT_PROVIDED,
    DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET,
    WORLDLINE_PAYMENT_TERMINAL,
    REQUEST_API_TIMEOUT,
    YES,
    THIRD_PARTY_DATA_IMPORT,
    SWARCO_SHEET_REQUIRED_FIELDS,
    ADVAM_SHEET_REQUIRED_FIELDS,
    PAYTER_PAYMENT_TERMINAL,
    ADVAM_PAYMENT_TERMINAL,
    GET_REQUEST,
    POST_REQUEST,
    DRIIVZ_SHEET_REQUIRED_FIELDS,
)
from sharedServices.model_files.station_models import (
    Stations,
    ChargePoint,
    ValetingTerminals,
)
from sharedServices.model_files.config_models import BaseConfigurations
from sharedServices.model_files.contactless_models import (
    ContactlessReceiptEmailTracking,
    ThirdPartyServicesData,
    ReceiptHeroReceiptsData
)
from sharedServices.common import (
    redis_connection,
    array_to_string_converter,
    string_to_array_converter,
    hasher,
    date_formater_for_contactless_receipts,
    filter_function_for_base_configuration,
    filter_url,
    custom_round_function,
)
from sharedServices.email_common_functions import (
    email_sender,
    send_exception_email_function,
)
from sharedServices.contactless_common_functions import (
    get_payter_transactions_from_data_api,
)
from sharedServices.driivz_api_gateway_functions import (
    get_driivz_api_gateway_dms_ticket
)
from sharedServices.sentry_tracers import traced_request

from .helper_functions import (
    driivz_api,
    payter_api,
    thirdparty_api_selector,
)

from .app_level_constants import (
    CUSTOM_SEARCH,
    CUSTOMER_CARE_EMAIL,
    AMOUNT_TOLERANCE,
    SESSION_NOT_FOUND_ERROR_MESSAGE,
    DRIIVZ,
    PAYTER,
    BILLING_PLAN_CODE,
    BILLING_PLAN_CODE_VALUE,
    DATE_FORMAT_FOR_DRIIVZ,
    SUCCESSFULLY_FETCHED_DATA,
    FAILED,
    COMPLETE,
    MIN_MONTHS_RANGE,
    MIN_DATE_FOR_DATA_RETRNTION_KEY,
    GET_RECEIPTS_TIMEOUT_VALUE,
    SWARCO,
    ADVAM,
    TIME_TOLERANCE,
    WORLDLINE_PLAN,
    PAYTER_PLAN,
    ADVAM_PLAN,
)

from sharedServices.model_files.contactless_models import (
    ValetingTransactionData,
)

import pprint

# --- Config for third-party sources ---
THIRD_PARTY_SHEET_CONFIG = {
    'swarco': {
        'required_fields': SWARCO_SHEET_REQUIRED_FIELDS,
        'group_by': 'End Date',
        'grouping_func': lambda df: df['End Date'].str[:10],
        'extra_processing': 'swarco',
    },
    'advam': {
        'required_fields': ADVAM_SHEET_REQUIRED_FIELDS,
        'group_by': 'Authorised',
        'grouping_func': lambda df: df['Authorised'].str[:10],
        'extra_processing': 'advam',
    },
    'driivz': {
        'required_fields': DRIIVZ_SHEET_REQUIRED_FIELDS,
        'group_by': 'Authorised',
        'grouping_func': lambda df: df['Authorised'].str[:10],
        'extra_processing': 'driivz',
    },
}

THIRD_PARTY_SOURCES = [
    {"value": "driivz", "label": "Driivz"},
    {"value": "swarco", "label": "Swarco"},
    {"value": "advam", "label": "Advam"},
]

def process_thirdparty_json_data(json_data, source, request, **kwargs):
    """Generalized function to process third-party JSON data and store in DB/cache."""
    create_array = []
    update_array = []
    for data_date, data_to_save in json_data.items():
        if data_date:
            # Per-source extra processing (e.g., cost calculation for swarco)
            for session_data in data_to_save:
                if source == SWARCO:
                    swarco_session_tarrif = kwargs.get('swarco_session_tarrif', 0.79)
                    swarco_tax_rate = kwargs.get('swarco_tax_rate', 20)
                    total_cost = custom_round_function(
                        Decimal(str(session_data["Total kWh"])) * Decimal(swarco_session_tarrif),
                        2, True)
                    total_cost_without_tax = custom_round_function(
                        Decimal(str(total_cost)) / (1 + (Decimal(swarco_tax_rate) / 100)),
                        2, True)
                    tax_amount = custom_round_function(
                        Decimal(f"{total_cost}") - Decimal(f"{total_cost_without_tax}"),
                        2, True)
                    session_data["Cost"] = {
                        "currency": "GBP",
                        "totalTax": tax_amount,
                        "totalTaxRate": float(swarco_tax_rate),
                        "total": total_cost,
                    }
                session_data.pop("Date for Grouping", None)
                for key in session_data:
                    if math.isnan(try_float(session_data[key])):
                        session_data[key] = None
            data_to_upload, action = swarco_or_advam_data_db_operations(
                data_date,
                json_data[data_date],
                source,
                request.user.full_name,
            )
            if action == "Create":
                create_array = create_array + data_to_upload
            else:
                update_array = update_array + data_to_upload
    if create_array:
        ThirdPartyServicesData.objects.bulk_create(create_array)
    if update_array:
        ThirdPartyServicesData.objects.bulk_update(
            update_array,
            ["data", "updated_date", "updated_by"],
        )
    return JsonResponse(
        status=200, data={"message": f"File data uploaded successfully for {source.title()}!"}
    )


def detect_source_from_filename(file_name):
    lower_name = file_name.lower()
    found = []
    for key in ['swarco', 'driivz', 'advam']:
        if key in lower_name:
            found.append(key)
    if len(found) == 1:
        return found[0]
    elif len(found) > 1:
        return 'ambiguous', found
    else:
        return None


def process_thirdparty_excel_sheet(uploaded_file, file_source, request, file_extension, file_name=None):
    """Generalized function to process excel/csv sheets for any third-party source."""
    print(f"[DEBUG] Uploaded file name: {file_name}")
    # Validate file_source against allowed sources
    allowed_sources = [src["value"] for src in THIRD_PARTY_SOURCES]
    if file_source not in allowed_sources:
        print(f"[ERROR] Unsupported or missing source: {file_source}")
        return JsonResponse(status=406, data={"error": f"Unsupported or missing source: {file_source}. Allowed: {allowed_sources}"})
    print(f"[DEBUG] file_source (final): {file_source}")
    config = THIRD_PARTY_SHEET_CONFIG.get(file_source.lower())
    print(f"[DEBUG] config used: {config}")
    if not config:
        print(f"[ERROR] Unsupported source: {file_source}")
        return JsonResponse(status=406, data={"error": f"Unsupported source: {file_source}"})
    # Read file
    if file_source in ['swarco', 'driivz']:
        header_row = 1
    else:
        header_row = 0
    print(f"[DEBUG] Reading file as {'excel' if file_extension == 'xlsx' else 'csv'} with header row {header_row}...")
    data_frame = (
        pd.read_excel(uploaded_file, header=header_row)
        if file_extension == "xlsx"
        else pd.read_csv(uploaded_file, header=header_row, encoding="latin1")
    )
    print(f"[DEBUG] Uploaded columns: {list(data_frame.columns)}")
    print(f"[DEBUG] Required fields: {config['required_fields']}")
    # Validate required fields
    if not set(config['required_fields']).issubset(set(data_frame.columns)):
        print(f"[ERROR] Missing required fields: {set(config['required_fields']) - set(data_frame.columns)}")
        return return_missing_field_error(
            set(data_frame.columns), set(config['required_fields'])
        )
    # Per-source extra processing (e.g., for swarco, advam, driivz)
    if file_source == 'swarco':
        swarco_tax_rate = filter_function_for_base_configuration(
            "swarco_tax_rate_base_config_key", "20"
        )
        swarco_billing_plan = filter_function_for_base_configuration(
            "swarco_billing_plan_base_config_key", "Swarco-Plan"
        )
        swarco_session_tarrif = filter_function_for_base_configuration(
            "swarco_session_tarrif_base_config_key", "0.79"
        )
        data_frame = data_frame[data_frame["Billing Plan"].isnull()].copy()
        data_frame["End Date"] = data_frame["End Date"].astype(str)
        data_frame["Start Date"] = data_frame["Start Date"].astype(str)
        data_frame["Date for Grouping"] = data_frame["End Date"].str[:10]
        data_frame["Billing Plan"].fillna(swarco_billing_plan, inplace=True)
        grouped_df = data_frame.groupby("Date for Grouping")
        json_data = {date: group.to_dict(orient="records") for date, group in grouped_df}
        print(f"[DEBUG] Grouped data keys: {list(json_data.keys())}")
        return process_thirdparty_json_data(
            json_data, file_source, request,
            swarco_session_tarrif=swarco_session_tarrif, swarco_tax_rate=swarco_tax_rate
        )
    elif file_source == 'driivz':
        driivz_tax_rate = filter_function_for_base_configuration(
            "driivz_tax_rate_base_config_key", "20"
        )
        driivz_session_tarrif = filter_function_for_base_configuration(
            "driivz_session_tarrif_base_config_key", "0.79"
        )
        allowed_billing_plans = [WORLDLINE_PLAN, PAYTER_PLAN, ADVAM_PLAN]
        data_frame = data_frame[data_frame["Billing Plan"].isin(allowed_billing_plans)].copy()
        data_frame["End Date"] = data_frame["End Date"].astype(str)
        data_frame["Start Date"] = data_frame["Start Date"].astype(str)
        data_frame["Date for Grouping"] = data_frame["End Date"].str[:10]
        grouped_df = data_frame.groupby("Date for Grouping")
        json_data = {date: group.to_dict(orient="records") for date, group in grouped_df}
        print(f"[DEBUG] Grouped data keys: {list(json_data.keys())}")
        return process_driivz_json_data(
            json_data, file_source, request,
            driivz_session_tarrif=driivz_session_tarrif, driivz_tax_rate=driivz_tax_rate
        )
    elif file_source == 'advam':
        print(f"[DEBUG] Entering advam processing block.")
        data_frame["Authorised"] = data_frame["Authorised"].astype(str)
        data_frame["Custom Unique Key"] = (
            data_frame["Authorised"]
            + data_frame["Card"]
            + data_frame["Transaction Amount"].astype(str)
            + data_frame["CPID"]
        )
        data_frame["Date for Grouping"] = data_frame["Authorised"].str[:10]
        data_frame = data_frame[
            ADVAM_SHEET_REQUIRED_FIELDS + ["Date for Grouping", "Custom Unique Key"]
        ]
        grouped_df = data_frame.groupby("Date for Grouping")
        json_data = {date: group.to_dict(orient="records") for date, group in grouped_df}
        return process_thirdparty_json_data(json_data, file_source, request)
    else:
        print(f"[ERROR] Unsupported file source: {file_source}")
        return JsonResponse(status=406, data={"error": f"Unsupported file source: {file_source}"})


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=THIRD_PARTY_DATA_IMPORT)
def get_thirdparty_data(request):
    """stores thirdparty data into database manually"""
    try:
        success_message = ""
        error_message = ""
        url_data = filter_url(
            request.user.role_id.access_content.all(), THIRD_PARTY_DATA_IMPORT
        )
        if request.method == "POST":
            if request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest':
                file_source = request.POST.get("source")
                file_name = request.POST.get("fileName")
                uploaded_file = request.FILES.get("dataFile")
                if file_name.split(".")[-1] in ["xlsx", "csv"]:
                    if file_name and uploaded_file:
                        # Now supports swarco, advam, driivz, and future sources
                        return process_thirdparty_excel_sheet(
                            uploaded_file,
                            file_source,
                            request,
                            file_name.split(".")[-1],
                            file_name=file_name
                        )
                    return JsonResponse(
                        status=404, data={"error": "File details not found."}
                    )
                return JsonResponse(
                    status=406, data={"error": "File format not accepted."}
                )
            date = request.POST.get("date")
            source = request.POST.get("source")
            print(f"Date :{date}, Source :{source}, user :{request.user.full_name}")
            if date and source:
                date = datetime.strptime(date, "%Y-%m-%d")
                res = thirdparty_api_selector(
                    source, date, request.user.full_name
                )
                if res.data["status"] is True:
                    success_message = res.data["message"]
                else:
                    error_message = res.data["message"]
                return render(
                    request,
                    "contactless/manually_thirdparty_data_import.html",
                    context={
                        "data": url_data,
                        "error": error_message,
                        "success": success_message,
                    },
                )
            error_message = "Please enter required data"
        return render(
            request,
            "contactless/manually_thirdparty_data_import.html",
            context={
                "data": url_data,
                "error": error_message,
                "success": success_message,
                "sources": THIRD_PARTY_SOURCES,
            },
        )
    except COMMON_ERRORS + (FileNotFoundError,) as _:
        traceback.print_exc()
        return JsonResponse(
            status=500, data={"error": "Something went wrong!"}
        )


def station_data_formater_for_auto_complete_api_for_app(station):
    """this function formats station data for auto complete API for App"""
    charge_points = ChargePoint.objects.filter(station_id=station, deleted=NO)
    valeting_terminals = ValetingTerminals.objects.filter(
        station_id=station, deleted=NO, status="Active"
    )
    station_payment_terminal = string_to_array_converter(station.payment_terminal)
    return {
        "id": station.id,
        "station_id": station.station_id,
        "station": (
            str(station.station_name)
            + ", "
            + str(station.post_code)
            + ", "
            + str(station.station_id)
        ),
        "charge_point_ids": [
            charge_point.charger_point_id
            for charge_point in charge_points
            if charge_point.charger_point_id
        ],
        "terminal_ids": [
            charge_point.payter_terminal_id
            for charge_point in charge_points
            if charge_point.payter_terminal_id
        ]
        + [
            valeting_terminal.payter_serial_number
            for valeting_terminal in valeting_terminals
            if valeting_terminal.payter_serial_number
        ],
        "station_payment_terminal": (
            WORLDLINE_PAYMENT_TERMINAL
            if WORLDLINE_PAYMENT_TERMINAL
            in station_payment_terminal
            else str(station_payment_terminal)
        ),
        "receipt_hero_site_name": station.receipt_hero_site_name,
        "valeting_available_on_station": station.valeting == YES,
    }


def station_data_formater_for_auto_complete_api(station):
    """this function formats station data for auto complete API"""
    charge_points = ChargePoint.objects.filter(station_id=station, deleted=NO)
    valeting_terminals = ValetingTerminals.objects.filter(
        station_id=station, deleted=NO, status="Active"
    )
    return {
        "id": station.id,
        "station_id": station.station_id,
        "station": (
            str(station.station_name)
            + ", "
            + str(station.post_code)
            + ", "
            + str(station.station_id)
        ),
        "brand": station.brand,
        "charge_point_ids": [
            charge_point.charger_point_id
            for charge_point in charge_points
            if charge_point.charger_point_id
        ],
        "terminal_ids": [
            charge_point.payter_terminal_id
            for charge_point in charge_points
            if charge_point.payter_terminal_id
        ]
        + [
            valeting_terminal.payter_serial_number
            for valeting_terminal in valeting_terminals
            if valeting_terminal.payter_serial_number
        ],
        "charge_point_names": [
            charge_point.charger_point_name
            for charge_point in charge_points
            if charge_point.charger_point_name
        ],
        "station_payment_terminal": string_to_array_converter(
            station.payment_terminal
        ),
        "receipt_hero_site_name": station.receipt_hero_site_name,
        "valeting_available_on_station": station.valeting == YES,
    }


class StationListAutoCompleteAPI(APIView):
    """station search with auto compelete API"""

    # Permission classes are used to restrict the user
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """get stations with provided key"""
        try:
            is_contactless_portal = self.request.query_params.get(
                "is_contactless_portal", "No"
            )
            is_contactless_portal = is_contactless_portal == "Yes"
            station_data = (
                redis_connection.get("contactless_stations_list")
                if is_contactless_portal
                else redis_connection.get("contactless_stations_list_for_app")
            )
            if station_data:
                data = string_to_array_converter(station_data.decode("utf-8"))
            else:
                stations = Stations.objects.filter(
                    ~Q(payment_terminal="None"),
                    deleted=NO,
                    status="Active",
                )
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=400
                ) as executor:
                    data = executor.map(
                        (
                            station_data_formater_for_auto_complete_api
                            if is_contactless_portal
                            else station_data_formater_for_auto_complete_api_for_app
                        ),
                        list(stations),
                    )
                data = sorted(
                    data,
                    key=lambda station_details: station_details["station"],
                )
                redis_connection.set(
                    (
                        "contactless_stations_list"
                        if is_contactless_portal
                        else "contactless_stations_list_for_app"
                    ),
                    array_to_string_converter(data),
                )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Fetched stations list.",
                    "data": data,
                    "get_receipts_timeout_value": int(
                        filter_function_for_base_configuration(
                            "get_receipts_timeout_value",
                            GET_RECEIPTS_TIMEOUT_VALUE,
                        )
                    ),
                }
            )

        except COMMON_ERRORS as error:
            print("Get station list API failed due to exception -> ")
            print(error)
            start_caching_station_finder_data = threading.Thread(
                target=send_exception_email_function,
                args=[request.build_absolute_uri(), str(error)],
                daemon=True
            )
            start_caching_station_finder_data.start()
            return API_ERROR_OBJECT


def check_driivz_or_swarco_amount(
    commited_amount, driivz_or_swarco_sessions, is_swarco_receipt=False
):
    """this function returns true if driivz
    session amount matches with payter amount"""
    positive_limit = commited_amount + AMOUNT_TOLERANCE
    negative_limit = 0
    if commited_amount > AMOUNT_TOLERANCE:
        negative_limit = commited_amount - AMOUNT_TOLERANCE
    if is_swarco_receipt:
        return [
            session
            for session in driivz_or_swarco_sessions
            if (
                session["Cost"]["total"] >= negative_limit
                and session["Cost"]["total"] <= positive_limit
            )
        ]
    return [
        session
        for session in driivz_or_swarco_sessions
        if (
            session["cost"]["total"] >= negative_limit
            and session["cost"]["total"] <= positive_limit
        )
    ]


def print_for_portal(
    station_db_id,
    station_id,
    card_last_4,
    session_date_time,
    driivz_sessions,
    terminal_ids,
    paid_amount,
):
    """this function filters sessions from payter"""
    station = Stations.objects.filter(station_id=station_id).first()
    start_date = (
        int(
            (
                timezone.localtime(session_date_time) - timedelta(hours=6)
            ).timestamp()
        )
        * 1000
    )
    end_date = (
        int(
            (
                timezone.localtime(session_date_time) + timedelta(hours=6)
            ).timestamp()
        )
        * 1000
    )
    terminal_ids_string = " OR ".join(terminal_ids)
    payload = json.dumps(
        {
            "index": "Transactions",
            "maxResults": 100,
            "query": (
                (
                    f"extra-TXN-MASKED-PAN:*{card_last_4} AND committedAmount:{int(Decimal(str(paid_amount))*100)} AND serialNumber:("
                    + terminal_ids_string
                    + ")"
                )
            ),
            "sorts": [{"field": "txnTimestamp", "asc": False}],
            "filters": [
                {
                    "type": "range",
                    "field": "@timestamp",
                    "from": start_date,
                    "to": end_date,
                }
            ],
        }
    )

    response = get_payter_transactions_from_data_api(payload)
    if response.status_code == 401:
        response = get_payter_transactions_from_data_api(payload, True)

    sessions = []
    valeting_tax_rate = filter_function_for_base_configuration(
        VALETING_TAX_RATE, DEFAULT_VALETING_TAX_RATE
    )
    if response.status_code == 200:
        transactions = json.loads(response.content)["documents"]
        for session in transactions:
            if "committedAmount" in session:
                commited_amount = session["committedAmount"] / 100
                if all(
                    word in session["terminalDomain"]
                    for word in VALETING_KEY_WORDS
                ):
                    session["@timestamp"] = (
                        date_formater_for_contactless_receipts(
                            session["@timestamp"]
                        )
                    )
                    sessions.append(
                        {
                            "payter_data": {**session},
                            "station_db_id": station_db_id,
                            "station_id": station_id,
                            "station_name": get_driivz_station_name_for_station_id(
                                station.station_id, station.site_title
                            ),
                            "receipt_for": "Valeting",
                            "valeting_tax_rate": float(valeting_tax_rate),
                            "description_of_service": "Valeting",
                        }
                    )
                else:
                    session_matching = check_driivz_or_swarco_amount(
                        commited_amount, driivz_sessions
                    )
                    if session_matching:
                        for matched_driivz_session in session_matching:
                            matched_driivz_session["startOn"] = (
                                date_formater_for_contactless_receipts(
                                    matched_driivz_session["startOn"]
                                )
                            )
                            matched_driivz_session["stopOn"] = (
                                date_formater_for_contactless_receipts(
                                    matched_driivz_session["stopOn"]
                                )
                            )
                            matched_driivz_session["station"]["address"]["address1"] = (
                                get_driivz_station_name_for_station_id(station.station_id, station.site_title)
                                + ","
                            )
                            sessions.append(
                                {
                                    "driivz_data": {**matched_driivz_session},
                                    "payter_data": {**session},
                                    "station_db_id": station_db_id,
                                    "station_id": station_id,
                                    "receipt_for": "Charging Session",
                                }
                            )
    return sessions

def getAdvamInPayterFormat(advam_receipts, station_db_id, station_id):
    result = []
    for key, value in advam_receipts.items():
        if key == "EV_Advam":
            for advam_swarco in value:
                advam = advam_swarco.get("advam")
                swarco = advam_swarco.get("swarco")
                payter = {
                    "extra-TXN-MASKED-PAN": advam.get("Card"),
                    "committedAmount": int(advam.get("Transaction Amount")*100),
                    "id": str(swarco.get("ID")),
                    "brandName": advam.get("Type"),
                    "paymentType": "EMV",
                    "currency": "GBP",
                    "ifd": "CONTACTLESS",
                    "@timestamp": datetime.strptime(advam.get("Authorised"), "%Y-%m-%d %H:%M:%S")
                }
                driivz = {
                    "transactionId": swarco.get("ID"),
                    "totalEnergy": swarco.get("Total kWh"),
                    "startOn": datetime.strptime(swarco.get("Start Date"), "%Y-%m-%d %H:%M:%S"),
                    "stopOn": datetime.strptime(swarco.get("End Date"), "%Y-%m-%d %H:%M:%S"),
                    "caption": swarco.get("Charger").split(",")[0],
                    "address": {
                        "address1": advam_swarco.get("station_address")
                    },
                    "cost": {
                        "currency": "GBP",
                        "totalTaxRate": 20.0
                    }
                }
                result_object = {
                    "payter_data": payter,
                    "driivz_data": driivz,
                    "station_db_id": station_db_id,
                    "station_id": station_id,
                    "receipt_for": "Charging Session"
                }
                result.append(result_object)
    return result

def get_session_data_directly_from_thirdparty_source_for_portal(
    station_db_id,
    station_id,
    card_last_4,
    charge_point_ids,
    terminal_ids,
    sessions_date,
    paid_amount=None,
):
    """getting session directly from thirdparty"""

    session_date_time = datetime.strptime(
        sessions_date, "%Y-%m-%d %H:%M"
    ).replace(tzinfo=pytz.UTC)
    date_from = datetime.strftime(
        session_date_time - timedelta(hours=2), DATE_FORMAT_FOR_DRIIVZ
    )
    date_to = datetime.strftime(
        session_date_time + timedelta(hours=2), DATE_FORMAT_FOR_DRIIVZ
    )
    if not terminal_ids:
        print(
            "Terminal ID's not provided for below receipt details"
            + "\n"
            + f"Station ID -> {station_id},"
            + "\n"
            + f"Card last four digits -> {card_last_4} ,"
            + "\n"
            + f"Session date and time -> {sessions_date}"
            + "\n"
            + f"Paid amount -> {paid_amount},"
            + "\n"
        )
        return False
    # driivz API to get sessions in time range
    response = driivz_api(date_from, date_to)
    sessions = []
    sessions = print_for_portal(
        station_db_id,
        station_id,
        card_last_4,
        session_date_time,
        [
            session
            for session in (
                json.loads(response.content)["transactions"]
                if response.status_code == 200
                else []
            )
            if (
                BILLING_PLAN_CODE in session
                and session[BILLING_PLAN_CODE] in BILLING_PLAN_CODE_VALUE
                and (str(session["station"]["id"]) in charge_point_ids)
                and "total" in session["cost"]
            )
        ],
        terminal_ids,
        paid_amount,
    )
    return sessions


class SendSessionDataEmail(APIView):
    """send user receipt email"""

    # Permission classes are used to restrict the user
    permission_classes = [permissions.AllowAny]

    def post(self, send_user_receipt_email):
        """send user receipt email"""
        try:
            email = str(send_user_receipt_email.data.get("email", None))
            session_data = send_user_receipt_email.data.get(
                "session_data", None
            )
            pdf_file_name = str(
                send_user_receipt_email.data.get("pdf_file_name", None)
            )
            pdf_file = send_user_receipt_email.data.get("pdf_file", None)
            if (
                email is None
                or pdf_file is None
                or pdf_file_name is None
                or session_data is None
            ):
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Please provide required data.",
                    }
                )
            session_data = json.loads(session_data)
            if (
                (
                    session_data["receipt_for"] == "Charging Session"
                    and (
                        "driivz_data" not in session_data
                        or "transactionId" not in session_data["driivz_data"]
                        or "payter_data" not in session_data
                        or "@timestamp" not in session_data["payter_data"]
                    )
                )
                or (
                    session_data["receipt_for"] == "Swarco Charging Session"
                    and (
                        "swarco_data" not in session_data
                        or "ID" not in session_data["swarco_data"]
                        or "advam_data" not in session_data
                        or "Authorised" not in session_data["advam_data"]
                    )
                )
                or (
                    session_data["receipt_for"] == "RH Charging Session"
                    and (
                        "driivz_data" not in session_data
                        or "transactionId" not in session_data["driivz_data"]
                        or "RH_data" not in session_data
                        or "transactionDateTime" not in session_data["RH_data"]
                    )
                )
                or (
                    session_data["receipt_for"] == "Valeting"
                    and (
                        "payter_data" not in session_data
                        or "@timestamp" not in session_data["payter_data"]
                    )
                )
            ):
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Failed to get data for session details.",
                    }
                )
            unique_session_id = str(
                session_data["driivz_data"]["transactionId"]
                if session_data["receipt_for"]
                in ["Charging Session", "RH Charging Session"]
                else (
                    session_data["swarco_data"]["ID"]
                    if session_data["receipt_for"] == "Swarco Charging Session"
                    else session_data["payter_data"]["transactionId"]
                )
            )
            data_source = (
                "driivz and worldline"
                if session_data["receipt_for"] == "RH Charging Session"
                else (
                    "driivz and payter"
                    if session_data["receipt_for"] == "Charging Session"
                    else (
                        "swarco and advam"
                        if session_data["receipt_for"]
                        == "Swarco Charging Session"
                        else "payter"
                    )
                )
            )
            email_sent_records = (
                ContactlessReceiptEmailTracking.objects.filter(
                    email=hasher(email),
                    session_id=unique_session_id,
                    created_date__date=timezone.now().date(),
                    source=data_source,
                ).count()
            )
            maximum_emails_can_send = BaseConfigurations.objects.filter(
                base_configuration_key="contactless_max_emails_sending_count"
            ).first()
            if maximum_emails_can_send is None:
                maximum_emails_can_send = 5
            else:
                maximum_emails_can_send = int(
                    maximum_emails_can_send.base_configuration_value
                )
            if email_sent_records >= maximum_emails_can_send:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": (
                            "Exceeded the daily limit for email receipts."
                        ),
                    }
                )
            session_date = (
                session_data["RH_data"]["transactionDateTime"]
                .split("T")[0]
                .split("-")
                if "RH_data" in session_data
                else (
                    session_data["advam_data"]["Authorised"]
                    .split(" ")[0]
                    .split("-")
                    if "swarco_data" in session_data
                    else session_data["payter_data"]["@timestamp"]
                    .split("T")[0]
                    .split("-")
                )
            )
            session_date.reverse()
            email_subject = (
                "MFG Contactless Payment Receipt "
                + str("-".join(session_date))
                + " - "
                + unique_session_id
            )
            email_sent = email_sender(
                config("DJANGO_APP_SEND_USER_RECEIPT_TEMPLATE_ID"),
                email,
                {"subject": email_subject},
                attachment_data=base64.b64decode(pdf_file),
                attachment_name=pdf_file_name,
            )
            if email_sent:
                ContactlessReceiptEmailTracking.objects.create(
                    email=hasher(email),
                    session_id=unique_session_id,
                    created_date=timezone.now(),
                    updated_date=timezone.now(),
                    source=data_source,
                )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Email sent successfully.",
                }
            )

        except COMMON_ERRORS as error:
            print("Send Session Data Email API failed due to exception -> ")
            print(error)
            start_caching_station_finder_data = threading.Thread(
                target=send_exception_email_function,
                args=[
                    send_user_receipt_email.build_absolute_uri(),
                    str(error),
                ],
                daemon=True
            )
            start_caching_station_finder_data.start()
            return API_ERROR_OBJECT


def store_thirdparty_data(todays_date=None):
    """Getting thirdparty data Cron Job"""
    months_for_data_retention = filter_function_for_base_configuration(
        MIN_DATE_FOR_DATA_RETRNTION_KEY, MIN_MONTHS_RANGE
    )
    # all the dates required for getting to and from date for driivz and payter
    # min date is required for deleting the data from the database less than this mentioned date
    if todays_date is None:
        todays_date = timezone.localtime(timezone.now())
    todays_date = datetime.combine(todays_date.date(), datetime.min.time())
    previous_date = todays_date - timedelta(days=1)
    min_date_for_data_retention = previous_date - relativedelta(
        months=int(months_for_data_retention), days=1
    )
    # getting driivz data from driivz API and storing it to database and cache
    to_date = datetime.strftime(todays_date, DATE_FORMAT_FOR_DRIIVZ)
    from_date = datetime.strftime(previous_date, DATE_FORMAT_FOR_DRIIVZ)

    driivz_response = driivz_api(from_date, to_date)
    driivz_response_data_str = None
    if driivz_response.status_code == 200 and driivz_response is not None:
        driivz_response_data = json.loads(driivz_response.content)[
            "transactions"
        ]
        sessions = filter(
            lambda session: BILLING_PLAN_CODE in session
            and session[BILLING_PLAN_CODE] in BILLING_PLAN_CODE_VALUE,
            driivz_response_data,
        )
        driivz_response_data_str = json.dumps(list(sessions))
    try:
        driivz_db = ThirdPartyServicesData.objects.filter(
            source=DRIIVZ, data_date=previous_date.replace(tzinfo=pytz.UTC)
        )
        if not driivz_db:
            ThirdPartyServicesData.objects.create(
                data_date=previous_date.replace(tzinfo=pytz.UTC),
                source=DRIIVZ,
                data=(
                    driivz_response_data_str
                    if (
                        driivz_response.status_code == 200 and
                        driivz_response_data_str
                    )
                    else ""
                ),
                status=(
                    COMPLETE if driivz_response.status_code == 200 else FAILED
                ),
                created_date=timezone.localtime(timezone.now()),
                updated_date=timezone.localtime(timezone.now()),
                updated_by="Cron Job",
                details=(
                    SUCCESSFULLY_FETCHED_DATA
                    if driivz_response.status_code == 200
                    else driivz_response.text
                ),
            )
            ThirdPartyServicesData.objects.filter(
                data_date=min_date_for_data_retention.replace(tzinfo=pytz.UTC)
            ).delete()
            redis_connection.delete(
                f"{DRIIVZ}-{min_date_for_data_retention.date()}"
            )
        else:
            driivz_db.update(
                data_date=previous_date.replace(tzinfo=pytz.UTC),
                source=DRIIVZ,
                data=(
                    driivz_response_data_str
                    if driivz_response.status_code == 200
                    else ""
                ),
                status=(
                    COMPLETE if driivz_response.status_code == 200 else FAILED
                ),
                updated_date=timezone.localtime(timezone.now()),
                updated_by="Manual Entry",
                details=(
                    SUCCESSFULLY_FETCHED_DATA
                    if driivz_response.status_code == 200
                    else driivz_response.text
                ),
            )
        if driivz_response.status_code == 200:
            redis_connection.set(
                f"{DRIIVZ}-{previous_date.date()}",
                array_to_string_converter(list(sessions)),
            )
    except ConnectionError as error:
        print(
            "Store thirparty data Cron job failed due to error =>"
            + "\n"
            + f"{error}"
        )

    # getting payter data from payter API and storing it to database and cache
    start_date = int((previous_date).timestamp()) * 1000
    end_date = int((todays_date).timestamp()) * 1000
    payter_response = payter_api(start_date, end_date)
    if payter_response.status_code == 200:
        payter_response_data = json.loads(payter_response.content)["documents"]
        payter_response_data_str = json.dumps(payter_response_data)
    try:
        payter_db = ThirdPartyServicesData.objects.filter(
            source=PAYTER, data_date=previous_date.replace(tzinfo=pytz.UTC)
        )
        if not payter_db:
            ThirdPartyServicesData.objects.create(
                data_date=previous_date.replace(tzinfo=pytz.UTC),
                source=PAYTER,
                data=(
                    payter_response_data_str
                    if payter_response.status_code == 200
                    else ""
                ),
                status=(
                    COMPLETE if payter_response.status_code == 200 else FAILED
                ),
                created_date=timezone.localtime(timezone.now()),
                updated_date=timezone.localtime(timezone.now()),
                updated_by="Cron Job",
                details=(
                    SUCCESSFULLY_FETCHED_DATA
                    if payter_response.status_code == 200
                    else payter_response.reason
                ),
            )
            ThirdPartyServicesData.objects.filter(
                data_date=min_date_for_data_retention.replace(tzinfo=pytz.UTC)
            ).delete()
            redis_connection.delete(
                f"{PAYTER}-{min_date_for_data_retention.date()}"
            )
        else:
            payter_db.update(
                data_date=previous_date.replace(tzinfo=pytz.UTC),
                source=PAYTER,
                data=(
                    payter_response_data_str
                    if payter_response.status_code == 200
                    else ""
                ),
                status=(
                    COMPLETE if payter_response.status_code == 200 else FAILED
                ),
                updated_date=timezone.localtime(timezone.now()),
                updated_by="Manual Entry",
                details=(
                    SUCCESSFULLY_FETCHED_DATA
                    if payter_response.status_code == 200
                    else payter_response.reason
                ),
            )
        if payter_response.status_code == 200:
            redis_connection.set(
                f"{PAYTER}-{previous_date.date()}",
                array_to_string_converter(payter_response_data),
            )
    except COMMON_ERRORS + (ConnectionError,) as error:
        print(f"Exception during retriving payter data -> {error}")


def get_driivz_sites_list_and_store_it_in_database_and_cache():
    """this function fetches DRIIVZ station list and stores it in the database and cache"""
    auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket()
    if auth_response is not None and auth_response.status_code != 200:
        return None
    response = traced_request(
        POST_REQUEST,
        config("DJANGO_APP_DRIIVZ_API_GATEWAY_BASE_URL") +
        "/api-gateway/v1/sites/filter?pageSize=100&pageNumber=0&sortBy=id%3Aasc",
        headers={
            "Content-Type": "application/json",
            "dmsTicket": dms_ticket
        },
        json={},
        timeout=REQUEST_API_TIMEOUT,
    )
    if response.status_code == 403:
        auth_response, dms_ticket = get_driivz_api_gateway_dms_ticket(
            generate_token=True
        )
        if auth_response is not None and auth_response.status_code != 200:
            return None
        response = traced_request(
            POST_REQUEST,
            config("DJANGO_APP_DRIIVZ_API_GATEWAY_BASE_URL") +
            "/api-gateway/v1/sites/filter?pageSize=100&pageNumber=0&sortBy=id%3Aasc",
            headers={
                "Content-Type": "application/json",
                "dmsTicket": dms_ticket
            },
            json={},
            timeout=REQUEST_API_TIMEOUT,
        )
    if response.status_code == 200:
        driivz_sites_data = json.loads(response.content)
        db_sites_data = Stations.objects.only(
            "id",
            "station_id",
            "driivz_display_name",
        )
        sites_dict_with_station_id_as_key = {}
        for site in db_sites_data:
            sites_dict_with_station_id_as_key[site.station_id] = {
                "id": site.id,
                "station_id": site.station_id,
                "driivz_display_name": site.driivz_display_name,
            }
        sites_dict_with_site_id_and_display_name_relation = {}
        legacy_id_not_found = []

        for driivz_site in driivz_sites_data["data"]:
            if driivz_site.get('legacyId') is not None:
                sites_dict_with_site_id_and_display_name_relation[
                    driivz_site["legacyId"]
                ] = driivz_site["displayName"]
                if (
                    driivz_site["legacyId"] in sites_dict_with_station_id_as_key
                    and sites_dict_with_station_id_as_key[driivz_site["legacyId"]][
                        "driivz_display_name"
                    ]
                    != driivz_site["displayName"]
                ):
                    Stations.objects.filter(
                        id=sites_dict_with_station_id_as_key[driivz_site["legacyId"]]["id"]
                    ).update(driivz_display_name=driivz_site["displayName"])
                else:
                    legacy_id_not_found.append(driivz_site['name'])
        if len(legacy_id_not_found)>0:
            print("Legacy id not found for stations : ",legacy_id_not_found)
        redis_connection.set(
            "sites_data_with_site_id_and_driivz_display_name_relation",
            json.dumps(sites_dict_with_site_id_and_display_name_relation),
        )
    else:
        print(response.json())


def get_driivz_station_name_for_station_id(station_id, site_title):
    """This function will return the driivz station name for station id"""
    sites_data_with_site_id_and_driivz_display_name_relation = redis_connection.get(
        "sites_data_with_site_id_and_driivz_display_name_relation"
    )
    if sites_data_with_site_id_and_driivz_display_name_relation:
        sites_data_with_site_id_and_driivz_display_name_relation = json.loads(
            sites_data_with_site_id_and_driivz_display_name_relation
        )
        if station_id in sites_data_with_site_id_and_driivz_display_name_relation:
            return sites_data_with_site_id_and_driivz_display_name_relation[station_id]
    db_site_details = Stations.objects.filter(station_id=station_id).first()
    if db_site_details and db_site_details.driivz_display_name:
        return db_site_details.driivz_display_name
    return site_title

def delete_valeting_data():
    """This function will delete valeting data from database and cache with configurable time (90 days default)"""
    valeting_data_retention_period = filter_function_for_base_configuration(
        "valeting_data_retention_period", 90
    )
    if valeting_data_retention_period is None:
        valeting_data_retention_period = 90
    else:
        valeting_data_retention_period = int(
            valeting_data_retention_period
        )
    min_date_for_data_retention = timezone.now() - timedelta(
        days=valeting_data_retention_period
    )
    min_date_for_data_retention = datetime.combine(
        min_date_for_data_retention.date(), datetime.min.time()
    )
    try:
        ValetingTransactionData.objects.filter(
                transaction_date__date__lte=min_date_for_data_retention.replace(tzinfo=pytz.UTC)
            ).delete()
    except COMMON_ERRORS as error:
        print(f"Exception during deleting valeting data -> {error}")

class StoreThirdpartyDataCRONJobAPI(APIView):
    """Cronjonb API"""

    @classmethod
    def post(cls, cron_job_request):
        """Post method to initialize cron job api"""
        try:
            secret_key_azure = cron_job_request.data.get("secret_key", None)
            if secret_key_azure is None:
                return SECRET_KEY_NOT_PROVIDED
            if not handler.verify(
                secret_key_azure, DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET
            ):
                return SECRET_KEY_IN_VALID
            start_storing_driivz_sites_data = threading.Thread(
                target=get_driivz_sites_list_and_store_it_in_database_and_cache,
                daemon=True
            )
            start_storing_driivz_sites_data.start()
            
            start_storing_thirdparty_data = threading.Thread(
                target=store_thirdparty_data,
                daemon=True
            )
            start_storing_thirdparty_data.start()

            start_delete_valeting_data = threading.Thread(
                target=delete_valeting_data,
            )
            start_delete_valeting_data.setDaemon(True)
            start_delete_valeting_data.start()
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Cron job initiated.",
                }
            )
        except COMMON_ERRORS:
            return API_ERROR_OBJECT


def process_sessions_for_advam_data_for_portal(
    swarco_sessions,
    advam_sessions,
    station_db_id,
    station_id,
):
    """Processing swarco and adwam data"""
    station = Stations.objects.filter(station_id=station_id).first()
    sessions = []
    for session in advam_sessions:
        if "Transaction Amount" in session:
            transaction_amount = session["Transaction Amount"]
            session_matching = check_driivz_or_swarco_amount(
                transaction_amount, swarco_sessions, True
            )
            if session_matching:
                for matched_driivz_or_swarco_session in session_matching:
                    matched_driivz_or_swarco_session["Start Date"] = (
                        date_formater_for_contactless_receipts(
                            matched_driivz_or_swarco_session["Start Date"],
                            True,
                        )
                    )
                    matched_driivz_or_swarco_session["End Date"] = (
                        date_formater_for_contactless_receipts(
                            matched_driivz_or_swarco_session["End Date"], True
                        )
                    )
                    sessions.append(
                        {
                            "swarco_data": {
                                **matched_driivz_or_swarco_session
                            },
                            "advam_data": {**session},
                            "station_name": get_driivz_station_name_for_station_id(
                                station.station_id, station.site_title
                            ),
                            "station_db_id": station_db_id,
                            "station_id": station_id,
                            "receipt_for": "Swarco Charging Session",
                        }
                    )

    return sessions


def process_sessions_for_payter_data_for_portal(
    driivz_data,
    payter_data,
    station_db_id,
    station_id,
):
    """Processing driivz and payter data"""
    station = Stations.objects.filter(station_id=station_id).first()
    sessions = []
    valeting_tax_rate = filter_function_for_base_configuration(
        VALETING_TAX_RATE, DEFAULT_VALETING_TAX_RATE
    )
    for session in payter_data:
        if "committedAmount" in session:
            commited_amount = session["committedAmount"] / 100
            if all(
                word in session["terminalDomain"]
                for word in VALETING_KEY_WORDS
            ):
                session["@timestamp"] = date_formater_for_contactless_receipts(
                    session["@timestamp"]
                )
                sessions.append(
                    {
                        "payter_data": {**session},
                        "station_db_id": station_db_id,
                        "station_id": station_id,
                        "station_name": get_driivz_station_name_for_station_id(
                            station.station_id, station.site_title
                        ),
                        "receipt_for": "Valeting",
                        "valeting_tax_rate": float(valeting_tax_rate),
                        "description_of_service": "Valeting",
                    }
                )
            else:
                session_matching = check_driivz_or_swarco_amount(
                    commited_amount, driivz_data
                )
                if session_matching:
                    for matched_driivz_session in session_matching:
                        matched_driivz_session["startOn"] = (
                            date_formater_for_contactless_receipts(
                                matched_driivz_session["startOn"]
                            )
                        )
                        matched_driivz_session["stopOn"] = (
                            date_formater_for_contactless_receipts(
                                matched_driivz_session["stopOn"]
                            )
                        )
                        matched_driivz_session["station"]["address"]["address1"] = (
                            get_driivz_station_name_for_station_id(station.station_id, station.site_title)
                            + ","
                        )
                        sessions.append(
                            {
                                "driivz_data": {**matched_driivz_session},
                                "payter_data": {**session},
                                "station_db_id": station_db_id,
                                "station_id": station_id,
                                "receipt_for": "Charging Session",
                            }
                        )
    return sessions


def set_source_data_in_cache(source, user_entered_date_time):
    """this function sets the source data from database to cache"""
    db_data = ThirdPartyServicesData.objects.filter(
        source=source, data_date__date=user_entered_date_time.date()
    ).first()
    if db_data:
        redis_connection.set(
            f"{source}-{user_entered_date_time.date()}", db_data.data
        )
    return db_data


def process_worldline_receipts(*args):
    """This function process sessions for worldline"""
    (
        station_db_id,
        station_id,
        sessions_date,
        card_last_4,
        paid_amount,
        user_entered_date_string,
        receipt_hero_site_name,
        driivz_data,
        charge_point_ids
    ) = args 
    # get request id from RH API
    site_details = Stations.objects.get(id=station_db_id)
    print("Worldline receipt fetching initiated")
    receipt_hero_request = traced_request(
        POST_REQUEST,
        config("DJANGO_APP_RECEIPT_HERO_ENDPOINT"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f'Token {config("DJANGO_APP_RECEIPT_HERO_ACCESS_TOKEN")}',
        },
        data=json.dumps(
            {
                "locationName": receipt_hero_site_name,
                "panLastFour": f"{card_last_4}",
                "date": user_entered_date_string,
                "amount": int(Decimal(str(paid_amount)) * 100),
            }
        ),
        timeout=REQUEST_API_TIMEOUT,
    )
    print(f"RH API response => {receipt_hero_request.content}")
    if receipt_hero_request.status_code == 200:
        print(
            "RH API Success"
            + "\n"
            + f"Station ID -> {station_id},"
            + "\n"
            + f"Card last four digits -> {card_last_4} ,"
            + "\n"
            + f"Session date and time -> {sessions_date}"
            + "\n"
            + f"Paid amount -> {paid_amount} ,"
            + "\n"
        )
        response_data = json.loads(receipt_hero_request.content)
        if response_data and "requestUUID" in response_data:
            print(
                "Fetched request UUID"
                + "\n"
                + f"Station ID -> {station_id},"
                + "\n"
                + f"Card last four digits -> {card_last_4} ,"
                + "\n"
                + f"Session date and time -> {sessions_date}"
                + "\n"
                + f"Paid amount -> {paid_amount} ,"
                + "\n"
            )
            request_uuid = response_data["requestUUID"]
            receipt_data_from_cache = redis_connection.get(
                f"RH-{request_uuid}"
            )
            # In cacahe check for RH receipt for this id
            if receipt_data_from_cache not in [None, b"", b"[]"]:
                print(
                    "Receipt present in cache"
                    + "\n"
                    + f"Station ID -> {station_id},"
                    + "\n"
                    + f"Card last four digits -> {card_last_4} ,"
                    + "\n"
                    + f"Session date and time -> {sessions_date}"
                    + "\n"
                    + f"Paid amount -> {paid_amount} ,"
                    + "\n"
                )
                return {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Fetched sessions list.",
                    "data": {
                        "sessions": json.loads(receipt_data_from_cache),
                    },
                }
            # In DB check for RH receipt for this id
            receipt_data_from_db = ReceiptHeroReceiptsData.objects.filter(
                request_id=request_uuid
            ).first()
            if (
                receipt_data_from_db
                and receipt_data_from_db.rh_data
                and receipt_data_from_db.driivz_data
            ):
                print(
                    "Receipt data present in Database"
                    + "\n"
                    + f"Station ID -> {station_id},"
                    + "\n"
                    + f"Card last four digits -> {card_last_4} ,"
                    + "\n"
                    + f"Session date and time -> {sessions_date}"
                    + "\n"
                    + f"Paid amount -> {paid_amount} ,"
                    + "\n"
                )
                sessions = []
                receipt_rh_data = json.loads(receipt_data_from_db.rh_data)[0]
                for matched_driivz_session in json.loads(receipt_data_from_db.driivz_data)[0]:
                    matched_driivz_session["startOn"] = (
                        date_formater_for_contactless_receipts(
                            matched_driivz_session["startOn"]
                        )
                    )
                    matched_driivz_session["stopOn"] = (
                        date_formater_for_contactless_receipts(
                            matched_driivz_session["stopOn"]
                        )
                    )
                    sessions.append(
                        {
                            "driivz_data": {**matched_driivz_session},
                            "RH_data": {**receipt_rh_data},
                            "station_db_id": station_db_id,
                            "station_id": station_id,
                            "receipt_for": "RH Charging Session",
                        }
                    )             
                redis_connection.set(
                    f"RH-{request_uuid}", json.dumps(sessions)
                )
                return {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Fetched sessions list.",
                    "data": {
                        "sessions": sessions,
                    },
                }
            elif receipt_data_from_db is None:
                if (
                    driivz_data is None
                    or driivz_data == b""
                    or driivz_data == b"[]"
                ):
                    session_date_time = datetime.strptime(
                        sessions_date, "%Y-%m-%d %H:%M"
                    ).replace(tzinfo=pytz.UTC)
                    date_from = datetime.strftime(
                        session_date_time - timedelta(hours=2), DATE_FORMAT_FOR_DRIIVZ
                    )
                    date_to = datetime.strftime(
                        session_date_time + timedelta(hours=2), DATE_FORMAT_FOR_DRIIVZ
                    )
                    driivz_response_data = driivz_api(date_from, date_to)

                    driivz_data = []
                    if driivz_response_data.status_code == 200:
                        driivz_data = json.loads(driivz_response_data.content)["transactions"]
                else:
                    driivz_data = json.loads(driivz_data)
                filtered_driivz_data = list(
                    filter(
                        lambda session: (
                            (
                                str(session["station"]["id"]) in charge_point_ids
                            )
                            and "total" in session["cost"]
                        ),
                        driivz_data
                    )
                )
                filtered_driivz_data = check_driivz_or_swarco_amount(
                    float(paid_amount), filtered_driivz_data
                )
                for drrivz_data in filtered_driivz_data:
                    drrivz_data["station"]["address"]["address1"] = (
                        get_driivz_station_name_for_station_id(
                            site_details.station_id,
                            site_details.site_title
                        )
                        + ","
                    )
                ReceiptHeroReceiptsData.objects.create(
                    request_id=request_uuid,
                    driivz_data=json.dumps(
                        [filtered_driivz_data, station_db_id, station_id]
                    ),
                    created_date=timezone.localtime(timezone.now())
                )
            return {
                "status_code": status.HTTP_200_OK,
                "status": True,
                "message": "Fetched sessions list.",
                "data": {
                    "request_uuid": request_uuid,
                },
            }
        print(
            "Request UUID not present in API response"
            + "\n"
            + f"Station ID -> {station_id},"
            + "\n"
            + f"Card last four digits -> {card_last_4} ,"
            + "\n"
            + f"Session date and time -> {sessions_date}"
            + "\n"
            + f"Paid amount -> {paid_amount} ,"
            + "\n"
        )
    print(
        "RH API Fail"
        + "\n"
        + f"Station ID -> {station_id},"
        + "\n"
        + f"Card last four digits -> {card_last_4} ,"
        + "\n"
        + f"Session date and time -> {sessions_date}"
        + "\n"
        + f"Paid amount -> {paid_amount} ,"
        + "\n"
    )
    return False


class GetUserSessionsListAPIForApp(APIView):
    """Api to get user sessions list"""

    # Permission classes are used to restrict the user
    permission_classes = [permissions.AllowAny]

    def post(self, get_user_sessions_request):
        """Fetching sessions list"""
        try:
            station_db_id = get_user_sessions_request.data.get("id", False)
            station_id = get_user_sessions_request.data.get(
                "station_id", False
            )
            charge_point_ids = get_user_sessions_request.data.get(
                "charge_point_ids", False
            )
            terminal_ids = get_user_sessions_request.data.get(
                "terminal_ids", False
            )
            sessions_date = get_user_sessions_request.data.get(
                "sessions_date", False
            )
            paid_amount = get_user_sessions_request.data.get(
                "paid_amount", False
            )
            card_last_4 = get_user_sessions_request.data.get(
                "card_last_4", False
            )
            receipt_hero_site_name = get_user_sessions_request.data.get(
                "receipt_hero_site_name", False
            )
            valeting_available_on_station = get_user_sessions_request.data.get(
                "valeting_available_on_station", False
            )
            print(
                "Receipt details in request :"
                + "\n"
                + f"Station ID -> {station_id},"
                + "\n"
                + f"Paid amount -> {paid_amount} ,"
                + "\n"
                + f"Session date and time -> {sessions_date}"
                + "\n"
                + f"Card last four digits -> {card_last_4} ,"
                + "\n"
            )
            min_date_for_data_retention = (
                filter_function_for_base_configuration(
                    MIN_DATE_FOR_DATA_RETRNTION_KEY, MIN_MONTHS_RANGE
                )
            )
            customer_care_email = filter_function_for_base_configuration(
                "mfg_contactless_customer_care_email", CUSTOMER_CARE_EMAIL
            )
            session_not_able_to_find_message = (
                filter_function_for_base_configuration(
                    "session_not_able_to_find_message",
                    SESSION_NOT_FOUND_ERROR_MESSAGE,
                )
            )
            session_not_able_to_find_response = Response(
                {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "status": False,
                    "message": "Failed to find receipts",
                    "session_not_able_to_find_message": session_not_able_to_find_message,
                    "customer_care_email": customer_care_email,
                }
            )
            # all the required dates
            todays_date = timezone.now().date()
            station_payment_terminal = (
                Stations.objects.filter(station_id=station_id)
                .first()
                .payment_terminal
            )
            previous_date = todays_date - timedelta(days=1)
            min_date = previous_date - relativedelta(
                months=int(min_date_for_data_retention)
            )
            # converting the date entered by user into required format
            user_entered_date = sessions_date.split(" ")[0]
            user_entered_date_time = datetime.strptime(
                user_entered_date, "%Y-%m-%d"
            )
            # variables to get thirdparty data from cache
            driivz_data = redis_connection.get(
                f"{DRIIVZ}-{user_entered_date_time.date()}"
            )
            payter_data = redis_connection.get(
                f"{PAYTER}-{user_entered_date_time.date()}"
            )
            rh_transactions = []
            rh_request_id = None
            driivz_source_data = None
            advam_in_payter_format = []
            if ADVAM_PAYMENT_TERMINAL in station_payment_terminal:
                fetch_receipt = FetchReceiptData()
                fetch_receipt.type = CUSTOM_SEARCH
                fetch_receipt.card_number = card_last_4
                fetch_receipt.date = user_entered_date_time
                fetch_receipt.amount = float(paid_amount)
                station = get_object_by("station_id", station_id, get_all_stations())
                fetch_receipt.charge_point_names = station.get('charge_point_names')
                fetch_receipt.tolerance_amount = float(filter_function_for_base_configuration("contactless_tolerance_amount", AMOUNT_TOLERANCE))
                fetch_receipt.tolerance_time = timedelta(minutes=int(filter_function_for_base_configuration("contactless_tolerance_time_in_minutes", TIME_TOLERANCE)))
                fetch_receipt.all_charge_points = get_charge_points()
                result_queue = Queue()
                fetch_receipt.advam(result_queue)
                advam_receipts = {}
                while not result_queue.empty():
                    advam_receipts.update(result_queue.get())
                if advam_receipts:
                    advam_in_payter_format = getAdvamInPayterFormat(advam_receipts, station_db_id, station_id)

            if (
                driivz_data is None
                or driivz_data == b""
                or driivz_data == b"[]"
            ):
                print(
                    "Driivz data not present in cache for below request ->"
                    + "\n"
                    + f"Station ID -> {station_id},"
                    + "\n"
                    + f"Card last four digits -> {card_last_4} ,"
                    + "\n"
                    + f"Paid amount -> {paid_amount} ,"
                    + "\n"
                    + f"Session date and time -> {sessions_date}"
                    + "\n"
                )
                driivz_source_data = set_source_data_in_cache(
                    DRIIVZ,
                    user_entered_date_time,
                )
                driivz_data = (
                    driivz_source_data.data
                    if (
                        driivz_source_data
                        and driivz_source_data.data
                        and json.loads(driivz_source_data.data)
                    )
                    else None
                )
            if WORLDLINE_PAYMENT_TERMINAL in station_payment_terminal:
                rh_transactions_response = process_worldline_receipts(
                    station_db_id,
                    station_id,
                    sessions_date,
                    card_last_4,
                    paid_amount,
                    user_entered_date,
                    receipt_hero_site_name,
                    driivz_data,
                    charge_point_ids,
                )
                if rh_transactions_response is False:
                    return session_not_able_to_find_response
                if (
                    valeting_available_on_station
                    and "data" in rh_transactions_response
                ):
                    if "sessions" in rh_transactions_response["data"]:
                        rh_transactions = rh_transactions_response["data"][
                            "sessions"
                        ]
                    if "request_uuid" in rh_transactions_response["data"]:
                        rh_request_id = rh_transactions_response["data"][
                            "request_uuid"
                        ]
                else:
                    return Response(
                        {
                            **rh_transactions_response,
                            "session_not_able_to_find_message": session_not_able_to_find_message,
                            "customer_care_email": customer_care_email,
                        }
                    )

            print("Payter receipt fetching initiated")
            if (
                todays_date == user_entered_date_time.date()
                or user_entered_date_time.date() < min_date
            ):
                print("Date is less than retension period")
                sessions = get_session_data_directly_from_thirdparty_source_for_portal(
                    station_db_id,
                    station_id,
                    card_last_4,
                    charge_point_ids,
                    terminal_ids,
                    sessions_date,
                    paid_amount,
                )
                if sessions or advam_in_payter_format:
                    return Response(
                        {
                            "status_code": status.HTTP_200_OK,
                            "status": True,
                            "message": "Fetched sessions list.",
                            "session_not_able_to_find_message": session_not_able_to_find_message,
                            "customer_care_email": customer_care_email,
                            "data": {
                                "sessions": rh_transactions + sessions + advam_in_payter_format,
                                "request_uuid": rh_request_id,
                            },
                        }
                    )
                print(
                    "Failed to fetch below session details directly from third party API"
                    + "\n"
                    + f"Station ID -> {station_id},"
                    + "\n"
                    + f"Card last four digits -> {card_last_4} ,"
                    + "\n"
                    + f"Session date and time -> {sessions_date}"
                    + "\n"
                    + f"Paid amount -> {paid_amount} ,"
                    + "\n"
                )
                return session_not_able_to_find_response
            # checking wether the date is present in cache and the data is not empty
            if not driivz_data:
                print(
                    "Driivz data not present in database for below request ->"
                    + "\n"
                    + f"Station ID -> {station_id},"
                    + "\n"
                    + f"Card last four digits -> {card_last_4} ,"
                    + "\n"
                    + f"Paid amount -> {paid_amount} ,"
                    + "\n"
                    + f"Session date and time -> {sessions_date}"
                    + "\n"
                )
                sessions = get_session_data_directly_from_thirdparty_source_for_portal(
                    station_db_id,
                    station_id,
                    card_last_4,
                    charge_point_ids,
                    terminal_ids,
                    sessions_date,
                    paid_amount,
                )
                if sessions or advam_in_payter_format:
                    return Response(
                        {
                            "status_code": status.HTTP_200_OK,
                            "status": True,
                            "message": "Fetched sessions list.",
                            "session_not_able_to_find_message": session_not_able_to_find_message,
                            "customer_care_email": customer_care_email,
                            "data": {
                                "sessions": rh_transactions + sessions + advam_in_payter_format,
                                "request_uuid": rh_request_id,
                            },
                        }
                    )
                print(
                    "Failed to fetch below session details directly from third party API"
                    + "\n"
                    + f"Station ID -> {station_id},"
                    + "\n"
                    + f"Card last four digits -> {card_last_4} ,"
                    + "\n"
                    + f"Paid amount -> {paid_amount} ,"
                    + "\n"
                    + f"Session date and time -> {sessions_date}"
                    + "\n"
                )
                return session_not_able_to_find_response
            if (
                payter_data is None
                or payter_data == b""
                or payter_data == b"[]"
            ):
                print(
                    "Payter data not present in cache for below request ->"
                    + "\n"
                    + f"Station ID -> {station_id},"
                    + "\n"
                    + f"Card last four digits -> {card_last_4} ,"
                    + "\n"
                    + f"Paid amount -> {paid_amount} ,"
                    + "\n"
                    + f"Session date and time -> {sessions_date}"
                    + "\n"
                )
                source_data = set_source_data_in_cache(
                    PAYTER,
                    user_entered_date_time,
                )
                if (
                    not source_data
                    or not source_data.data
                    or not json.loads(source_data.data)
                ):
                    print(
                        "Payter data not present in database for below request ->"
                        + "\n"
                        + f"Station ID -> {station_id},"
                        + "\n"
                        + f"Card last four digits -> {card_last_4} ,"
                        + "\n"
                        + f"Paid amount -> {paid_amount} ,"
                        + "\n"
                        + f"Session date and time -> {sessions_date}"
                        + "\n"
                    )
                    sessions = get_session_data_directly_from_thirdparty_source_for_portal(
                        station_db_id,
                        station_id,
                        card_last_4,
                        charge_point_ids,
                        terminal_ids,
                        sessions_date,
                        paid_amount,
                    )
                    if sessions or advam_in_payter_format:
                        return Response(
                            {
                                "status_code": status.HTTP_200_OK,
                                "status": True,
                                "message": "Fetched sessions list.",
                                "session_not_able_to_find_message": session_not_able_to_find_message,
                                "customer_care_email": customer_care_email,
                                "data": {
                                    "sessions": rh_transactions + sessions + advam_in_payter_format,
                                    "request_uuid": rh_request_id,
                                },
                            }
                        )
                    print(
                        "Failed to fetch below session details directly from third party API"
                        + "\n"
                        + f"Station ID -> {station_id},"
                        + "\n"
                        + f"Card last four digits -> {card_last_4} ,"
                        + "\n"
                        + f"Paid amount -> {paid_amount} ,"
                        + "\n"
                        + f"Session date and time -> {sessions_date}"
                        + "\n"
                    )
                    return session_not_able_to_find_response
                payter_data = source_data.data
            sessions = []
            paid_amount_in_pennies = int(Decimal(str(paid_amount)) * 100)
            sessions = process_sessions_for_payter_data_for_portal(
                list(
                    filter(
                        lambda session: (
                            str(session["station"]["id"]) in charge_point_ids
                        )
                        and "total" in session["cost"],
                        json.loads(driivz_data),
                    )
                ),
                list(
                    filter(
                        lambda transaction: (
                            "committedAmount" in transaction
                            and "serialNumber" in transaction
                            and "extra-TXN-MASKED-PAN" in transaction
                            and transaction["extra-TXN-MASKED-PAN"][-4:]
                            == card_last_4
                            and transaction["committedAmount"]
                            == paid_amount_in_pennies
                            and transaction["serialNumber"] in terminal_ids
                        ),
                        json.loads(payter_data),
                    )
                ),
                station_db_id,
                station_id,
            )

            if not sessions:
                print(
                    "Failed to fetch below session details from Cached data"
                    + "\n"
                    + f"Station ID -> {station_id},"
                    + "\n"
                    + f"Card last four digits -> {card_last_4} ,"
                    + "\n"
                    + f"Paid amount -> {paid_amount} ,"
                    + "\n"
                    + f"Session date and time -> {sessions_date}"
                    + "\n"
                )
                return session_not_able_to_find_response
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Fetched sessions list.",
                    "session_not_able_to_find_message": session_not_able_to_find_message,
                    "customer_care_email": customer_care_email,
                    "data": {
                        "sessions": rh_transactions + sessions + advam_in_payter_format,
                        "request_uuid": rh_request_id,
                    },
                }
            )
        except COMMON_ERRORS as error:
            print(
                "Get receipts list API for portal failed due to exception -> "
            )
            print(error)
            start_caching_station_finder_data = threading.Thread(
                target=send_exception_email_function,
                args=[
                    get_user_sessions_request.build_absolute_uri(),
                    str(error),
                ],
                daemon=True
            )
            start_caching_station_finder_data.start()
            return API_ERROR_OBJECT


class GetUserSessionsListAPIForPortal(APIView):
    """API to get user sessions list with swarco and advam"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Fetching sessions list"""
        try:
            data = self.extract_data(request)
            self.log_receipt_details(data, False)
            configuration = self.fetch_configuration()
            response = self.prepare_not_found_response(configuration)
            recaptcha_creds_data = {
                "secret": config("DJANGO_APP_CONTACTLESS_RECAPTCHA_TOKEN"),
                "response": data["recaptcha_token"],
            }
            recaptcha_request = traced_request(
                POST_REQUEST,
                config("DJANGO_APP_CONTACTLESS_RECAPTCHA_URL"),
                data=recaptcha_creds_data,
            )
            result = recaptcha_request.json()
            if not result.get("success"):
                return Response(
                    {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "status": False,
                        "message": "Fetched sessions list.",
                        "session_not_able_to_find_message": configuration[
                            "session_not_found_msg"
                        ],
                        "customer_care_email": configuration[
                            "customer_care_email"
                        ],
                    }
                )
            session_data = self.fetch_sessions(data)
            if session_data:
                return self.success_response(session_data, configuration)
            self.log_receipt_details(data, True)
            return response

        except COMMON_ERRORS as error:
            self.handle_exception(request, error)
            return API_ERROR_OBJECT

    def extract_data(self, request):
        """Extracts and returns data from the request."""
        fields = [
            "id",
            "station_id",
            "charge_point_ids",
            "charge_point_names",
            "terminal_ids",
            "sessions_date",
            "paid_amount",
            "card_last_4",
            "receipt_hero_site_name",
            "valenting_available_on_station",
            "recaptcha_token",
        ]
        return {field: request.data.get(field, False) for field in fields}

    def log_receipt_details(self, data, failed_to_find_session):
        """Logs receipt details from the request."""
        (
            print(f"Failed to fetch session details for: {data}")
            if failed_to_find_session
            else print(f"Receipt details in request: {data}")
        )

    def fetch_configuration(self):
        """Fetches and returns configuration settings."""
        return {
            "min_date": filter_function_for_base_configuration(
                MIN_DATE_FOR_DATA_RETRNTION_KEY, MIN_MONTHS_RANGE
            ),
            "customer_care_email": filter_function_for_base_configuration(
                "mfg_contactless_customer_care_email", CUSTOMER_CARE_EMAIL
            ),
            "session_not_found_msg": filter_function_for_base_configuration(
                "session_not_able_to_find_message",
                SESSION_NOT_FOUND_ERROR_MESSAGE,
            ),
        }

    def prepare_not_found_response(self, configuration):
        """Prepares and returns a 'not found' response."""
        return Response(
            {
                "status_code": status.HTTP_404_NOT_FOUND,
                "status": False,
                "message": "Failed to find receipts",
                "session_not_able_to_find_message": configuration[
                    "session_not_found_msg"
                ],
                "customer_care_email": configuration["customer_care_email"],
            }
        )

    def station_payment_terminal_selector(
        self, station_id, user_entered_date_time
    ):
        station_payment_terminal = (
            Stations.objects.filter(station_id=station_id)
            .first()
            .payment_terminal
        )
        station_payment_terminal = string_to_array_converter(
            station_payment_terminal
        )
        todays_date = timezone.now().date()
        if station_payment_terminal:
            if (
                user_entered_date_time.date() == todays_date
                and ADVAM_PAYMENT_TERMINAL in station_payment_terminal
            ):
                station_payment_terminal.remove(ADVAM_PAYMENT_TERMINAL)
        return station_payment_terminal

    def fetch_sessions(self, data):
        """Fetches session data based on the provided data and configuration."""
        session_data_set = {"sessions": [], "rh_request_id": ""}
        station_db_id = data["id"]
        user_entered_date_time = datetime.strptime(
            data["sessions_date"].split(" ")[0], "%Y-%m-%d"
        )
        station_payment_terminal = self.station_payment_terminal_selector(
            data["station_id"], user_entered_date_time
        )
        if station_payment_terminal:
            driivz_data = redis_connection.get(
                    f"{DRIIVZ}-{user_entered_date_time.date()}"
                )
            driivz_data = self.process_data(
                    driivz_data, DRIIVZ, user_entered_date_time
                )
            if WORLDLINE_PAYMENT_TERMINAL in station_payment_terminal:
                rh_transactions_response = process_worldline_receipts(
                    station_db_id,
                    data["station_id"],
                    data["sessions_date"],
                    data["card_last_4"],
                    data["paid_amount"],
                    data["sessions_date"].split(" ")[0],
                    data["receipt_hero_site_name"],
                    driivz_data,
                    data["charge_point_ids"]
                )
                if (
                    rh_transactions_response
                    and "data" in rh_transactions_response
                    # and data["valenting_available_on_station"]
                ):
                    if "sessions" in rh_transactions_response["data"]:
                        session_data_set[
                            "sessions"
                        ] += rh_transactions_response["data"]["sessions"]
                    if "request_uuid" in rh_transactions_response["data"]:
                        session_data_set["rh_request_id"] = (
                            rh_transactions_response["data"]["request_uuid"]
                        )

            if (
                PAYTER_PAYMENT_TERMINAL in station_payment_terminal
                or data["valenting_available_on_station"]
            ):
                driivz_data = redis_connection.get(
                    f"{DRIIVZ}-{user_entered_date_time.date()}"
                )
                payter_data = redis_connection.get(
                    f"{PAYTER}-{user_entered_date_time.date()}"
                )
                payter_sessions = []
                payter_data = self.process_data(
                    payter_data, PAYTER, user_entered_date_time
                )
                driivz_data = self.process_data(
                    driivz_data, DRIIVZ, user_entered_date_time
                )
                paid_amount_in_pennies = int(
                    Decimal(data["paid_amount"]) * 100
                )
                if driivz_data and payter_data:
                    payter_sessions = (
                        process_sessions_for_payter_data_for_portal(
                            list(
                                filter(
                                    lambda session: (
                                        str(session["station"]["id"])
                                        in data["charge_point_ids"]
                                    )
                                    and "total" in session["cost"],
                                    json.loads(driivz_data),
                                )
                            ),
                            list(
                                filter(
                                    lambda transaction: (
                                        "committedAmount" in transaction
                                        and "serialNumber" in transaction
                                        and "extra-TXN-MASKED-PAN"
                                        in transaction
                                        and transaction[
                                            "extra-TXN-MASKED-PAN"
                                        ][-4:]
                                        == data["card_last_4"]
                                        and transaction["committedAmount"]
                                        == paid_amount_in_pennies
                                        and transaction["serialNumber"]
                                        in data["terminal_ids"]
                                    ),
                                    json.loads(payter_data),
                                )
                            ),
                            station_db_id,
                            data["station_id"],
                        )
                    )
                else:
                    payter_sessions = get_session_data_directly_from_thirdparty_source_for_portal(
                        station_db_id,
                        data["station_id"],
                        data["card_last_4"],
                        data["charge_point_ids"],
                        data["terminal_ids"],
                        data["sessions_date"],
                        data["paid_amount"],
                    )
                if payter_sessions:
                    session_data_set["sessions"] += payter_sessions
                else:
                    print("********** No sessions found for payter **********")

            if ADVAM_PAYMENT_TERMINAL in station_payment_terminal:
                swarco_data = redis_connection.get(
                    f"{SWARCO}-{user_entered_date_time.date()}"
                )
                advam_data = redis_connection.get(
                    f"{ADVAM}-{user_entered_date_time.date()}"
                )
                swarco_data = self.process_data(
                    swarco_data, SWARCO, user_entered_date_time
                )
                advam_data = self.process_data(
                    advam_data, ADVAM, user_entered_date_time
                )
                advam_sessions = []
                if swarco_data and advam_data:
                    advam_sessions = (
                        process_sessions_for_advam_data_for_portal(
                            list(
                                filter(
                                    lambda session: (
                                        session["Charger"].split(",")[0]
                                        in data["charge_point_names"]
                                    )
                                    and "Cost" in session
                                    and "total" in session["Cost"],
                                    json.loads(swarco_data),
                                )
                            ),
                            list(
                                filter(
                                    lambda transaction: (
                                        "Transaction Amount" in transaction
                                        and "CPID" in transaction
                                        and "Card" in transaction
                                        and isinstance(
                                            transaction["Card"], str
                                        )
                                        and transaction["Card"][-4:]
                                        == (data["card_last_4"])
                                        and Decimal(
                                            str(
                                                transaction[
                                                    "Transaction Amount"
                                                ]
                                            )
                                        )
                                        == Decimal(data["paid_amount"])
                                        and transaction["CPID"]
                                        in data["charge_point_names"]
                                    ),
                                    json.loads(advam_data),
                                )
                            ),
                            station_db_id,
                            data["station_id"],
                        )
                    )
                if advam_sessions:
                    session_data_set["sessions"] += advam_sessions
                else:
                    print("********** No sessions found for advam **********")
            return session_data_set

    def process_data(self, source_data, source_key, user_entered_date_time):
        """save data to cache if present in db"""
        if source_data is None or source_data == b"" or source_data == b"[]":
            source_data = set_source_data_in_cache(
                source_key, user_entered_date_time
            )
            if (
                not source_data
                or not source_data.data
                or not json.loads(source_data.data)
            ):
                return None
            return source_data.data
        return source_data

    def success_response(self, session_data, configuration):
        """Prepares and returns a success response with session data."""
        return Response(
            {
                "status_code": status.HTTP_200_OK,
                "status": True,
                "message": "Fetched sessions list.",
                "session_not_able_to_find_message": configuration[
                    "session_not_found_msg"
                ],
                "customer_care_email": configuration["customer_care_email"],
                "data": session_data,
            }
        )

    def log_failed_fetch(self, data):
        """Logs failed fetch details."""
        print(f"Failed to fetch session details for: {data}")

    def handle_exception(self, request, error):
        """Handles exceptions and logs them."""
        print(f"API failed due to exception: {error}")
        send_exception_email_function(request.build_absolute_uri(), str(error))


def return_missing_field_error(
    set_of_fields_present_in_sheets, set_of_required_fields_sheet
):
    missing_fields = list(
        set_of_required_fields_sheet - set_of_fields_present_in_sheets
    )
    return JsonResponse(
        status=406,
        data={
            "error": f'These required field are missing : {", ".join(missing_fields)}'
        },
    )


def swarco_or_advam_data_db_operations(data_date, data, source, updated_by):
    """This function stores swarco and advam data in database"""
    previous_entry = ThirdPartyServicesData.objects.filter(
        data_date=datetime.strptime(data_date, "%Y-%m-%d").replace(
            tzinfo=pytz.UTC
        ),
        source=source.lower(),
    )
    if previous_entry:
        helper_list = []
        unique_key = "ID" if source == SWARCO else "Custom Unique Key"
        for entry in previous_entry:
            entry.data = array_to_string_converter(
                list(
                    {
                        record[unique_key]: record
                        for record in (
                            string_to_array_converter(entry.data) + data
                        )
                    }.values()
                )
            )
            entry.updated_date = timezone.localtime(timezone.now())
            entry.updated_by = updated_by
            helper_list.append(entry)
        redis_connection.set(
            f"{source}-{data_date}",
            array_to_string_converter(
                list(
                    {
                        record[unique_key]: record
                        for record in (
                            string_to_array_converter(
                                previous_entry.first().data
                            )
                            + data
                        )
                    }.values()
                )
            ),
        )
        return [helper_list, "Update"]
    redis_connection.set(
        f"{source}-{data_date}",
        array_to_string_converter(data),
    )
    return [
        [
            ThirdPartyServicesData(
                data_date=datetime.strptime(data_date, "%Y-%m-%d").replace(
                    tzinfo=pytz.UTC
                ),
                source=source.lower(),
                data=array_to_string_converter(data),
                status=COMPLETE,
                created_date=timezone.localtime(timezone.now()),
                updated_date=timezone.localtime(timezone.now()),
                updated_by=updated_by,
                details=(SUCCESSFULLY_FETCHED_DATA),
            )
        ],
        "Create",
    ]


def try_float(v):
    try:
        return float(v)
    except Exception:
        return 0

def map_sheet_row_to_driivz_obj(sheet_row, tax_rate=20, session_tarrif=None):
    """
    Map a sheet row (dict) to the desired Driivz object structure.
    Handles value conversion, cost parsing, and missing fields.
    Calculates totalTax and total as in the swarco flow if session_tarrif is provided.
    Converts time fields from HH:MM:SS to seconds.
    """
    def parse_cost(cost_val):
        if isinstance(cost_val, str):
            try:
                return float(cost_val.replace('£', '').replace(',', '').strip())
            except Exception:
                return None
        if isinstance(cost_val, (int, float)):
            return float(cost_val)
        return None

    def parse_bool(val):
        if isinstance(val, str):
            return val.strip().lower() in ("yes", "true", "1")
        return bool(val) if val is not None else None

    def parse_hms_to_seconds(hms):
        if not hms or not isinstance(hms, str):
            return None
        try:
            parts = hms.strip().split(":")
            if len(parts) == 3:
                h, m, s = map(int, parts)
                return h * 3600 + m * 60 + s
            elif len(parts) == 2:
                m, s = map(int, parts)
                return m * 60 + s
            elif len(parts) == 1:
                return int(parts[0])
        except Exception:
            return None
        return None

    total_kwh = sheet_row.get("Total kWh")
    cost_val = sheet_row.get("Cost")
    if session_tarrif is not None and total_kwh is not None:
        try:
            total_cost = custom_round_function(
                Decimal(str(total_kwh)) * Decimal(str(session_tarrif)), 2, True)
            total_cost_without_tax = custom_round_function(
                Decimal(str(total_cost)) / (1 + (Decimal(tax_rate) / 100)), 2, True)
            total_tax = custom_round_function(
                Decimal(str(total_cost)) - Decimal(str(total_cost_without_tax)), 2, True)
        except Exception:
            total_cost = parse_cost(cost_val)
            total_cost_without_tax = None
            total_tax = None
    else:
        total_cost = parse_cost(cost_val)
        if total_cost is not None:
            try:
                total_cost_without_tax = custom_round_function(
                    Decimal(str(total_cost)) / (1 + (Decimal(tax_rate) / 100)), 2, True)
                total_tax = custom_round_function(
                    Decimal(str(total_cost)) - Decimal(str(total_cost_without_tax)), 2, True)
            except Exception:
                total_cost_without_tax = None
                total_tax = None
        else:
            total_cost_without_tax = None
            total_tax = None
    cost_dict = {
        "currency": "GBP",
        "totalTax": float(total_tax) if total_tax is not None else None,
        "totalTaxRate": float(tax_rate),
        "total": float(total_cost) if total_cost is not None else None,
    }

    accepted_val = sheet_row.get("Accepted")
    accepted_bool = parse_bool(accepted_val)
    plan_code = sheet_row.get("Billing Plan")

    extra_data = sheet_row.get("Extra Data")
    error_code = None
    if extra_data and "Stop Reason:" in extra_data:
        try:
            error_code = extra_data.split("Stop Reason:")[1].split(";")[0].strip()
        except Exception:
            error_code = None
    
    charger_host = {
        "id": None,
        "name": None,
    }

    charger_id_val = None
    charger_col = sheet_row.get("Charger")
    if charger_col:
        charger_id_val = charger_col.split(",")[0].strip()

    if not hasattr(map_sheet_row_to_driivz_obj, "_charge_points_cache"):
        map_sheet_row_to_driivz_obj._charge_points_cache = get_charge_points()
    charge_points = map_sheet_row_to_driivz_obj._charge_points_cache
    matched_cp = next((cp for cp in charge_points if cp["charger_point_name"] == charger_id_val), None)
    charger_id_final = matched_cp["charger_point_id"] if matched_cp else None
    # print(f"[DEBUG] Charger ID Check for {charger_id_val} :", charger_id_final)
    return {
        "id": sheet_row.get("ID"),
        "connectorStatus": None,  # Not in sheet
        "connectorType": None,    # Not in sheet
        "transactionStatus": None,  # Not in sheet
        "transactionBillingStatus": None,  # Not in sheet
        "stopReason": error_code,  # Extracted from Extra Data
        "accountNumber": None,  # Not in sheet
        "planId": None,  # Not in sheet
        "chargePower": None,  # Not in sheet
        "connectorId": None,  # Not in sheet
        "meterReadOnStart": sheet_row.get("Start kWh"),
        "meterReadOnStop": sheet_row.get("End kWh"),
        "smart": sheet_row.get("Smart?"),
        "startedOn": sheet_row.get("Start Date"),
        "stoppedOn": sheet_row.get("End Date"),
        "chargeTime": parse_hms_to_seconds(sheet_row.get("Total Time")),
        "plugTimeInSeconds": None,  # Not in sheet
        "chargeEnergySupplyTimeInSeconds": None,  # Not in sheet
        "chargerId": charger_id_final,
        "vehicleSoc": None,  # Not in sheet
        "planCode": plan_code,
        "cardId": None,  # Not in sheet
        "cardNumber": sheet_row.get("Start Card"),
        "cardType": None,  # Not in sheet
        "totalChargingTime": parse_hms_to_seconds(sheet_row.get("Total Charging Time")),
        "totalEnergy": sheet_row.get("Total kWh"),
        "tariffId": None,  # Not in sheet
        "evseId": sheet_row.get("Evse Id"),
        "accepted": accepted_bool,
        "errorInfo": {"errorCode": error_code},
        "cost": cost_dict,
        "chargerHost": charger_host,
        "startSource": sheet_row.get("Start Source"),
        "stopSource": sheet_row.get("Stop Source"),
    }

def process_driivz_json_data(json_data, source, request, **kwargs):
    """
    Map each record to the Driivz object structure, group by key, and upsert to cache and DB.
    Handles missing keys and NaN values as in the swarco flow.
    Passes tax rate and session tariff to the mapping function for consistent tax calculation.
    """
    print("[DRIIVZ] process_driivz_json_data: Mapping, grouping, and upserting Driivz data...")
    tax_rate = float(kwargs.get("driivz_tax_rate", 20))
    session_tarrif = kwargs.get("driivz_session_tarrif")
    mapped_records = []
    skipped_records = 0
    for date, records in json_data.items():
        print(f"[DRIIVZ] Date: {date} - Number of records: {len(records)}")
        for rec in records:
            driivz_obj = map_sheet_row_to_driivz_obj(rec, tax_rate=tax_rate, session_tarrif=session_tarrif)
            # Clean NaN/None
            for k in list(driivz_obj.keys()):
                v = driivz_obj[k]
                if isinstance(v, dict):
                    for subk in list(v.keys()):
                        subv = v[subk]
                        if subv is None or (isinstance(subv, float) and pd.isna(subv)):
                            v[subk] = None
                if v is None or (isinstance(v, float) and pd.isna(v)):
                    driivz_obj[k] = None
            if 'id' in driivz_obj:
                for time_key in ['startedOn', 'stoppedOn']:
                    val = driivz_obj.get(time_key)
                    if isinstance(val, str):
                        try:
                            dt = parser.parse(val)
                            driivz_obj[time_key] = dt.timestamp()
                        except Exception as e:
                            print(f"[DRIIVZ] Failed to parse {time_key}: {val} ({e})")
                            driivz_obj[time_key] = None
            if not (driivz_obj.get('id') or driivz_obj.get('transactionId')):
                print(f"[DRIIVZ][SKIP] Record missing id/transactionId: {driivz_obj}")
                skipped_records += 1
            mapped_records.append(driivz_obj)
    print(f"[DRIIVZ] Total mapped records: {len(mapped_records)} (Skipped: {skipped_records})")
    if mapped_records:
        print(f"[DRIIVZ] Sample mapped record: {mapped_records[0]}")
    else:
        print("[DRIIVZ] No mapped records!")
    # Group by Driivz key
    grouped = group_driivz(mapped_records)
    print(f"[DRIIVZ] Number of groups formed: {len(grouped)}")
    if grouped:
        for i, (k, v) in enumerate(grouped.items()):
            print(f"[DRIIVZ] Group key: {k} -> {len(v)} records")
            if i < 3:
                print(f"[DRIIVZ] Sample record in group: {v[0] if v else 'EMPTY'}")
            if i >= 2:
                break
    else:
        print("[DRIIVZ] No groups formed! Check if mapping or grouping logic is correct.")
    print(f"[DRIIVZ] Calling bulk_upsert_driivz_cache with keys: {list(grouped.keys())}")
    upserted_cache_count = bulk_upsert_driivz_cache(grouped)
    print(f"[DRIIVZ] bulk_upsert_driivz_cache returned: {upserted_cache_count}")
    print(f"[DRIIVZ] Calling bulk_upsert_driivz_database with keys: {list(grouped.keys())}")
    new_data_count_db, updated_data_count_db = bulk_upsert_driivz_database(grouped)
    print(f"[DRIIVZ] bulk_upsert_driivz_database returned: new={new_data_count_db}, updated={updated_data_count_db}")
    print(f"[DRIIVZ] Upserted {upserted_cache_count} cache records, {new_data_count_db} new DB, {updated_data_count_db} updated DB.")
    return JsonResponse(status=200, data={
        "message": "Driivz data uploaded and upserted successfully.",
        "cache_upserted": upserted_cache_count,
        "db_new": new_data_count_db,
        "db_updated": updated_data_count_db
    })
    