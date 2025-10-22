"""common functions"""

import math
import re
import secrets
import operator
import string
import json
import decimal
import base64
import io
import firebase_admin
from firebase_admin import credentials, messaging
from functools import reduce
from hashlib import sha256
from datetime import datetime, timedelta
from io import StringIO
import xlsxwriter
import redis
import pytz
import pandas as pd
import jwt
from passlib.hash import django_pbkdf2_sha256 as handler
from cryptography.fernet import Fernet
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.utils import timezone
from decouple import config
from PIL import Image
import numpy as np
import traceback
# pylint:disable=import-error
from sharedServices.model_files.bulk_models import (
    BulkUploadErrorMessages,
    BulkUploadProgress,
)
from .model_files.app_user_models import Profile
from .model_files.station_models import (
    Stations,
    StationServices,
    ChargePoint
)
from .model_files.config_models import (
    BaseConfigurations,
    ConnectorConfiguration,
    MapMarkerConfigurations,
    ServiceConfiguration,
)
from .constants import (
    BLOCKED_USERS_EMAILS_LIST,
    BLOCKED_USERS_PHONE_LIST,
    EMAIL_REGEX,
    LAT,
    LON,
    PAGINATION_COUNT,
    TOKEN_COOKIE_MAX_AGE,
    TOKEN_EXPIRATION_TIME,
    urls,
    OTP_LIMIT,
    YES,
    NO,
    PASSWORD_REGEX,
    COMING_SOON_CONST,
    MFG_RAPID,
    MFG_NORMAL,
    OTHER_RAPID,
    OTHER_NORMAL,
    REGEX,
    SEARCH_REGEX,
    SEARCH_AND_EMAIL_REGEX,
    APP_VERSION_FOUR,
    ACTIVE,
    VAT_PERCENTAGE
)

from .model_files.ocpi_charge_detail_records_models import OCPIChargeDetailRecords

from sharedServices.constants import ROBOTS_TXT_RULES
from django.http import HttpResponse

def robots_txt(request):
    """Django view to serve robots.txt using shared configuration."""
    return HttpResponse("\n".join(ROBOTS_TXT_RULES), content_type="text/plain")

cred = credentials.Certificate(
    {
        "type": "service_account",
        "project_id": config("DJANGO_APP_FCM_PROJECT_ID_V4"),
        "private_key_id": config("DJANGO_APP_FCM_PRIVATE_KEY_ID_V4"),
        "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQCqQFAGBW/pJlI2\n2jhvfEVLAEYwu68WNYd9yQb7AZn5Z4w/Jen+PvmRvJEICDIU0edBGCDLLFbjVDTx\n75rBGlPdbUzx0KA8MDwNCP0/dLGOEB2OmToXY8eIFZpTadKetG9sZ8LDyNxiA8X1\nbmnO8sGzoyVkI+6kRfmrY230I1KQeZfg4bE4qYc5bM5VuNzqo2AX6KJx5bg9NnLd\nQQOCAup2Xp79bN0Qk1EpRBZAv+0tWAhJhrsrNUcPABrHN/2TN1kN98M3bva3CUDE\nAVzwNWxqEJZk7WFM2Q9hkmRtvzrpvjn0kDAMQlxaL2wK/kkfMThSWQQbzvWY08F/\noZWrXLXzAgMBAAECggEADlSoh8E4aNMxc22N95Bp0sTco6iAtelelM9xl3pMiCpX\nq08ZMa4CWuqY+Kib8pWylg+eXwvF6o/BfyXwjFWXfpl/MxGhEz/qJhy+GHPNqEwh\n+MlcEvDysDlFSsUrFfHROTpIsis7pcJ0jNK09FcJyAGxGYtOwKQlPnB5pmW8wu1e\nGIT7IAGDxRcokDVfLGCWI6iAocj4IEtPpR4ZsLX5vBEhcinFvP63Ic/2RXVunqR2\np8jW9plowDqB+DphsBTRqosPghprHaNgIXRjKAIHYipaHrP1d80ZHWF4W7/jAmCz\nRkYVu1xlANdGd5JVTEwqc//2RQNSJoQnt4shdw18uQKBgQDYhRmcskyaiVHIsF9m\nFhacHwnQ21yPwvL6Sk9pnPG32Nnj/z45/JsP7ID3AvRYV2BLygYgx3loDCI4pnZR\nzzpyV7Izq6zzv1VRlxSWgwg66vWuiKSp2mTkKrMIe6d2Hb4PS3w4XHX5JWzFteIW\nPaEMhJr010vzv1UPa32O7hkoawKBgQDJS3Fo6krWJx4fx15F0FCZXCByZT9mR0oK\nUOtkQgjM+9J7xiLyfWgoVtCfU4bxY7wjC1kHv6uou5MjChIevR6UpiKRavO5yEau\neEms3Ir8QnDz7G4E7vVqAMJGSXbjtuBHS1gLkwVJseew2b+Z5Zoo9xglFGhQ6QDs\nhKLybZYqmQKBgBEhTqpwDNF5JchL8/A+tSE672rfwA37rX+R24COky0pceuw6Ppr\netUir/1a9Xv7xbmZTSzQu1E5DIgQ23GThJtBRu8BmRhbveNLoaxax47pwfBCDU0G\n406N9kYoilI0/jF1lmlbH1ZL2LQ3tKBv1csIvr26Pt8U9yTWK0PgoIrrAoGAAk6C\nAzDEIMYb+0M+mlAzzD4ZBRaR7msctxeMSv7SuP6dv9taZSr4uZWdGGZNopCBBGnJ\n4GPa5LkZi4o/AOkr44ov1TjDiDp6TN+GAJwaX5+nSbRI4neWiltt3n5TBXMACPEd\nFizeH6URQZ6NKodOB/Ak76/XLi4tW4h9kYed8+kCgYAN22n9FkVxmnBDX9i1XIec\nZ+OrZJrt++2ok1xKZmwzYDB6NmsPkQXwbrWNsmn1urbKILnII48Gm0Q/waH3gobm\nde6oLGtQNLW+pzEgvDg9vTcg2TWQ9TQ+/56UO+xInTfufsLv4xLkIlLDGhrNUVjU\nCA219iJKhnzpM0YrVraYig==\n-----END PRIVATE KEY-----\n",
        "client_email": config("DJANGO_APP_FCM_CLIENT_EMAIL_V4"),
        "client_id": config("DJANGO_APP_FCM_CLIENT_ID_V4"),
        "auth_uri": config("DJANGO_APP_FCM_AUTH_URI_V4"),
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": config("DJANGO_APP_FCM_CLIENT_CERT_URL_V4"),
        "universe_domain": "googleapis.com",
    }
)

firebase_admin.initialize_app(cred)

# Values used in the application for calculating business logic
DJANGO_APP_REFRESH_TOKEN_SECRET = config("DJANGO_APP_REFRESH_TOKEN_SECRET")
RADIUS = 8100
PROMOTION_RADIUS = 48280

# Redis connection to manage caching of data between APIs and admin portal
redis_connection = redis.StrictRedis(
    host=config("DJANGO_APP_AZURE_REDIS_HOST"),
    port=config("DJANGO_APP_AZURE_REDIS_PORT"),
    db=0,
    password=config("DJANGO_APP_AZURE_REDIS_PASSWORD"),
    ssl=True,
)


def hasher(data):
    """this function hashes string without salt"""
    data_sha = sha256()
    data_sha.update(data.encode())
    return base64.urlsafe_b64encode(data_sha.digest()).decode("utf-8")


def check_integer(str_input):
    """this function checks whether given string
    can be converted to integer or not"""
    try:
        int(str_input)
        return True
    except ValueError:
        return False


# used in session details key of history APIs &
# session payment details
def check_is_float(val):
    """this function determines whether number is int or float"""
    return val - int(val) != 0


# function to remove extra spaces
def remove_extra_spaces(string_body):
    """this function removes extra spaces from strings"""
    string_body = str(string_body)
    if isinstance(string_body, str):
        return re.sub(" +", " ", string_body)
    return ""


def error_messages_object_formatter(error_keys, error_values):
    """this function formats error object"""
    error_object = {}
    for count, error_key in enumerate(error_keys):
        error_object[remove_extra_spaces(f"{error_key}")] = (
            remove_extra_spaces(error_values[count])
        )
    return error_object


def format_token(token):
    """this function formats token"""
    return str(token).split("b'")[1].split("'")[0]


# this function prevents concurrent logins
def handle_concurrent_user_login(user_id, token):
    """handeles concurrent logins in app"""
    profile = Profile.objects.filter(
        user_id=user_id, app_access_token=str(token)
    ).only('id')
    if profile.first():
        return True
    return False


# This function is the search validator.
def search_validator(search, screen=None):
    """search validator"""
    regex = SEARCH_REGEX
    search_and_email_regex = SEARCH_AND_EMAIL_REGEX
    if screen == "search and email accepted" and (
        search and (re.search(search_and_email_regex, search) or search == "")
    ):
        return search
    elif search and (re.search(regex, search) or search == ""):
        return search
    return ""


# This function is the email validator.
def email_validator(email):
    """email validator"""
    regex = EMAIL_REGEX
    return re.search(regex, email)


# This function is the password validator.
def password_validator(password):
    """password validator"""
    reg = PASSWORD_REGEX
    pat = re.compile(reg)
    return re.search(pat, password) and len(password) > 7


def not_valid(data_type, value):
    """data validation check"""
    if value:
        regex = REGEX[data_type]
        compile_regex = re.compile(regex)
        return not re.search(compile_regex, str(value))
    return True


def get_connector(con):
    """get connector details function"""
    connectors = ConnectorConfiguration.objects.all()
    for connector in connectors:
        if connector.connector_plug_type_name == con:
            return connector.get_image_path()
    return ""


def first_page_records(total_length, count, number_list):
    """pagination and filter function"""
    for i in range(1, math.ceil(total_length / count) + 1):
        number_list.append(i)
    return number_list


def last_page_records(number_value, number_list):
    """pagination and filter function"""
    for _ in range(3):
        number_list.append(None)
    for i in range(int(number_value) - 2, int(number_value) + 3):
        number_list.append(i)
    for _ in range(3):
        number_list.append(None)
    return number_list


def paginator_track_record(page_num, number_list):
    """pagination and filter function"""
    for i in range(6, int(page_num) + 4):
        number_list.append(i)
    for _ in range(3):
        number_list.append(None)
    return number_list


def paginator_end_record(page_num, number_list, total_length, count):
    """pagination and filter function"""
    for _ in range(3):
        number_list.append(None)
    for i in range(int(page_num) - 3, math.ceil(total_length / count) - 5):
        number_list.append(i)
    return number_list


def remaining_page(number_list, page_num, total_length, count):
    """pagination and filter function"""
    if (int(page_num) - 3) <= 5:
        number_list = paginator_track_record(page_num, number_list)
    elif (int(page_num) + 3) >= (math.ceil(total_length / count) - 5):
        number_list = paginator_end_record(
            page_num, number_list, total_length, count
        )
    else:
        number_list = last_page_records(page_num, number_list)
    return number_list


def pagination_function(total_length, count, page_num):
    """pagination and filter function"""
    number_list = []
    if math.ceil(total_length / count) < 15:
        number_list = first_page_records(total_length, count, number_list)
        return number_list

    middle_number = math.ceil(total_length / count) / 2
    for i in range(1, 6):
        number_list.append(i)
    if int(page_num) < 5 or int(page_num) > (
        math.ceil(total_length / count) - 4
    ):
        number_list = last_page_records(middle_number, number_list)
    else:
        number_list = remaining_page(
            number_list, page_num, total_length, count
        )
    for i in range(
        math.ceil(total_length / count) - 5,
        math.ceil(total_length / count) + 1,
    ):
        number_list.append(i)
    return number_list


def pagination_and_filter_func(page_num, table, array_of_filters=[], screen=None):
    """pagination and filter function"""
    count = int(
        BaseConfigurations.objects.get(
            base_configuration_key=PAGINATION_COUNT
        ).base_configuration_value
    )
    count = int(count)
    filtered_table = table
    argument_list = []  # This only use for search
    url = ""
    total_length = 0
    skvalue = ""
    for i in array_of_filters:
        keys = list(i.keys())
        values = list(i.values())
        if values[0] is not None and values[0] != "All":
            if keys[0] == "search":
                iterator_keys = values[1]
                url += f"&search={values[0]}"
                search_results = []
                for iterator_key in iterator_keys:
                    search_results.append(
                        filtered_table.filter(**{iterator_key: values[0]})
                    )
                for search_count, search_item in enumerate(search_results):
                    if search_count == 0:
                        filtered_table = search_item
                    else:
                        filtered_table = filtered_table | search_item
            else:
                url += f'&{keys[0].split("__")[0]}={values[0]}'
                if (
                    keys[0].split("__")[0] == "brand"
                    and values[0] == "EV Power"
                ):
                    filtered_table = filtered_table.filter(
                        Q(brand=values[0]) | Q(is_ev=YES)
                    )
                else:
                    filtered_table = filtered_table.filter(
                        **{keys[0]: values[0]}
                    )
        if screen and values[0] is None:
            filtered_table = filtered_table.filter(**{keys[0]: "Active"})
        if screen and values[0] == "All":
            url += f'&{keys[0].split("__")[0]}={values[0]}'
    if len(argument_list) > 0:
        filtered_table = filtered_table.filter(
            reduce(operator.or_, argument_list)
        )
        url += f"&search={skvalue}"
    # calculating the length of array/queryset.
    if isinstance(table, list):
        total_length = len(filtered_table)
    else:
        total_length = filtered_table.count()
        filtered_table = list(filtered_table)
    paginator = Paginator(filtered_table, count)
    if int(page_num) <= 0 or int(page_num) > math.ceil(total_length / count):
        page_num = 1
    page = paginator.page(page_num)
    last_record_number = int(page_num) * count
    first_record_number = last_record_number - (count - 1)
    last_record_number = min(last_record_number, total_length)
    number_list = pagination_function(total_length, count, page_num)
    prev_page = int(page_num) - 1
    next_page = int(page_num) + 1
    if prev_page <= 0:
        prev_page = None
    if next_page > math.ceil(total_length / count):
        next_page = None
    if len(page) == 0:
        first_record_number = 0
    return {
        "filtered_table": page,
        "data_count": total_length,
        "url": url,
        "first_record_number": first_record_number,
        "last_record_number": last_record_number,
        "number_list": number_list,
        "next_page": next_page,
        "prev_page": prev_page,
        "filtered_table_for_export": filtered_table,
        "count":count,
    }

def paginate_data(filtered_table, page_num):
        count = int(
        BaseConfigurations.objects.get(
            base_configuration_key=PAGINATION_COUNT
        ).base_configuration_value
        )
        total_length = len(filtered_table)
        paginator = Paginator(filtered_table, count)
        if int(page_num) <= 0 or int(page_num) > math.ceil(total_length / count):
            page_num = 1
        page = paginator.page(page_num)
        last_record_number = int(page_num) * count
        first_record_number = last_record_number - (count - 1)
        last_record_number = min(last_record_number, total_length)
        number_list = pagination_function(total_length, count, page_num)
        prev_page = int(page_num) - 1
        next_page = int(page_num) + 1
        if prev_page <= 0:
            prev_page = None
        if next_page > math.ceil(total_length / count):
            next_page = None
        if len(page) != 0:
            first_record_number = 0
        return {
        "total_length": total_length,
        "first_record_number": first_record_number,
        "last_record_number": last_record_number,
        "number_list": number_list,
        "prev_page": prev_page,
        "next_page": next_page,
        "page":page
        }


def order_by_function(table, order_by_array):
    """order by function"""
    url = ""
    for i in order_by_array:
        for key, value in i.items():
            if value[1]:
                if value[1] == "Ascending":
                    table = table.order_by(key)
                else:
                    table = table.order_by(f"-{key}")
                url = f"&{value[0]}={value[1]}"
    return {"ordered_table": table, "url": url}


def filter_url(contents, current_page):
    """filter urls function"""
    url_list = []
    for i in contents:
        url = ""
        for key, value in urls.items():
            if key == i.name:
                url = value
        if i.name == current_page:
            url_list.append({"name": i.name, "url": url, "state": "active"})
        else:
            url_list.append({"name": i.name, "url": url, "state": ""})
    return url_list


# this function is used to find whether object is
# previously inserted in the list or not
def contains(array, filter_function):
    """this function return True if filter condition is true for list"""
    for item in array:
        if filter_function(item):
            return True
    return False


def return_otp_limit():
    """returns max otp user can receive."""
    return int(
        BaseConfigurations.objects.get(
            base_configuration_key=OTP_LIMIT
        ).base_configuration_value
    )


def time_formatter_for_hours(val):
    """this is time formatter function"""
    val = val * 1000
    formatted_time = ""
    second = 1000
    minute = second * 60
    hour = minute * 60
    hours = math.floor(val / hour)
    minutes = math.floor(val % hour / minute)
    seconds = math.floor(val % minute / second)
    if hours > 0:
        if hours > 9:
            formatted_time += f"{hours}:"
        else:
            formatted_time += f"0{hours}:"
        if minutes > 0:
            if minutes > 9:
                formatted_time += f"{minutes} hrs"
            else:
                formatted_time += f"0{minutes} hrs"
        else:
            formatted_time += "00 hrs"
    else:
        if minutes > 0:
            if minutes > 9:
                formatted_time += f"{minutes}:"
            else:
                formatted_time += f"0{minutes}:"
        else:
            formatted_time += "00:"
        if seconds > 0:
            if seconds > 9:
                formatted_time += f"{seconds} mins"
            else:
                formatted_time += f"0{seconds} mins"
        else:
            formatted_time += "00 mins"
    return formatted_time


def date_formater_for_frontend_date(date):
    """this is date formater to format string date to datetime"""
    if "/" in date:
        newdatetime = timezone.localtime(
            datetime.strptime(date, "%d/%m/%Y").replace(
                hour=0, minute=0, tzinfo=pytz.UTC
            )
        )
        return newdatetime


def date_difference_function(from_date, formatted_to_date):
    if from_date and formatted_to_date < date_formater_for_frontend_date(
        from_date
    ):
        from_date = None
    date_difference = datetime.now() - formatted_to_date.replace(tzinfo=None)
    return date_difference


def end_date_formater_for_frontend_date(date):
    """This is promotion end date formatter"""
    if "/" in date:
        newdatetime = timezone.localtime(
            datetime.strptime(date, "%d/%m/%Y").replace(
                hour=23, minute=59, tzinfo=pytz.UTC
            )
        )
    return newdatetime


def generate_token_func(user_id, authorization_id):
    """This function generates token"""
    jwt_secret = secrets.token_hex(16)
    jwt_algorithm = "HS256"
    jwt_exp_delta_minutes = TOKEN_EXPIRATION_TIME
    expires_on = timezone.localtime(timezone.now()) + timedelta(
        minutes=jwt_exp_delta_minutes
    )
    payload = {
        "user_id": user_id,
        "exp": expires_on,
        "authorization_id": authorization_id,
    }
    refresh_token_payload = {
        "user_id": user_id,
        "authorization_id": authorization_id,
    }
    jwt_token = jwt.encode(payload, jwt_secret, jwt_algorithm)
    refresh_token = jwt.encode(
        refresh_token_payload, DJANGO_APP_REFRESH_TOKEN_SECRET, jwt_algorithm
    )
    return [jwt_token, jwt_secret, expires_on, refresh_token]


def rad(item):
    """radian return"""
    return item * math.pi / 180


# function to calculate distance in meters
def get_distance(point_one, point_two):
    """function to calculate distance in meters"""
    one_km = 6371137
    d_lat = rad(point_two[LAT] - point_one[LAT])
    d_long = rad(point_two[LON] - point_one[LON])

    rough_distance = math.sin(d_lat / 2) * math.sin(d_lat / 2) + math.cos(
        rad(point_one[LAT])
    ) * math.cos(rad(point_two[LAT])) * math.sin(d_long / 2) * math.sin(
        d_long / 2
    )

    curve = 2 * math.atan2(
        math.sqrt(rough_distance), math.sqrt(1 - rough_distance)
    )
    distance = one_km * curve
    return distance


def get_session_api_call_time():
    """get session api"""

    session_api_call_time = BaseConfigurations.objects.filter(
        base_configuration_key="session_api_call_time"
    ).first()
    return (
        int(session_api_call_time.base_configuration_value)
        if session_api_call_time
        else 15001
    )


def get_station_distance(station_ditance_value, user_latitude, user_longitude):
    """this function calculates distance between
    station and usr location"""
    station_distance = get_distance(
        {
            "latitude": station_ditance_value["latitude"],
            "longitude": station_ditance_value["longitude"],
        },
        {"latitude": user_latitude, "longitude": user_longitude},
    )
    return station_distance


def get_station_address(station):
    """this function returns formatted address of station"""
    address = ""
    if station.station_address1 != "nan" and len(station.station_address1) > 0:
        if (
            len(station.station_address2) > 0
            or len(station.station_address3) > 0
        ) and len(station.station_address1) > 0:
            if (
                station.station_address2 != "nan"
                and station.station_address3 != "nan"
            ):
                address += station.station_address1 + ", "
            else:
                address += station.station_address1
        else:
            address += station.station_address1

    if station.station_address2 != "nan":
        if (
            len(station.station_address3) > 0
            and len(station.station_address2) > 0
            and station.station_address3 != "nan"
        ):
            address += station.station_address2 + ", "
        else:
            address += station.station_address2
    if len(station.station_address3) > 0 and station.station_address3 != "nan":
        address += station.station_address3

    if len(station.post_code) > 0:
        address += ", " + station.post_code
    return address


def get_station_connector_speed(station, ultra_rapid_devices):
    """this function provide speed of connector"""
    if station.is_mfg == YES:
        if ultra_rapid_devices.first():
            return MFG_RAPID
        return MFG_NORMAL
    if ultra_rapid_devices.first():
        return OTHER_RAPID
    return OTHER_NORMAL


def get_ultra_devices(station):
    """this functions returns ultra devices"""
    return Stations.objects.filter(
        id=station.id,
        deleted=NO,
        station_connectors__connector_type="Ultra-Rapid",
    ).distinct()


def get_station_brand_logo(station, app_version=APP_VERSION_FOUR, get_small_image=False, non_ev = False):
    """this function returns brand logo of station"""
    if station.status == COMING_SOON_CONST:
        coming_soon_marker = MapMarkerConfigurations.objects.filter(
            map_marker_key="-".join(COMING_SOON_CONST.split(" "))
        ).first()
        return (
            coming_soon_marker.get_image_path() if coming_soon_marker else ""
        )
    if app_version == APP_VERSION_FOUR:
        station_chargepoint_list = ChargePoint.objects.filter(
            station_id=station, charger_point_status=ACTIVE
        )
        if non_ev:
            v4_marker= MapMarkerConfigurations.objects.filter(
            map_marker_key=(
                "Fuel Site"
                if ((station.is_ev == YES and bool(station_chargepoint_list.first()) and station.station_type == 'MFG EV plus Forecourt') or station.is_ev == NO )
                else ""
            )
            ).first()
        else:
            v4_marker= MapMarkerConfigurations.objects.filter(
                map_marker_key=(
                    "EV Site"
                    if station.is_ev == YES and bool(station_chargepoint_list.first())
                    else "Fuel Site"
                )
            ).first()
        if v4_marker:
            return (
                v4_marker.get_small_image_path()
                if get_small_image else
                v4_marker.get_image_path()
            )
        return ""

    if station.is_ev == YES:
        query_string = ""
        ultra_rapid_devices = get_ultra_devices(station)
        query_string = get_station_connector_speed(
            station, ultra_rapid_devices
        )
        if len(query_string) > 0:
            marker = (
                MapMarkerConfigurations.objects.filter(
                    map_marker_key=query_string
                )
                .first()
                .get_image_path()
            )
            return marker

    if MapMarkerConfigurations.objects.filter(
        map_marker_key=station.brand
    ).first():
        marker = (
            MapMarkerConfigurations.objects.filter(
                map_marker_key=station.brand
            )
            .first()
            .get_image_path()
        )
        return marker
    return ""


# Bulk upload common functions
def field_tracking_func(fields, data_frame):
    """bulk upload field tracker function"""
    field_tracker = []
    for field in fields:
        if field not in data_frame:
            field_tracker.append(field)
    return field_tracker


def field_checker_func(fields, data_frame, row_no):
    """bulk upload field check function"""
    empty = False
    empty_fields = []
    for field in fields:
        if pd.isna(data_frame[field][row_no]):
            empty = True
            empty_fields.append(field)
        else:
            field_value = str(data_frame[field][row_no]).strip()
            if len(field_value) == 0:
                empty = True
                empty_fields.append(field)
    return [empty, empty_fields]


def field_checker_func_with_ignore_fields(fields, data_frame, row_no, ignore_field_indexes):
    """bulk upload field check function with ignored fields by index"""
    empty = False
    empty_fields = []
    for idx, field in enumerate(fields):
        if pd.isna(data_frame[field][row_no]):
            if idx in ignore_field_indexes:
                data_frame[field][row_no] = ""
            else:
                empty = True
                empty_fields.append(field)
        else:
            field_value = str(data_frame[field][row_no]).strip()
            if len(field_value) == 0:
                if idx in ignore_field_indexes:
                    data_frame[field][row_no] = ""
                else:
                    empty = True
                    empty_fields.append(field)
    return [empty, empty_fields]


def array_string_striper(arr):
    """this function strips extra spaces from strings in array"""
    stripped_arr = []
    for element in arr:
        stripped_arr.append(element.strip())
    return stripped_arr


# bulk download common function
def export_data_function_multi_tabs(
    table, columns_for_sheet, rows_for_sheet, filenames
):
    """common function to export data in sheet"""
    output = io.BytesIO()
    # Even though the final file will be in memory the module uses temp
    # files during assembly for efficiency. To avoid this on servers that
    # don't allow temp files, for example the Google APP Engine, set the
    # 'in_memory' Workbook() constructor option as shown in the docs.
    workbook = xlsxwriter.Workbook(output)
    bold = workbook.add_format({"bold": True})
    for file_index, filename in enumerate(filenames):
        worksheet = workbook.add_worksheet(filename)
        row_num = 0
        # Insertinh header row of sheet
        columns = columns_for_sheet[file_index]
        for count, column_item in enumerate(columns):
            worksheet.write(row_num, count, column_item, bold)

        # Inserting other rows in sheet
        for data in table[file_index]:
            row_num += 1
            col_num = 0
            for row in rows_for_sheet[file_index]:
                if data[row] is None or data[row] == "nan":
                    worksheet.write(row_num, col_num, str(""))
                    col_num += 1
                    continue
                if row == "payment_terminal":
                    worksheet.write(
                        row_num,
                        col_num,
                        str(
                            "|".join(
                                string_to_array_converter(
                                    data[row]
                                )
                            )
                        ).replace("Worldline", "Receipt Hero"),
                    )
                    col_num += 1
                    continue
                if row == "amenities" and filename == "Valeting Terminals":
                    worksheet.write(
                        row_num,
                        col_num,
                        str(
                            "|".join(
                                list(
                                    ServiceConfiguration.objects.filter(
                                        id__in=string_to_array_converter(
                                            data[row]
                                        )
                                    ).values_list("service_name", flat=True)
                                )
                            )
                        ),
                    )
                if row == "user_id__encrypted_email":
                    if data["user_id__key"] is None:
                        worksheet.write(row_num, col_num, "Not Available")
                        col_num += 1
                        continue
                    decrypter = Fernet(data["user_id__key"])
                    decrypted_email = decrypter.decrypt(
                        data["user_id__encrypted_email"]
                    ).decode()
                    worksheet.write(row_num, col_num, str(decrypted_email))
                    col_num += 1
                    continue
                if row == "user_id__key":
                    continue
                else:
                    worksheet.write(row_num, col_num, str(data[row]))
                col_num += 1

    # Close the workbook before sending the data.
    workbook.close()

    # Rewind the buffer.
    output.seek(0)
    # Set up the Http response.
    filename = f"{filenames[0] + str(datetime.now().date())}.xlsx"
    response = HttpResponse(
        output,
        content_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


# This is a common function to export data in the form of excel sheet.
def export_data_function(table, columns_for_sheet, rows_for_sheet, filename):
    """common function to export data in sheet"""
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    bold = workbook.add_format({"bold": True})
    worksheet = workbook.add_worksheet(filename)
    row_num = 0
    # Insertinh header row of sheet
    columns = columns_for_sheet
    for count, column_item in enumerate(columns):
        worksheet.write(row_num, count, column_item, bold)

    # Inserting other rows in sheet
    for data in table:
        row_num += 1
        col_num = 0
        for row in rows_for_sheet:
            if data[row] is None or data[row] == "nan":
                worksheet.write(row_num, col_num, str(""))
            else:
                worksheet.write(row_num, col_num, str(data[row]))
            col_num += 1
    # Close the workbook before sending the data.
    workbook.close()
    # Rewind the buffer.
    output.seek(0)
    # Set up the Http response.
    filename = f"{filename + str(datetime.now().date())}.xlsx"
    response = HttpResponse(
        output,
        content_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )
    response["Content-Disposition"] = f"attachment; filename={filename}"
    return response


# Image converter Base64 to normal file
def image_converter(image):
    """base64 image converter to upload in djnago image field"""
    image_format, imgstr = image.split(";base64,")
    imgdata = base64.b64decode(imgstr)
    image_raw_file = Image.open(io.BytesIO(imgdata))
    width, height = image_raw_file.size
    ext = image_format.split("/")[-1]
    return [imgstr, ext, width, height, image_raw_file]


# This function converts array into string
def array_to_string_converter(arr):
    """converts list to string"""
    string_converter = StringIO()
    if arr is not None:
        json.dump(arr, string_converter)
        converted_data = string_converter.getvalue()
    else:
        converted_data = None
    return converted_data


# this function converts string into array
def string_to_array_converter(value):
    """converts string to list"""
    if value:
        try:
            iinput_output = StringIO(value)
            converted_data = json.load(iinput_output)
            return list(converted_data)
        except Exception as e:
            print("Failed to load json due to error : ",e,"\n Returning None")
            traceback.print_exc()
            return {}
    return None


def remove_all_cache():
    """this function removes all cache"""
    redis_connection.delete("contactless_stations_list")
    redis_connection.set(
        "station_finder_filter_list", "[]"
    )
    redis_connection.set(
        "api_promotions_stations", "[]"
    )
    redis_connection.set(
        "api_loyalty_stations", "[]"
    )
    caching_trip_planner_data()
    redis_connection.set(
        "trip_planner_filter", "[]"
    )
    redis_connection.set("icons_from_cache", "[]")

    redis_connection.set(
        "station_finder_promotions", "[]"
    )
    redis_connection.set(
        "api_promotions_shops", "[]"
    )


def get_station_services(station):
    """this function returns station services"""
    return list(
        i.service_id.id
        for i in (
            StationServices.objects.select_related("service_id")
            .filter(~Q(service_id=None), station_id=station, deleted=NO)
            .order_by("service_id__service_unique_identifier")
        )
    )


def caching_trip_planner_data():
    """this functions caches trip planner data"""
    stations = Stations.objects.filter(deleted=NO)
    route_stations_array = []
    for station in stations:
        promotion_available = False
        marker = ""
        if station.is_ev == YES:
            query_string = ""
            ultra_rapid_devices = get_ultra_devices(station)
            if station.is_mfg == YES:
                if ultra_rapid_devices.first():
                    query_string = MFG_RAPID
                else:
                    query_string = MFG_NORMAL
            else:
                if ultra_rapid_devices.first():
                    query_string = OTHER_RAPID
                else:
                    query_string = OTHER_NORMAL
            if len(query_string) > 0:
                marker = (
                    MapMarkerConfigurations.objects.filter(
                        map_marker_key=query_string
                    )
                    .first()
                    .get_image_path()
                )
        else:
            if MapMarkerConfigurations.objects.filter(
                map_marker_key=station.brand
            ).first():
                marker = (
                    MapMarkerConfigurations.objects.filter(
                        map_marker_key=station.brand
                    )
                    .first()
                    .get_image_path()
                )
        station_services = get_station_services(station)
        connector_list = []
        services_type = {}
        if station.is_ev == YES:
            station_connectors = (
                Stations.objects.filter(id=station.id)
                .values("station_connectors__plug_type_name")
                .distinct()
            )
            services_type = {
                i.id: {
                    "id": i.id,
                    "url": i.get_image_path(),
                    "service_name": i.service_name,
                    "service_type": i.service_type,
                }
                for i in (ServiceConfiguration.objects.all())
            }
            for station_connector in station_connectors:
                if station_connector["station_connectors__plug_type_name"]:
                    connector = ConnectorConfiguration.objects.filter(
                        connector_plug_type_name=station_connector[
                            "station_connectors__plug_type_name"
                        ]
                    )
                    if connector.first():
                        connector_list.append(
                            {
                                "id": str(connector.first().id),
                                "connector": station_connector[
                                    "station_connectors__plug_type_name"
                                ],
                                "image": connector.first().get_image_path(),
                            }
                        )
        route_stations_array.append(
            {
                "id": station.id,
                "is_mfg": station.is_mfg,
                "station_id": station.station_id,
                "station_name": station.station_name,
                "brand": station.brand,
                "post_code": station.post_code,
                "brand_logo": marker,
                "lat": station.latitude,
                "lng": station.longitude,
                "station_address": get_station_address(station),
                "promotion_available": promotion_available,
                "stores": [
                    services_type[service]
                    for service in station_services
                    if services_type
                    and services_type[service]["service_type"] != "Amenity"
                    and service in services_type
                ],
                "amenities": [
                    services_type[service]
                    for service in station_services
                    if services_type
                    and services_type[service]["service_type"] == "Amenity"
                    and service in services_type
                ],
                "connectors": connector_list,
            }
        )
    redis_connection.set(
        "trip_planner_api_stations",
        array_to_string_converter(list(route_stations_array)),
    )


# Function to remove spaces from string
def remove_whitespace(value):
    """remove whitespaces from string"""
    return "".join(value.split())


def randon_string_generator():
    """random string genrator"""
    return "".join(
        secrets.choice(string.ascii_letters + string.digits) for _ in range(15)
    )


def decrypt_user_mail(user):
    """this function decrypts user email"""
    user_key = user.key
    decrypter = Fernet(user_key)
    return decrypter.decrypt(user.encrypted_email).decode()


def upload_progress_database(
    type_message, bulk_upload_progress, total_data_count
):
    """this function upload progress"""
    if bulk_upload_progress.first():
        bulk_upload_progress.update(
            total_rows_count=total_data_count,
            uploaded_rows_count=0,
            uploading_status="uploading",
            created_date=timezone.localtime(timezone.now()),
        )
    else:
        BulkUploadProgress.objects.create(
            uploaded_for=type_message,
            total_rows_count=total_data_count,
            uploaded_rows_count=0,
            uploading_status="uploading",
            created_date=timezone.localtime(timezone.now()),
        )


def upload_progress_errors_database(type_message, error_records):
    """this function upload progress"""
    if error_records.first():
        error_records.update(
            errors=array_to_string_converter([]),
            ready_to_export=NO,
            created_date=timezone.localtime(timezone.now()),
        )
    else:
        BulkUploadErrorMessages.objects.create(
            uploaded_for=type_message,
            errors=array_to_string_converter([]),
            ready_to_export=NO,
            created_date=timezone.localtime(timezone.now()),
        )


def set_token_cache(token_data, request, response, authorization):
    """this function set token"""
    hashed_token = handler.hash(str(token_data[0]))
    hashed_authorization_id = handler.hash(f"{authorization.first().id}")
    if request.COOKIES.get("remember_me", "default") == YES:
        response.set_cookie(
            "token",
            str(token_data[0]),
            max_age=TOKEN_COOKIE_MAX_AGE,
        )
        response.set_cookie(
            "refresh_token",
            token_data[3],
            max_age=TOKEN_COOKIE_MAX_AGE,
        )
        response.set_cookie("remember_me", YES, max_age=TOKEN_COOKIE_MAX_AGE)
        response.set_cookie(
            "token_verification_string",
            hashed_token,
            max_age=TOKEN_COOKIE_MAX_AGE,
        )
        response.set_cookie(
            "token_auth",
            hashed_authorization_id,
            max_age=TOKEN_COOKIE_MAX_AGE,
        )
    else:
        response.set_cookie("token", str(token_data[0]))
        response.set_cookie("refresh_token", token_data[3])
        response.set_cookie("remember_me", YES)
        response.set_cookie("token_verification_string", hashed_token)
        response.set_cookie("token_auth", hashed_authorization_id)
    return response


def date_formater_for_contactless_receipts(date, is_swarco_receipt=False):
    """This function returns formated date for app contcatless receipts"""
    if is_swarco_receipt:
        if validate_dateformat(date,"%Y-%m-%d %H:%M:%S"):
            return timezone.localtime(
                timezone.datetime.strptime(date, "%Y-%m-%d %H:%M:%S").replace(
                    tzinfo=pytz.UTC
                )
            ).strftime("%Y-%m-%dT%H:%M:%S.%f%z")
        else:
            return date
    return timezone.localtime(
        timezone.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S.%f%z")
    ).strftime("%Y-%m-%dT%H:%M:%S.%f%z")


def filter_function_for_base_configuration(data_key, static_variable):
    """this function gets filtered data from base configuration"""
    base_config_obj = redis_connection.get(data_key)
    if not base_config_obj:
        base_config_obj = BaseConfigurations.objects.filter(
            base_configuration_key=data_key
        ).first()
        if base_config_obj is None:
            redis_connection.set(f"{data_key}", static_variable)
            return static_variable
        redis_connection.set(
            f"{data_key}", base_config_obj.base_configuration_value
        )
        return base_config_obj.base_configuration_value
    return base_config_obj.decode("utf-8")

def base_configuration(data_key, data_value=None, forceUpdate=False):
    if forceUpdate:
        value_str = str(data_value)
        redis_connection.set(data_key, value_str)
        BaseConfigurations.objects.update_or_create(
            base_configuration_key=data_key,
            defaults={
                'base_configuration_value': value_str,
                'created_date': timezone.localtime(timezone.now())
            }
        )
        return value_str

    cached_value = redis_connection.get(data_key)
    if cached_value:
        return cached_value.decode('utf-8')

    base_config_obj = BaseConfigurations.objects.filter(
        base_configuration_key=data_key
    ).first()

    if not base_config_obj:
        if data_value is None:
            return None
        
        base_config_obj = BaseConfigurations.objects.create(
            base_configuration_key=data_key,
            base_configuration_value=str(data_value),
            created_date=timezone.localtime(timezone.now())
        )

    redis_connection.set(data_key, base_config_obj.base_configuration_value)
    return base_config_obj.base_configuration_value


# Loyalty id added for sending notifications from Loyalty module
def send_push(
    subject,
    msg,
    registration_tokens,
    image,
    screens,
    inapp_notification,
    reference_id=""
):
    """This function triggers FCM Notifications"""
    try:
        print("Registration tokens count =======================> ", len(registration_tokens))

        push_notification_message = messaging.Notification(
            title=subject,
            body=msg,
            image=image,
        )
        success_count = 0
        failure_count = 0
        # Process tokens in batches
        for i in range(0, len(registration_tokens), 500):
            batch_tokens = registration_tokens[i:i + 500]
            # Create and send messages for each token in the batch
            results = []
            for token in batch_tokens:
                message = messaging.Message(
                    notification=push_notification_message,
                    data={
                        "screen": screens,
                        "reference_id": reference_id,
                        "inapp_notification": inapp_notification
                    },
                    token=base64.b64decode(token).decode("utf-8")
                )
                try:
                    response = messaging.send(message)
                    results.append((token, response, True))
                    success_count += 1
                except Exception as e:
                    print('='*50, e)
                    results.append((token, str(e), False))
                    failure_count += 1
            # Log results for the batch
            print(f"Batch {i // 500 + 1} results:")
            print(f"Success count for batch {i // 500 + 1}: {success_count}")
            print(f"Failure count for batch {i // 500 + 1}: {failure_count}")
        print(f"Total successful messages: {success_count}")
        print(f"Total failed messages: {failure_count}")
        return success_count
    except Exception as error:
        print(f"An error occurred: {error}")


def custom_round_function(value, digit_accuracy=0, is_float=True):
    """this function overcomes the drawbacks  of 'round' function"""
    decimal.getcontext().rounding = decimal.ROUND_HALF_UP
    rounded_value = round(decimal.Decimal(str(value)), digit_accuracy)
    return float(str(rounded_value)) if is_float else rounded_value


def get_blocked_emails_and_phone_numbers():
    """get blocked emails and phone numbers"""

    blocked_phone_numbers = BaseConfigurations.objects.filter(
        base_configuration_key=BLOCKED_USERS_PHONE_LIST
    ).first()

    blocked_phone_numbers = (
        list(json.loads(blocked_phone_numbers.base_configuration_value))
        if blocked_phone_numbers
        else []
    )

    blocked_emails = BaseConfigurations.objects.filter(
        base_configuration_key=BLOCKED_USERS_EMAILS_LIST
    ).first()

    blocked_emails = (
        list(json.loads(blocked_emails.base_configuration_value))
        if blocked_emails
        else []
    )
    blocked_phone_numbers.reverse()
    blocked_emails.reverse()
    return [blocked_emails, blocked_phone_numbers]

def is_base64(string_value):
    """check if the value is basee64"""
    try:
        base64.b64decode(string_value, validate=True)
        return True
    except Exception:
        return False

def validate_dateformat(date_text,date_format):
    try:
        if date_text != datetime.strptime(date_text, date_format).strftime(date_format):
            raise ValueError
        return True
    except ValueError:
        return False
    
def get_node_secret():
    token = redis_connection.get("NODE_SECRET_TOKEN")
    if not token:
        node_backend_token = BaseConfigurations.objects.filter(
            base_configuration_key="NODE_SECRET_TOKEN"
        ).values('base_configuration_value').first()
        token = node_backend_token['base_configuration_value']
    else:
        token = token.decode('utf-8')
    return token

def get_data_from_cache(key):
    value = redis_connection.get(key)
    if isinstance(value, bytes):
        value = value.decode()
    else:
        value = BaseConfigurations.objects.filter(base_configuration_key = key).first().base_configuration_value
        redis_connection.set(key, value)
    return value if value else VAT_PERCENTAGE

def ensure_str(token):
    if isinstance(token, bytes):
        return token.decode('utf-8')
    return token

def get_cdr_details(session):
    """this function gets cdr details for ocpi session"""
    cdr_list = OCPIChargeDetailRecords.objects.filter(
        charging_session_id_id=session
        )
    return cdr_list