"""history apis"""

# Date - 11/11/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on
#                       APIs related to trip and charging session histories.
#   Name            - History APIs
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 29/05/2025


# These are all the imports that we are exporting from
# different module's from project or library.
import json
from datetime import datetime
from dateutil import parser
from decimal import Decimal
import pytz
from rest_framework.views import APIView
from rest_framework import permissions, status
from rest_framework.response import Response
import pandas as pd
from django.utils import timezone
from django.db.models import Q
import traceback
from django.forms.models import model_to_dict
from django.db.models import Q, Case, When, F,OuterRef, Subquery
from sharedServices.model_files.config_models import BaseConfigurations


# pylint:disable=import-error
from sharedServices.common import (
    string_to_array_converter,
    time_formatter_for_hours,
    handle_concurrent_user_login,
    custom_round_function,
    get_data_from_cache,
)
from sharedServices.email_common_functions import (
    get_formated_driivz_start_and_stop_date
)
from sharedServices.constants import (
    LAST_3_MONTH_HISTORY_VALUE,
    LAST_6_MONTH_HISTORY_VALUE,
    NEWER_TO_OLDER,
    LAST_3_MONTH_HISTORY,
    LAST_6_MONTH_HISTORY,
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    OCPI_LOCATIONS_KEY,
    DATE_TIME_FORMAT,
    VAT_PERCENTAGE_KEY
)
from sharedServices.model_files.trip_models import Trips
from sharedServices.model_files.app_user_models import Profile
from sharedServices.model_files.charging_session_models import ChargingSession
from sharedServices.model_files.transaction_models import Transactions
from sharedServices.model_files.station_models import Stations, ChargePoint
from sharedServices.model_files.contactless_models import (
    ContactlessSessionsDownloadedReceipts,
)
from sharedServices.model_files.ocpi_locations_models import OCPIConnector,OCPILocation
from sharedServices.model_files.ocpi_credentials_models import OCPICredentials
from sharedServices.model_files.ocpi_charge_detail_records_models import OCPIChargeDetailRecords
from sharedServices.ocpi_common_functions import (
    get_tariff_amount,
    get_cdr_cost
)
from sharedServices.constants import (
    DRIIVZ_START_ON,
    DRIIVZ_STOP_ON,
    KWH,
    SWARCO_END_TIME,
    SWARCO_START_TIME,
    TOTAL_ENERGY,
    SWARCO,
    DRIIVZ,
    CHARGING_SESSION,
    YES
)

from backendServices.backend_app_constants import (
    MULTIPLE_LOGIN,
    TRIP_ID_NOT_PROVIDED,
    TRIP_NOT_FOUND,
    UNAUTHORIZED,
)
from .serializers import (
    ChargingSessionDetailsHistorySerializer,
    ChargingSessionHistorySerializer,
    TripHistorySerializer,
    TripHistoryDetailsSerializer,
    get_payment_details_for_session
)

from sharedServices.model_files.ocpi_sessions_models import OCPISessions
from sharedServices.model_files.station_models import StationConnector


DRIIVZ_DATE_TIME_FORMAT = "%d/%m/%Y %H:%M"

class TripHistoryAPI(APIView):
    """trip history viewset"""

    # Permission classes are used to restrict the user
    permission_classes = [permissions.IsAuthenticated]

    def get(self, trip_history):
        """get method to fetch user  trip history"""
        try:
            print("Inside TripHistoryAPI")
            if not trip_history.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                trip_history.user.id, trip_history.auth
            ):
                return MULTIPLE_LOGIN
            ordering_type = self.request.query_params.get(
                "ordering_type", NEWER_TO_OLDER
            )
            history_between = self.request.query_params.get(
                "history_between", LAST_3_MONTH_HISTORY
            )

            user_trips = Trips.objects.filter(user_id=trip_history.user)
            if history_between == LAST_3_MONTH_HISTORY:
                date_filter = timezone.localtime(
                    timezone.now()
                ) - pd.DateOffset(months=LAST_3_MONTH_HISTORY_VALUE)
                user_trips = user_trips.filter(created_date__gte=date_filter)

            if history_between == LAST_6_MONTH_HISTORY:
                date_filter = timezone.localtime(
                    timezone.now()
                ) - pd.DateOffset(months=LAST_6_MONTH_HISTORY_VALUE)
                user_trips = user_trips.filter(created_date__gte=date_filter)

            if ordering_type == NEWER_TO_OLDER:
                user_trips = user_trips.order_by("-created_date")
            serializer = TripHistorySerializer(user_trips, many=True)
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Fetched trip history data.",
                    "data": serializer.data,
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Trip history api failed for user -> \
                    {trip_history.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


class TripHistoryDetailAPI(APIView):
    """trip history details  viewset"""

    # Permission classes are used to restrict the user
    permission_classes = [permissions.IsAuthenticated]

    def get(self, trip_history_detail):
        """get method to fetch user  trip history details"""
        try:
            print("Inside TripHistoryDetailAPI")
            if not trip_history_detail.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                trip_history_detail.user.id, trip_history_detail.auth
            ):
                return MULTIPLE_LOGIN
            user = trip_history_detail.user
            trip_id_history = self.request.query_params.get("trip_id", False)
            if (
                trip_id_history is False
                or not str(trip_id_history).isnumeric()
            ):
                return f"{TRIP_ID_NOT_PROVIDED} or is invalid"
            trip_id_history = int(trip_id_history)
            trips_history = Trips.objects.filter(
                id=trip_id_history, user_id=user
            )
            if trips_history.first() is None:
                return TRIP_NOT_FOUND
            trip_history_serializer = TripHistoryDetailsSerializer(
                trips_history, many=True
            )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Fetched trip history details.",
                    "data": trip_history_serializer.data,
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Trip history details api failed for user -> \
                    {trip_history_detail.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


class ChargingSessionHistoryAPI(APIView):
    """charging session history  viewset"""

    # Permission classes are used to restrict the user
    permission_classes = [permissions.IsAuthenticated]

    def get(self, charging_session):
        """get method to fetch user charging sessions history"""
        try:
            print(f"Inside ChargingSessionHistoryAPI")
            if not charging_session.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                charging_session.user.id, charging_session.auth
            ):
                return MULTIPLE_LOGIN

            ordering_type = self.request.query_params.get(
                "ordering_type", NEWER_TO_OLDER
            )
            history_between = self.request.query_params.get(
                "history_between", None
            )
            user_transactions = Transactions.objects.filter(
                customer_id=charging_session.user.customer_id,
                payment_for=CHARGING_SESSION,
            )
            session_payment_data = {}
            for transation in user_transactions:
                session_db_id = transation.payment_for_reference_id
                payment_response = string_to_array_converter(
                    transation.payment_response
                )[0]
                if (
                    payment_response["payment"]["card_details"]["card"][
                        "card_brand"
                    ]
                    != "SQUARE_GIFT_CARD"
                    and payment_response["payment"]["status"] == "COMPLETED"
                ):
                    if (
                        str(transation.payment_for_reference_id)
                        in session_payment_data
                    ):
                        session_payment_data[f"{session_db_id}"].append(
                            payment_response
                        )
                    else:
                        session_payment_data[f"{session_db_id}"] = [
                            payment_response
                        ]

            user_charging_sessions = ChargingSession.objects.filter(
                ~Q(charging_data=None)
                & ~Q(payment_response=None)
                & ~Q(chargepoint_id=None)
                & ~Q(station_id=None)
                & ~Q(connector_id=None),
                user_id=charging_session.user,
                paid_status="paid",
            )
            if history_between and history_between == LAST_3_MONTH_HISTORY:
                date_filter = timezone.localtime(
                    timezone.now()
                ) - pd.DateOffset(months=LAST_3_MONTH_HISTORY_VALUE)
                user_charging_sessions = user_charging_sessions.filter(
                    start_time__gte=date_filter
                )

            if history_between and history_between == LAST_6_MONTH_HISTORY:
                date_filter = timezone.localtime(
                    timezone.now()
                ) - pd.DateOffset(months=LAST_6_MONTH_HISTORY_VALUE)
                user_charging_sessions = user_charging_sessions.filter(
                    start_time__gte=date_filter
                )

            total_power_consumed = 0
            total_amout = 0
            total_session_duration = 0
            user_charging_sessions = sorted(
                user_charging_sessions,
                key=lambda x: (
                    get_formated_driivz_start_and_stop_date(
                        json.loads(x.charging_data)[0][DRIIVZ_START_ON]
                    )
                ),
                reverse=ordering_type == NEWER_TO_OLDER,
            )
            for session in user_charging_sessions:
                charging_data_helper = string_to_array_converter(
                    session.charging_data
                )[0]
                if (
                    session.back_office == SWARCO
                    and KWH in charging_data_helper
                ):
                    charging_session_end_time = datetime.strptime(
                        charging_data_helper[SWARCO_END_TIME],
                        "%Y-%m-%dT%H:%M:%S",
                    )
                    charging_session_start_time = datetime.strptime(
                        charging_data_helper[SWARCO_START_TIME],
                        "%Y-%m-%dT%H:%M:%S",
                    )
                    total_power_consumed += Decimal(
                        str(charging_data_helper[KWH])
                    )

                if (
                    session.back_office == DRIIVZ
                    and TOTAL_ENERGY in charging_data_helper
                ):
                    charging_session_start_time = get_formated_driivz_start_and_stop_date(
                        charging_data_helper[DRIIVZ_START_ON]
                    )
                    charging_session_end_time = get_formated_driivz_start_and_stop_date(
                        charging_data_helper[DRIIVZ_STOP_ON]
                    )
                    total_power_consumed += Decimal(
                        str(charging_data_helper[TOTAL_ENERGY])
                    )
                if session.total_cost:
                    total_amout += Decimal(str(session.total_cost))
                total_session_duration += int(
                    (
                        charging_session_end_time - charging_session_start_time
                    ).total_seconds()
                )
            total_session_duration = time_formatter_for_hours(
                total_session_duration
            )
            serializer = ChargingSessionHistorySerializer(
                user_charging_sessions,
                many=True,
                context={"session_payment_data": session_payment_data},
            )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Fetched charging session history data.",
                    "data": {
                        "user_sessions": [
                            {
                                **session_data,
                                **{
                                    "payter_or_rh_unique_id": None,
                                    "driivz_transaction_id": None,
                                    "session_tariff": None,
                                },
                            }
                            for session_data in serializer.data
                        ],
                        "overal_sessions_data": {
                            "total_power_consumed": custom_round_function(
                                total_power_consumed, 2
                            ),
                            "total_amout": custom_round_function(
                                int(total_amout) / 100, 2
                            ),
                            "total_session_duration": total_session_duration,
                        },
                    },
                }
            )

        except COMMON_ERRORS as exception:
            print(
                f"Charging session history api failed for user -> \
                    {charging_session.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


class ReceiptsListAPI(APIView):
    """Receipts list API"""

    # Permission classes are used to restrict the user
    permission_classes = [permissions.IsAuthenticated]

    def get(self, receipts_list_request):
        """get method to fetch user charging sessions history"""
        try:
            print(f"Inside ReceiptsListAPI")
            if not receipts_list_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                receipts_list_request.user.id, receipts_list_request.auth
            ):
                return MULTIPLE_LOGIN
            stations_data = {
                station.id: (
                    station.driivz_display_name
                    if station.driivz_display_name else
                    station.site_title
                )
                for station in Stations.objects.all().only(
                    'id', 'site_title', 'driivz_display_name'
                )
            }
            
            def transaction_data_formatter(transaction_data):
                """this function formats the transaction data"""
                charging_data = string_to_array_converter(transaction_data["charging_data"])[0]
                remaining_cost = 0
                if transaction_data["preauth_status"] == 'collected':
                    user_due_data = Profile.objects.filter(
                        user_id=transaction_data["user_id_id"]
                    ).only(
                        'have_amount_due', 'due_amount_data'
                    ).first()
                    if user_due_data and user_due_data.have_amount_due == YES:
                        user_due_amount_data = string_to_array_converter(
                            user_due_data.due_amount_data
                        )
                        for session_data in user_due_amount_data:
                            if str(transaction_data["id"]) == str(session_data["reference_id"]):
                                remaining_cost = int(session_data["amount"]) / 100
                session_date = get_formated_driivz_start_and_stop_date(
                    charging_data[DRIIVZ_START_ON],
                    provide_local_time_dates=True
                )
                session_date_updated = get_formated_driivz_start_and_stop_date(
                    charging_data[DRIIVZ_START_ON]
                )
                return {
                    "id": transaction_data["id"],
                    "station_name": (
                        stations_data[transaction_data['station_id']]
                        if transaction_data['station_id'] in stations_data else
                        'NA'
                    ),
                    "date": session_date,
                    "created_date": session_date_updated.strftime(DRIIVZ_DATE_TIME_FORMAT),
                    "total_energy": format(charging_data[TOTAL_ENERGY], ".2f"),
                    "total_cost": charging_data["cost"]["total"],
                    "remaining_cost": remaining_cost,
                    "paid_status": transaction_data["paid_status"],
                    "app_receipt": True,
                    "is_ocpi_receipt":False
                }
            
            def ocpi_transaction_data_formatter(transaction_data):
                """this function formats the transaction data"""

                remaining_cost = 0
                
                location = OCPILocation.objects.filter(id = transaction_data['location_id']).first()
   
                user_due_data = Profile.objects.filter(
                    user_id=transaction_data["user_id_id"]
                ).only(
                    'have_amount_due', 'due_amount_data'
                ).first()
                if user_due_data and user_due_data.have_amount_due == YES:
                    user_due_amount_data = string_to_array_converter(
                        user_due_data.due_amount_data
                    )
                    for session_data in user_due_amount_data:
                        if str(transaction_data["id"]) == str(session_data["reference_id"]):
                            remaining_cost = int(session_data["amount"]) / 100
                session_date = get_formated_driivz_start_and_stop_date(
                    transaction_data["start_datetime"],
                    provide_local_time_dates=True,
                    ocpi_format = True
                )

                station = transaction_data['station_id']
                total_cost_incl,_,energy = get_cdr_cost(transaction_data["id"])
                station_name = location.name if location else station.station_name
                return {
                    "id": transaction_data["id"],
                    "station_name": (
                        station_name
                        if station_name else
                        'NA'
                    ),
                    "date": session_date,
                    "created_date": datetime.strftime(timezone.localtime(transaction_data["start_datetime"]),DRIIVZ_DATE_TIME_FORMAT),
                    "total_energy": energy if energy is not None else transaction_data['kwh'],
                    #handle corrupt cdr
                    "total_cost": total_cost_incl if total_cost_incl != 0 else transaction_data['total_cost_incl'] if transaction_data['total_cost_incl'] is not None else 0,
                    "remaining_cost": remaining_cost,
                    "paid_status": transaction_data["paid_status"],
                    "app_receipt": True,
                    "is_ocpi_receipt":True
                }

            def contactless_transaction_data_formatter(transaction_data):
                """this function formats the transaction data"""
                receipt_data = string_to_array_converter(
                    transaction_data["receipt_data"]
                )
                if transaction_data["is_version_4_receipt"]:
                    receipt_data = receipt_data[0]
                    session_date = datetime.strptime(
                        receipt_data["startTime"],
                        DRIIVZ_DATE_TIME_FORMAT
                    ).replace(tzinfo=pytz.UTC)
                    return {
                        "id": transaction_data["id"],
                        "station_name": receipt_data["stationName"],
                        "date": session_date,
                        "total_energy": format(receipt_data["energyUsed"], ".2f"),
                        "total_cost": receipt_data["amountPaid"],
                        "app_receipt": False,
                        "is_ocpi_receipt":False
                    }
                driivz_data = (
                    receipt_data[0]["driivz_data"]
                    if "driivz_data" in receipt_data[0] else
                    receipt_data[0]
                )
                session_date = get_formated_driivz_start_and_stop_date(
                    driivz_data[DRIIVZ_START_ON],
                    provide_local_time_dates=True
                )
                return {
                    "id": transaction_data["id"],
                    "station_name": (
                        stations_data[receipt_data['station_db_id']]
                        if 'station_db_id' in receipt_data else
                        ''
                    ),
                    "date": session_date,
                    "total_energy": format(driivz_data[TOTAL_ENERGY], ".2f"),
                    "total_cost": driivz_data["cost"]["total"],
                    "app_receipt": False,
                    "is_ocpi_receipt":False
                }
            transactions = sorted(
                [
                    transaction_data_formatter(user_charging_session)
                    for user_charging_session in ChargingSession.objects.filter(
                        ~Q(charging_data=None)
                        & ~Q(chargepoint_id=None)
                        & ~Q(paid_status='On Hold')
                        & ~Q(station_id=None)
                        & ~Q(connector_id=None)
                        & ~Q(total_cost="0"),
                        charging_data__icontains="BILLED",
                        user_id=receipts_list_request.user,
                        session_status="completed",
                    ).only(
                        'id',
                        'charging_data',
                        'station_id',
                        'paid_status',
                        'user_id_id',
                        'preauth_status'
                    ).values(
                        'id',
                        'charging_data',
                        'station_id',
                        'paid_status',
                        'user_id_id',
                        'preauth_status'
                    )
                ] + [
                    contactless_transaction_data_formatter(
                        contactless_session
                    )
                    for contactless_session in ContactlessSessionsDownloadedReceipts.objects.filter(
                        Q(
                            receipt_data__icontains='Charging Session'
                        ) |
                        Q(
                            receipt_data__icontains='RH Charging Session'
                        ) |
                        Q(
                            is_version_4_receipt=True
                        ),
                        user_id=receipts_list_request.user
                    ).only(
                        'id', 'receipt_data', 'is_version_4_receipt'
                    ).values('id', 'receipt_data', 'is_version_4_receipt')
                ] + [
                    ocpi_transaction_data_formatter(user_charging_session)
                    for user_charging_session in OCPISessions.objects.filter(
                        ~Q(charging_data=None)
                        & ~Q(paid_status__in=['On Hold'])
                        & ~Q(location_id=None)
                        & ~Q(connector_id=None)
                        & ~Q(total_cost_incl="0"),
                        user_id=receipts_list_request.user,
                        session_status="completed",
                    ).only(
                        'id',
                        'charging_data',
                        'paid_status',
                        'location_id',
                        'user_id_id',
                        'preauth_status',
                        'start_datetime',
                        'back_office',
                        'location_id',
                        'station_id',
                        'kwh',
                        'total_cost_incl'
                    ).values(
                        'id',
                        'charging_data',
                        'paid_status',
                        'location_id',
                        'user_id_id',
                        'preauth_status',
                        'start_datetime',
                        'back_office',
                        'location_id',
                        'station_id',
                        'kwh',
                        'total_cost_incl'
                    )
                ],
                key=lambda x: x["date"],
                reverse=True,
            )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Fetched receipts successfully!",
                    "data": [
                        {
                            **transaction,
                            'date': transaction['date'].strftime(
                                DRIIVZ_DATE_TIME_FORMAT
                            )
                        }
                        for transaction in transactions
                    ]
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Charging session history api failed for user -> \
                    {receipts_list_request.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


def get_ocpi_session_details_v4(session):
    """this function returns session details"""

    total_cost_incl_vat, total_cost_excl_vat, total_energy = get_cdr_cost(session.id)
    # total_cost_incl_vat = total_cost_incl_vat if total_cost_incl_vat is not None and total_cost_incl_vat == 0 else session.total_cost_incl
    # total_cost_excl_vat = total_cost_excl_vat if total_cost_excl_vat is not None and total_cost_excl_vat == 0 else session.total_cost_excl

    payment_data = string_to_array_converter(session.payment_response)[0]
    charging_session_start_time = get_formated_driivz_start_and_stop_date(
        session.start_datetime,
        ocpi_format = True
    )
    charging_session_end_time = get_formated_driivz_start_and_stop_date(
        session.end_datetime,
        ocpi_format = True
    )
    payment_completed_at_time = get_formated_driivz_start_and_stop_date(
        (int(parser.parse(str(session.payment_completed_at)).timestamp()))
    ) if session.payment_completed_at else False
    charging_duration = int(
        (
            datetime.strptime(charging_session_end_time,DATE_TIME_FORMAT) - datetime.strptime(charging_session_start_time,DATE_TIME_FORMAT)
        ).total_seconds()
    )
    
    # cost_data = session.charging_data[0]["cost"]
    # cost_data = session.total_cost_incl
    # total_cost = 0
    tax_amount = 0
    total_cost_without_tax = 0
    tax_rate = 0
    card_brand = "NA"
    card_last_four = "NA"
    session_id = session.id
    session_payment_data = {
        f"{session_id}": []
    }
    total_cost = session.total_cost_incl
    tax_amount = total_cost_incl_vat - total_cost_excl_vat#Decimal(total_cost_incl_vat - total_cost_excl_vat)
    # tax_rate = Decimal(str(round(
    #     (cost_data["totalTax"] /(cost_data["total"] - cost_data["totalTax"])) * 100
    # ))) if cost_data["total"] > 0 else 0
    tax_rate = Decimal(str(round(
        (tax_amount/total_cost_excl_vat) * 100)
        )) if total_cost_excl_vat > 0 else total_cost_incl_vat
    
    tariff_ids = OCPIConnector.objects.filter(id = session.connector_id_id)
    tariff_amount = get_tariff_amount(tariff_ids.first().tariff_ids,session.country_code,session.party_id, timezone.localtime(session.start_datetime))
    total_cost_without_tax = total_cost_excl_vat
    if "payment" in payment_data:
        card_brand = payment_data["payment"]["card_details"]["card"]["card_brand"]
        card_last_four = payment_data["payment"]["card_details"]["card"]["last_4"]
    user_transactions = Transactions.objects.filter(
        ~Q(payment_response = None),
        payment_for_reference_id=session_id,
        is_ocpi_session = True
    )
    for transation in user_transactions:
        payment_response = string_to_array_converter(
            transation.payment_response
        )[0]
        if (
            payment_response["payment"]["card_details"]["card"][
                "card_brand"
            ]
            != "SQUARE_GIFT_CARD"
            and payment_response["payment"]["status"] == "COMPLETED"
        ):
            session_payment_data[f"{session_id}"].append(
                payment_response
            )
    remaining_cost = 0
    # if session.preauth_status == 'collected':
    user_due_data = Profile.objects.filter(
        user=session.user_id
    ).only(
        'have_amount_due', 'due_amount_data'
    ).first()
    if user_due_data and user_due_data.have_amount_due == YES:
        user_due_amount_data = string_to_array_converter(
            user_due_data.due_amount_data
        )
        for session_data in user_due_amount_data:
            if str(session.id) == str(session_data["reference_id"]):
                remaining_cost = int(session_data["amount"]) / 100
    elif session.paid_status == "unpaid":
        remaining_cost = total_cost
    co_ordinates = session.location_id.coordinates
    latitude = float(co_ordinates['latitude'])
    longitude = float(co_ordinates['longitude'])
    
    end_dt_utc = datetime.strptime(charging_session_end_time, '%Y-%m-%dT%H:%M:%S')
    end_dt_utc = end_dt_utc.replace(tzinfo=pytz.UTC)
    start_dt_utc = datetime.strptime(charging_session_start_time, '%Y-%m-%dT%H:%M:%S')
    start_dt_utc = start_dt_utc.replace(tzinfo=pytz.UTC)
    return {
        "id": session.id,
        "is_ocpi_receipt":True,
        "vatPercentage":session.vat_percentage,
        "amountPaid": format(total_cost if total_cost_incl_vat == 0 else total_cost_incl_vat, ".2f"),
        "remainingCost": remaining_cost,
        "amountWithoutTax": format(total_cost_without_tax if total_cost_excl_vat == 0 else total_cost_excl_vat, ".2f"),
        "taxRate": tariff_amount if tariff_amount is not None else tax_rate,
        "taxAmount": format(tax_amount, ".4f"),
        "duration": charging_duration,
        "cardBrand": card_brand,
        "cardLastFour": card_last_four,
        "chargerId": session.chargepoint_id.charger_point_name,
        "endTime": timezone.localtime(end_dt_utc).strftime('%d/%m/%Y %H:%M'),
        "energyUsed": total_energy if total_energy > 0 else session.kwh,
        "latitude": latitude,
        "longitude": longitude,
        "paymentDate": (
            payment_completed_at_time.strftime(DRIIVZ_DATE_TIME_FORMAT)
            if session.payment_completed_at else
            "NA"
        ),
        "sessionId": string_to_array_converter(session.charging_data)[0][
            "transactionId" if "transactionId" in string_to_array_converter(session.charging_data)[0] else session.id
        ] if string_to_array_converter(session.charging_data)[0] is not None else session.id,
        "startTime": timezone.localtime(start_dt_utc).strftime('%d/%m/%Y %H:%M'),
        "stationAddress": session.location_id.get_full_address(),
        "stationName": session.location_id.name if session.location_id.name is not None else session.station_id.station_name,
        'paidStatus': session.paid_status,
        "appReceipt": True,
        "paymentDetails": get_payment_details_for_session(
            session,
            session_payment_data,
            v4_api_request=True,
            is_ocpi_session = True
        ),
        'tariffAmount': session.session_tariff,
        'vatPercentage': get_data_from_cache(VAT_PERCENTAGE_KEY)
    }



def get_session_details_according_to_back_office_v4(session):
    """this function returns session details"""
    charging_data = string_to_array_converter(session.charging_data)[0]
    if session.payment_response:
        payment_data = string_to_array_converter(session.payment_response)[0]
        charging_session_start_time = get_formated_driivz_start_and_stop_date(
            charging_data[DRIIVZ_START_ON]
        )
        charging_session_end_time = get_formated_driivz_start_and_stop_date(
            charging_data[DRIIVZ_STOP_ON]
        )
        payment_completed_at_time = get_formated_driivz_start_and_stop_date(
            (int(parser.parse(str(session.payment_completed_at)).timestamp()))
        ) if session.payment_completed_at else False
        charging_duration = int(
            (
                charging_session_end_time - charging_session_start_time
            ).total_seconds()
        )
        cost_data = charging_data["cost"]
        total_cost = 0
        tax_amount = 0
        total_cost_without_tax = 0
        tax_rate = 0
        card_brand = "NA"
        card_last_four = "NA"
        session_id = session.id
        session_payment_data = {
            f"{session_id}": []
        }
        total_cost = cost_data["total"]
        tax_rate = Decimal(str(round(
            (cost_data["totalTax"] /(cost_data["total"] - cost_data["totalTax"])) * 100
        ))) if cost_data["total"] > 0 else 0
        tax_amount = cost_data["totalTax"]
        total_cost_without_tax = total_cost - tax_amount
        if "payment" in payment_data:
            card_brand = payment_data["payment"]["card_details"]["card"]["card_brand"]
            card_last_four = payment_data["payment"]["card_details"]["card"]["last_4"]
        user_transactions = Transactions.objects.filter(
            payment_for_reference_id=session_id,
            is_ocpi_session = False
        )
        # for transation in user_transactions:
        payment_response = string_to_array_converter(
            session.payment_response
        )[0]
        if (
            payment_response["payment"]["card_details"]["card"][
                "card_brand"
            ]
            != "SQUARE_GIFT_CARD"
            and payment_response["payment"]["status"] == "COMPLETED"
        ):
            session_payment_data[f"{session_id}"].append(
                payment_response
            )
        remaining_cost = 0
        if session.preauth_status == 'collected':
            user_due_data = Profile.objects.filter(
                user=session.user_id
            ).only(
                'have_amount_due', 'due_amount_data'
            ).first()
            if user_due_data and user_due_data.have_amount_due == YES:
                user_due_amount_data = string_to_array_converter(
                    user_due_data.due_amount_data
                )
                for session_data in user_due_amount_data:
                    if str(session.id) == str(session_data["reference_id"]):
                        remaining_cost = int(session_data["amount"]) / 100
        elif session.paid_status == "unpaid":
            remaining_cost = total_cost
        return {
            "id": session.id,
            "is_ocpi_receipt":False,
            "amountPaid": format(total_cost, ".2f"),
            "remainingCost": remaining_cost,
            "amountWithoutTax": format(total_cost_without_tax, ".2f"),
            "taxRate": tax_rate,
            "taxAmount": format(tax_amount, ".2f"),
            "duration": charging_duration,
            "cardBrand": card_brand,
            "cardLastFour": card_last_four,
            "chargerId": session.chargepoint_id_id,
            "endTime": charging_session_end_time.strftime(DRIIVZ_DATE_TIME_FORMAT),
            "energyUsed": charging_data[TOTAL_ENERGY],
            "latitude": session.station_id.latitude,
            "longitude": session.station_id.longitude,
            "paymentDate": (
                payment_completed_at_time.strftime(DRIIVZ_DATE_TIME_FORMAT)
                if session.payment_completed_at else
                "NA"
            ),
            "sessionId": charging_data[
                "transactionId" if "transactionId" in charging_data else "id"
            ],
            "startTime": charging_session_start_time.strftime(DRIIVZ_DATE_TIME_FORMAT),
            "stationAddress": session.station_id.get_full_address(),
            "stationName": (
                session.station_id.driivz_display_name
                if session.station_id.driivz_display_name else
                session.station_id.site_title
            ),
            'paidStatus': session.paid_status,
            "appReceipt": True,
            "paymentDetails": get_payment_details_for_session(
                session,
                session_payment_data,
                v4_api_request=True
            ),
            'tariffAmount': session.session_tariff,
            'vatPercentage': get_data_from_cache(VAT_PERCENTAGE_KEY)
        }
    return None


class ReceiptDetailsAPI(APIView):
    """Receipts details API"""

    # Permission classes are used to restrict the user
    permission_classes = [permissions.IsAuthenticated]

    def get(self, receipts_details_request):
        """get method to fetch user charging sessions history"""
        try:
            print(f"Inside ReceiptDetailsAPI")
            if not receipts_details_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                receipts_details_request.user.id, receipts_details_request.auth
            ):
                return MULTIPLE_LOGIN
            receipt_id = self.request.query_params.get(
                "receipt_id", False
            )
            is_app_receipt = self.request.query_params.get(
                "is_app_receipt", "false"
            ) == "true"
            is_ocpi_receipt = self.request.query_params.get(
                "is_ocpi_receipt", "false"
            ) == "true"
            if (receipt_id is None) or (is_ocpi_receipt is None):
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Invalid receipt details provided.",
                    }
                )
            receipt_details = {}
            if is_app_receipt:
                if not is_ocpi_receipt:
                    session_details = ChargingSession.objects.filter(
                            id=receipt_id,
                            user_id=receipts_details_request.user,
                        ).only(
                            'id',
                            'charging_data',
                            'station_id',
                            'chargepoint_id',
                            'paid_status',
                            'payment_response',
                            'session_tariff'
                        ).first()
                    if session_details is not None:
                        receipt_details = get_session_details_according_to_back_office_v4(
                            session_details
                        )
                else:
                    # connector_string_subquery = Connector.objects.filter(
                    #     id=OuterRef('connector_id')  
                    # ).values('connector_id')[:1] 

                    # s_connector_subquery = StationConnector.objects.filter(
                    #     connector_id=Subquery(connector_string_subquery),
                    #     back_office=OuterRef('back_office')                         
                    # ).values('charge_point_id_id')[:1]

                    session_details = OCPISessions.objects.filter(
                        id=receipt_id,
                        user_id=receipts_details_request.user,
                    ).all().first()
                    if not session_details or session_details.payment_response is None:
                        return Response(
                            {
                                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                                "status": False,
                                "message": "Unable to display receipt details with failed payment"
                            }
                        )
                    receipt_details = get_ocpi_session_details_v4(session_details)
            else:
                transaction_data = ContactlessSessionsDownloadedReceipts.objects.filter(
                    id=receipt_id,
                    user_id=receipts_details_request.user
                ).first()
                receipt_data = string_to_array_converter(
                    transaction_data.receipt_data
                )[0]
                if transaction_data.is_version_4_receipt:
                    receipt_details = receipt_data
                    total_cost_data = receipt_details["paymentDetails"]["total_paid"]
                    total_cost_without_tax = (total_cost_data / (100 + int(get_data_from_cache(VAT_PERCENTAGE_KEY))) * 100 * 100) / 100
                    tax_rate_amount = (((total_cost_without_tax * int(get_data_from_cache(VAT_PERCENTAGE_KEY))) / 100) * 100) / 100
                    if "vatPercentage" not in receipt_details:
                        receipt_details["vatPercentage"] = int(get_data_from_cache(VAT_PERCENTAGE_KEY))
                    if "amountWithoutTax" not in receipt_details:
                        receipt_details["amountWithoutTax"] =  format(total_cost_without_tax, ".2f")
                    if "taxAmount" not in receipt_details:
                        receipt_details["taxAmount"] =  format(tax_rate_amount, ".2f")
                
                else:
                    driivz_data = (
                        receipt_data["driivz_data"]
                        if "driivz_data" in receipt_data else
                        receipt_data
                    )
                    charger_data = ChargePoint.objects.filter(
                        charger_point_id=(
                            driivz_data['station']['id']
                            if "station" in driivz_data else
                            driivz_data['chargerId']
                        )
                    ).first()
                    if charger_data:
                        return Response(
                            {
                                "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                                "status": False,
                                "message": "Charger details not found!"
                            }
                        )
                    charging_session_start_time = get_formated_driivz_start_and_stop_date(
                        driivz_data[DRIIVZ_START_ON]
                    )
                    charging_session_end_time = get_formated_driivz_start_and_stop_date(
                        driivz_data[DRIIVZ_STOP_ON]
                    )
                    charging_duration = int(
                        (
                            charging_session_end_time - charging_session_start_time
                        ).total_seconds()
                    )
                    cost_data = driivz_data["cost"]
                    total_cost = 0
                    tax_amount = 0
                    total_cost_without_tax = 0
                    tax_rate = 0
                    total_cost = cost_data["total"]
                    tax_rate = Decimal(str(round(
                        (cost_data["totalTax"] /(cost_data["total"] - cost_data["totalTax"])) * 100
                    ))) if cost_data["total"] > 0 else 0
                    tax_amount = cost_data["totalTax"]
                    total_cost_without_tax = total_cost - tax_amount
                    if "payter_data" in receipt_data:
                        card_brand = receipt_data["payter_data"]["brandName"]
                        card_last_four = receipt_data["payter_data"]["maskedPAN"][:-4]
                        payment_completed_at = datetime.strptime(
                            receipt_data["payter_data"]["@timestamp"],
                            "%Y-%m-%dT%H:%M:%S.000Z"
                        ).strftime(DRIIVZ_DATE_TIME_FORMAT)
                    else:
                        card_brand = receipt_data["RH_data"]["cardBrand"]
                        card_last_four = receipt_data["RH_data"]["maskedPan"][:-4]
                        payment_completed_at = datetime.strptime(
                            receipt_data["RH_data"]["transactionDateTime"],
                            "%Y-%m-%dT%H:%M:%S"
                        ).strftime(DRIIVZ_DATE_TIME_FORMAT)
                    receipt_details = {
                        'vatPercentage': get_data_from_cache(VAT_PERCENTAGE_KEY),
                        "is_ocpi_receipt":is_ocpi_receipt,
                        "amountPaid": format(total_cost, ".2f"),
                        "amountWithoutTax": format(total_cost_without_tax, ".2f"),
                        "taxRate": tax_rate,
                        "taxAmount": format(tax_amount, ".2f"),
                        "duration": charging_duration,
                        "cardBrand": card_brand,
                        "cardLastFour": card_last_four,
                        "chargerId": charger_data.charger_point_name,
                        "endTime": charging_session_end_time.strftime(DRIIVZ_DATE_TIME_FORMAT) if not is_ocpi_receipt else timezone.localtime(charging_session_end_time).strftime(DRIIVZ_DATE_TIME_FORMAT),
                        "energyUsed": driivz_data[TOTAL_ENERGY],
                        "latitude": charger_data.station_id.latitude,
                        "longitude": charger_data.station_id.longitude,
                        "paymentDate": payment_completed_at,
                        "sessionId": driivz_data[
                            "transactionId" if "transactionId" in driivz_data else "id"
                        ],
                        "startTime": charging_session_start_time.strftime(DRIIVZ_DATE_TIME_FORMAT) if not is_ocpi_receipt else timezone.localtime(charging_session_start_time).strftime(DRIIVZ_DATE_TIME_FORMAT),
                        "stationAddress": charger_data.station_id.get_full_address(),
                        "stationName": (
                            charger_data.station_id.driivz_display_name
                            if charger_data.station_id.driivz_display_name else
                            charger_data.station_id.site_title
                        ),
                        "appReceipt": False,
                        "paymentDetails": {
                            "card": f"************{card_last_four}",
                            "type": (
                                f"CONTACTLESS - {receipt_data['payter_data']['paymentType']}"
                                if "payter_data" in receipt_data
                                else "CONTACTLESS - EMV"
                            ),
                            "currency": receipt_data["driivz_data"]["cost"]["currency"],
                        }
                    }
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Fetched receipt details successfully!",
                    "data": receipt_details
                }
            )
        except COMMON_ERRORS as exception:
            traceback.print_exc()
            print(
                f"Charging session history api failed for user -> \
                    {receipts_details_request.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


class GetReceiptGenerationStatus(APIView):
    """Get receipt generation status"""

    # Permission classes are used to restrict the user
    permission_classes = [permissions.IsAuthenticated]

    def get(self, receipts_details_request):
        """get method to get receipt generation process"""
        try:
            print(f"Inside ReceiptDetailsAPI")
            if not receipts_details_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                receipts_details_request.user.id, receipts_details_request.auth
            ):
                return MULTIPLE_LOGIN

            emp_session_id = self.request.query_params.get(
                "emp_session_id", False
            )
            if emp_session_id is False:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Invalid receipt identifier provided.",
                    }
                )
            charging_session = OCPISessions.objects.filter(
                ~Q(charging_data=None)
                & ~Q(chargepoint_id=None)
                & ~Q(station_id=None)
                & ~Q(connector_id=None)
                & ~Q(payment_response=None),
                session_id=emp_session_id,
                user_id=receipts_details_request.user,
                session_status="completed",
            ).only(
                'id',
                'charging_data',
                'paid_status',
                'station_id',
                'chargepoint_id',
                'paid_status',
                'payment_response'
            ).first()
            if charging_session is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": (
                            "The payment is pending. "+
                            "Please wait, and you'll see the receipt in the app history."
                        )
                    }
                )
            if charging_session and charging_session.total_cost_excl == "0":
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": (
                            "A receipt cannot be generated as the transaction amount is zero."
                        )
                    }
                )
            if charging_session.payment_response:

                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "Fetched receipt details successfully!",
                        "data": get_ocpi_session_details_v4(
                            charging_session
                        )
                    }
                )
            return Response(
                {
                    "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                    "status": True,
                    "message": "Something went wrong",
                    "data": None
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Charging session history api failed for user -> \
                    {receipts_details_request.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


class ChargingSessionHistoryDetailAPI(APIView):
    """charging session history detail  viewset"""

    # Permission classes are used to restrict the user
    permission_classes = [permissions.IsAuthenticated]

    def get(self, charging_session_history):
        """get method to fetch user charging sessions history details"""
        try:
            print("Inside ChargingSessionHistoryDetailAPI")
            if not charging_session_history.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                charging_session_history.user.id, charging_session_history.auth
            ):
                return MULTIPLE_LOGIN
            user = charging_session_history.user
            session_id = self.request.query_params.get("session_id", False)
            if session_id is False or not str(session_id).isnumeric():
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Session id not provided or is not a number",
                    }
                )
            session_id = int(session_id)
            sessions = ChargingSession.objects.filter(
                id=session_id, user_id=user
            )
            if sessions.first() is None:
                return Response(
                    {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "status": False,
                        "message": "Session with provided id not found!!",
                    }
                )
            session_history_serializer = (
                ChargingSessionDetailsHistorySerializer(sessions, many=True)
            )
            serializer_data = {**session_history_serializer.data}
            serializer_data["session_tariff"] = None
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Fetched charging session history details.",
                    "data": serializer_data,
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Charging session history details api failed for user -> \
                    {charging_session_history.user.id} due to exception ->\
                          {exception}"
            )
            return API_ERROR_OBJECT

