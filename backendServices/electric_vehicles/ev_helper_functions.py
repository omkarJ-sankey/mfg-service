"""Electric vehicles APIs helper functions"""

# Date - 31/01/2022


# File details-
#   Author          - Manish Pawar
#   Description     - This file contains function to handle ev data.
#   Name            - Electric vehicle helper functions
#   Modified by     - Manish Pawar
#   Modified date   - 31/01/2022


# These are all the imports that we are exporting from different
# module's from project or library.
import math
from fuzzywuzzy import fuzz

from django.db.models import Q

from decouple import config

# pylint:disable=import-error
from sharedServices.constants import (
    DEFAULT_CONNECTOR_IMAGE,
    EV_MODEL_COMPARER_MATCH_PERCENTAGE,
    NOT_AVAILABLE,
)
from sharedServices.model_files.vehicle_models import ElectricVehicleDatabase
from sharedServices.model_files.config_models import ConnectorConfiguration
from sharedServices.common import custom_round_function

from .app_level_constants import (
    APPROX_PERFECT_MATCH,
    ZERO_MATCHED,
    KM_TO_MILES_CONVERSION_FACTOR,
)

BLOB_CDN_URL = config("DJANGO_APP_CDN_BASE_URL")


def kilometer_to_miles_converter(value_in_km):
    """this function converts km values to miles"""
    return math.ceil(float(value_in_km) * KM_TO_MILES_CONVERSION_FACTOR)


def electric_vehicle_details_extractor(ev_data, user_ev_data=None):
    """this function exctracts details of ev"""
    data = {
        "id": ev_data.id,
        "misc_body": (
            ev_data.misc_body if ev_data.misc_body else NOT_AVAILABLE
        ),
        "vehicle_id": ev_data.vehicle_id,
        "vehicle_make": ev_data.vehicle_make,
        "vehicle_model": ev_data.vehicle_model,
        "vehicle_model_version": ev_data.vehicle_model_version,
        "range_real": (
            kilometer_to_miles_converter(ev_data.range_real)
            if ev_data.range_real and ev_data.range_real != "0"
            else NOT_AVAILABLE
        ),
        "battery_capacity_useable": (
            ev_data.battery_capacity_useable
            if ev_data.battery_capacity_useable
            and ev_data.battery_capacity_useable != "0"
            else NOT_AVAILABLE
        ),
        "recommended_charger": (
            ev_data.fastcharge_plug
            if ev_data.fastcharge_plug
            else NOT_AVAILABLE
        ),
        "max_charge_speed": (
            ev_data.max_charge_speed
            if ev_data.max_charge_speed
            and ev_data.max_charge_speed != "0"
            else NOT_AVAILABLE
        ),
        "ev_image": ev_data.get_ev_image(),
    }
    if user_ev_data:
        data["vehicle_registration_number"] = user_ev_data.vehicle_registration_number
        data["vehicle_nickname"] = user_ev_data.vehicle_nickname
    connector_data = []
    if ev_data.charge_plug:
        charge_plug_image = ConnectorConfiguration.objects.filter(
            connector_plug_type_name=ev_data.charge_plug
        )
        if charge_plug_image.first():
            connector_data.append(
                {
                    "plug_name": ev_data.charge_plug,
                    "image": charge_plug_image.first().get_image_path(),
                }
            )
        else:
            connector_data.append(
                {
                    "plug_name": ev_data.charge_plug,
                    "image": DEFAULT_CONNECTOR_IMAGE,
                }
            )
    if ev_data.fastcharge_plug:
        fastcharge_plug_image = ConnectorConfiguration.objects.filter(
            connector_plug_type_name=ev_data.fastcharge_plug
        )
        if fastcharge_plug_image.first():
            connector_data.append(
                {
                    "plug_name": ev_data.fastcharge_plug,
                    "image": fastcharge_plug_image.first().get_image_path(),
                }
            )
        else:
            connector_data.append(
                {
                    "plug_name": ev_data.fastcharge_plug,
                    "image": DEFAULT_CONNECTOR_IMAGE,
                }
            )
    data["connector_details"] = connector_data

    return data


def electric_vehicle_details_query_handler_function(ev_data_helper):
    """this function returns the proper detailed set of ev data"""
    data = {
        "id": ev_data_helper["id"],
        "misc_body": ev_data_helper["misc_body"],
        "vehicle_make": ev_data_helper["vehicle_make"],
        "vehicle_model": ev_data_helper["vehicle_model"],
        "vehicle_model_version": ev_data_helper["vehicle_model_version"],
        "battery_capacity_useable": ev_data_helper["battery_capacity_useable"],
        "fastcharge_chargespeed": ev_data_helper["fastcharge_chargespeed"],
        "max_charge_speed": ev_data_helper["max_charge_speed"],
        "ev_image": f"{BLOB_CDN_URL}{ev_data_helper['ev_image']}",
    }
    return data


def ev_model_find_perfect_match(string_one, string_two):
    """this function is used to calculate similar models for"""
    if (len(string_one) <= len(string_two)) and string_one in string_two:
        return True
    elif (len(string_two) < len(string_one)) and string_two in string_one:
        return True
    return False


def string_similarity_calculator(string_one, string_two):
    """this function calculates string similarities"""
    perfect_match = ev_model_find_perfect_match(
        string_one.strip(), string_two.strip()
    )
    if perfect_match:
        return APPROX_PERFECT_MATCH
    matching_ratio = int(
        fuzz.ratio(string_two.lower().strip(), string_one.lower().strip())
    )
    if matching_ratio >= EV_MODEL_COMPARER_MATCH_PERCENTAGE:
        string_one_parts = string_one.split(" ")
        string_two_parts = string_two.split(" ")
        if len(string_two_parts) > len(string_one_parts):
            iteration_count = len(string_one_parts)
        else:
            iteration_count = len(string_two_parts)
        match_percetanges_of_parts = []
        for iteration in range(iteration_count):
            match_percetanges_of_parts.append(
                int(
                    fuzz.ratio(
                        "".join(
                            e
                            for e in string_two_parts[iteration]
                            if e.isalnum()
                        ),
                        "".join(
                            e
                            for e in string_one_parts[iteration]
                            if e.isalnum()
                        ),
                    )
                )
            )
        mean_of_all_parts = sum(match_percetanges_of_parts) / len(
            match_percetanges_of_parts
        )
        if (
            mean_of_all_parts >= EV_MODEL_COMPARER_MATCH_PERCENTAGE
            and ZERO_MATCHED
            not in match_percetanges_of_parts[
                : int(len(match_percetanges_of_parts) / 2) + 1
            ]
        ):
            return APPROX_PERFECT_MATCH
        else:
            return ZERO_MATCHED
    else:
        return matching_ratio


def find_ev_model_name_by_splitting(car_make, car_model):
    """this function finds ev model by splitting db name and provided name
    and compares the similarity percentage.
    """
    ev_data = ElectricVehicleDatabase.objects.filter(
        ~Q(ev_image=None),
        ~Q(ev_thumbnail_image=None),
        vehicle_make=car_make,
    ).values()
    filtered_ev_data = list(
        filter(
            lambda ev: (
                string_similarity_calculator(
                    " ".join(
                        [
                            f"{ev['vehicle_make'].lower()}",
                            f"{ev['vehicle_model'].lower()}",
                            (
                                f"{ev['vehicle_model_version'].lower()}"
                                if ev["vehicle_model_version"]
                                else ""
                            ),
                        ]
                    ),
                    " ".join([f"{car_make.lower()}", f"{car_model.lower()}"]),
                )
                >= EV_MODEL_COMPARER_MATCH_PERCENTAGE
            ),
            ev_data,
        )
    )

    data = [
        electric_vehicle_details_query_handler_function(filtered_ev)
        for filtered_ev in filtered_ev_data
    ]
    return data


def ev_range_formatter(array_of_range):
    """This function return ev range of"""

    def sort_ev_range(ev_range):
        return ev_range

    array_of_range = sorted(
        [
            kilometer_to_miles_converter(int(ev_range))
            for ev_range in array_of_range
            if isinstance(int(ev_range), int)
        ],
        key=sort_ev_range,
    )

    if len(array_of_range) > 1:
        return f"{array_of_range[0]} - {array_of_range[-1]}"
    if len(array_of_range) > 0:
        return f"{array_of_range[0]}"
    return NOT_AVAILABLE


def ev_name_formatter(array_of_keys):
    """this function returns formatted name of ev"""
    ev_name = ""
    for key in array_of_keys:
        if key:
            if len(ev_name) > 0:
                ev_name += f" {key}"
            else:
                ev_name = f"{key}"
    return ev_name


def energy_consumption_calculator(ev_range, battery):
    """this function returns the energy consumption for ev"""
    if isinstance(int(ev_range), int) and isinstance(int(battery), int):
        return custom_round_function(
            kilometer_to_miles_converter(ev_range) / battery, 2
        )
    return ""
