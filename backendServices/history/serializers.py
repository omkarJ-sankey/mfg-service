"""History serializers"""

# Date - 11/11/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file contains Serializers to make operation
#                       on database, to restrict fields of database.
#   Name            - Histoy Serializers
#   Modified by     - Manish Pawar
#   Modified date   - 11/11/2021


# imports required for serializers
from datetime import datetime
from decimal import Decimal
import pytz
import googlemaps
from decouple import config
from django.utils import timezone
from rest_framework import serializers

# pylint:disable=import-error
from sharedServices.model_files.config_models import ConnectorConfiguration
from sharedServices.model_files.station_models import Stations
from sharedServices.model_files.trip_models import Trips
from sharedServices.model_files.charging_session_models import ChargingSession

from sharedServices.common import (
    string_to_array_converter,
    remove_extra_spaces,
    time_formatter_for_hours,
)
from sharedServices.shared_station_serializer import (
    StationDetailsLogoSerializer,
)
from sharedServices.common_session_functions import (
    return_multiple_card_details,
)
from sharedServices.email_common_functions import (
    get_formated_driivz_start_and_stop_date
)
from sharedServices.constants import (
    DRIIVZ_START_ON,
    DRIIVZ_STOP_ON,
    KWH,
    SWARCO_END_TIME,
    SWARCO_START_TIME,
    TOTAL_ENERGY,
    DATE_TIME_FORMAT,
)

from backendServices.charging_sessions.app_level_constants import (
    SWARCO,
    DRIIVZ,
)
from sharedServices.ocpi_common_functions import get_cdr_cost


gmaps = googlemaps.Client(key=config("DJANGO_APP_GOOGLE_API_KEY"))


class TripHistorySerializer(serializers.ModelSerializer):
    """trip serializer to fetch user history trips"""

    # Following code defines the meta data for serializer
    # such as Which database and it's
    # fields are going to used to do oprations.

    start_location = serializers.SerializerMethodField("get_start_location")
    end_location = serializers.SerializerMethodField("get_end_location")
    trip_id = serializers.SerializerMethodField("get_trip_id")
    trip_date = serializers.SerializerMethodField("get_trip_date")

    @classmethod
    def get_start_location(cls, trip):
        """get trip start location"""
        return remove_extra_spaces(
            gmaps.reverse_geocode(trip.source)[0]["formatted_address"]
        )

    @classmethod
    def get_end_location(cls, trip):
        """get trip end location"""
        return remove_extra_spaces(
            gmaps.reverse_geocode(trip.destination)[0]["formatted_address"]
        )

    @classmethod
    def get_trip_id(cls, trip):
        """get trip id appended with TRP"""
        return f"TRP{trip.id}"

    @classmethod
    def get_trip_date(cls, trip):
        """get trip date in proper format"""
        return timezone.localtime(trip.created_date).date().strftime(
            "%d/%m/%Y"
        ) + timezone.localtime(trip.created_date).time().strftime("%H:%M")

    class Meta:
        """meta data"""

        model = Trips
        fields = (
            "id",
            "trip_id",
            "start_location",
            "end_location",
            "miles",
            "trip_date",
        )


class TripHistoryDetailsSerializer(serializers.ModelSerializer):
    """trip serializer to fetch user history trips"""

    # Following code defines the meta data for serializer
    # such as Which database and it's
    # fields are going to used to do oprations.

    start_location = serializers.SerializerMethodField("get_start_location")
    end_location = serializers.SerializerMethodField("get_end_location")
    added_spot_location = serializers.SerializerMethodField(
        "get_added_spot_location"
    )
    trip_id = serializers.SerializerMethodField("get_trip_id")
    trip_date = serializers.SerializerMethodField("get_trip_date")
    trip_stations = serializers.SerializerMethodField("get_trip_stations")

    @classmethod
    def get_start_location(cls, trip):
        """get trip start location"""
        return remove_extra_spaces(
            gmaps.reverse_geocode(trip.source)[0]["formatted_address"]
        )

    @classmethod
    def get_end_location(cls, trip):
        """get trip end location"""
        return remove_extra_spaces(
            gmaps.reverse_geocode(trip.destination)[0]["formatted_address"]
        )

    @classmethod
    def get_trip_id(cls, trip):
        """get trip id appended with TRP"""
        return f"TRP{trip.id}"

    @classmethod
    def get_added_spot_location(cls, trip):
        """get trip added spot"""
        if trip.add_spot_place_id:
            return remove_extra_spaces(
                gmaps.reverse_geocode(trip.add_spot_place_id)[0][
                    "formatted_address"
                ]
            )
        return False

    @classmethod
    def get_trip_date(cls, trip):
        """get trip date in proper format"""
        return timezone.localtime(trip.created_date).date().strftime(
            "%d/%m/%Y"
        ) + timezone.localtime(trip.created_date).time().strftime("%H:%M")

    @classmethod
    def get_trip_stations(cls, trip):
        """get trip added stations"""
        stations = []
        if trip.stations_data:
            stations_ids = string_to_array_converter(trip.stations_data)
            station_from_db = Stations.objects.filter(id__in=stations_ids)
            serializer = StationDetailsLogoSerializer(
                station_from_db, many=True
            )
            stations = serializer.data
        return stations

    class Meta:
        """meta data"""

        model = Trips
        fields = (
            "id",
            "trip_id",
            "start_location",
            "end_location",
            "added_spot_location",
            "miles",
            "trip_date",
            "miles",
            "duration",
            "ev_current_battery",
            "trip_stations",
            "ev_range",
        )


def get_session_details_according_to_back_office(session):
    """this function returns session details"""
    if session.payment_response and session.charging_data:
        charging_data = string_to_array_converter(session.charging_data)
        power_consumed = 0
        total_cost = "0"
        charging_session_end_time = None
        charging_session_start_time = None
        charging_duration = 0
        if session.back_office == SWARCO and KWH in charging_data[0]:
            charging_session_end_time = datetime.strptime(
                charging_data[0][SWARCO_END_TIME], DATE_TIME_FORMAT
            )
            charging_session_start_time = datetime.strptime(
                charging_data[0][SWARCO_START_TIME], DATE_TIME_FORMAT
            )
            power_consumed = charging_data[0][KWH]
        if session.back_office == DRIIVZ and TOTAL_ENERGY in charging_data[0]:
            charging_session_start_time = get_formated_driivz_start_and_stop_date(
                charging_data[0][DRIIVZ_START_ON]
            )
            charging_session_end_time = get_formated_driivz_start_and_stop_date(
                charging_data[0][DRIIVZ_STOP_ON]
            )
            power_consumed = charging_data[0][TOTAL_ENERGY]
        if charging_session_end_time and charging_session_start_time:
            charging_duration = time_formatter_for_hours(
                int(
                    (
                        charging_session_end_time - charging_session_start_time
                    ).total_seconds()
                )
            )

        cost_data = charging_data[0]["cost"]
        total_cost = 0
        tax_amount = 0
        total_cost_without_tax = 0
        tax_rate = 0
        # if session.is_reviewed == f"{ADMIN_SCREENING}-{EDIT_HOLD_PAYMENT}":
        total_cost = cost_data["total"]
        tax_rate = Decimal(str(round(
            (cost_data["totalTax"] /(cost_data["total"] - cost_data["totalTax"])) * 100
        ))) if cost_data["total"] > 0 else 0
        tax_amount = cost_data["totalTax"]
        total_cost_without_tax = total_cost - tax_amount
        # else:
        #     total_cost = Decimal(str(cost_data["total"]))
        #     total_cost_without_tax = Decimal(
        #         str(cost_data["total"])
        #     ) - Decimal(str(cost_data["totalTax"]))
        #     tax_amount = Decimal(str(cost_data["totalTax"]))
        #     tax_rate = (
        #         format(Decimal(str(cost_data["totalTaxRate"])), ".2f")
        #         if check_is_float(cost_data["totalTaxRate"])
        #         else f"{int(cost_data['totalTaxRate'])}"
        #     )
        return {
            "power_consumed": power_consumed,
            "total_cost_without_tax": format(total_cost_without_tax, ".2f"),
            "tax_rate": tax_rate,
            "total_cost": format(total_cost, ".2f"),
            "tax_amount": format(tax_amount, ".2f"),
            "duration": charging_duration,
        }
    return False


def get_payment_details_for_session(session, session_payment_data, v4_api_request=False, is_ocpi_session = False):
    """get payment details"""
    payment_data = (
        string_to_array_converter(session.payment_response)[0]
        if session.payment_response
        else None
    )

    if payment_data and "payment" in payment_data:
        (
            primary_card_number,
            secondary_card_number,
            primary_card_payment_time,
            _,
            secondary_card_payment_time,
            _,
            primary_card_amount,
            secondary_card_amount,
            primary_card_brand,
            secondary_card_brand,
        ) = return_multiple_card_details(
            session, session_payment_data, v4_api_request
        )
        if is_ocpi_session:
            total_cost_incl_vat,_,_ = get_cdr_cost(session)
            session_total_cost = total_cost_incl_vat*100
        else :
            session_total_cost = int(session.total_cost)
        # session_total_cost = session.total_cost_incl*100 if is_ocpi_session and session.total_cost_incl is not None else int(session.total_cost)
        total_amount = (
            Decimal(str(session_total_cost)) / 100
            if session_total_cost and isinstance(session_total_cost, (int, float, Decimal)) #str(session_total_cost).isnumeric()
            else 0
        )
        voucher_amount = (
            Decimal(str(session.deducted_voucher_amount)) / 100
            if session.deducted_voucher_amount is not None
            else 0
        )
        total_paid = total_amount - voucher_amount
        payment_details = payment_data["payment"]["card_details"]["card"]
        return (
            {
                "primary_card_number": primary_card_number,
                "primary_card_payment_time": primary_card_payment_time,
                "secondary_card_number": secondary_card_number,
                "secondary_card_payment_time": secondary_card_payment_time,
                "primary_card_amount": primary_card_amount,
                "secondary_card_amount": secondary_card_amount,
                "primary_card_brand": primary_card_brand,
                "secondary_card_brand": secondary_card_brand,
                "currency": payment_data["payment"]["total_money"][
                    "currency"
                ],
                "card": f"************{payment_details['last_4']}",
                "brand": payment_details["card_brand"],
                "voucher_amount": voucher_amount,
                "total_paid": total_paid,
                "is_multicard_payment": True,
            }
            if primary_card_number
            and primary_card_payment_time
            and secondary_card_number
            and secondary_card_payment_time
            and primary_card_amount
            and secondary_card_amount
            and session.preauth_status == "collected"
            else (
                {
                    "card": f"************{payment_details['last_4']}",
                    "brand": payment_details["card_brand"],
                    "type": f"CONNECT APP - {payment_details['card_type']}",
                    "currency": payment_data["payment"]["total_money"][
                        "currency"
                    ],
                    "voucher_amount": voucher_amount,
                    "total_paid": total_paid,
                }
                if payment_details["card_brand"] != "SQUARE_GIFT_CARD"
                else {
                    "card": "NA",
                    # "brand": None,
                    "type": "MFG Connect - Voucher",
                    "currency": payment_data["payment"]["total_money"][
                        "currency"
                    ],
                    "voucher_amount": voucher_amount,
                    "total_paid": total_paid,
                }
            )
        )
    return None


class ChargingSessionHistorySerializer(serializers.ModelSerializer):
    """Charging session serializer to fetch user history sessions"""

    # Following code defines the meta data for serializer
    # such as Which database and it's
    # fields are going to used to do oprations.

    session_id = serializers.SerializerMethodField("get_session_id")
    start_time = serializers.SerializerMethodField("get_start_time")
    end_time = serializers.SerializerMethodField("get_end_time")
    chargepoint_details = serializers.SerializerMethodField(
        "get_chargepoint_details"
    )
    connector_details = serializers.SerializerMethodField(
        "get_connector_details"
    )
    session_details = serializers.SerializerMethodField("get_session_details")
    station_name = serializers.SerializerMethodField(
        "get_session_station_name"
    )
    station_id = serializers.SerializerMethodField("get_session_station_id")
    address = serializers.SerializerMethodField("get_station_address")
    charger = serializers.SerializerMethodField("get_charger")
    payment_details = serializers.SerializerMethodField("get_payment_details")

    @classmethod
    def get_session_station_name(cls, session):
        """get station id"""
        if session.station_id:
            return (
                session.station_id.driivz_display_name
                if session.station_id.driivz_display_name else
                session.station_id.site_title
            )
        return ""

    @classmethod
    def get_charger(cls, session):
        """get payment details"""
        return session.chargepoint_id.charger_point_name

    @classmethod
    def get_session_station_id(cls, session):
        """get station id"""
        if session.station_id:
            return session.station_id.station_id
        return ""

    @classmethod
    def get_station_address(cls, session):
        """get station address"""
        if session.station_id:
            return session.station_id.get_full_address()
        return ""

    def get_payment_details(self, session):
        """get payment details"""
        return get_payment_details_for_session(session, self.context["session_payment_data"])

    @classmethod
    def get_session_details(cls, session):
        """get session details"""
        return get_session_details_according_to_back_office(session)

    @classmethod
    def get_chargepoint_details(cls, session):
        """get chargepoint name with its id"""
        if session.chargepoint_id:
            return remove_extra_spaces(
                f"{session.chargepoint_id.charger_point_name} \
                - {session.chargepoint_id.charger_point_id}"
            )
        return ""

    @classmethod
    def get_connector_details(cls, session):
        """get session connector details"""
        if session.connector_id:
            session_connector_image = ConnectorConfiguration.objects.filter(
                connector_plug_type=session.connector_id.plug_type_name
            )
            if session_connector_image.first():
                image_path = session_connector_image.first().get_image_path()
                return {
                    "connector_data": remove_extra_spaces(
                        f"{session.connector_id.plug_type_name} - \
                            {session.connector_id.max_charge_rate}KW"
                    ),
                    "connector_image": image_path,
                }
        return {}

    @classmethod
    def get_session_id(cls, session):
        """get session id"""
        return f"{session.id}"

    @classmethod
    def get_start_time(cls, session):
        """get session starting  date time in proper format"""
        charging_data = string_to_array_converter(session.charging_data)
        charging_start_time = None
        if session.back_office == SWARCO and KWH in charging_data[0]:
            charging_start_time = timezone.localtime(
                datetime.strptime(
                    charging_data[0][SWARCO_START_TIME], DATE_TIME_FORMAT
                ).replace(tzinfo=pytz.UTC)
            )
        if session.back_office == DRIIVZ and TOTAL_ENERGY in charging_data[0]:
            charging_start_time = get_formated_driivz_start_and_stop_date(
                charging_data[0][DRIIVZ_START_ON],
                provide_local_time_dates=True
            )
        if charging_start_time:
            return (
                charging_start_time.date().strftime("%d/%m/%Y")
                + " "
                + charging_start_time.time().strftime("%H:%M")
            )
        return ""

    @classmethod
    def get_end_time(cls, session):
        """get session ending  date time in proper format"""
        charging_data = string_to_array_converter(session.charging_data)
        if session.back_office == SWARCO and KWH in charging_data[0]:
            charging_end_time = timezone.localtime(
                datetime.strptime(
                    charging_data[0][SWARCO_END_TIME], DATE_TIME_FORMAT
                ).replace(tzinfo=pytz.UTC)
            )
        if session.back_office == DRIIVZ and TOTAL_ENERGY in charging_data[0]:
            charging_end_time = get_formated_driivz_start_and_stop_date(
                charging_data[0][DRIIVZ_STOP_ON],
                provide_local_time_dates=True
            )
        return (
            charging_end_time.date().strftime("%d/%m/%Y")
            + " "
            + charging_end_time.time().strftime("%H:%M")
        )

    class Meta:
        """meta data"""

        model = ChargingSession
        fields = (
            "id",
            "session_id",
            "start_time",
            "end_time",
            "chargepoint_details",
            "connector_details",
            "session_details",
            "station_name",
            "station_id",
            "address",
            "payment_details",
            "charger",
            "session_tariff",
        )


class ChargingSessionDetailsHistorySerializer(serializers.ModelSerializer):
    """Charging session serializer to fetch user history session details"""

    # Following code defines the meta data for serializer
    # such as Which database and it's
    # fields are going to used to do oprations.

    session_id = serializers.SerializerMethodField("get_session_id")
    session_start_date_time = serializers.SerializerMethodField(
        "get_session_start_date_time"
    )
    session_end_date_time = serializers.SerializerMethodField(
        "get_session_end_date_time"
    )

    device_name = serializers.SerializerMethodField("get_device_name")
    device_id = serializers.SerializerMethodField("get_device_id")
    connector_type = serializers.SerializerMethodField("get_connector_type")

    session_details = serializers.SerializerMethodField("get_session_details")

    session_station_details = serializers.SerializerMethodField(
        "get_session_station_details"
    )

    @classmethod
    def get_session_station_details(cls, session):
        """get session stations details"""
        if session.station_id:
            serializer = StationDetailsLogoSerializer(session.station_id)
            return serializer.data
        return False

    @classmethod
    def get_session_details(cls, session):
        """get session details"""
        return get_session_details_according_to_back_office(session)

    @classmethod
    def get_device_name(cls, session):
        """get chargepoint name"""
        if session.chargepoint_id:
            return session.chargepoint_id.charger_point_name
        return ""

    @classmethod
    def get_device_id(cls, session):
        """get chargepoint id"""
        if session.chargepoint_id:
            return session.chargepoint_id.charger_point_id
        return ""

    @classmethod
    def get_connector_type(cls, session):
        """get session connector details"""
        if session.connector_id:
            return (
                session.connector_id.plug_type_name
                + "-"
                + f"{session.connector_id.max_charge_rate}KW"
            )
        return ""

    @classmethod
    def get_session_id(cls, session):
        """get session id"""
        return f"{session.id}"

    @classmethod
    def get_session_start_date_time(cls, session):
        """get session starting  date time in proper format"""
        charging_data = string_to_array_converter(session.charging_data)
        if session.back_office == SWARCO and KWH in charging_data[0]:
            charging_start_time = timezone.localtime(
                datetime.strptime(
                    charging_data[0][SWARCO_START_TIME], DATE_TIME_FORMAT
                ).replace(tzinfo=pytz.UTC)
            )
        if session.back_office == DRIIVZ and TOTAL_ENERGY in charging_data[0]:
            charging_start_time = timezone.localtime(
                datetime.strptime(
                    charging_data[0][DRIIVZ_START_ON].split(".")[0],
                    DATE_TIME_FORMAT,
                ).replace(tzinfo=pytz.UTC)
            )
        return (
            charging_start_time.date().strftime("%d/%m/%Y")
            + " "
            + charging_start_time.time().strftime("%H:%M")
        )

    @classmethod
    def get_session_end_date_time(cls, session):
        """get session ending  date time in proper format"""
        charging_data = string_to_array_converter(session.charging_data)
        if session.back_office == SWARCO and KWH in charging_data[0]:
            charging_end_time = timezone.localtime(
                datetime.strptime(
                    charging_data[0][SWARCO_END_TIME], DATE_TIME_FORMAT
                ).replace(tzinfo=pytz.UTC)
            )
        if session.back_office == DRIIVZ and TOTAL_ENERGY in charging_data[0]:
            charging_end_time = get_formated_driivz_start_and_stop_date(
                charging_data[0][DRIIVZ_STOP_ON],
                provide_local_time_dates=True
            )
        return (
            charging_end_time.date().strftime("%d/%m/%Y")
            + " "
            + charging_end_time.time().strftime("%H:%M")
        )

    class Meta:
        """meta data"""

        model = ChargingSession
        fields = (
            "id",
            "session_id",
            "emp_session_id",
            "session_start_date_time",
            "session_end_date_time",
            "device_name",
            "device_id",
            "connector_type",
            "session_details",
            "session_station_details",
            "session_tariff",
        )
