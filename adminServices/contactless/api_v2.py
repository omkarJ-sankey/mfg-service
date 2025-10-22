"""New Contactless Portal APIs"""

#  File details-
#   Author      - Aditya Dhadke
#   Description - This file contains APIs for 'New Contactless Portal'.
#   Name        - New Contactless Portal APIs
#   Date        - 04-10-2024

import base64
from collections import defaultdict
import json
from queue import Queue
import threading
import time
from datetime import datetime, timedelta
import concurrent.futures
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
import pytz
from dateutil import parser
import requests 
import urllib.parse

# pylint: disable-msg=W0622
from passlib.hash import django_pbkdf2_sha256 as handler
from decouple import config

from django.db.models import Q
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Prefetch

from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response

# pylint:disable=import-error

# pylint: disable-msg=C0412
from sharedServices.model_files.valeting_models import ValetingMachine
from sharedServices.constants import (
    NO,
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    REQUEST_API_TIMEOUT,
    SECRET_KEY_IN_VALID,
    SECRET_KEY_NOT_PROVIDED,
    DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET,
    POST_REQUEST,
    FAILED,
    COMEPLETED,
    AMPECO_SESSIONS_ENDPOINT,
)
from sharedServices.model_files.station_models import (
    ChargePoint,
    Stations,
)
from sharedServices.model_files.contactless_models import (
    ContactlessReceiptEmailTracking,
    ReceiptHeroReceiptsData,
    ThirdPartyServicesData,
    DriivzData,
    ValetingTransactionData,
    AmpecoData,
)
from sharedServices.common import (
    hasher,
    redis_connection,
    filter_function_for_base_configuration,
)
from sharedServices.email_common_functions import (
    email_sender,
    send_exception_email_function,
)
from sharedServices.contactless_common_functions import (
    DJANGO_APP_PAYTER_BASE_URL,
    advam_api,
    generate_payter_tokens,
    get_payter_transactions_from_data_api,
)
from sharedServices.sentry_tracers import traced_request
from .helper_functions import (
    driivz_api_v2
)

from .app_level_constants import (
    ADVAM,
    ADVAM_API_DATE_FORMAT,
    ADVAM_PAYMENT_TERMINAL,
    AMOUNT_TOLERANCE,
    BRAND_MORRISONS,
    COMPLETE,
    CUSTOM_SEARCH,
    CUSTOMER_CARE_EMAIL,
    CUSTOMER_CARE_PHONE,
    DRIIVZ,
    DRIIVZ_V1,
    DRIIVZ_V2,
    EV,
    GET_RECEIPTS_TIMEOUT_VALUE,
    HEADOFFICE_ADDRESS,
    MORRISONS,
    PAYTER_PAYMENT_TERMINAL,
    PDI_MORRISONS,
    PAYTER,
    PAYTER_PLAN,
    PLAN_CODE,
    DATE_FORMAT_FOR_DRIIVZ_V2,
    SUCCESSFULLY_FETCHED_DATA,
    SWARCO,
    SWARCO_HISTORY_DATA_DATE,
    TIME_TOLERANCE,
    VALETING,
    WORLDLINE_PAYMENT_TERMINAL,
    WORLDLINE_PLAN,
    CONTACTLESS_RECEIPTS_TAX_RATE,
    VALETING_VAT_RATE,
    AMPECO,
    ADVAM_PLAN,
)

from sharedServices.model_files.ocpi_locations_models import (OCPILocation, OCPIConnector, OCPIEVSE)

class StationListAutoCompleteAPI_V5(APIView):
    """station search with auto compelete API"""

    # Permission classes are used to restrict the user
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """get stations with provided key"""
        try:
            data = get_all_stations()
            result = []
            for value in data:
                result.append({"label": f"{value['station_name']}, {value['post_code']}, {value['station_id']}", "value": {value['station_id']}})
            return Response(result, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {
                    "message": "Something went wrong",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class EmailReceipt(APIView):
    """Email Contactless Receipt"""

    # Permission classes are used to restrict the user
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Email Contactless Receipt API"""
        try:
            email = request.data.get("email", None)
            pdf_file = request.data.get("pdf_file", None)
            transaction_id = request.data.get("transaction_id", None)
            data_source = request.data.get("data_source", None)
            date = request.data.get("date", None)

            email_sent_records = ContactlessReceiptEmailTracking.objects.filter(
                email=hasher(email),
                session_id=transaction_id,
                created_date__date=timezone.now().date(),
                source=data_source,
            ).count()

            maximum_emails_can_send = filter_function_for_base_configuration(
                "contactless_max_emails_sending_count", 5
            )

            if email_sent_records >= int(maximum_emails_can_send):
                return Response(
                    {
                        "message": "Exceeded the daily limit for email receipts.",
                    },
                    status=status.HTTP_406_NOT_ACCEPTABLE,
                )

            email_subject = f"MFG Contactless Payment Receipt {date} - {transaction_id}"

            email_sent = email_sender(
                config("DJANGO_APP_SEND_USER_RECEIPT_TEMPLATE_ID"),
                email,
                {"subject": email_subject},
                attachment_data=base64.b64decode(pdf_file),
                attachment_name=f"mfg-contactless-receipt_{date}",
            )

            if email_sent:
                ContactlessReceiptEmailTracking.objects.create(
                    email=hasher(email),
                    session_id=transaction_id,
                    created_date=timezone.now(),
                    updated_date=timezone.now(),
                    source=data_source,
                )
            return Response(
                {
                    "message": "Receipt sent successfully.",
                }
            )
        except COMMON_ERRORS as error:
            print(f"Send Session Data Email API failed due to exception -> ")
            print(error)
            start_caching_station_finder_data = threading.Thread(
                target=send_exception_email_function,
                args=[
                    request.build_absolute_uri(),
                    str(error),
                ],
            )
            start_caching_station_finder_data.setDaemon(True)
            start_caching_station_finder_data.start()
            return Response(
                {
                    "message": "Something went wrong",
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class GetUserSessionsListAPIForPortalV5(APIView):
    """Contactless receipt API for web app"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Fetching sessions list"""
        try:
            # Recaptcha
            recaptcha_response = recaptcha(request)
            if not recaptcha_response.get("success"):
                return Response(status=status.HTTP_400_BAD_REQUEST,data={"message": "Recaptcha failed"})
            # Fetch Data
            fetch_receipt = FetchReceiptData()
            data = fetch_receipt.receipt_api(request)
            customer_care_email = filter_function_for_base_configuration("mfg_contactless_customer_care_email", CUSTOMER_CARE_EMAIL)
            headoffice_address = filter_function_for_base_configuration("mfg_contactless_headoffice_address", HEADOFFICE_ADDRESS)
            customer_care_phone = filter_function_for_base_configuration("mfg_customer_care", CUSTOMER_CARE_PHONE)
            if data:
                return Response(
                    status=status.HTTP_200_OK,
                    data={
                        "customer_care_email": customer_care_email,
                        "customer_care_phone": customer_care_phone,
                        "headoffice_address": headoffice_address,
                        "data": data,
                        "get_receipts_timeout_value": int(
                            filter_function_for_base_configuration(
                                "get_receipts_timeout_value",
                                GET_RECEIPTS_TIMEOUT_VALUE,
                            )
                        ),
                    },
                )
            return Response(status=status.HTTP_404_NOT_FOUND, data={"message": "Failed to find receipts","customer_care_email": customer_care_email})
        except COMMON_ERRORS:
            traceback.print_exc()
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR,data={"message": "Something went wrong"})
        

class GetUserSessionsListAPIForAppV5(APIView):
    """Contactless receipt API for mobile app"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Fetching sessions list"""
        try:
            # Fetch Data
            fetch_receipt = FetchReceiptData()
            data = fetch_receipt.receipt_api_for_app(request)
            customer_care_email = filter_function_for_base_configuration("mfg_contactless_customer_care_email", CUSTOMER_CARE_EMAIL)
            headoffice_address = filter_function_for_base_configuration("mfg_contactless_headoffice_address", HEADOFFICE_ADDRESS)
            customer_care_phone = filter_function_for_base_configuration("mfg_customer_care", CUSTOMER_CARE_PHONE)
            if data:
                return Response(
                    status=status.HTTP_200_OK,
                    data={
                        "customer_care_email": customer_care_email,
                        "customer_care_phone": customer_care_phone,
                        "headoffice_address": headoffice_address,
                        "data": data,
                        "tax_rate": int(
                            filter_function_for_base_configuration(
                                "contactless_receipts_tax_rate",
                                CONTACTLESS_RECEIPTS_TAX_RATE,
                            )
                        ),
                        "get_receipts_timeout_value": int(
                            filter_function_for_base_configuration(
                                "get_receipts_timeout_value",
                                GET_RECEIPTS_TIMEOUT_VALUE,
                            )
                        ),
                    },
                )
            return Response(status=status.HTTP_404_NOT_FOUND, data={"message": "Failed to find receipts","customer_care_email": customer_care_email})
        except COMMON_ERRORS:
            traceback.print_exc()
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR,data={"message": "Something went wrong"})


class RH_Driivz(APIView):
    """API to get user sessions list with swarco and advam"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Fetching sessions list"""
        try:
            # Secret
            secret_key_azure = request.data.get("secret_key", None)
            if secret_key_azure is None:
                return SECRET_KEY_NOT_PROVIDED
            if not handler.verify(secret_key_azure, DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET):
                return Response(status=status.HTTP_406_NOT_ACCEPTABLE, data={"message": "Secret key is not valid."})
            
            #Fetch Data
            fetch_receipt = FetchReceiptData()
            data = fetch_receipt.rh_ocpi_ampeco_driivz_api(request)
            if data:
                return Response(status=status.HTTP_200_OK, data=data)
            return Response(status=status.HTTP_304_NOT_MODIFIED, data={"message": "No changes"})
        except COMMON_ERRORS:
            traceback.print_exc()
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR,data={"message": "Something went wrong"})


class FetchReceiptData():

    def __init__(self):
        self.type = None
        self.card_number = None
        self.date = None
        self.amount = None
        self.location = None
        self.station_brand = None
        self.rh_sitename = None
        self.payment_terminal = None
        self.payter_terminal_ids = None
        self.worldline_terminal_ids = None
        self.charge_point_names = None
        self.recaptcha_token = None
        self.station_name = None
        self.all_stations = None
        self.all_charge_points = None
        self.tolerance_amount = None
        self.tolerance_time = None
        self.rh_data = None
        self.valeting_machines = None
        
    def receipt_api(self, request):
        """Fetches session data based on the provided data and configuration."""
        self.set_receipt_instance_data(request)
        self.log_receipt_details()
        result_queue = Queue()
        if self.type == MORRISONS:
            self.morrisons(result_queue)
        elif self.type == EV:
            start = time.time()
            with ThreadPoolExecutor(max_workers=3) as executor:
                futs = [
                    executor.submit(self.worldline, result_queue),
                    executor.submit(self.payter, result_queue),
                    executor.submit(self.advam, result_queue)
                ]
                print([fut.result() for fut in concurrent.futures.as_completed(futs)])
            end = time.time()
            print(f"Time taken for ev is {round(end-start,1)} seconds")
        elif self.type == VALETING:
            self.valeting(result_queue)
        elif self.type == CUSTOM_SEARCH:
            start = time.time()
            futs = []

            if self.station_brand == BRAND_MORRISONS:
                futs.append(self.morrisons)

            if PAYTER_PAYMENT_TERMINAL in self.payment_terminal:
                futs.append(self.payter)

            if WORLDLINE_PAYMENT_TERMINAL in self.payment_terminal:
                futs.append(self.worldline)

            if ADVAM_PAYMENT_TERMINAL in self.payment_terminal:
                futs.append(self.advam)
                
            futs.append(self.valeting)
            if futs:
                with ThreadPoolExecutor(max_workers=len(futs)) as executor:
                    future_to_task = {executor.submit(task, result_queue): task for task in futs}
                    print([fut.result() for fut in as_completed(future_to_task)])
            else:
                print("Payment terminals are empty or invalid for site:", self.location)

            end = time.time()
            print(f"Time taken {round(end-start,1)} seconds")
        else:
            print("Invalid type")

        all_sessions = {}
        while not result_queue.empty():
            all_sessions.update(result_queue.get())
        return all_sessions

    def receipt_api_for_app(self, request):
        """Fetches session data based on the provided data and configuration."""
        self.set_receipt_instance_data_for_app(request)
        self.log_receipt_details()
        result_queue = Queue()
        start = time.time()
        with ThreadPoolExecutor(max_workers=3) as executor:
            futs = [
                executor.submit(self.worldline, result_queue),
                executor.submit(self.payter, result_queue),
                executor.submit(self.advam, result_queue)
            ]
            print([fut.result() for fut in concurrent.futures.as_completed(futs)])
        end = time.time()
        print(f"Time taken {round(end-start,1)} seconds")
        all_sessions = {}
        while not result_queue.empty():
            all_sessions.update(result_queue.get())
        return all_sessions
    

    def valeting(self, result_queue):
        """Handle valeting transactions"""
        try:
            # Get valeting data from database
            valeting_data = ValetingTransactionData.objects.filter(
                transaction_date__date=self.date.date(),
                card_number__endswith=self.card_number
            )
            matching_data = []
            for transaction in valeting_data:
                data = json.loads(transaction.data)
                products = data.get("body", {}).get("Data", {}).get("Products", [])
                if not products:
                    continue
                    
                valeting_machine_id = data.get("body", {}).get("Data", {}).get("Machine ID")
                valeting_machine = get_object_by(
                    "machine_id", valeting_machine_id, self.valeting_machines
                )
                
                if not valeting_machine:
                    continue
                    
                product_payed_value = float(data.get("body", {}).get("Data", {}).get("Payed Value", 0))
                vat_rate = float(filter_function_for_base_configuration("valeting_vat_rate", VALETING_VAT_RATE))
                vat_amount = (product_payed_value * vat_rate) / 100
                
                if self.type == CUSTOM_SEARCH:
                    requested_site_id = str(self.location)
                    if requested_site_id != valeting_machine['station_id']:
                        print(f"Skipping valeting data for site: {valeting_machine['station_id']} as it doesn't match requested site: {requested_site_id}")
                        continue
                    
                    if self.amount is not None:
                        if round(abs(product_payed_value - self.amount), 2) > self.tolerance_amount:
                            print(f"Skipping valeting data for amount: {product_payed_value} as it's outside tolerance for requested amount: {self.amount}")
                            continue
                
                matching_data.append({
                    "Station": valeting_machine['station_name'],
                    "Type of service": data.get("body", {}).get("Data", {}).get("Machine Name", ""),
                    "Card": data.get("body", {}).get("Data", {}).get("Card String", ""),
                    "Brand": data.get("body", {}).get("Data", {}).get("Brand", ""),
                    "Type": "CONTACTLESS EMV",
                    "Transaction ID": data.get("body", {}).get("Data", {}).get("Transaction ID", ""),
                    "Transaction time": data.get("body", {}).get("Data", {}).get("Authorization Time", ""),
                    "Total cost (excl. VAT)": product_payed_value - vat_amount,
                    "VAT @ 20%": vat_amount,
                    "Total cost (incl. VAT)": product_payed_value,
                    "Station Address": valeting_machine['station_address']
                })

            if matching_data:
                print(f"matching_data: {matching_data}")
                result_queue.put({"Valeting": matching_data})
                return f"{len(matching_data)} - Valeting receipts"
            return "Valeting data not found"
        except Exception as e:
            traceback.print_exc()
            print(f"Error processing valeting data: {str(e)}")
            return "Error processing valeting data"

    def rh_ocpi_ampeco_driivz_api(self, request):
        self.set_rh_driivz_instance_data(request)
        isUpserted = self.insert_rh_data()
        if isUpserted:
            # Get rh driivz matching data
            # Try OCPI/Ampeco first
            matching_data = self.get_matching_rh_combined_data([self.rh_data])
            if not matching_data:
                print("RH - Driivz Matching data not found")
                return None
            return {"EV_Worldline":matching_data}
        return False

    def insert_rh_data(self):
        isInserted = False
        request_uuid = self.rh_data["requestUUID"]
        transaction_id = self.rh_data["wolTransactionId"]
        rh, created = ReceiptHeroReceiptsData.objects.get_or_create(
            transaction_id=transaction_id,
            defaults={
                "request_id": request_uuid,
                "rh_data": json.dumps(self.rh_data),
                "created_date": timezone.now(),
                "updated_by": "Webhook",
            }
        )
        if created:
            isInserted = True
        return isInserted

    def set_receipt_instance_data(self, request):
        self.type = request.data.get('type')
        self.card_number = request.data.get('card_number')
        self.date = datetime.strptime(request.data.get('date'), '%Y-%m-%d')
        self.all_stations = get_all_stations()
        self.all_charge_points = get_charge_points()
        self.tolerance_amount = float(filter_function_for_base_configuration("contactless_tolerance_amount", AMOUNT_TOLERANCE))
        self.tolerance_time = timedelta(minutes=int(filter_function_for_base_configuration("contactless_tolerance_time_in_minutes", TIME_TOLERANCE)))
        if self.type == VALETING:
            self.valeting_machines = get_all_valeting_machines()
        if self.type == CUSTOM_SEARCH:
            self.amount = float(request.data.get('amount')) if request.data.get('amount') else None
            self.location = request.data.get('location')
            start_time = time.time()
            station = get_object_by("station_id", self.location, self.all_stations)
            if station:
                self.station_name = station.get('station_name')
                self.station_brand = station.get('station_brand')
                self.payment_terminal = station.get('payment_terminal')
                self.charge_point_names = station.get('charge_point_names')
                self.payter_terminal_ids = station.get('payter_terminal_ids')
                self.worldline_terminal_ids = station.get('worldline_terminal_ids')
                self.rh_sitename = station.get('rh_sitename')
                self.valeting_machines = get_all_valeting_machines()
            end_time = time.time()
            print(f"Fetched station data in {round(end_time-start_time,1)} seconds")
    
    def set_receipt_instance_data_for_app(self, request):
        self.type = 'EV'
        self.card_number = request.data.get('card_number')
        self.date = datetime.strptime(request.data.get('date'), '%Y-%m-%d')
        self.all_stations = get_all_stations()
        self.all_charge_points = get_charge_points()
        self.tolerance_amount = float(filter_function_for_base_configuration("contactless_tolerance_amount", AMOUNT_TOLERANCE))
        self.tolerance_time = timedelta(minutes=int(filter_function_for_base_configuration("contactless_tolerance_time_in_minutes", TIME_TOLERANCE)))

    def set_rh_driivz_instance_data(self, request):
        self.rh_data = request.data.get('rh')
        self.date = datetime.strptime(self.rh_data["transactionDateTime"], "%Y-%m-%dT%H:%M:%S").replace(hour=0, minute=0, second=0, microsecond=0)
        self.card_number = self.rh_data["maskedPan"][-4:]
        self.all_charge_points = get_charge_points()
        self.all_stations = get_all_stations()
        self.tolerance_amount = float(filter_function_for_base_configuration("contactless_tolerance_amount", AMOUNT_TOLERANCE))
        self.tolerance_time = timedelta(minutes=int(filter_function_for_base_configuration("contactless_tolerance_time_in_minutes", TIME_TOLERANCE)))

    def morrisons(self, result_queue):
        morrisons_redis_key = f"{PDI_MORRISONS}-{self.date.date()}"
        # morrisons_whole_day = redis_connection.get(morrisons_redis_key)
        # morrisons_data = self.process_sessions_for_morrisons(morrisons_whole_day,is_cache=True)

        # if not morrisons_data:
        morrisons_whole_day = process_data(None, PDI_MORRISONS, self.date)
        morrisons_data = self.process_sessions_for_morrisons(morrisons_whole_day,is_cache=False)

        if morrisons_data:
            result_queue.put({"Morrisons":morrisons_data})
            return f"{len(morrisons_data)} - Morrisons receipts"
        return "Morrisons data not found"

    def process_sessions_for_morrisons(self, morrisons_whole_day, is_cache):
        if is_cache:
            print("\nIn cache :")
        else:
            print("\nIn Database :")
        if not morrisons_whole_day:
            print(f"Morrison data is not available for the date {self.date.date()}")
            return None
        morrisons_whole_day = json.loads(morrisons_whole_day)
        morrisons_list = list(
            filter(
                lambda transaction: (
                    transaction["CardNumber"][-4:] == self.card_number
                    and transaction["ProductUnit"] == "L"
                    and (
                        self.type != CUSTOM_SEARCH
                        or 
                        (
                            (
                                transaction["IsBunkering"] == 1
                                or 
                                (
                                    self.amount is None
                                    or 
                                    round(abs(transaction["ProductValue"] - self.amount),2) <= self.tolerance_amount
                                )
                            )
                            and 
                            (
                                self.location is None
                                or transaction["StationID"] == self.location
                            )
                        )
                    )
                ),
                morrisons_whole_day,
            )
        )
        for transaction in morrisons_list:
            station = get_object_by("station_id", transaction["StationID"], self.all_stations)
            transaction["StationName"] = station.get('station_name')
            transaction["StationAddress"] = station.get('full_address')

        if morrisons_list:
            required_keys = {'StationName', 'CardNumber', 'Acquirer', 'TransactionType', 'MerchantNumber', 'ProductDescription', 'ProductCount', 'ProductUnit', 'TransactionDate', 'TransactionTime', 'ProductValue', 'IsBunkering', 'StationAddress'}
            sessions = filter_keys(morrisons_list, required_keys)
            return sessions
        return None

    def worldline(self, session_data_set):
        request_uuid = self.rh_api(self.card_number, self.date)
        if not request_uuid:
            return "Request UUID not found in RH API"
        rh_data = self.get_rh_data(request_uuid)
        if not rh_data:
            rh_data = {"socket":{"key":f"RH-{request_uuid}"}}
            session_data_set.put({"EV_Worldline":rh_data})
            return "Worldline data not found in db, returning request_uuid only"

        # Log data
        keys = ["requestUUID", "merchantName", "amount", "maskedPan", "transactionDateTime", "terminalId"]
        self.log_data_by(rh_data, keys, "RH data")
        # Try Ampeco first, then Driivz for each item
        matching_data = self.get_matching_rh_combined_data(rh_data)
        if not matching_data:
            return "Matching data not found"
        session_data_set.put({"EV_Worldline":matching_data})
        return f"{len(rh_data)} - RH receipts, {len(matching_data)} - Matching Receipts with driivz/ampeco"

    def payter(self, session_data_set):
        payter_data = self.get_payter_data()
        if not payter_data:
            return "Payter data not found"
        keys = ["serialNumber", "committedAmount", "extra-TXN-MASKED-PAN", "@timestamp"]
        self.log_data_by(payter_data, keys, "Payter data")
        # Try Ampeco first, then Driivz for each item
        matching_data = self.get_matching_payter_combined_data(payter_data)
        if not matching_data:
            return "Payter and driivz/ampeco matching data not found"
        session_data_set.put({"EV_Payter":matching_data})
        return f"{len(payter_data)} - Payter receipts, {len(matching_data)} - Matching Receipts with driivz/ampeco"

    def advam(self, session_data_set):
        advam_data = self.get_advam_data()
        if not advam_data:
            return "Advam data not found"
        if self.date <= SWARCO_HISTORY_DATA_DATE:
            swarco_data = self.get_swarco_data()
            if not swarco_data:
                return "Swarco data not found"
            matching_data = self.get_matching_advam_swarco_data(advam_data, swarco_data)
        else:
            # Try Ampeco first, then Driivz for each item
            matching_data = self.get_matching_advam_combined_data(advam_data)
        if not matching_data:
            return "Advam Matching data not found"
        session_data_set.put({"EV_Advam":matching_data})
        return f"{len(advam_data)} - Advam receipts, {len(matching_data)} - Matching Receipts with swarco/driivz/ampeco"

    def get_rh_data(self, request_uuid):
        list = ReceiptHeroReceiptsData.objects.filter(request_id=request_uuid)
        if list:
            all_data = []
            for data in list:
                all_data.append(json.loads(data.rh_data))
            if all_data:
                return self.filter_rh(all_data)
        print(f"RH data is not available in db for request_id : {request_uuid}")
        return None

    def filter_rh(self, rh_data):
        if self.type != CUSTOM_SEARCH:
            return rh_data
        rh_data = list(
            filter(
                lambda transaction: (
                    (self.amount is None or (round(abs(transaction["amount"] - self.amount),2) <= self.tolerance_amount))
                    and transaction["terminalId"] in self.worldline_terminal_ids
                ),
                rh_data
            )
        )
        return rh_data

    def get_matching_rh_driivz_data(self, rh_data):
        matching_data = []
        for r in rh_data:
            charge_point = get_object_by("worldline_terminal_id", r["terminalId"], self.all_charge_points)
            if not charge_point or not charge_point["charger_point_id"]:
                print(f"[Driivz] RH: Charge point for terminal {r['terminalId']} not found")
                continue
            driivz = self.get_driivz_data_by(self.date,WORLDLINE_PLAN,charge_point_id=charge_point["charger_point_id"])
            if not driivz:
                continue
            transaction_amount = float(r["amount"])
            transaction_datetime = datetime.strptime(r["transactionDateTime"], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=pytz.UTC)
            matched_driivz, driivz_response_version = self.filter_driivz(driivz, transaction_amount, transaction_datetime)
            if not matched_driivz:
                print(f"RH - matching driivz data is not available for card: {self.card_number} and amount: {transaction_amount}")
                continue
            charge_point = self.get_charge_point_by(matched_driivz, driivz_response_version)
            if not charge_point:
                print("RH - Charge point data is not available")
                return None
            r = filter_keys(r, {'requestUUID', 'maskedPan','cardBrand','transactionDateTime','amount'})
            if driivz_response_version == "v1":
                matched_driivz = filter_keys(matched_driivz, {'transactionId', 'totalEnergy', 'startOn', 'stopOn', 'chargeTime', 'cost'})
            else:
                matched_driivz = filter_keys(matched_driivz, {'id', 'totalEnergy', 'startedOn', 'stoppedOn', 'chargeTime', 'cost', 'cost'})
            matching_data.append({
                "rh": {**r},
                "driivz": {"version": driivz_response_version, "data": matched_driivz},
                "station_name": charge_point["station_name"],
                "station_address": charge_point["station_address"],
                "charge_point_name": charge_point["charger_point_name"],
                "latitude": charge_point["latitude"],
                "longitude": charge_point["longitude"],
                "vat_percentage": matched_driivz["cost"]["tax_rate"],
                "tax_amount": matched_driivz["cost"]["totalTax"],
                "amount_without_tax": round(abs(matched_driivz["cost"]["total"] - matched_driivz["cost"]["totalTax"]), 2),
            })
        return matching_data

    def get_charge_point_by(self, driivz, version):
        if version == DRIIVZ_V1:
            charge_point_name = driivz["station"]["caption"]
            charge_point = get_object_by("charger_point_name", charge_point_name, self.all_charge_points)
        else:
            charge_id = driivz["chargerId"]
            charge_point = get_object_by("charger_point_id", str(charge_id), self.all_charge_points)
        return charge_point

    def filter_driivz(self, driivz, transaction_amount, transaction_datetime):
        matched_driivz = list(
                filter(
                    lambda transaction: (
                        round(abs(transaction["cost"]["total"] - transaction_amount), 2) <= self.tolerance_amount
                        and (
                            self.tolerance_time == timedelta(minutes=0)
                            or (
                                ("id" in transaction or abs(transaction_datetime - datetime.strptime(transaction["stopOn"], "%Y-%m-%dT%H:%M:%S.%f%z").replace(tzinfo=pytz.UTC)))
                                and
                                ("id" not in transaction or abs(transaction_datetime - datetime.fromtimestamp(transaction["stoppedOn"]).replace(tzinfo=pytz.UTC)) <= self.tolerance_time)
                            )
                        )
                    ),
                    driivz
                )
            )
        if not matched_driivz:
            return None, None
        matched_driivz = (
            min(matched_driivz, key=lambda x: abs(float(x.get("cost", {}).get("total") or 0) - float(transaction_amount)))
            if len(matched_driivz) > 1
            else (matched_driivz[0] if matched_driivz else None)
        )
        if "tax_rate" not in matched_driivz["cost"]:
            matched_driivz["cost"]["tax_rate"] = float(filter_function_for_base_configuration("contactless_receipts_tax_rate", CONTACTLESS_RECEIPTS_TAX_RATE))
        driivz_response_version = DRIIVZ_V2 if "id" in matched_driivz else DRIIVZ_V1
        return matched_driivz, driivz_response_version

    def rh_api(self, card_number, date):
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
                    "panLastFour": f"{card_number}",
                    "date": datetime.strftime(date, "%Y-%m-%d")
                }
            ),
            timeout=REQUEST_API_TIMEOUT,
        )
        print(f"RH API response => {receipt_hero_request.content}")
        if receipt_hero_request.status_code == 200:
            response_data = json.loads(receipt_hero_request.content)
            if response_data and "requestUUID" in response_data:
                request_uuid = response_data["requestUUID"]
                return request_uuid
        return None

    def get_payter_data(self):
        payter_data = redis_connection.get(f"{PAYTER}-{self.date.date()}")
        if not payter_data:
            print(f"Payter data is not available in cache")
            payter_data = process_data(payter_data, PAYTER, self.date)
        if not payter_data:
            print(f"Payter data is not available in database")
            start = time.time()
            payter_data = self.get_payter_from_api_by(self.date, self.card_number)
            end = time.time()
            print(f"Payter api time taken {round(end-start,1)} sec")
        if not payter_data:
            print(f"Payter data is not available in API")
        if payter_data:
            payter_data = self.filter_payter(payter_data)
            return payter_data
        return payter_data

    def get_payter_from_api_by(self, date, card_number):
        utc_date = date.replace(tzinfo=pytz.UTC)
        start_date = int((timezone.localtime(utc_date)).timestamp()) * 1000
        end_date = (
            int((timezone.localtime(utc_date) + timedelta(hours=24)).timestamp()) * 1000
        )
        payload = json.dumps(
            {
                "index": "Transactions",
                "maxResults": 100,
                "query": f"extra-TXN-MASKED-PAN:*{card_number}",
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
            response = get_payter_transactions_from_data_api(payload, generate_new_token=True)

        if response.status_code == 200:
            payter_data = json.loads(response.content)["documents"]
        else:
            print("API Failed", f"status code : {response.status_code}")
            payter_data = None
        return payter_data

    def filter_payter(self, payter_data):
        if isinstance(payter_data, (str, bytes, bytearray)):
            payter_data = json.loads(payter_data)
        payter_data = list(
            filter(
                lambda transaction: (
                    "committedAmount" in transaction
                    and "serialNumber" in transaction
                    and "extra-TXN-MASKED-PAN" in transaction
                    and "@timestamp" in transaction
                    and "state" == "COMMITTED"
                    and transaction["extra-TXN-MASKED-PAN"][-4:] == self.card_number
                    and (
                        self.type != CUSTOM_SEARCH
                        or (
                            (self.amount is None or transaction["committedAmount"] == self.amount * 100)
                            and transaction["serialNumber"] in self.payter_terminal_ids
                        )
                    )
                ),
                payter_data,
            )
        )
        for transaction in payter_data:
            if transaction.get("paymentType") == "EMV":
                transaction["paymentType"] = "CONTACTLESS - EMV"
        return payter_data

    def log_data_by(self, list_data, keys, name):
        print(name)
        for p in list_data:
            print("\t-------------------------------")
            for key, value in p.items():
                if key in keys:
                    print(f"\t{key}: {value}")
            print("\t-------------------------------")

    def get_payter_transactions_from_data_api(body, generate_new_token=False):
        """this API returns payter transactions"""

        url = f"{DJANGO_APP_PAYTER_BASE_URL}/Data"

        payter_token = generate_payter_tokens(generate_new_token)
        if payter_token is None:
            print("Failed to generate new payter tokens")
            return payter_token
        headers = {
            "Content-Type": "application/json",
            "Authorization": f'CURO-TOKEN token="{payter_token}"',
        }

        return traced_request(POST_REQUEST, url, headers=headers, data=body, timeout=REQUEST_API_TIMEOUT)

    def get_matching_payter_driivz_data(self, payter_data):
        matching_data = []
        for p in payter_data:
            charge_point = get_object_by("payter_terminal_id", p["serialNumber"], self.all_charge_points)
            if not charge_point or not charge_point["charger_point_id"]:
                print(f"Payter: Charge point for {p['serialNumber']} not found")
                continue
            driivz = self.get_driivz_data_by(self.date,PAYTER_PLAN,charge_point_id=charge_point["charger_point_id"])
            if not driivz:
                continue
            transaction_amount = float(p["committedAmount"]/100)
            transaction_datetime = datetime.strptime(p["@timestamp"], "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.UTC)
            matched_driivz, driivz_response_version = self.filter_driivz(driivz, transaction_amount, transaction_datetime)
            if not matched_driivz:
                print(f"Payter - matching driivz data is not available for card: {self.card_number} and amount: {transaction_amount}")
                continue
            p = filter_keys(p, {'id' ,'maskedPAN', 'brandName', 'txnTimestamp', 'committedAmount', 'paymentType'})
            if driivz_response_version == "v1":
                matched_driivz = filter_keys(matched_driivz, {'transactionId', 'totalEnergy', 'startOn', 'stopOn', 'chargeTime', 'cost'})
            else:
                matched_driivz = filter_keys(matched_driivz, {'id', 'totalEnergy', 'startedOn', 'stoppedOn', 'chargeTime', 'cost'})
            matching_data.append({
                "payter": {**p},
                "driivz": {"version": driivz_response_version, "data": matched_driivz},
                "station_name": charge_point["station_name"],
                "station_address": charge_point["station_address"],
                "charge_point_name": charge_point["charger_point_name"],
                "latitude": charge_point["latitude"],
                "longitude": charge_point["longitude"],
                "vat_percentage": matched_driivz["cost"]["tax_rate"],
                "tax_amount": matched_driivz["cost"]["totalTax"],
                "amount_without_tax": round(abs(matched_driivz["cost"]["total"] - matched_driivz["cost"]["totalTax"]),2),
            })
        return matching_data

    def get_advam_data(self):
        advam_data = redis_connection.get(f"{ADVAM}-{self.date.date()}")
        if not advam_data:
            print(f"Advam data is not available in cache")
            advam_data = process_data(advam_data, ADVAM, self.date)
        if advam_data:
            advam_data = json.loads(advam_data)
        else:
            print(f"Advam data is not available in database")
            start = time.time()
            advam_data = self.get_advam_from_api_by(self.date)
            end = time.time()
            print(f"Advam api time taken {round(end-start,1)} sec")
        if not advam_data:
            print(f"Advam data is not available in API")
        if advam_data:
            advam_data = self.filter_advam(advam_data)
            return advam_data
        return advam_data
    
    def get_advam_from_api_by(self, date):
        from_time = datetime.combine(date.date(), datetime.min.time()).strftime(ADVAM_API_DATE_FORMAT)
        to_time = datetime.combine(date.date(), datetime.max.time()).strftime(ADVAM_API_DATE_FORMAT)
        advam_data = advam_api(from_time, to_time)
        return advam_data

    def filter_advam(self, advam_data_list):
        filtered_data = []
        for advam_data in advam_data_list:
            if "guid" in advam_data:  # New format
                if (
                    advam_data.get("amountCents") is not None
                    and advam_data.get("equipmentId")
                    and advam_data.get("maskedPAN")
                    and isinstance(advam_data["maskedPAN"], str)
                    and advam_data["maskedPAN"][-4:] == self.card_number
                    and (
                        self.type != CUSTOM_SEARCH
                        or (
                            (self.amount is None or advam_data["amountCents"] == int(self.amount * 100))
                            and advam_data["equipmentId"] in self.charge_point_names
                        )
                    )
                ):
                    filtered_data.append({
                        "Transaction Amount": advam_data["amountCents"] / 100,
                        "CPID": advam_data["equipmentId"],
                        "Card": advam_data["maskedPAN"],
                        "Type": advam_data["cardType"],
                        "Authorised": datetime.strptime(advam_data["effectiveDate"], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")
                    })
            else:  # Old format
                if (
                    advam_data.get("Transaction Amount") is not None
                    and advam_data.get("CPID")
                    and advam_data.get("Card")
                    and isinstance(advam_data["Card"], str)
                    and advam_data["Card"][-4:] == self.card_number
                    and (
                        self.type != CUSTOM_SEARCH
                        or (
                            (self.amount is None or advam_data["Transaction Amount"] == self.amount)
                            and advam_data["CPID"] in self.charge_point_names
                        )
                    )
                ):
                    filtered_data.append(advam_data)
        
        keys = ["Transaction Amount", "CPID", "Card", "Authorised"]
        self.log_data_by(filtered_data, keys, "Advam data")
        return filtered_data

    def get_swarco_data(self):
        swarco_data = redis_connection.get(f"{SWARCO}-{self.date.date()}")
        if not swarco_data:
            print(f"Swarco data is not available in cache")
            swarco_data = process_data(swarco_data, SWARCO, self.date)
        if not swarco_data:
            print(f"Swarco data is not available in database")
            return None

        swarco_data = self.filter_swarco(swarco_data)
        return swarco_data

    def filter_swarco(self, swarco_data):
        swarco_data = list(
            filter(
                lambda session: (
                    "Cost" in session
                    and "total" in session["Cost"]
                    and (
                        self.type != CUSTOM_SEARCH
                        or (session["Charger"].split(",")[0] in self.charge_point_names)
                    )
                ),
                json.loads(swarco_data)
            )
        )
        return swarco_data

    def get_matching_advam_swarco_data(self, advam_data, swarco_data):
        matching_data = []
        for a in advam_data:
            matched_swarco = list(
                filter(
                    lambda transaction: (
                        transaction["Charger"].split(",")[0] == a["CPID"] 
                        and round(abs(transaction["Cost"]["total"] - a["Transaction Amount"]), 2) <= self.tolerance_amount
                        and (
                            self.tolerance_time == timedelta(minutes=0)
                            or (
                                abs(datetime.strptime(a["Authorised"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.UTC) - datetime.strptime(transaction["Start Date"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.UTC))
                                <= self.tolerance_time
                            )
                        )
                    ),
                    swarco_data
                )
            )
            if not matched_swarco:
                continue
            charge_point = get_object_by("charger_point_name", a["CPID"], self.all_charge_points)
            a = filter_keys(a, {'Custom Unique Key', 'Card','Type','Authorised','Transaction Amount'})
            matched_swarco = filter_keys(matched_swarco, {'Charger', 'ID', 'Total kWh', 'Start Date', 'End Date', 'Total Time', 'Cost'})
            matching_data.append(
                {
                    "advam": {**a},
                    "swarco": {**matched_swarco[0]},
                    "station_name": charge_point["station_name"],
                    "station_address": charge_point["station_address"],
                    "charge_point_name": charge_point["charger_point_name"],
                    "latitude": charge_point["latitude"],
                    "longitude": charge_point["longitude"],
                    # "tax_amount": matched_swarco["cost"]["totalTax"],
                    # "amount_without_tax": matched_swarco["cost"]["total"] - matched_swarco["cost"]["totalTax"],

                }
            )
        return matching_data

    def get_matching_advam_driivz_data(self, advam_data):
        matching_data = []
        for a in advam_data:
            charge_point = get_object_by("charger_point_name",a["CPID"],self.all_charge_points)
            if not charge_point or not charge_point["charger_point_id"]:
                print(f"Advam: Charge point for {a['CPID']} not found")
                continue
            driivz = self.get_driivz_data_by(self.date,ADVAM_PLAN,charge_point_id=charge_point["charger_point_id"])
            if not driivz:
                continue
            transaction_amount = a["Transaction Amount"]
            transaction_datetime = datetime.strptime(a["Authorised"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.UTC)
            matched_driivz, driivz_response_version = self.filter_driivz(driivz, transaction_amount, transaction_datetime)
            if not matched_driivz:
                print(f"Advam - matching driivz data is not available for card: {self.card_number} and amount: {transaction_amount}")
                continue
            a = filter_keys(a, {'Custom Unique Key', 'Card','Type','Authorised','Transaction Amount'})
            if driivz_response_version == "v1":
                matched_driivz = filter_keys(matched_driivz, {'transactionId', 'totalEnergy', 'startOn', 'stopOn', 'chargeTime', 'cost'})
            else:
                matched_driivz = filter_keys(matched_driivz, {'id', 'totalEnergy', 'startedOn', 'stoppedOn', 'chargeTime', 'cost', 'cost'})
            matching_data.append({
                "advam": {**a},
                "driivz": {"version": driivz_response_version, "data": matched_driivz},
                "station_name": charge_point["station_name"],
                "station_address": charge_point["station_address"],
                "charge_point_name": charge_point["charger_point_name"],
                "latitude": charge_point["latitude"],
                "longitude": charge_point["longitude"],
                "vat_percentage": matched_driivz["cost"]["tax_rate"],
                "tax_amount": matched_driivz["cost"]["totalTax"],
                "amount_without_tax": round(abs(matched_driivz["cost"]["total"] - matched_driivz["cost"]["totalTax"]), 2),  
            })
        return matching_data


    def get_matching_rh_ocpi_ampeco_data(self, rh_data):
        matching_data = []
        for r in rh_data:
            charge_point = get_object_by("worldline_terminal_id", r["terminalId"], self.all_charge_points)
            if not charge_point or not charge_point["charger_point_id"]:
                print(f"[AMpeco] RH: Charge point for terminal {r['terminalId']} not found")
                continue
            ocpi_sessions = self.get_ocpi_sessions(
                self.date,
                amount=float(r["amount"]),
                charge_point_ids=[charge_point["ampeco_charge_point_id"]],
                time_tolerance=self.tolerance_time
            )
            if not ocpi_sessions:
                continue
            if len(ocpi_sessions) > 1 and r.get("amount") is not None:
                matched_session = min(ocpi_sessions, key=lambda s: abs(float(s.get("cost", {}).get("total") or 0) - float(r["amount"])))
            else:
                matched_session = ocpi_sessions[0]
            charge_point = get_object_by("ampeco_charge_point_id", matched_session.get("chargePointId"), self.all_charge_points)
            matching_data.append({
                "rh": filter_keys(r, {'requestUUID', 'maskedPan','cardBrand','transactionDateTime','amount'}),
                "ampeco": matched_session,
                "station_name": charge_point["ampeco_site_title"],
                "station_address": charge_point["station_address"],
                "charge_point_name": charge_point["ampeco_charge_point_name"] if charge_point else None,
                "latitude": charge_point["latitude"],
                "longitude": charge_point["longitude"],
                "vat_percentage": matched_session["cost"]["tax_rate"],
                "tax_amount": matched_session["cost"]["totalTax"],
                "amount_without_tax": round(abs(matched_session["cost"]["total"] - matched_session["cost"]["totalTax"]), 2),                
            })
        return matching_data

    def get_matching_payter_ocpi_ampeco_data(self, payter_data):
        matching_data = []
        for p in payter_data:
            print(f"Payter: charge point: {p['serialNumber']}")
            charge_point = get_object_by("payter_terminal_id", p["serialNumber"], self.all_charge_points)
            if not charge_point or not charge_point["ampeco_charge_point_id"]:
                print(f"Payter: Ampeco charge point for {p['serialNumber']} not found")
                continue
            ocpi_sessions = self.get_ocpi_sessions(
                self.date,
                amount=float(p["committedAmount"]/100),
                charge_point_ids=[charge_point["ampeco_charge_point_id"]],
                time_tolerance=self.tolerance_time
            )
            print(f"[DEBUG] ocpi_sessions: {ocpi_sessions}")
            if not ocpi_sessions:
                continue
            if len(ocpi_sessions) > 1 and p.get("committedAmount") is not None:
                matched_session = min(ocpi_sessions, key=lambda s: abs(float(s.get("cost", {}).get("total") or 0) - float(p["committedAmount"])))
                print(f"[DEBUG] matched_session: {matched_session}")
            else:
                matched_session = ocpi_sessions[0]
            matching_data.append({
                "payter": filter_keys(p, {'id' ,'maskedPAN', 'brandName', 'txnTimestamp', 'committedAmount', 'paymentType'}),
                "ampeco": matched_session,
                "station_name": charge_point["ampeco_site_title"],
                "station_address": charge_point["station_address"],
                "charge_point_name": charge_point["ampeco_charge_point_name"],
                "latitude": charge_point["latitude"],
                "longitude": charge_point["longitude"],
                "vat_percentage": matched_session["cost"]["tax_rate"],
                "tax_amount": matched_session["cost"]["totalTax"],
                "amount_without_tax": round(abs(matched_session["cost"]["total"] - matched_session["cost"]["totalTax"]), 2), 
            })
        return matching_data

    def get_matching_advam_ocpi_ampeco_data(self, advam_data):
        matching_data = []
        for a in advam_data:
            charge_point = get_object_by("ampeco_charge_point_name",a["CPID"],self.all_charge_points)
            if not charge_point or not charge_point["ampeco_charge_point_id"]:
                print(f"Advam: Ampeco charge point for {a['CPID']} not found")
                continue
            ocpi_sessions = self.get_ocpi_sessions(
                self.date,
                amount=a["Transaction Amount"],
                charge_point_ids=[charge_point["ampeco_charge_point_id"]],
                time_tolerance=self.tolerance_time
            )
            if not ocpi_sessions:
                continue
            if len(ocpi_sessions) > 1 and a.get("Transaction Amount") is not None:
                matched_session = min(ocpi_sessions, key=lambda s: abs(float(s.get("cost", {}).get("total") or 0) - float(a["Transaction Amount"])))
            else:
                matched_session = ocpi_sessions[0]
            matching_data.append({
                "advam": filter_keys(a, {'Custom Unique Key', 'Card','Type','Authorised','Transaction Amount'}),
                "ampeco": matched_session,
                "station_name": charge_point["ampeco_site_title"],
                "station_address": charge_point["station_address"],
                "charge_point_name": charge_point["ampeco_charge_point_name"],
                "latitude": charge_point["latitude"],
                "longitude": charge_point["longitude"],
                "vat_percentage": matched_session["cost"]["tax_rate"],
                "tax_amount": matched_session["cost"]["totalTax"],
                "amount_without_tax": round(abs(matched_session["cost"]["total"] - matched_session["cost"]["totalTax"]), 2),
            })
        return matching_data

    def get_driivz_data_by(self, date, billing_plan_code, charge_point_id=None, station_id=None):
        """
        Get Driivz data from the cache/database/api based on the 
        date, billing plan, and charge point (for payter).
        """
        key = get_driivz_key(date, billing_plan_code, charge_point_id, station_id)
        # Cache
        if date.date() != datetime.now().date():
            driivz = redis_connection.get(key)
            if driivz:
                return json.loads(driivz)
            print(f"driivz data is not available in cache for key : {key}")

            # Database
            try:
                driivz = DriivzData.objects.get(key=key)
            except ObjectDoesNotExist:
                driivz = None
            if driivz and driivz.data:
                redis_connection.set(key, driivz.data)
                return json.loads(driivz.data)
            print(f"driivz data is not available in db for key : {key}")

            # Backward Compatibility
            driivz = self.backward_compatibility_driivz_data(date, key)
            if driivz:
                return driivz

        # API
        from_date = date.strftime(DATE_FORMAT_FOR_DRIIVZ_V2) #date's 12am
        to_date = (date + timedelta(days=1)).strftime(DATE_FORMAT_FOR_DRIIVZ_V2) #Next date's 12am
        charge_point_ids = []
        if charge_point_id:
            charge_point_ids.append(charge_point_id)
        if station_id:
            station = get_object_by("station_id", station_id, self.all_stations)
            charge_point_ids.extend(station["charge_point_ids"])
        driivz_api = get_driivz_from_api(from_date,to_date,charge_point_ids)
        if driivz_api:
            driivz = driivz_api.get(key)
            # bulk_upsert_driivz_cache(driivz_api)
            # bulk_upsert_driivz_database(driivz_api)
        if driivz:
            return driivz
        print(f"driivz data is not available in API for {date}, {billing_plan_code}{', ' + charge_point_id if charge_point_id else ''}{', ' + station_id if station_id else ''}")
        return None

    def backward_compatibility_driivz_data(self, date, key):
        driivz = (
            redis_connection.get(f"{DRIIVZ}-{date.date()}")
            or ThirdPartyServicesData.objects.filter(
                source=DRIIVZ, data_date__date=date.date()
            )
            .values_list("data", flat=True)
            .first()
        )
        return group_driivz(json.loads(driivz)).get(key) if driivz else None

    def log_receipt_details(self):
        """Logs receipt details from the request."""
        print("Input data")
        unnecessary_data = [
            "args",
            "kwargs",
            "_negotiator",
            "headers",
            "format_kwarg",
            "request",
            "all_stations",
            "all_charge_points",
            "recaptcha_token",
            "valeting_machines"
        ]
        for key, value in self.__dict__.items():
            if key not in unnecessary_data:
                print(f"\t{key}: {value}")

    def get_ocpi_sessions(self, date, amount=None, charge_point_ids=None, time_tolerance=None):
        """
        Fetch Ampeco sessions: check cache, then DB, then API. Use key f"Ampeco:{date.strftime('%Y%m%d')}:{charge_point_id}" for each charge_point_id.
        Optimized for readability: No card number logic, clear filtering and mapping.
        """
        print("\n================ [STEP 1] Entered get_ocpi_sessions =================\n")
        print(f"[STEP 1] date={date}, amount={amount}, charge_point_ids={charge_point_ids}, time_tolerance={time_tolerance}")

        # Step 2: Gather all sessions from cache, DB, or API
        all_sessions = []
        found_all = True
        if charge_point_ids:
            for i, cp_id in enumerate(charge_point_ids):
                key = f"Ampeco:{date.strftime('%Y%m%d')}:{cp_id}"
                print(f"Trying cache key: {key}")
                cached = redis_connection.get(key)
                sessions = None
                if cached:
                    try:
                        sessions = json.loads(cached)
                    except Exception as e:
                        print(f"[Cache] Exception loading cache for {key}: {e}")
                        sessions = None
                if not sessions:
                    db_obj = AmpecoData.objects.filter(key=key).first()
                    if db_obj and db_obj.data:
                        try:
                            sessions = json.loads(db_obj.data)
                        except Exception as e:
                            print(f"[DB] Exception loading DB data for {key}: {e}")
                            sessions = None
                if not sessions:
                    found_all = False
                    break
                all_sessions.extend(sessions)
        else:
            found_all = False

        if not found_all:
            started_after_iso = date.strftime("%Y-%m-%dT00:00:00.000Z")
            started_before_iso = date.strftime("%Y-%m-%dT23:59:59.999Z")
            grouped_sessions, _ = get_ampeco_from_api(started_after_iso, started_before_iso)
            sessions = []
            if charge_point_ids:
                for cp_id in charge_point_ids:
                    key = f"Ampeco:{date.strftime('%Y%m%d')}:{cp_id}"
                    group = grouped_sessions.get(key, [])
                    redis_connection.set(key, json.dumps(group))
                    sessions.extend(group)
            else:
                for key, group in grouped_sessions.items():
                    redis_connection.set(key, json.dumps(group))
                    sessions.extend(group)
            all_sessions = sessions

        # Step 3: Filter and map sessions
        filtered_sessions = list(filter(
            lambda session: (
                # Amount filter
                (
                    amount is None or
                    (
                        session.get("totalAmount") and session["totalAmount"].get("withTax") is not None and
                        abs(float(session["totalAmount"]["withTax"]) - float(amount)) <= (self.tolerance_amount or 0.10)
                    )
                )
                # Time tolerance filter
                and (
                    not time_tolerance or not session.get("stoppedAt") or (
                        (lambda session_end: (
                            (isinstance(session_end, str) and (
                                (lambda dt: abs((dt - date).total_seconds()) <= time_tolerance.total_seconds() if dt else False)(
                                    (datetime.fromisoformat(session_end.replace("Z", "+00:00")) if session_end else None)
                                )
                            )) or
                            (not isinstance(session_end, str) and abs((session_end - date).total_seconds()) <= time_tolerance.total_seconds())
                        ))(session.get("stoppedAt"))
                    )
                )
            ),
            all_sessions
        ))

        mapped_sessions = []
        for session in filtered_sessions:
            started_on = session.get("startedAt")
            stopped_on = session.get("stoppedAt")
            charge_time = None
            if started_on and stopped_on:
                try:
                    start_dt = datetime.fromisoformat(started_on.replace("Z", "+00:00"))
                    stop_dt = datetime.fromisoformat(stopped_on.replace("Z", "+00:00"))
                    charge_time = (stop_dt - start_dt).total_seconds()
                except Exception as e:
                    print(f"Error parsing charge time: {e}")

            cost_obj = None
            total_amount = session.get("totalAmount")
            if total_amount and "withTax" in total_amount and "withoutTax" in total_amount:
                with_tax = total_amount.get("withTax", 0)
                without_tax = total_amount.get("withoutTax", 0)
                cost_obj = {
                    "currency": "GBP",
                    "totalTax": round(with_tax - without_tax, 2),
                    "total": with_tax,
                    "tax_rate": session.get("tax_rate") or float(filter_function_for_base_configuration("contactless_receipts_tax_rate", CONTACTLESS_RECEIPTS_TAX_RATE))
                }
            mapped = {
                "id": session.get("id"),
                "totalEnergy": round(session.get("energyConsumption", {}).get("total", 0) / 1000, 2),
                "startedOn": started_on,
                "stoppedOn": stopped_on,
                "chargeTime": charge_time,
                "chargePointId": str(session.get("chargePointId")),
                "cost": cost_obj,
            }
            mapped_sessions.append(mapped)
        print(f"[STEP 3] Total filtered and mapped sessions: {len(mapped_sessions)}")
        return mapped_sessions

    def get_matching_rh_combined_data(self, rh_data):
        matching_data = []
        try:
            ampeco_matches = self.get_matching_rh_ocpi_ampeco_data(rh_data) or []
        except Exception as e:
            print(f"Exception in get_matching_rh_ocpi_ampeco_data: {e}")
            ampeco_matches = []
        matched_rh_ids = set()
        for match in ampeco_matches:
            matching_data.append(match)
            try:
                if 'rh' in match and match['rh'] and 'requestUUID' in match['rh'] and match['rh']['requestUUID']:
                    matched_rh_ids.add(match['rh']['requestUUID'])
            except Exception as e:
                print(f"Exception extracting RH unique key: {e}")
        unmatched_rh_data = [r for r in rh_data if r.get('requestUUID') not in matched_rh_ids]
        try:
            driivz_matches = self.get_matching_rh_driivz_data(unmatched_rh_data) or []
        except Exception as e:
            print(f"Exception in get_matching_rh_driivz_data: {e}")
            driivz_matches = []
        if driivz_matches:
            matching_data.extend(driivz_matches)
        return matching_data

    def get_matching_payter_combined_data(self, payter_data):
        matching_data = []
        try:
            ampeco_matches = self.get_matching_payter_ocpi_ampeco_data(payter_data) or []
        except Exception as e:
            print(f"Exception in get_matching_payter_ocpi_ampeco_data: {e}")
            ampeco_matches = []
        matched_payter_ids = set()
        for match in ampeco_matches:
            matching_data.append(match)
            try:
                if 'payter' in match and match['payter'] and 'id' in match['payter'] and match['payter']['id']:
                    matched_payter_ids.add(match['payter']['id'])
            except Exception as e:
                print(f"Exception extracting Payter unique key: {e}")
        unmatched_payter_data = [p for p in payter_data if p.get('id') not in matched_payter_ids]
        try:
            driivz_matches = self.get_matching_payter_driivz_data(unmatched_payter_data) or []
        except Exception as e:
            print(f"Exception in get_matching_payter_driivz_data: {e}")
            driivz_matches = []
        if driivz_matches:
            matching_data.extend(driivz_matches)
        return matching_data

    def get_matching_advam_combined_data(self, advam_data):
        matching_data = []
        try:
            ampeco_matches = self.get_matching_advam_ocpi_ampeco_data(advam_data) or []
        except Exception as e:
            print(f"Exception in get_matching_advam_ocpi_ampeco_data: {e}")
            ampeco_matches = []
        matched_advam_keys = set()
        for match in ampeco_matches:
            matching_data.append(match)
            try:
                if 'advam' in match and match['advam']:
                    advam_key = f"{match['advam']['Transaction Amount']}_{match['advam']['Authorised']}_{match['advam']['Card']}"
                    matched_advam_keys.add(advam_key)
            except Exception as e:
                print(f"Exception extracting Advam unique key: {e}")

        unmatched_advam_data = [
            a for a in advam_data
            if f"{a.get('Transaction Amount')}_{a.get('Authorised')}_{a.get('Card')}" not in matched_advam_keys
        ]
        try:
            driivz_matches = self.get_matching_advam_driivz_data(unmatched_advam_data) or []
        except Exception as e:
            print(f"Exception in get_matching_advam_driivz_data: {e}")
            driivz_matches = []
        if driivz_matches:
            matching_data.extend(driivz_matches)
        return matching_data

def recaptcha(request):
    recaptcha_creds_data = {
            "secret": config("DJANGO_APP_CONTACTLESS_RECAPTCHA_TOKEN"),
            "response": request.data.get('recaptcha_token'),
        }
    recaptcha_request = traced_request(
        POST_REQUEST,
        config("DJANGO_APP_CONTACTLESS_RECAPTCHA_URL"),
        data=recaptcha_creds_data,
    )
    result = recaptcha_request.json()
    print("Recaptcha Result",json.dumps(result,indent=4))
    return result


def process_data(source_data, source_key, user_entered_date_time):
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


def set_source_data_in_cache(source, user_entered_date_time):
    """this function sets the source data from database to cache"""
    db_data = ThirdPartyServicesData.objects.filter(
        source=source, data_date__date=user_entered_date_time.date()
    ).first()
    if db_data and source != PDI_MORRISONS:
        redis_connection.set(
            f"{source}-{user_entered_date_time.date()}", db_data.data
        )
    return db_data


def get_charge_points():
    data = redis_connection.get("charge_points")
    if data:
        return json.loads(data)
    data = list(
        ChargePoint.objects
        .select_related("station_id")
        .values_list(
            "station_id__station_id","charger_point_id", "charger_point_name", "payter_terminal_id", "worldline_terminal_id", "station_id__driivz_display_name", "station_id__site_title", "station_id__station_address1", "station_id__station_address2", "station_id__station_address3", "station_id__latitude", "station_id__longitude", "station_id__post_code", "ampeco_charge_point_id", "ampeco_charge_point_name", "station_id__ampeco_site_title"
        )
    )
    data = [
        {
            "station_id": station_id,
            "charger_point_id": charger_point_id,
            "charger_point_name": charger_point_name,
            "payter_terminal_id": payter_terminal_id,
            "worldline_terminal_id": worldline_terminal_id,
            "station_name": driivz_display_name if driivz_display_name else site_title,
            "station_address": ", ".join(
                filter(
                    None,
                    [
                        station_address1.strip(),
                        station_address2.strip(),
                        station_address3.strip(),
                        post_code.strip(),
                    ],
                )
            ),
            "latitude": latitude,
            "longitude": longitude,
            "ampeco_charge_point_id": ampeco_charge_point_id, 
            "ampeco_charge_point_name": ampeco_charge_point_name,
            "ampeco_site_title": ampeco_site_title if ampeco_site_title else site_title
        }
        for station_id, charger_point_id, charger_point_name, payter_terminal_id, worldline_terminal_id, driivz_display_name, site_title, station_address1, station_address3, station_address2, latitude, longitude, post_code, ampeco_charge_point_id, ampeco_charge_point_name, ampeco_site_title in data
    ]
    redis_connection.set("charge_points", json.dumps(data))
    return data


def get_object_by(key, value, array):
    return next((x for x in array if x[key] == value), None)

def get_all_stations():
    #Get from cache
    data = redis_connection.get("station_data")
    if data:
        return json.loads(data)

    #Get from Database
    stations = list(
        Stations.objects.filter(
            ~Q(payment_terminal="None"),
            deleted=NO,
            status="Active"
        ).prefetch_related(
            Prefetch('charge_points', to_attr='charge_points_list')
        )
    )
    data = []
    for station in stations:
        station_id = station.station_id
        station_brand = station.brand
        address1 = station.station_address1
        address2 = station.station_address2
        address3 = station.station_address3
        latitude = station.latitude
        longitude = station.longitude
        post_code = station.post_code
        payment_terminal = json.loads(station.payment_terminal) if station.payment_terminal else None
        charge_point_names = [cp.charger_point_name for cp in station.charge_points_list]
        charge_point_ids = [cp.charger_point_id for cp in station.charge_points_list]
        payter_terminal_ids = [cp.payter_terminal_id for cp in station.charge_points_list]
        worldline_terminal_ids = [cp.worldline_terminal_id for cp in station.charge_points_list]
        station_name = station.driivz_display_name if station.driivz_display_name else station.site_title
        rh_sitename = station.receipt_hero_site_name if station.receipt_hero_site_name else None
        ampeco_site_id = station.ampeco_site_id if station.ampeco_site_id else None
        ampeco_site_title = station.ampeco_site_title if station.ampeco_site_title else None
        ampeco_charge_point_ids = [cp.ampeco_charge_point_id for cp in station.charge_points_list]
        ampeco_charge_point_names = [cp.ampeco_charge_point_name for cp in station.charge_points_list]

        data.append({
            "station_id": station_id,
            "station_brand": station_brand,
            "payment_terminal": payment_terminal,
            "charge_point_names": charge_point_names,
            "charge_point_ids": charge_point_ids,
            "payter_terminal_ids": payter_terminal_ids,
            "worldline_terminal_ids": worldline_terminal_ids,
            "station_name": station_name,
            "address1": address1,
            "address2": address2,
            "address3": address3,
            "latitude": latitude,
            "longitude": longitude,
            "full_address": ", ".join(
                filter(
                    None,
                    [address1.strip(), address2.strip(), address3.strip(), post_code.strip()],
                )
            ),
            "post_code": post_code,
            "rh_sitename": rh_sitename,
            "ampeco_site_id": ampeco_site_id,
            "ampeco_site_title": ampeco_site_title,
            "ampeco_charge_point_ids": ampeco_charge_point_ids,
            "ampeco_charge_point_names": ampeco_charge_point_names
        })
    redis_connection.set("station_data", json.dumps(data))
    return data

def get_all_valeting_machines():
    data = redis_connection.get("valeting_machines")
    if data:
        return json.loads(data)
    data = list(
        ValetingMachine.objects
        .filter(deleted=False, is_active=True)
        .select_related("station_id")
        .values_list(
            "station_id__station_id",
            "machine_id",
            "machine_name",
            "station_id__driivz_display_name",
            "station_id__site_title",
            "station_id__station_address1",
            "station_id__station_address2",
            "station_id__station_address3",
            "station_id__latitude",
            "station_id__longitude",
            "station_id__post_code"
        )
    )
    data = [
        {
            "machine_id": machine_id,
            "machine_name": machine_name,
            "station_id": station_id,
            "station_name": driivz_display_name if driivz_display_name else site_title,
            "station_address": ", ".join(
                filter(
                    None,
                    [
                        station_address1.strip(),
                        station_address2.strip(),
                        station_address3.strip(),
                        post_code.strip(),
                    ],
                )
            ),
            "latitude": latitude,
            "longitude": longitude,
        }
        for station_id, machine_id, machine_name, driivz_display_name, site_title, station_address1, station_address2, station_address3, latitude, longitude, post_code in data
    ]
    redis_connection.set("valeting_machines", json.dumps(data))
    return data

class UpdateDriivzCRONJobAPI(APIView):
    """Driivz Cronjonb API"""

    @classmethod
    def post(cls, cron_job_request):
        """
        Takes date-from and date-to from request, fetches driivz 
        data from driivz api and stores in cache and database.
        date format : %Y-%m-%dT%H:%M:%S.%fZ
        """
        try:
            secret_key_azure = cron_job_request.data.get("secret_key", None)
            if secret_key_azure is None:
                return SECRET_KEY_NOT_PROVIDED
            if not handler.verify(
                secret_key_azure, DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET
            ):
                return SECRET_KEY_IN_VALID

            from_date = cron_job_request.data.get("from-date", None)
            to_date = cron_job_request.data.get("to-date", None)

            if not from_date or not to_date:
                return Response(
                    {
                        "message": "from-date and to-date is required. format: '%Y-%m-%dT%H:%M:%S.%fZ'",
                    },
                    status= status.HTTP_400_BAD_REQUEST
                )
            start_time = time.time()
            driivz_data = get_driivz_from_api(from_date,to_date)
            upserted_cache_count = bulk_upsert_driivz_cache(driivz_data)
            new_data_count_db, updated_data_count_db = bulk_upsert_driivz_database(driivz_data)
            end_time = time.time()

            response = f"In database: Added {new_data_count_db} records and updated {updated_data_count_db} records. In cache: Added/Updated {upserted_cache_count} records."

            print(response)
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": response,
                    "time-elapsed":f"{round(end_time-start_time,1)} Seconds"
                }
            )
        except COMMON_ERRORS as e:
            traceback.print_exc()
            return API_ERROR_OBJECT


def get_driivz_from_api(from_date,to_date,charge_point_ids=None):
    driivz_response = driivz_api_v2(from_date, to_date, charge_point_ids)
    if driivz_response:
        tax_rate_percentage = float(filter_function_for_base_configuration("contactless_receipts_tax_rate", CONTACTLESS_RECEIPTS_TAX_RATE))
        sessions = []
        for response in driivz_response:
            if (
                    PLAN_CODE in response and
                response.get("transactionStatus") == "BILLED" and
                isinstance(response.get("cost"), dict) and
                "total" in response["cost"]
            ):
                response["cost"]["tax_rate"] = tax_rate_percentage
                sessions.append(response)
        driivz_response_data = group_driivz(sessions)
        return driivz_response_data
    else:
        return []


def group_driivz(all_driivz):
    grouped_data = defaultdict(list)
    all_charge_points = get_charge_points()
    for driivz in all_driivz:
        if "id" in driivz:
            #New response format
            date = datetime.fromtimestamp(driivz['startedOn'], tz=pytz.UTC)
            charge_point_id = driivz['chargerId']
            charge_point = get_object_by("charger_point_id", str(charge_point_id), all_charge_points)
            if not charge_point or not charge_point["station_id"]:
                continue
            station_id = charge_point["station_id"]
            planCode = driivz['planCode']
        else:
            #Old response format
            date = parser.parse(driivz['startOn'])
            charge_point = get_object_by("charger_point_name", driivz['station']['caption'], all_charge_points)
            if not charge_point or not charge_point["charger_point_id"]:
                continue
            station_id = charge_point["station_id"]
            charge_point_id = charge_point["charger_point_id"]
            planCode = driivz['billingPlanCode']
        driivz_key = get_driivz_key(date, planCode, charge_point_id, station_id)
        grouped_data[driivz_key].append(driivz)
    return dict(grouped_data)


def bulk_upsert_driivz_cache(grouped_data):
    """Upsert driivz cache data in bulk"""
    with redis_connection.pipeline() as pipe:
        upsert_count = 0
        for key, multiple_driivz_data in grouped_data.items():
            data, add_or_update = upsert_driivz_cache_obj(key, multiple_driivz_data)
            if add_or_update:
                pipe.set(key, json.dumps(data))
                upsert_count += 1

        if pipe.command_stack:
            pipe.execute()

        return upsert_count


def upsert_driivz_cache_obj(key, multiple_driivz_data):
    """This method checks if driivz data needs to be added or updated 
    in cache and provides data with status"""
    existing_cache = redis_connection.get(key)

    if existing_cache is None:
        return multiple_driivz_data, True
    
    existing_cache_data = json.loads(existing_cache)
    add_or_update = False

    for driivz_data in multiple_driivz_data:
        if not driivz_object_exists(existing_cache_data, driivz_data):
            existing_cache_data.append(driivz_data)
            add_or_update = True

    return existing_cache_data, add_or_update


def bulk_upsert_driivz_database(driivz_data_list):
    """Upsert Driivz db data in bulk"""
    keys = list(driivz_data_list.keys())
    existing_db_data_list = list(DriivzData.objects.filter(key__in=keys))
    
    index = {entity.key: entity for entity in existing_db_data_list}
    
    data_to_add = []
    data_to_update = []
    current_time = timezone.now()

    for key, fresh_data in driivz_data_list.items():
        entity = index.get(key, None)
        
        if entity is None:
            data_to_add.append(DriivzData(
                key=key,
                data=json.dumps(fresh_data),
                created_date=current_time,
                updated_by='Cron_Job'
            ))
        else:
            updated_data = update_driivz_db_obj(key, fresh_data, index, current_time)
            if updated_data:
                data_to_update.append(updated_data)

    if data_to_add:
        DriivzData.objects.bulk_create(data_to_add)

    if data_to_update:
        fields_to_update = ['data', 'updated_date', 'updated_by']
        DriivzData.objects.bulk_update(data_to_update, fields_to_update)
    
    return len(data_to_add), len(data_to_update)


def update_driivz_db_obj(key, multiple_driivz_data, existing_db_data_dict, current_time):
    existing_db_data = existing_db_data_dict.get(key, None)
    
    if existing_db_data is None:
        return None
    
    existing_data = json.loads(existing_db_data.data) if existing_db_data.data else []

    is_updated = False
    for driivz_data in multiple_driivz_data:
        if not driivz_object_exists(existing_data, driivz_data):
            existing_data.append(driivz_data)
            is_updated = True

    if is_updated:
        existing_db_data.data = json.dumps(existing_data)
        existing_db_data.updated_date = current_time
        existing_db_data.updated_by = 'Cron_Job'
        return existing_db_data

    return None


def driivz_object_exists(existing_data, driivz_data):
    """Check if driivz data exists by amount."""
    IsObjectExists = any(
        (existing_item.get('id') or existing_item.get('transactionId')) ==
        (driivz_data.get('id') or driivz_data.get('transactionId'))
        for existing_item in existing_data
    )
    return IsObjectExists


def get_driivz_key(date, planCode=None, charge_point_id=None, station_id=None):
    if planCode == WORLDLINE_PLAN:
        key = f"Driivz:{date.strftime('%Y%m%d')}:{planCode}:{charge_point_id}"
    elif planCode == PAYTER_PLAN and charge_point_id:
        key = f"Driivz:{date.strftime('%Y%m%d')}:{planCode}:{charge_point_id}"
    elif planCode == ADVAM_PLAN and charge_point_id:
        key = f"Driivz:{date.strftime('%Y%m%d')}:{planCode}:{charge_point_id}"
    else:
        key = f"Driivz:{date.strftime('%Y%m%d')}:other:{charge_point_id}"
    return key

def filter_keys(data, required_keys):
    if isinstance(data, dict):
        return {key: data[key] for key in required_keys if key in data}
    return [{key: d[key] for key in required_keys if key in d} for d in data]


class UpdateAdvamCRONJobAPI(APIView):
    """Advam Cronjonb API"""

    @classmethod
    def post(cls, cron_job_request):
        """
        Takes date-from and date-to from request, fetches advam 
        data from advam api and stores in cache and database.
        date format : %Y-%m-%dT%H:%M:%SZ
        """
        try:
            secret_key_azure = cron_job_request.data.get("secret_key", None)
            if secret_key_azure is None:
                return SECRET_KEY_NOT_PROVIDED
            if not handler.verify(
                secret_key_azure, DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET
            ):
                return SECRET_KEY_IN_VALID

            from_date = cron_job_request.data.get("from-date", None)
            to_date = cron_job_request.data.get("to-date", None)

            if not from_date or not to_date:
                return Response(
                    {
                        "message": "from-date and to-date is required. format: '%Y-%m-%dT%H:%M:%SZ'",
                    },
                    status= status.HTTP_400_BAD_REQUEST
                )
            start_time = time.time()
            advam_data = get_advam_from_api(from_date,to_date)
            if advam_data:
                upserted_cache_count = bulk_upsert_advam_cache(advam_data)
                new_data_count_db, updated_data_count_db = bulk_upsert_advam_database(advam_data)
                response = f"In database: Added {new_data_count_db} records and updated {updated_data_count_db} records. In cache: Added/Updated {upserted_cache_count} records."
            else:
                response = "Advam data could not be added/updated due to an API error or data unavailability."
            end_time = time.time()
            print(response)
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": response,
                    "time-elapsed":f"{round(end_time-start_time,1)} Seconds"
                }
            )
        except COMMON_ERRORS as e:
            traceback.print_exc()
            return API_ERROR_OBJECT


def get_advam_from_api(from_date, to_date):
    advam_response = advam_api(from_date, to_date)
    if advam_response:
        sessions = filter(
            lambda session: "action" in session
            and session["action"] == "C",
            advam_response
        )
        advam_response_data = group_advam(list(sessions))
        return advam_response_data
    else:
        return []


def group_advam(all_advam):
    grouped_data = defaultdict(list)
    for advam in all_advam:
        date = datetime.strptime(advam['effectiveDate'], ADVAM_API_DATE_FORMAT)
        formatted_date = datetime.strftime(date, "%Y-%m-%d")
        grouped_data[formatted_date].append(advam)
    return dict(grouped_data)


def bulk_upsert_advam_cache(grouped_data):
    """Upsert advam cache data in bulk"""
    with redis_connection.pipeline() as pipe:
        upsert_count = 0
        for date, multiple_advam_data in grouped_data.items():
            advam_cache_key = f"{ADVAM}-{date}"
            data, add_or_update = upsert_advam_cache_obj(advam_cache_key, multiple_advam_data)
            if add_or_update:
                pipe.set(advam_cache_key, json.dumps(data))
                upsert_count += 1

        if pipe.command_stack:
            pipe.execute()

        return upsert_count


def upsert_advam_cache_obj(key, multiple_advam_data):
    """This method checks if advam data needs to be added or updated 
    in cache and provides data with status"""
    existing_cache = redis_connection.get(key)

    if existing_cache is None:
        return multiple_advam_data, True
    
    existing_cache_data = json.loads(existing_cache)
    add_or_update = False

    for advam_data in multiple_advam_data:
        if not advam_object_exists(existing_cache_data, advam_data):
            existing_cache_data.append(advam_data)
            add_or_update = True

    return existing_cache_data, add_or_update


def bulk_upsert_advam_database(advam_data_list):
    """Upsert Advam db data in bulk"""
    dates = list(advam_data_list.keys())
    date_objects = [datetime.strptime(d, "%Y-%m-%d").date() for d in dates]
    existing_db_data_list = list(ThirdPartyServicesData.objects.filter(data_date__date__in=date_objects, source=ADVAM))
    
    index = {datetime.strftime(entity.data_date, "%Y-%m-%d"): entity for entity in existing_db_data_list}
    
    data_to_add = []
    data_to_update = []
    current_time = timezone.localtime(timezone.now())

    for date, fresh_data in advam_data_list.items():
        entity = index.get(date, None)
        
        if entity is None:
            data_to_add.append(ThirdPartyServicesData(
                data_date=datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=pytz.UTC),
                source=ADVAM,
                data=json.dumps(fresh_data),
                status=COMPLETE,
                created_date=timezone.localtime(timezone.now()),
                updated_date=timezone.localtime(timezone.now()),
                updated_by="Cron_Job",
                details=SUCCESSFULLY_FETCHED_DATA,
            ))
        else:
            updated_data = update_advam_db_obj(date, fresh_data, index, current_time)
            if updated_data:
                data_to_update.append(updated_data)

    if data_to_add:
        ThirdPartyServicesData.objects.bulk_create(data_to_add)

    if data_to_update:
        fields_to_update = ['data', 'updated_date', 'updated_by']
        ThirdPartyServicesData.objects.bulk_update(data_to_update, fields_to_update)
    
    return len(data_to_add), len(data_to_update)


def update_advam_db_obj(date, multiple_advam_data, existing_db_data_dict, current_time):
    existing_db_data = existing_db_data_dict.get(date, None)
    
    if existing_db_data is None:
        return None
    
    existing_data = json.loads(existing_db_data.data) if existing_db_data.data else []

    is_updated = False
    for advam_data in multiple_advam_data:
        if not advam_object_exists(existing_data, advam_data):
            existing_data.append(advam_data)
            is_updated = True

    if is_updated:
        existing_db_data.data = json.dumps(existing_data)
        existing_db_data.updated_date = current_time
        existing_db_data.updated_by = 'Cron_Job'
        return existing_db_data

    return None


def advam_object_exists(existing_data, advam_data):
    """Check if advam data exists by guid."""
    IsObjectExists = any(
        existing_item.get('guid') == advam_data.get('guid') for existing_item in existing_data
    )
    return IsObjectExists

def get_ampeco_from_api(from_date, to_date):
    print(f"\n[API] Calling Ampeco API for sessions from {from_date} to {to_date}...")
    AMPECO_BASE_URL = config("DJANGO_APP_AMPECO_BASE_URL")
    AMPECO_TOKEN = config("DJANGO_APP_AMPECO_TOKEN")
    params = {
        "filter[startedAfter]": from_date.replace("T", " ").replace("Z", ""),
        "filter[startedBefore]": to_date.replace("T", " ").replace("Z", ""),
        "page": 1,
    }
    headers = {
        "Authorization": f"Bearer {AMPECO_TOKEN}",
        "accept": "application/json",
    }
    all_sessions = []
    try:
        while True:
            url = AMPECO_BASE_URL + AMPECO_SESSIONS_ENDPOINT + "?" + urllib.parse.urlencode(params)
            print(f"[API] GET {url}")
            
            response = requests.get(url, headers=headers, timeout=120)
            print(f"[API] Response status: {response.status_code}")       
            if response.status_code != 200:
                print(f"[API] Error response: {response.text}")
                return None, response.text
            
            data = response.json()
            sessions = data.get("data") or []
            all_sessions.extend(sessions)
            
            meta = data.get("meta", {})
            print(f"[API] Page {meta.get('current_page')} of {meta.get('last_page')} | Sessions this page: {len(sessions)} | Total so far: {len(all_sessions)}")
            if meta.get("current_page") >= meta.get("last_page"):
                break
            
            params["page"] += 1
        return group_ampeco(all_sessions), None
    except Exception as e:
        print(f"[API] Exception occurred: {e}")
        return None, str(e)

def group_ampeco(all_ampeco):
    grouped_data = defaultdict(list)
    tax_rate_percentage = float(filter_function_for_base_configuration("contactless_receipts_tax_rate", CONTACTLESS_RECEIPTS_TAX_RATE))
    for session in all_ampeco:
        try:
            date = session.get("startedAt")
            session["tax_rate"] = tax_rate_percentage
            if date:
                date = datetime.fromisoformat(date.replace("Z", "+00:00"))
            else:
                continue
            charge_point_id = session.get("chargePointId")
            if not charge_point_id:
                continue
            ampeco_key = get_ampeco_key(date, charge_point_id)
            grouped_data[ampeco_key].append(session)
        except Exception:
            continue
    return dict(grouped_data)

def get_ampeco_key(date, charge_point_id):
    return f"Ampeco:{date.strftime('%Y%m%d')}:{charge_point_id}"

def bulk_upsert_ampeco_cache(grouped_data):
    print("\n[Cache] Bulk upserting Ampeco data into cache...")
    with redis_connection.pipeline() as pipe:
        upsert_count = 0
        for key, multiple_ampeco_data in grouped_data.items():
            data, add_or_update = upsert_ampeco_cache_obj(key, multiple_ampeco_data)
            if add_or_update:
                print(f"[Cache] Upserting key: {key} (new/updated)")
                pipe.set(key, json.dumps(data))
                upsert_count += 1
            else:
                print(f"[Cache] Key: {key} already up-to-date.")
        if pipe.command_stack:
            pipe.execute()
        print(f"[Cache] Bulk upsert complete. Total upserted: {upsert_count}")
        return upsert_count

def upsert_ampeco_cache_obj(key, multiple_ampeco_data):
    existing_cache = redis_connection.get(key)
    if existing_cache is None:
        return multiple_ampeco_data, True
    existing_cache_data = json.loads(existing_cache)
    add_or_update = False
    for ampeco_data in multiple_ampeco_data:
        if not ampeco_object_exists(existing_cache_data, ampeco_data):
            existing_cache_data.append(ampeco_data)
            add_or_update = True
    return existing_cache_data, add_or_update

def bulk_upsert_ampeco_database(ampeco_data_list):
    print("\n[DB] Bulk upserting Ampeco data into database...")
    keys = list(ampeco_data_list.keys())
    existing_db_data_list = list(AmpecoData.objects.filter(key__in=keys))
    index = {entity.key: entity for entity in existing_db_data_list}
    data_to_add = []
    data_to_update = []
    current_time = timezone.now()
    for key, fresh_data in ampeco_data_list.items():
        entity = index.get(key, None)
        if entity is None:
            print(f"[DB] Adding new record for key: {key}")
            data_to_add.append(AmpecoData(
                key=key,
                data=json.dumps(fresh_data),
                created_date=current_time,
                updated_by='Cron_Job'
            ))
        else:
            print(f"[DB] Updating existing record for key: {key}")
            updated_data = update_ampeco_db_obj(key, fresh_data, index, current_time)
            if updated_data:
                data_to_update.append(updated_data)
    if data_to_add:
        AmpecoData.objects.bulk_create(data_to_add)
        print(f"[DB] Bulk created {len(data_to_add)} new records.")
    if data_to_update:
        fields_to_update = ['data', 'updated_date', 'updated_by']
        AmpecoData.objects.bulk_update(data_to_update, fields_to_update)
        print(f"[DB] Bulk updated {len(data_to_update)} records.")
    print(f"[DB] Bulk upsert complete. New: {len(data_to_add)}, Updated: {len(data_to_update)}")
    return len(data_to_add), len(data_to_update)

def update_ampeco_db_obj(key, multiple_ampeco_data, existing_db_data_dict, current_time):
    existing_db_data = existing_db_data_dict.get(key, None)
    if existing_db_data is None:
        return None
    existing_data = json.loads(existing_db_data.data) if existing_db_data.data else []
    is_updated = False
    for ampeco_data in multiple_ampeco_data:
        if not ampeco_object_exists(existing_data, ampeco_data):
            existing_data.append(ampeco_data)
            is_updated = True
    if is_updated:
        existing_db_data.data = json.dumps(existing_data)
        existing_db_data.updated_date = current_time
        existing_db_data.updated_by = 'Cron_Job'
        return existing_db_data
    return None

def ampeco_object_exists(existing_data, ampeco_data):
    # Use session id as unique
    return any(existing_item.get('id') == ampeco_data.get('id') for existing_item in existing_data)

class UpdateAmpecoCRONJobAPI(APIView):
    """Ampeco Cronjob API"""

    @classmethod
    def post(cls, cron_job_request):
        """
        Takes date-from and date-to from request, fetches Ampeco data from Ampeco API and stores in cache and database.
        date format : %Y-%m-%dT%H:%M:%S.%fZ
        """
        try:
            print("\n================ Ampeco CRON Job Triggered ================")
            secret_key_azure = cron_job_request.data.get("secret_key", None)
            print(f"[Checkpoint] Received secret_key: {'Provided' if secret_key_azure else 'None'}")
            if secret_key_azure is None:
                print("[Error] Secret key not provided.")
                return SECRET_KEY_NOT_PROVIDED
            if not handler.verify(
                secret_key_azure, DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET
            ):
                print("[Error] Secret key is invalid.")
                return SECRET_KEY_IN_VALID

            from_date = cron_job_request.data.get("from-date", None)
            to_date = cron_job_request.data.get("to-date", None)
            print(f"[Checkpoint] from-date: {from_date}, to-date: {to_date}")

            if not from_date or not to_date:
                print("[Error] from-date and/or to-date not provided.")
                return Response(
                    {
                        "message": "from-date and to-date is required. format: '%Y-%m-%dT%H:%M:%S.%fZ'",
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            start_time = time.time()
            print("[Checkpoint] Fetching Ampeco data from API...")
            ampeco_data, error_details = get_ampeco_from_api(from_date, to_date)
            if not ampeco_data:
                print(f"[Error] Ampeco API fetch failed. Details: {error_details}")
                # Handle API failure or empty/null data from Ampeco API
                is_empty_data = False
                is_api_failure = False
                if ampeco_data is None:
                    # If error_details is present, treat as API failure
                    if error_details:
                        is_api_failure = True
                    else:
                        is_empty_data = True
                elif isinstance(ampeco_data, dict) and len(ampeco_data) == 0:
                    is_empty_data = True
                elif isinstance(ampeco_data, list) and len(ampeco_data) == 0:
                    is_empty_data = True

                error_key = f"AmpecoError:{from_date}_{to_date}:{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                fetch_error_reason = error_details or ("Ampeco API returned empty or null data." if is_empty_data else "Unknown error.")

                if is_api_failure:
                    # send_exception_email_function("Ampeco API fetch failed", error_details)
                    print(f"[Error] Ampeco API fetch failed. Details: {error_details}")
                    AmpecoData.objects.update_or_create(
                        key=error_key,
                        defaults={
                            "data": None,
                            "created_date": timezone.now(),
                            "updated_date": timezone.now(),
                            "updated_by": "Cron_Job",
                            "fetch_error_details": fetch_error_reason,
                        }
                    )
                    end_time = time.time()
                    print(f"[Result] Ampeco API fetch failed. Error stored. Time elapsed: {round(end_time-start_time,1)} Seconds\n============================================================\n")
                    return Response(
                        {
                            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                            "status": False,
                            "message": f"Ampeco API fetch failed. Error stored. Time elapsed: {round(end_time-start_time,1)} Seconds",
                            "error": fetch_error_reason,
                            "data": None
                        }
                    )
                elif is_empty_data:
                    print(f"[Warning] Ampeco API returned empty or null data. Details: {error_details}")
                    AmpecoData.objects.update_or_create(
                        key=error_key,
                        defaults={
                            "data": None,
                            "created_date": timezone.now(),
                            "updated_date": timezone.now(),
                            "updated_by": "Cron_Job",
                            "fetch_error_details": fetch_error_reason,
                        }
                    )
                    end_time = time.time()
                    print(f"[Result] Ampeco API returned empty/null data. Info stored. Time elapsed: {round(end_time-start_time,1)} Seconds\n============================================================\n")
                    return Response(
                        {
                            "status_code": status.HTTP_200_OK,
                            "status": True,
                            "message": f"Ampeco API returned empty or null data. Info stored. Time elapsed: {round(end_time-start_time,1)} Seconds",
                            "error": fetch_error_reason,
                            "data": None
                        }
                    )
            print(f"[Checkpoint] Ampeco API fetch successful. Records fetched: {len(ampeco_data) if hasattr(ampeco_data, '__len__') else 'Unknown'}")
            print("[Checkpoint] Upserting data into cache...")
            upserted_cache_count = bulk_upsert_ampeco_cache(ampeco_data)
            print(f"[Result] Cache upsert complete. Records added/updated: {upserted_cache_count}")
            print("[Checkpoint] Upserting data into database...")
            new_data_count_db, updated_data_count_db = bulk_upsert_ampeco_database(ampeco_data)
            print(f"[Result] Database upsert complete. New records: {new_data_count_db}, Updated records: {updated_data_count_db}")
            end_time = time.time()
            response = f"In database: Added {new_data_count_db} records and updated {updated_data_count_db} records. In cache: Added/Updated {upserted_cache_count} records."
            print(f"[Success] {response}")
            print(f"[Time] Total time elapsed: {round(end_time-start_time,1)} Seconds\n================ Ampeco CRON Job Complete =================\n")
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": response,
                    "time-elapsed":f"{round(end_time-start_time,1)} Seconds"
                }
            )
        except COMMON_ERRORS as e:
            import traceback
            print("[Exception] An error occurred during Ampeco CRON job execution.")
            traceback.print_exc()
            return API_ERROR_OBJECT
