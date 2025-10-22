"""bulk upload helpr functions"""
# Date - 23/11/2021

# File details-
#   Author          - Manish Pawar
#   Description     - This file is contains bulk upload helper functions.
#   Name            - Promotions Bulk upload helper functions
#   Modified by     - Manish Pawar
#   Modified date   - 23/11/2021

# imports required to create views
import pandas as pd
from django.db.models import Q

# pylint:disable=import-error
from sharedServices.model_files.station_models import (
    StationServices,
    Stations,
)
from sharedServices.model_files.config_models import ServiceConfiguration
from sharedServices.model_files.promotions_models import Promotions
from sharedServices.common import (
    array_string_striper,
    array_to_string_converter,
    field_checker_func,
    remove_whitespace,
    error_messages_object_formatter,
)
from sharedServices.constants import (
    NO,
    STATION_ID,
    UNQUIE_BAR_CODE,
    UNQUIE_OPS_REGION,
    UNQUIE_RETAILBAR_CODE,
)


def station_id_assign(
    i,
    stations,
    shops,
    promotion_unique_id,
    error_tracker,
    promotions_assign_data_frame,
    station_services_query_set,
    stations_queryset,
):
    """station assign"""
    if "|" in str(promotions_assign_data_frame[STATION_ID][i]):
        station_ids_list = promotions_assign_data_frame[STATION_ID][i].split(
            "|"
        )
        station_ids_list = array_string_striper(station_ids_list)
    elif (str(promotions_assign_data_frame[STATION_ID][i])).strip() == "All":
        station_ids_list = [
            station_in_qs.station_id for station_in_qs in stations
        ]
    else:
        station_ids_list = [str(promotions_assign_data_frame[STATION_ID][i])]
    # Validating station ids
    station_ids = [
        s_id
        for s_id in station_ids_list
        if station_services_query_set.filter(
            ~Q(service_name="Amenity"),
            station_id__station_id=s_id,
            deleted=NO,
            service_id__service_name__in=shops,
        )
        .distinct()
        .first()
    ]
    # Errors for invalid station ids
    for s_id in station_ids_list:
        if s_id not in station_ids:
            station_found = stations_queryset.filter(station_id=s_id)
            if station_found.first():
                station_services_check = station_services_query_set.filter(
                    ~Q(service_name="Amenity"),
                    station_id__station_id=s_id,
                    deleted=NO,
                    service_id__service_name__in=shops,
                ).distinct()
                if not station_services_check.first():
                    error_tracker.append(
                        error_messages_object_formatter(
                            [UNQUIE_RETAILBAR_CODE, "Error"],
                            [
                                f"{promotion_unique_id}\
                                    (Promotion Assign Tab)",
                                f"Provided shops are not \
                                    available on station {s_id}",
                            ],
                        )
                    )
            else:
                error_tracker.append(
                    error_messages_object_formatter(
                        [UNQUIE_RETAILBAR_CODE, "Error"],
                        [
                            f"{promotion_unique_id}\
                                (Promotion Assign Tab)",
                            f'Station with provided Station id\
                                "{s_id}" not found',
                        ],
                    )
                )
    return [
        error_tracker,
        stations.filter(
            station_id__in=station_ids
        )
    ]


def ops_region_assign(
    i,
    stations,
    promotion_unique_id,
    error_tracker,
    promotions_assign_data_frame,
):
    """ops region assign"""
    apply_to_all_ops_regions = False
    if "|" in str(promotions_assign_data_frame[UNQUIE_OPS_REGION][i]):
        ops_regions = str(
            promotions_assign_data_frame[UNQUIE_OPS_REGION][i]
        ).split("|")
        ops_regions = array_string_striper(ops_regions)
    elif (
        str(promotions_assign_data_frame[UNQUIE_OPS_REGION][i])
    ).strip() == "All":
        apply_to_all_ops_regions = True
    else:
        ops_regions = [str(promotions_assign_data_frame[UNQUIE_OPS_REGION][i])]

    # Error messages for wrong operation regions
    if not apply_to_all_ops_regions:
        wrong_ops_regions = [
            ops_region
            for ops_region in ops_regions
            if not stations.filter(operation_region=ops_region).first()
        ]
        ops_region_error_message = ""
        for ops in wrong_ops_regions:
            if len(ops_region_error_message) > 0:
                ops_region_error_message += f", {ops}"
            else:
                ops_region_error_message = ops
        if len(ops_region_error_message) > 0:
            error_tracker.append(
                error_messages_object_formatter(
                    [UNQUIE_RETAILBAR_CODE, "Error"],
                    [
                        f"{promotion_unique_id}\
                            (Promotion Assign Tab)",
                        f'Stations with these operation \
                            regions not found  -> \
                                "{ops_region_error_message}"',
                    ],
                )
            )
    return [
        ops_regions if not apply_to_all_ops_regions else None,
        error_tracker,
    ]


def region_assign(
    i,
    stations,
    promotion_unique_id,
    provided_ops_regions,
    error_tracker,
    promotions_assign_data_frame,
):
    """region assign"""
    apply_to_all_regions = False
    if "|" in str(promotions_assign_data_frame["Regions"][i]):
        regions = str(promotions_assign_data_frame["Regions"][i]).split("|")
        regions = array_string_striper(regions)
    elif (str(promotions_assign_data_frame["Regions"][i])).strip() == "All":
        apply_to_all_regions = True
    else:
        regions = [str(promotions_assign_data_frame["Regions"][i])]
    # Error messages for wrong regions
    if not apply_to_all_regions:
        wrong_regions = [
            region
            for region in regions
            if not stations.filter(region=region).first()
        ]
        region_error_message = ""
        for wrong_region in wrong_regions:
            if len(region_error_message) > 0:
                region_error_message += f", {wrong_region}"
            else:
                region_error_message = wrong_region
        if len(region_error_message) > 0:
            if provided_ops_regions:
                error_tracker.append(
                    error_messages_object_formatter(
                        [UNQUIE_RETAILBAR_CODE, "Error"],
                        [
                            f"{promotion_unique_id}\
                                (Promotion Assign Tab)",
                            f'Provided Regions -> \
                                "{region_error_message}" \
                                    is/are not belonging to provided \
                                        Operation regions',
                        ],
                    )
                )
            else:
                error_tracker.append(
                    error_messages_object_formatter(
                        [UNQUIE_RETAILBAR_CODE, "Error"],
                        [
                            f"{promotion_unique_id}\
                                (Promotion Assign Tab)",
                            f'Stations with these regions not found \
                                -> "{region_error_message}"',
                        ],
                    )
                )
    return [regions if not apply_to_all_regions else None, error_tracker]


def area_assign(
    i,
    stations,
    promotion_unique_id,
    provided_regions,
    provided_ops_regions,
    error_tracker,
    promotions_assign_data_frame,
):
    """area assign"""
    apply_to_all_areas = False
    if "|" in str(promotions_assign_data_frame["Area"][i]):
        areas = str(promotions_assign_data_frame["Area"][i]).split("|")
        areas = array_string_striper(areas)
    else:
        if (str(promotions_assign_data_frame["Area"][i])).strip() == "All":
            apply_to_all_areas = True
        else:
            areas = [str(promotions_assign_data_frame["Area"][i])]
    if not apply_to_all_areas:
        # Error messages for wrong areas
        wrong_areas = [
            area for area in areas if not stations.filter(area=area).first()
        ]
        areas_error_message = ""
        for wrong_area in wrong_areas:
            if len(areas_error_message) > 0:
                areas_error_message += f", {wrong_area}"
            else:
                areas_error_message = wrong_area
        if len(areas_error_message) > 0:
            if provided_regions:
                error_tracker.append(
                    error_messages_object_formatter(
                        [UNQUIE_RETAILBAR_CODE, "Error"],
                        [
                            f"{promotion_unique_id}\
                                (Promotion Assign Tab)",
                            f'Provided areas  -> \
                                "{areas_error_message}" is/are not \
                                    belonging to provided regions.',
                        ],
                    )
                )
            elif provided_ops_regions:
                error_tracker.append(
                    error_messages_object_formatter(
                        [UNQUIE_RETAILBAR_CODE, "Error"],
                        [
                            f"{promotion_unique_id}\
                                (Promotion Assign Tab)",
                            f'Provided areas -> \
                                "{areas_error_message}" is/are \
                                    not belonging to \
                                        provided Opertion regions.',
                        ],
                    )
                )
            else:
                error_tracker.append(
                    error_messages_object_formatter(
                        [UNQUIE_RETAILBAR_CODE, "Error"],
                        [
                            f"{promotion_unique_id}\
                                (Promotion Assign Tab)",
                            f'Stations with \
                                these areas not found -> \
                                    "{areas_error_message}".',
                        ],
                    )
                )
    return [areas if not apply_to_all_areas else None, error_tracker]


def validate_check(
    validator_helper,
    i,
    error_tracker_helper,
    promotion_unique_id,
    promotions_assign_list_of_fields_for_iteration,
    promotions_assign_data_frame,
):
    """validate check"""
    if validator_helper[0]:
        validator_one_helper = field_checker_func(
            promotions_assign_list_of_fields_for_iteration,
            promotions_assign_data_frame,
            i,
        )
        if len(promotions_assign_list_of_fields_for_iteration) != len(
            validator_one_helper[1]
        ):
            error_message_text_helper = ""
            for f_error in validator_helper[1]:
                if len(error_message_text_helper) > 0:
                    error_message_text_helper += f", {f_error}"
                else:
                    error_message_text_helper = f_error
            error_tracker_helper.append(
                error_messages_object_formatter(
                    [UNQUIE_RETAILBAR_CODE, "Error"],
                    [
                        f"{promotion_unique_id}\
                            (Promotion Assign Tab)",
                        f'Please provide these required fields -> \
                            "{error_message_text_helper}"',
                    ],
                )
            )
        return error_tracker_helper
    return None


def conditions_check(
    i,
    stations,
    promotion_unique_id,
    provided_regions,
    provided_ops_regions,
    error_tracker,
    promotions_assign_data_frame,
    shops,
    promotions_assignment_data,
    user,
):
    """conditions check"""
    stations_queryset = Stations.objects.filter()
    station_services_query_set = StationServices.objects.filter()
    if not pd.isna(promotions_assign_data_frame[STATION_ID][i]):
        (error_tracker, stations) = station_id_assign(
            i,
            stations,
            shops,
            promotion_unique_id,
            error_tracker,
            promotions_assign_data_frame,
            station_services_query_set,
            stations_queryset,
        )
    if not pd.isna(promotions_assign_data_frame[UNQUIE_OPS_REGION][i]):
        provided_ops_regions = True
        ops_regions, error_tracker = ops_region_assign(
            i,
            stations,
            promotion_unique_id,
            error_tracker,
            promotions_assign_data_frame,
        )
        if ops_regions:
            stations = stations.filter(operation_region__in=ops_regions)
    if not pd.isna(promotions_assign_data_frame["Regions"][i]):
        provided_regions = True
        regions, error_tracker = region_assign(
            i,
            stations,
            promotion_unique_id,
            provided_ops_regions,
            error_tracker,
            promotions_assign_data_frame,
        )
        if regions:
            stations = stations.filter(region__in=regions)
    if not pd.isna(promotions_assign_data_frame["Area"][i]):
        areas, error_tracker = area_assign(
            i,
            stations,
            promotion_unique_id,
            provided_regions,
            provided_ops_regions,
            error_tracker,
            promotions_assign_data_frame,
        )
        if areas:
            stations = stations.filter(area__in=areas)
    return [stations, promotions_assignment_data, error_tracker]


def promotion_assign_bulk_upload(
    i,
    promotions_assign_list_of_fields_helper,
    promotions_assign_data_frame_helper,
    promotion_assign_set_helper,
    promotions_assignment_data,
    user_helper,
    promotions_assign_list_of_fields_for_iteration_helper,
):
    """promotion assignment bulk upload"""
    promotions_queryset = Promotions.objects.filter()
    service_configurations = ServiceConfiguration.objects.filter()
    error_tracker = []
    stations = Stations.objects.filter()

    all_shop_list = [
        service_from_configuration.service_name
        for service_from_configuration in ServiceConfiguration.objects.filter(
            ~Q(service_type="Amenity")
        )
    ]
    validator = field_checker_func(
        promotions_assign_list_of_fields_helper,
        promotions_assign_data_frame_helper,
        i,
    )
    promotion = None
    shops = []
    station_ids = []
    provided_ops_regions = False
    provided_regions = False
    provided_areas = False
    promotion_unique_id = promotions_assign_data_frame_helper[UNQUIE_BAR_CODE][
        i
    ]
    validation_check = validate_check(
        validator,
        i,
        error_tracker,
        promotion_unique_id,
        promotions_assign_list_of_fields_for_iteration_helper,
        promotions_assign_data_frame_helper,
    )
    if validation_check is not None:
        return validation_check
    try:
        filter_promotion = promotions_queryset.filter(
            unique_code=remove_whitespace(
                str(promotions_assign_data_frame_helper[UNQUIE_BAR_CODE][i])
            )
        )
        if "All" in promotions_assign_data_frame_helper["Shop"][i].split("|"):
            shops = all_shop_list
        else:
            for shop in promotions_assign_data_frame_helper["Shop"][i].split(
                "|"
            ):
                shop_in_configuration = service_configurations.filter(
                    service_name=shop.strip()
                )
                if shop_in_configuration.first():
                    shops.append(shop.strip())
                else:
                    error_tracker.append(
                        error_messages_object_formatter(
                            [UNQUIE_RETAILBAR_CODE, "Error"],
                            [
                                f"{promotion_unique_id}\
                                    (Promotion Assign Tab)",
                                f'Shop column -> \
                                    "{shop}" is not added in \
                                        Admin Portal Food to \
                                            go/Retail configurations.',
                            ],
                        )
                    )
        if (
            filter_promotion.first()
            or remove_whitespace(
                str(promotions_assign_data_frame_helper[UNQUIE_BAR_CODE][i])
            )
            in promotion_assign_set_helper
        ):
            promotion = True

    except (KeyError, AttributeError) as error:
        error_tracker.append(
            error_messages_object_formatter(
                [UNQUIE_RETAILBAR_CODE, "Error"],
                [
                    f"{promotion_unique_id}\
                        (Promotion Assign Tab)",
                    f"Something went wrong while adding shops \
                        to promotions,\
                            Error-> {str(error)}",
                ],
            )
        )
    if not promotion:
        error_tracker.append(
            error_messages_object_formatter(
                [UNQUIE_RETAILBAR_CODE, "Error"],
                [
                    f"{promotion_unique_id}\
                        (Promotion Assign Tab)",
                    "Promotion with provided Unique \
                        barcode not found.",
                ],
            )
        )
        return [error_tracker, None]
    (stations, promotions_assignment_data, error_tracker,) = conditions_check(
        i,
        stations,
        promotion_unique_id,
        provided_regions,
        provided_ops_regions,
        error_tracker,
        promotions_assign_data_frame_helper,
        shops,
        promotions_assignment_data,
        user_helper,
    )
    if len(shops) > 0:
        stations = stations.filter(
            services_list__service_id__service_name__in=shops
        ).distinct()
        if len(stations) == 0:
            if provided_areas or provided_ops_regions or provided_regions:
                error_tracker.append(
                    error_messages_object_formatter(
                        [UNQUIE_RETAILBAR_CODE, "Error"],
                        [
                            f"{promotion_unique_id}\
                                (Promotion Assign Tab)",
                            "No stations found according to provided \
                                Operation regions/Regions/Areas \
                                    and Shops.",
                        ],
                    )
                )
            else:
                error_tracker.append(
                    error_messages_object_formatter(
                        [UNQUIE_RETAILBAR_CODE, "Error"],
                        [
                            f"{promotion_unique_id}\
                                (Promotion Assign Tab)",
                            "No stations found according \
                                to provided shops.",
                        ],
                    )
                )
    station_ids = [s.station_id for s in stations]
    promotions_assignment_data.append(
        {
            "promotion_instance_id": remove_whitespace(
                str(promotions_assign_data_frame_helper[UNQUIE_BAR_CODE][i])
            ),
            "station_ids": station_ids,
            "shop_ids": array_to_string_converter(shops),
            "user": user_helper,
        }
    )
    return [error_tracker, promotions_assignment_data]
