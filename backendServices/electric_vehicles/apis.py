"""Electric vehicles apis"""
# Date - 16/11/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on APIs related
#                       to electric vehicles.
#   Name            - Electric vehicle APIs
#   Modified by     - Shivkumar Kumbhar
#   Modified date   - 29/03/2023


# These are all the imports that we are exporting from
# different module's from project or library.

import json
import threading
import requests

from django.conf import settings
from django.db.models import Q
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.utils import timezone

import decouple
from decouple import config

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from passlib.hash import django_pbkdf2_sha256 as handler
from cryptography.fernet import Fernet

# pylint:disable=import-error
from sharedServices.common import (
    array_to_string_converter,
    handle_concurrent_user_login,
    redis_connection,
    string_to_array_converter,
    decrypt_user_mail,
)
from sharedServices.email_common_functions import (
    email_sender,
)
from sharedServices.constants import (
    NOT_AVAILABLE,
    VEHCILE_NOT_ADDED,
    VEHICLE_ID_NOT_PROVIDED,
    VEHICLE_NOT_FOUND,
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    SECRET_KEY_NOT_PROVIDED,
    SECRET_KEY_IN_VALID,
    REQUEST_API_TIMEOUT,
    DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET,
    GET_REQUEST,
)
from sharedServices.model_files.vehicle_models import (
    ElectricVehicleDatabase,
    UserEVs
)
from sharedServices.model_files.app_user_models import MFGUserEV
from backendServices.backend_app_constants import (
    MULTIPLE_LOGIN,
    UNAUTHORIZED,
)
from backendServices.auths.serializers import UserGetDetailsSerializer
from sharedServices.sentry_tracers import traced_request
from .db_operators import (
    insert_ev_details_func,
    update_ev_details_func,
    upload_ev_images_to_blob,
)
from .ev_helper_functions import (
    electric_vehicle_details_extractor,
    find_ev_model_name_by_splitting,
    ev_range_formatter,
    ev_name_formatter,
    energy_consumption_calculator,
)

CACHE_TTL = getattr(settings, "CACHE_TTL", DEFAULT_TIMEOUT)

BLOB_CDN_URL = config("DJANGO_APP_CDN_BASE_URL")


def bulk_create_and_update_ev_func(*arg):
    """this function is used to create and update evs"""
    list_of_arg = list(arg)
    try:
        insert_ev_details_func(list_of_arg[0])
        update_ev_details_func(list_of_arg[1])
        upload_ev_images_to_blob(list_of_arg[2])
    except COMMON_ERRORS as error:
        print(f"Bulk uploading ev data intrrupted due to -> {error}")


class RequestElectricVehicleDatabaseAPI(APIView):
    """Electric vehicle cronjonb API"""

    @classmethod
    def post(cls, electric_vehicle_request):
        """this is a cronjob api to fetch all evs from dvla database"""
        try:
            secret_key = electric_vehicle_request.data.get("secret_key", None)

            if secret_key is None:
                return SECRET_KEY_NOT_PROVIDED
            if not handler.verify(secret_key, DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET):
                return SECRET_KEY_IN_VALID
            # ev vehicles database fetch api call
            try:
                response = traced_request(
                    GET_REQUEST,
                    f"{config('DJANGO_APP_EV_DATABASE_BEV_URL')}",timeout=REQUEST_API_TIMEOUT
                )
            except (
                decouple.UndefinedValueError,
                requests.exceptions.ConnectionError,
            ):
                print(f"Failed to fetched data from ev database")
                print(f"Response -> {json.loads(response.content)}")
                return Response(
                    {
                        "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                        "status": False,
                        "message": "Failed to fetched data from ev \
                            database provider for bev's",
                    }
                )
            update_ev_array_list = []
            create_ev_array_list = []
            ev_images_array_list = []
            if response.status_code == 200:
                print("Successfully fetched Electric Vehicled details")
                ev_data = json.loads(response.content)
                for ev_vehicle in ev_data:
                    electric_vehicle_exists = (
                        ElectricVehicleDatabase.objects.filter(
                            vehicle_id=f"{ev_vehicle['Vehicle_ID']}",
                            ev_type="bev",
                        )
                    )
                    ev_images_array_list.append(
                        {
                            "vehicle_id": f"{ev_vehicle['Vehicle_ID']}",
                            "images": ev_vehicle["Images"],
                        }
                    )
                    if electric_vehicle_exists.first():
                        update_ev_array_list.append(ev_vehicle)
                    else:
                        create_ev_array_list.append(
                            ElectricVehicleDatabase(
                                misc_body=ev_vehicle["Misc_Body"],
                                vehicle_id=f"{ev_vehicle['Vehicle_ID']}",
                                vehicle_make=ev_vehicle["Vehicle_Make"],
                                vehicle_model=ev_vehicle["Vehicle_Model"],
                                vehicle_model_version=ev_vehicle[
                                    "Vehicle_Model_Version"
                                ],
                                range_real=ev_vehicle["Range_Real"],
                                battery_capacity_useable=ev_vehicle[
                                    "Battery_Capacity_Useable"
                                ],
                                charge_plug=ev_vehicle["Charge_Plug"],
                                ev_type="bev",
                                fastcharge_plug=ev_vehicle["Fastcharge_Plug"],
                                fastcharge_chargespeed=ev_vehicle[
                                    "Fastcharge_ChargeSpeed"
                                ],
                                max_charge_speed=ev_vehicle[
                                    "Fastcharge_Power_Max"
                                ],
                                electric_vehicle_object=(
                                    array_to_string_converter([ev_vehicle])
                                ),
                            )
                        )

            else:
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "status": False,
                        "message": response.text,
                    }
                )

            # hybrid ev vehicles database fetch api call
            try:
                response = traced_request(
                    GET_REQUEST,
                    f"{config('DJANGO_APP_EV_DATABASE_PHEV_URL')}",timeout=REQUEST_API_TIMEOUT
                )
            except (
                decouple.UndefinedValueError,
                requests.exceptions.ConnectionError,
            ):
                print("Failed to fetch hybrid EV vehicle")
                print(f"Response -> {json.loads(response.content)}")
                return Response(
                    {
                        "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                        "status": False,
                        "message": "Failed to fetched data from ev"
                        + "database provider for phev's",
                    }
                )
            if response.status_code == 200:
                print(
                    "Successfully fetched Hybrid Electric Vehicled details"
                )
                ev_data = json.loads(response.content)
                for ev_vehicle in ev_data:
                    ev_images_array_list.append(
                        {
                            "vehicle_id": f"{ev_vehicle['Vehicle_ID']}",
                            "images": ev_vehicle["Images"],
                        }
                    )
                    electric_vehicle_exists = (
                        ElectricVehicleDatabase.objects.filter(
                            vehicle_id=f"{ev_vehicle['Vehicle_ID']}",
                            ev_type="phev",
                        )
                    )
                    if electric_vehicle_exists.first():
                        update_ev_array_list.append(ev_vehicle)
                    else:
                        create_ev_array_list.append(
                            ElectricVehicleDatabase(
                                misc_body=ev_vehicle["Misc_Body"],
                                vehicle_id=f"{ev_vehicle['Vehicle_ID']}",
                                vehicle_make=ev_vehicle["Vehicle_Make"],
                                vehicle_model=ev_vehicle["Vehicle_Model"],
                                vehicle_model_version=ev_vehicle[
                                    "Vehicle_Model_Version"
                                ],
                                range_real=ev_vehicle["Range_Real"],
                                battery_capacity_useable=ev_vehicle[
                                    "Battery_Capacity_Useable"
                                ],
                                charge_plug=ev_vehicle["Charge_Plug"],
                                ev_type="phev",
                                fastcharge_plug=ev_vehicle["Fastcharge_Plug"],
                                fastcharge_chargespeed=ev_vehicle[
                                    "Fastcharge_ChargeSpeed"
                                ],
                                max_charge_speed=ev_vehicle[
                                    "Fastcharge_Power_Max"
                                ],
                                electric_vehicle_object=(
                                    array_to_string_converter([ev_vehicle])
                                ),
                            )
                        )
            else:
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "status": False,
                        "message": response.text,
                    }
                )

            start_time = threading.Thread(
                target=bulk_create_and_update_ev_func,
                args=[
                    create_ev_array_list,
                    update_ev_array_list,
                    ev_images_array_list,
                ],
                daemon=True
            )
            start_time.start()
            redis_connection.delete(
                "electric_vehicle_cache_data"
            )

            redis_connection.set(
                "conf_connector_list", array_to_string_converter(None)
            )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Cron job for electric vehicle executed "
                    + "successfully.",
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Request Electric Vehicle Data base API failed for user -> \
                    {electric_vehicle_request.user.id} due to exception -> \
                        {exception}"
            )
            return API_ERROR_OBJECT


class ElectricVehiclesData(APIView):
    """Electric vehicle list API"""

    @classmethod
    def get(cls, electric_vehicle_data):
        """get request to get ev  details list"""
        try:
            if not electric_vehicle_data.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                electric_vehicle_data.user.id, electric_vehicle_data.auth
            ):
                return MULTIPLE_LOGIN
            cahed_ev_data = redis_connection.get("electric_vehicle_cache_data")
            if cahed_ev_data:
                data = string_to_array_converter(cahed_ev_data.decode("utf-8"))
            else:
                ev_datas = list(
                    ElectricVehicleDatabase.objects
                    .order_by(
                        "vehicle_make",
                        "vehicle_model",
                        "vehicle_model_version",
                    )
                    .values(
                        "id",
                        "misc_body",
                        "vehicle_make",
                        "vehicle_model",
                        "vehicle_model_version",
                        "battery_capacity_useable",
                        "fastcharge_chargespeed",
                        "max_charge_speed",
                        "ev_thumbnail_image",
                        "ev_image"
                    )
                )
                data = [
                    {
                        "id": ev_data["id"],
                        "misc_body": ev_data["misc_body"],
                        "vehicle_make": ev_data["vehicle_make"],
                        "vehicle_model": ev_data["vehicle_model"],
                        "vehicle_model_version": ev_data[
                            "vehicle_model_version"
                        ],
                        "battery_capacity_useable": ev_data[
                            "battery_capacity_useable"
                        ],
                        "fastcharge_chargespeed": ev_data[
                            "fastcharge_chargespeed"
                        ],
                        "max_charge_speed": ev_data["max_charge_speed"],
                        "ev_image": (
                            BLOB_CDN_URL + ev_data["ev_thumbnail_image"]
                        ),
                    }
                    for ev_data in ev_datas if ev_data['ev_thumbnail_image'] and ev_data['ev_image']
                ]
                redis_connection.set(
                    "electric_vehicle_cache_data",
                    array_to_string_converter(data)
                )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Electric vehicles fetched.",
                    "data": data,
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Electric Vehicles Data API failed for user -> \
                    {electric_vehicle_data.user.id} due to exception -> \
                        {exception}"
            )
            return API_ERROR_OBJECT


class ElectricVehiclesDetailsAPI(APIView):
    """Electric vehicle details API"""

    @classmethod
    def post(cls, electric_vehicle_details):
        """get request to get detailed info of ev"""
        try:
            if not electric_vehicle_details.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                electric_vehicle_details.user.id, electric_vehicle_details.auth
            ):
                return MULTIPLE_LOGIN

            vehicle_id = electric_vehicle_details.data.get("vehicle_id", None)
            vehicle_registration_number = electric_vehicle_details.data.get(
                "vehicle_registration_number", None
            )
            if vehicle_id is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": VEHICLE_ID_NOT_PROVIDED,
                    }
                )
            ev_data = ElectricVehicleDatabase.objects.filter(
                id=int(vehicle_id)
            ).first()
            user_ev_data = UserEVs.objects.filter(
                user_id=electric_vehicle_details.user,
                vehicle_id_id=int(vehicle_id),
                vehicle_registration_number=vehicle_registration_number
            ).first()
            if ev_data is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": VEHICLE_NOT_FOUND,
                    }
                )

            data = electric_vehicle_details_extractor(ev_data, user_ev_data)
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Electric vehicle details fetched.",
                    "data": data,
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Electric Vehicles Details API failed for user -> \
                    {electric_vehicle_details.user.id} due to exception -> \
                        {exception}"
            )
            return API_ERROR_OBJECT


class ElectricVehiclesDetailsWithNumberPlateAPI(APIView):
    """Electric vehicle details API"""

    @classmethod
    def post(cls, electric_vehicle_details_number):
        """get electric details using number plate of vehicle"""
        try:
            if not electric_vehicle_details_number.auth:
                return UNAUTHORIZED
            if not handle_concurrent_user_login(
                electric_vehicle_details_number.user.id,
                electric_vehicle_details_number.auth,
            ):
                return MULTIPLE_LOGIN
            plate_number = electric_vehicle_details_number.data.get(
                "plate_number", None
            )

            if plate_number is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Plate number not provided.",
                    }
                )

            search_dvla_response = traced_request(
                GET_REQUEST,
                f'{config("DJANGO_APP_EV_DVLA_SEARCH_BASE_URL")}'
                + "?apikey="
                + f'{config("DJANGO_APP_EV_DVLA_API_KEY")}'
                + "&licencePlate="
                + f"{plate_number}", timeout=REQUEST_API_TIMEOUT
            )

            if search_dvla_response.status_code != 200:
                print(
                    "Failed to fetch vehicle details on the basis of Number Plate"
                )
                print(
                    f"Response -> {json.loads(search_dvla_response.content)}"
                )
                return Response(
                    {
                        "status_code": search_dvla_response.status_code,
                        "status": False,
                        "message": "Failed to fetch vehicle details.",
                    }
                )
            print(
                "Successfully fetched vehicle details on the basis of Number Plate"
            )
            response_data = json.loads(search_dvla_response.content)
            if "error" in list(response_data.keys()):
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "status": False,
                        "message": response_data["message"]
                        if response_data["error"] == 0
                        else "Invalid vehicle data provided",
                    }
                )

            ev_data = ElectricVehicleDatabase.objects.filter(
                ~Q(ev_image=None),
                ~Q(ev_thumbnail_image=None),
                vehicle_make=response_data["make"],
                vehicle_model=response_data["model"],
            )

            if ev_data.first():
                data = electric_vehicle_details_extractor(ev_data.first())
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": "Electric vehicle details fetched.",
                        "data": {
                            "ev_details": data,
                            "details_matched": True,
                            "plate_number": plate_number
                        },
                    }
                )

            if ev_data.first() is None:
                data = find_ev_model_name_by_splitting(
                    response_data["make"],
                    response_data["model"],
                )
                if len(data) == 0:
                    return Response(
                        {
                            "status_code": status.HTTP_404_NOT_FOUND,
                            "status": False,
                            "message": "Vehicle not found for provided "
                            + "number plate.",
                        }
                    )
                return Response(
                    {
                        "status_code": status.HTTP_200_OK,
                        "status": True,
                        "message": (
                            "We were unable to fetch vehicles for provided "
                            + "number so, listed are the similar vehicles."
                        ),
                        "data": {
                            "ev_details": data,
                            "details_matched": False,
                            "plate_number": plate_number
                        },
                    }
                )
            return response_data
        except COMMON_ERRORS + (
            requests.exceptions.ConnectionError,
        ) as exception:
            print(
                f"Electric Vehicles Details With Number Plate API failed \
                    for user -> {electric_vehicle_details_number.user.id} \
                        due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


class AddUserEVAPI(APIView):
    """Add user EV API"""

    @classmethod
    def post(cls, add_user_ev):
        """post method to add user ev"""
        try:
            if not add_user_ev.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                add_user_ev.user.id, add_user_ev.auth
            ):
                return MULTIPLE_LOGIN
            vehicle_id = add_user_ev.data.get("vehicle_id", None)
            user_vehicle_id = add_user_ev.data.get("user_vehicle_id", None)
            vehicle_registration_number = add_user_ev.data.get(
                "vehicle_registration_number", None
            )
            vehicle_nickname = add_user_ev.data.get("vehicle_nickname", None)
            user_mail = decrypt_user_mail(add_user_ev.user)
            if (
                vehicle_id is None
            ):
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Required data not provided",
                    }
                )
            ev_data = ElectricVehicleDatabase.objects.filter(
                ~Q(ev_image=None), ~Q(ev_thumbnail_image=None), id=vehicle_id
            )
            if ev_data.first() is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": VEHICLE_NOT_FOUND,
                    }
                )
            ev_data = ev_data.values(
                "id",
                "misc_body",
                "vehicle_id",
                "vehicle_make",
                "vehicle_model",
                "vehicle_model_version",
                "range_real",
                "battery_capacity_useable",
                "charge_plug",
                "fastcharge_plug",
                "fastcharge_chargespeed",
                "max_charge_speed",
                "ev_image",
                "electric_vehicle_object",
            ).first()
            user_evs = UserEVs.objects.filter(
                user_id=add_user_ev.user
            )
            vehicle = user_evs.filter(
                vehicle_id_id=int(vehicle_id)
            )

            if user_vehicle_id:
                if user_evs.filter(
                    id = user_vehicle_id,
                    vehicle_registration_number=vehicle_registration_number
                ).exists():
                    if user_evs.filter(
                        id = user_vehicle_id
                    ).first().vehicle_nickname != vehicle_nickname:
                        user_evs.filter(id=user_vehicle_id).update(
                            vehicle_nickname=vehicle_nickname,
                            updated_date=timezone.localtime(timezone.now())
                        )
                    else:
                        return Response(
                            {
                                "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                                "status": False,
                                "message": "A vehicle with this registration number has already been added."
                            }
                        )
                else:
                    if user_evs.filter(
                        vehicle_registration_number=vehicle_registration_number
                    ).exists():
                        return Response(
                            {
                                "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                                "status": False,
                                "message": "A vehicle with this registration number has already been added."
                            }
                        )
                    else:
                        user_evs.filter(id=user_vehicle_id).update(
                            vehicle_registration_number=vehicle_registration_number,
                            vehicle_nickname=vehicle_nickname,
                            updated_date=timezone.localtime(timezone.now())
                        )
                
                
            else:
                if vehicle_registration_number and (
                        user_evs.filter(
                            vehicle_registration_number=vehicle_registration_number
                        ).exists()):
                    return Response(
                        {
                            "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                            "status": False,
                            "message": "A vehicle with this registration number has already been added."
                        }
                    )
                UserEVs.objects.create(
                    vehicle_id_id=int(vehicle_id),
                    user_id=add_user_ev.user,
                    vehicle_nickname=vehicle_nickname,
                    vehicle_registration_number=vehicle_registration_number,
                    created_date=timezone.localtime(timezone.now()),
                    updated_date=timezone.localtime(timezone.now())
                )
                user_ev_added_confirmation_mail = config(
                    "DJANGO_APP_ADD_EV_CONFIRMATION_MAIL_ID"
                )
                decrypter = Fernet(add_user_ev.user.key)
                user_first_name = decrypter.decrypt(
                    add_user_ev.user.first_name
                ).decode()
                to_emails = [(user_mail, user_first_name)]
                ev_details = string_to_array_converter(
                    ev_data["electric_vehicle_object"]
                )
                # formatting ev range
                ev_range = ev_range_formatter(
                    [
                        ev_details[0]["Range_Real_WHwy"],
                        ev_details[0]["Range_Real_WCmb"],
                        ev_details[0]["Range_Real_WCty"],
                        ev_details[0]["Range_Real_BHwy"],
                        ev_details[0]["Range_Real_BCmb"],
                        ev_details[0]["Range_Real_BCty"],
                    ]
                )

                mail_data = {
                    "user_name": f"{user_first_name}".capitalize(),
                    "vehicle_id": ev_data["vehicle_id"],
                    "ev_name": ev_name_formatter(
                        [
                            ev_data["vehicle_make"],
                            ev_data["vehicle_model"],
                            ev_data["vehicle_model_version"],
                        ]
                    ),
                    "range": ev_range,
                    "battery": ev_data["battery_capacity_useable"]
                    if ev_data["battery_capacity_useable"]
                    and ev_data["battery_capacity_useable"] != "0"
                    else NOT_AVAILABLE,
                    "fast_port": ev_data["fastcharge_plug"]
                    if ev_data["fastcharge_plug"]
                    else NOT_AVAILABLE,
                    "fast_charge": ev_details[0]["Fastcharge_Power_Max"]
                    if ev_details[0]["Fastcharge_Power_Max"]
                    and ev_details[0]["Fastcharge_Power_Max"] != "0"
                    else "0",
                    "port_location": ev_details[0]["Fastcharge_Plug_Location"]
                    if ev_details[0]["Fastcharge_Plug_Location"]
                    else NOT_AVAILABLE,
                    "co2": ev_details[0]["Efficiency_Real_CO2"]
                    if ev_details[0]["Efficiency_Real_CO2"]
                    else "0",
                    "ev_image": f"{BLOB_CDN_URL}{ev_data['ev_image']}",
                    "energy_consumption": energy_consumption_calculator(
                        ev_details[0]["Range_Real"],
                        ev_details[0]["Battery_Capacity_Useable"],
                    ),
                }
                email_sender(user_ev_added_confirmation_mail, to_emails, mail_data)
            user = MFGUserEV.objects.get(id=add_user_ev.user.id)
            serializer = UserGetDetailsSerializer(
                user, context={"token": add_user_ev.auth}
            )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": f"Electric Vehicle {'added' if user_vehicle_id else 'updated'} successfully.",
                    "data": serializer.data,
                }
            )
        except COMMON_ERRORS:
            return API_ERROR_OBJECT


class RemoveUserEVAPI(APIView):
    """Remove user EV API"""

    @classmethod
    def post(cls, remove_user):
        """post method to remove user ev from user's added evs"""
        try:
            if not remove_user.auth:
                return UNAUTHORIZED
            if not handle_concurrent_user_login(
                remove_user.user.id, remove_user.auth
            ):
                return MULTIPLE_LOGIN
            vehicle_id = remove_user.data.get("vehicle_id", None)
            if vehicle_id is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": VEHICLE_ID_NOT_PROVIDED,
                    }
                )
            user_evs = UserEVs.objects.filter(
                id=vehicle_id,
                user_id=remove_user.user
            )
            if not user_evs.first():
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": VEHCILE_NOT_ADDED,
                    }
                )
            user_evs.delete()
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Electric Vehicle removed successfully.",
                    "data": UserGetDetailsSerializer(
                        MFGUserEV.objects.get(id=remove_user.user.id),
                        context={"token": remove_user.auth},
                    ).data,
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Remove user EV Default API failed for user -> \
                    {remove_user.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


class UserEVListAPI(APIView):
    """Returns list of user EV API"""

    @classmethod
    def get(cls, user_list_ev_request):
        """API to return list of user evs"""
        try:
            if not user_list_ev_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                user_list_ev_request.user.id, user_list_ev_request.auth
            ):
                return MULTIPLE_LOGIN

            user_evs = UserEVs.objects.filter(
                user_id=user_list_ev_request.user
            ).order_by('-created_date')
            user_default_ev = UserEVs.objects.filter(
                user_id=user_list_ev_request.user,
                default=True
            ).first()
            data = [
                {
                    "id": row_ev.vehicle_id.id,
                    "user_vehicle_id": row_ev.id,
                    "default": bool(
                        user_default_ev and row_ev.id == user_default_ev.id
                        or (not user_default_ev and count == 0)
                    ),
                    "vehicle_make": row_ev.vehicle_id.vehicle_make,
                    "vehicle_model": row_ev.vehicle_id.vehicle_model,
                    "vehicle_model_version": row_ev.vehicle_id.vehicle_model_version,
                    "battery_capacity_useable": row_ev.vehicle_id.battery_capacity_useable,
                    "fastcharge_chargespeed": row_ev.vehicle_id.fastcharge_chargespeed,
                    "vehicle_nickname": row_ev.vehicle_nickname,
                    "vehicle_registration_number": row_ev.vehicle_registration_number,
                    "ev_image": row_ev.vehicle_id.get_ev_image(),
                }
                for count, row_ev in enumerate(user_evs)
            ]
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Successfullly fetched user elctric vehicles.",
                    "data": data,
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"User EV List API failed for user -> \
                    {user_list_ev_request.user.id} due to exception ->\
                          {exception}"
            )
            return API_ERROR_OBJECT


class MakeEVDefaultAPI(APIView):
    """Returns list of user EV API"""

    @classmethod
    def post(cls, make_ev_default):
        """post request make ev deafult"""
        try:
            if not make_ev_default.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                make_ev_default.user.id, make_ev_default.auth
            ):
                return MULTIPLE_LOGIN

            vehicle_id = make_ev_default.data.get("vehicle_id", None)
            if vehicle_id is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": VEHICLE_ID_NOT_PROVIDED,
                    }
                )

            user_evs = UserEVs.objects.filter(
                id=vehicle_id
            )
            if user_evs.first():
                UserEVs.objects.filter(
                    user_id=make_ev_default.user
                ).update(default=False)
                user_evs.update(default=True)
            else:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": VEHCILE_NOT_ADDED,
                    }
                )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Successfullly added default electric vehicle.",
                    "data": UserGetDetailsSerializer(
                        MFGUserEV.objects.get(id=make_ev_default.user.id),
                        context={"token": make_ev_default.auth},
                    ).data,
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Make EV Default API failed for user -> \
                    {make_ev_default.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


class EVFiltersAPI(APIView):
    """Returns list of filters to filter EV API"""

    @classmethod
    def get(cls, ev_filters):
        """get request to fetch all ev filters"""
        try:
            if not ev_filters.auth:
                return UNAUTHORIZED
            if not handle_concurrent_user_login(
                ev_filters.user.id, ev_filters.auth
            ):
                return MULTIPLE_LOGIN
            ev_models_queryset = (
                ElectricVehicleDatabase.objects.filter(
                    ~Q(ev_image=None),
                    ~Q(ev_thumbnail_image=None),
                )
                .values("vehicle_make")
                .distinct()
            )
            vehicle_models = [
                vehicle_model["vehicle_make"]
                for vehicle_model in ev_models_queryset
            ]

            ev_bodies_queryset = (
                ElectricVehicleDatabase.objects.filter(
                    ~Q(ev_image=None),
                    ~Q(ev_thumbnail_image=None),
                )
                .values("misc_body")
                .distinct()
            )
            vehicle_bodies = [
                vehicle_body["misc_body"]
                for vehicle_body in ev_bodies_queryset
            ]

            data = {
                "vehicle_make": vehicle_models,
                "vehicle_bodies": vehicle_bodies,
            }

            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Successfullly fetched EV filters.",
                    "data": data,
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"EV Filters API failed for user -> {ev_filters.user.id}\
                      due to exception -> {exception}"
            )
            return API_ERROR_OBJECT
