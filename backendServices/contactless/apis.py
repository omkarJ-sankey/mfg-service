"""contactless APIs"""

# Date - 26/08/2022


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on APIs related
#                       to contactless.
#   Name            - Contactless APIs
#   Modified by     - Shivkumar Kumbhar
#   Modified date   - 29/03/2023


# These are all the imports that we are exporting from
# different module's from project or library.
from datetime import datetime
import threading
from decimal import Decimal
import pytz
import pandas as pd
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

# pylint:disable=import-error

from sharedServices.model_files.contactless_models import (
    ContactlessSessionsDownloadedReceipts,
)
from sharedServices.common import (
    handle_concurrent_user_login,
    array_to_string_converter,
    string_to_array_converter,
    time_formatter_for_hours,
    filter_function_for_base_configuration,
    custom_round_function,
)
from sharedServices.email_common_functions import (
    get_formated_driivz_start_and_stop_date
)
from sharedServices.constants import (
    DATE_TIME_FORMAT,
    DRIIVZ_START_ON,
    DRIIVZ_STOP_ON,
    TOTAL_ENERGY,
    LAST_3_MONTH_HISTORY_VALUE,
    LAST_6_MONTH_HISTORY_VALUE,
    NEWER_TO_OLDER,
    LAST_3_MONTH_HISTORY,
    LAST_6_MONTH_HISTORY,
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    PAYTER_TIME_STAMP,
    VALETING_TAX_RATE,
    DEFAULT_VALETING_TAX_RATE,
)
from sharedServices.email_common_functions import send_exception_email_function
from backendServices.backend_app_constants import MULTIPLE_LOGIN, UNAUTHORIZED


class SubmitDownloadedReceiptData(APIView):
    """Submit downloaded receipt data"""

    @classmethod
    def post(cls, dowload_receipt_request):
        """submit downloaded receipt"""
        try:
            if not dowload_receipt_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                dowload_receipt_request.user.id, dowload_receipt_request.auth
            ):
                return MULTIPLE_LOGIN
            driivz_transaction_id = dowload_receipt_request.data.get(
                "driivz_transaction_id", None
            )
            payter_or_rh_transaction_id = dowload_receipt_request.data.get(
                "payter_or_rh_transaction_id", None
            )
            receipt_data = dowload_receipt_request.data.get(
                "receipt_data", None
            )
            is_version_4_receipt = dowload_receipt_request.data.get(
                "is_version_4_receipt", False
            )
            if (
                driivz_transaction_id is None
                and payter_or_rh_transaction_id is None
            ) or receipt_data is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Failed to get required data to save receipt.",
                    }
                )
            receipt_already_saved = ContactlessSessionsDownloadedReceipts.objects.filter(
                user_id=dowload_receipt_request.user,
                user_account_number=(
                    dowload_receipt_request.user.user_profile.driivz_account_number
                ),
                driivz_transaction_id=driivz_transaction_id,
                payter_or_rh_transaction_id=payter_or_rh_transaction_id,
            )
            if receipt_already_saved.first():
                if is_version_4_receipt:
                    return Response(
                        {
                            "status_code": status.HTTP_200_OK,
                            "status": True,
                            "message": "Receipt already saved!",
                        }
                    )
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Provided receipt data is already added.",
                    }
                )
            save_receipt_data = None
            if is_version_4_receipt:
                save_receipt_data = ContactlessSessionsDownloadedReceipts.objects.create(
                    user_id=dowload_receipt_request.user,
                    user_account_number=(
                        dowload_receipt_request.user.user_profile.driivz_account_number
                    ),
                    driivz_transaction_id=driivz_transaction_id,
                    payter_or_rh_transaction_id=payter_or_rh_transaction_id,
                    receipt_data=array_to_string_converter([receipt_data]),
                    downloaded_date=timezone.now(),
                    is_version_4_receipt=is_version_4_receipt
                )
            else:
                save_receipt_data = ContactlessSessionsDownloadedReceipts.objects.create(
                    user_id=dowload_receipt_request.user,
                    user_account_number=(
                        dowload_receipt_request.user.user_profile.driivz_account_number
                    ),
                    driivz_transaction_id=driivz_transaction_id,
                    payter_or_rh_transaction_id=payter_or_rh_transaction_id,
                    receipt_data=array_to_string_converter([receipt_data]),
                    downloaded_date=timezone.now(),
                    session_cost=(
                        receipt_data["driivz_data"]["cost"]["total"]
                        if receipt_data["receipt_for"] == "Charging Session"
                        else None
                    ),
                    session_power_consumed=(
                        receipt_data["driivz_data"]["totalEnergy"]
                        if receipt_data["receipt_for"] == "Charging Session"
                        or receipt_data["receipt_for"] == "RH Charging Session"
                        else None
                    ),
                    session_duration=(
                        int(
                            (
                                datetime.strptime(
                                    receipt_data["driivz_data"][
                                        DRIIVZ_STOP_ON
                                    ].split(".")[0],
                                    DATE_TIME_FORMAT,
                                )
                                - datetime.strptime(
                                    receipt_data["driivz_data"][
                                        DRIIVZ_START_ON
                                    ].split(".")[0],
                                    DATE_TIME_FORMAT,
                                )
                            ).total_seconds()
                        )
                        if receipt_data["receipt_for"] == "Charging Session"
                        or receipt_data["receipt_for"] == "RH Charging Session"
                        else None
                    ),
                    session_date=(
                        timezone.localtime(
                            datetime.strptime(
                                receipt_data["driivz_data"][DRIIVZ_START_ON].split(
                                    "."
                                )[0],
                                DATE_TIME_FORMAT,
                            ).replace(tzinfo=pytz.UTC)
                        )
                        if receipt_data["receipt_for"] == "Charging Session"
                        or receipt_data["receipt_for"] == "RH Charging Session"
                        else timezone.localtime(
                            datetime.strptime(
                                receipt_data["payter_data"][
                                    PAYTER_TIME_STAMP
                                ].split(".")[0],
                                DATE_TIME_FORMAT,
                            ).replace(tzinfo=pytz.UTC)
                        )
                    ),
                    is_version_4_receipt=is_version_4_receipt
                )
            if save_receipt_data:
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "Receipt saved successfully!",
                    }
                )
            return Response(
                {
                    "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                    "status": False,
                    "message": "Failed to save receipt.",
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"'Submit downloaded receipt data' failed for user -> \
                    {dowload_receipt_request.user.id} \
                        due to exception -> {exception}"
            )
            start_caching_station_finder_data = threading.Thread(
                target=send_exception_email_function,
                args=[
                    dowload_receipt_request.build_absolute_uri(),
                    str(exception),
                ],
                daemon=True
            )
            start_caching_station_finder_data.start()
            return API_ERROR_OBJECT


def get_session_details(
    charging_data,
    charging_session_start_time=None,
    charging_session_end_time=None,
    receipt_for=None,
):
    """this function returns sessions details"""
    charging_duration = 0
    if (
        receipt_for == "Charging Session"
        or receipt_for == "RH Charging Session"
    ):
        power_consumed = charging_data["driivz_data"][TOTAL_ENERGY]
        cost_data = charging_data["driivz_data"]["cost"]
        charging_duration = time_formatter_for_hours(
            int(
                (
                    charging_session_end_time - charging_session_start_time
                ).total_seconds()
            )
        )
        total_cost_without_tax = format(
            (float(cost_data["total"]) - float(cost_data["totalTax"])),
            ".2f",
        )
        return {
            "power_consumed": power_consumed,
            "total_cost_without_tax": total_cost_without_tax,
            "total_tax_rate": cost_data["totalTaxRate"],
            "committed_amount": (
                charging_data["payter_data"]["committedAmount"]
                if "payter_data" in charging_data
                else charging_data["RH_data"]["amount"]
            ),
            "total_cost": (
                format(
                    float(
                        charging_data["payter_data"]["committedAmount"] / 100
                    ),
                    ".2f",
                )
                if "payter_data" in charging_data
                else charging_data["RH_data"]["amount"]
            ),
            "duration": charging_duration,
            "duration_in_seconds": int(
                (
                    charging_session_end_time - charging_session_start_time
                ).total_seconds()
            ),
        }
    else:
        charging_session_end_time = get_formated_driivz_start_and_stop_date(
            charging_data[DRIIVZ_STOP_ON]
        )
        charging_session_start_time = get_formated_driivz_start_and_stop_date(
            charging_data[DRIIVZ_START_ON]
        )
        power_consumed = charging_data[TOTAL_ENERGY]
        cost_data = charging_data["cost"]
        if charging_session_end_time and charging_session_start_time:
            charging_duration = time_formatter_for_hours(
                int(
                    (
                        charging_session_end_time - charging_session_start_time
                    ).total_seconds()
                )
            )

        total_cost_without_tax = format(
            (float(cost_data["total"]) - float(cost_data["totalTax"])), ".2f"
        )
        return {
            "power_consumed": power_consumed,
            "total_cost_without_tax": total_cost_without_tax,
            "total_tax_rate": cost_data["totalTaxRate"],
            "committed_amount": charging_data["committedAmount"],
            "total_cost": format(
                float(charging_data["committedAmount"] / 100), ".2f"
            ),
            "duration": charging_duration,
            "duration_in_seconds": int(
                (
                    charging_session_end_time - charging_session_start_time
                ).total_seconds()
            ),
        }


def format_contactless_receipt_object(receipt):
    """this function formats session data for contactless"""
    receipt_data = string_to_array_converter(receipt.receipt_data)[0]
    if "receipt_for" not in receipt_data:
        charging_start_time = get_formated_driivz_start_and_stop_date(
            receipt_data[DRIIVZ_START_ON]
        )
        charging_end_time = get_formated_driivz_start_and_stop_date(
            receipt_data[DRIIVZ_STOP_ON]
        )
        return {
            "id": None,
            "session_id": receipt_data["driivzTransactionId"],
            "charger": receipt_data["station"]["caption"],
            "start_time": (
                charging_start_time.date().strftime("%d/%m/%Y")
                + " "
                + charging_start_time.time().strftime("%H:%M")
            ),
            "end_time": (
                charging_end_time.date().strftime("%d/%m/%Y")
                + " "
                + charging_end_time.time().strftime("%H:%M")
            ),
            "session_details": get_session_details(
                receipt_data, charging_start_time, charging_end_time
            ),
            "station_name": (
                receipt_data["station"]["address"]["address1"].split(",")[0]
            ),
            "station_id": (
                receipt_data["list_receipt_data"]["station_id"]
                if "list_receipt_data" in receipt_data
                and "station_id" in receipt_data["list_receipt_data"]
                else ""
            ),
            "address": receipt_data["list_receipt_data"]["address"][
                "address1"
            ],
            "payment_details": {
                "card": receipt_data["extra-TXN-MASKED-PAN"],
                "brand": receipt_data["list_receipt_data"]["card_brand"],
                "type": f"CONTACTLESS - {receipt_data['paymentType']}",
                "currency": receipt_data["cost"]["currency"],
            },
            "payter_or_rh_unique_id": (
                receipt_data["list_receipt_data"]["payter_unique_id"]
                if "payter_unique_id" in receipt_data["list_receipt_data"]
                else receipt_data["list_receipt_data"][
                    "payter_or_rh_unique_id"
                ]
            ),
            "driivz_transaction_id": receipt_data["list_receipt_data"][
                "drrivz_transaction_id"
            ],
            "receipt_for": "Charging Session",
        }
    elif receipt_data["receipt_for"] in [
        "Charging Session",
        "RH Charging Session",
    ]:
        charging_start_time = get_formated_driivz_start_and_stop_date(
            receipt_data["driivz_data"][DRIIVZ_START_ON]
        )
        charging_end_time = get_formated_driivz_start_and_stop_date(
            receipt_data["driivz_data"][DRIIVZ_STOP_ON]
        )
        return {
            "id": None,
            "session_id": receipt_data["driivz_data"]["transactionId"],
            "charger": receipt_data["driivz_data"]["station"]["caption"],
            "start_time": (
                charging_start_time.date().strftime("%d/%m/%Y")
                + " "
                + charging_start_time.time().strftime("%H:%M")
            ),
            "end_time": (
                charging_end_time.date().strftime("%d/%m/%Y")
                + " "
                + charging_end_time.time().strftime("%H:%M")
            ),
            "session_details": get_session_details(
                receipt_data,
                charging_start_time,
                charging_end_time,
                receipt_data["receipt_for"],
            ),
            "station_name": (
                receipt_data["driivz_data"]["station"]["address"][
                    "address1"
                ].split(",")[0]
            ),
            "station_id": (
                receipt_data["station_id"]
                if "station_id" in receipt_data
                else ""
            ),
            "address": receipt_data["driivz_data"]["station"]["address"][
                "address1"
            ],
            "payment_details": {
                "card": (
                    receipt_data["payter_data"]["extra-TXN-MASKED-PAN"]
                    if "payter_data" in receipt_data
                    else receipt_data["RH_data"]["maskedPan"]
                ),
                "brand": (
                    receipt_data["payter_data"]["brandName"]
                    if "payter_data" in receipt_data
                    else receipt_data["RH_data"]["cardBrand"]
                ),
                "type": (
                    f"CONTACTLESS - {receipt_data['payter_data']['paymentType']}"
                    if "payter_data" in receipt_data
                    else "CONTACTLESS - EMV"
                ),
                "currency": receipt_data["driivz_data"]["cost"]["currency"],
            },
            "payter_or_rh_unique_id": (
                receipt_data["payter_data"]["id"]
                if "payter_data" in receipt_data
                else receipt_data["RH_data"]["requestUUID"]
            ),
            "driivz_transaction_id": receipt_data["driivz_data"][
                "transactionId"
            ],
            "receipt_for": (
                "Charging Session"
                if receipt_data["receipt_for"] == "Charging Session"
                else "RH Charging Session"
            ),
        }
    valeting_tax_rate = filter_function_for_base_configuration(
        VALETING_TAX_RATE, DEFAULT_VALETING_TAX_RATE
    )
    payter_timestamp = datetime.strptime(
        receipt_data["payter_data"][PAYTER_TIME_STAMP].split(".")[0],
        DATE_TIME_FORMAT,
    )
    return {
        "id": None,
        "payter_timestamp": (
            payter_timestamp.date().strftime("%d/%m/%Y")
            + " "
            + payter_timestamp.time().strftime("%H:%M")
        ),
        "station_name": receipt_data["station_name"],
        "station_id": (
            receipt_data["station_id"] if "station_id" in receipt_data else ""
        ),
        "payment_details": {
            "card": receipt_data["payter_data"]["extra-TXN-MASKED-PAN"],
            "brand": receipt_data["payter_data"]["brandName"],
            "type": f"CONTACTLESS - {receipt_data['payter_data']['paymentType']}",
            "currency": receipt_data["payter_data"]["currency"],
        },
        "total_cost_with_tax": receipt_data["payter_data"]["committedAmount"],
        "payter_unique_id": receipt_data["payter_data"]["id"],
        "payter_transaction_id": receipt_data["payter_data"]["transactionId"],
        "tax_rate": valeting_tax_rate,
        "description_of_service": "Valeting",
        "receipt_for": "Valeting",
    }


class ListDownloadedList(APIView):
    """downloaded receipt list"""

    def get(self, dowload_receipt_list_request):
        """downloaded receipt list"""
        try:
            if not dowload_receipt_list_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                dowload_receipt_list_request.user.id,
                dowload_receipt_list_request.auth,
            ):
                return MULTIPLE_LOGIN

            ordering_type = self.request.query_params.get(
                "ordering_type", NEWER_TO_OLDER
            )
            history_between = self.request.query_params.get(
                "history_between", None
            )
            user_sessions = (
                ContactlessSessionsDownloadedReceipts.objects.filter(
                    user_id=(dowload_receipt_list_request.user),
                    is_version_4_receipt=False
                ).order_by(
                    "-session_date"
                    if ordering_type == NEWER_TO_OLDER
                    else "session_date"
                )
            )
            if history_between and history_between == LAST_3_MONTH_HISTORY:
                date_filter = timezone.localtime(
                    timezone.now()
                ) - pd.DateOffset(months=LAST_3_MONTH_HISTORY_VALUE)
                user_sessions = user_sessions.filter(
                    session_date__gte=date_filter
                )

            if history_between and history_between == LAST_6_MONTH_HISTORY:
                date_filter = timezone.localtime(
                    timezone.now()
                ) - pd.DateOffset(months=LAST_6_MONTH_HISTORY_VALUE)
                user_sessions = user_sessions.filter(
                    session_date__gte=date_filter
                )
            data = [
                format_contactless_receipt_object(receipt)
                for receipt in user_sessions
            ]
            total_power_consumed = 0
            total_amount = 0
            total_session_duration = 0
            for session in data:
                if (
                    session["receipt_for"] == "Charging Session"
                    or session["receipt_for"] == "RH Charging Session"
                ):
                    session_details = session["session_details"]
                    total_power_consumed += Decimal(
                        str(session_details["power_consumed"])
                    )
                    total_amount += Decimal(str(session_details["total_cost"]))
                    total_session_duration += session_details[
                        "duration_in_seconds"
                    ]
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Fetched saved receipt successfully.",
                    "data": {
                        "sessions": data,
                        "overal_sessions_data": {
                            "total_power_consumed": custom_round_function(
                                total_power_consumed, 2
                            ),
                            "total_amout": custom_round_function(
                                total_amount, 2
                            ),
                            "total_session_duration": time_formatter_for_hours(
                                total_session_duration
                            ),
                        },
                    },
                }
            )

        except COMMON_ERRORS as exception:
            print(
                f"'downloaded receipt list' failed for user -> \
                    {dowload_receipt_list_request.user.id} \
                        due to exception -> {exception}"
            )
            start_caching_station_finder_data = threading.Thread(
                target=send_exception_email_function,
                args=[
                    dowload_receipt_list_request.build_absolute_uri(),
                    str(exception),
                ],
                daemon=True
            )
            start_caching_station_finder_data.start()
            return API_ERROR_OBJECT


class GetReceiptSavedStatus(APIView):
    """downloaded receipt list"""

    def get(self, receipt_saved_status_request):
        """downloaded receipt list"""
        try:
            if not receipt_saved_status_request.auth:
                return UNAUTHORIZED
            if not handle_concurrent_user_login(
                receipt_saved_status_request.user.id,
                receipt_saved_status_request.auth,
            ):
                return MULTIPLE_LOGIN
            driivz_transaction_id = self.request.query_params.get(
                "driivz_transaction_id", None
            )
            payter_or_rh_unique_id = self.request.query_params.get(
                "payter_or_rh_unique_id", None
            )
            if not payter_or_rh_unique_id:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Payter or RH unique id not found",
                    }
                )
            return Response(
                {
                    "is_saved": (
                        True
                        if ContactlessSessionsDownloadedReceipts.objects.filter(
                            user_id=receipt_saved_status_request.user,
                            user_account_number=(
                                receipt_saved_status_request.user.user_profile.driivz_account_number
                            ),
                            driivz_transaction_id=(
                                str(driivz_transaction_id)
                                if driivz_transaction_id
                                else None
                            ),
                            payter_or_rh_transaction_id=str(
                                payter_or_rh_unique_id
                            ),
                        )
                        else False
                    ),
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"'Receipt saved status Api' failed for user -> \
                    {receipt_saved_status_request.user.id} \
                        due to exception -> {exception}"
            )
            start_caching_station_finder_data = threading.Thread(
                target=send_exception_email_function,
                args=[
                    receipt_saved_status_request.build_absolute_uri(),
                    str(exception),
                ],
                daemon=True
            )
            start_caching_station_finder_data.start()
            return API_ERROR_OBJECT
