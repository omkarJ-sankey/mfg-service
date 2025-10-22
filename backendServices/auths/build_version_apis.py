"""build version  APIs"""
# Date - 03/02/2022


# File details-
#   Author          - Manish Pawar
#   Description     - This file contains build version APIs.
#   Name            - build version API
#   Modified by     - Shivkumar Kumbhar
#   Modified date   - 31/03/2023


# These are all the imports that we are exporting from different
# module's from project or library.
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import (
    authentication_classes,
    permission_classes,
)
from rest_framework.views import APIView

from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist

# pylint:disable=import-error
from sharedServices.model_files.config_models import BaseConfigurations
from sharedServices.common import string_to_array_converter, redis_connection
from sharedServices.constants import COMMON_ERRORS, API_ERROR_OBJECT, IS_3DS_AVAILABLE

from .error_messages import UNDER_MAINTENANCE_DEFAULT_MESSAGE


@authentication_classes([])
@permission_classes([])
class BuildChecker(APIView):
    """mobile build version cheker"""

    @classmethod
    def get(cls, build_check_version):
        """post method to check username uniquness"""
        try:
            os_type = build_check_version.query_params.get("os_type")
            if os_type:
                try:
                    version = BaseConfigurations.objects.get(
                        base_configuration_key=os_type
                    )
                    if version:
                        return Response(
                            {
                                "status_code": status.HTTP_200_OK,
                                "status": True,
                                "message": "version is available",
                                "data": version.base_configuration_value,
                            }
                        )
                except ObjectDoesNotExist:
                    return Response(
                        {
                            "status_code": status.HTTP_404_NOT_FOUND,
                            "status": False,
                            "message": "version history not available",
                        }
                    )
            return Response(
                {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "status": False,
                    "message": "os_type key is required",
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Build Checker API failed due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


def return_app_update_version_formatted_data(
    version,
    is_update_available,
    is_update_btn_enable,
    under_maintenance_status,
    under_maintenance_message,
    is_3ds_available,
):
    """this function return app update version formatted data"""
    frequently_used_cached_vars = redis_connection.get(
        "frequently_used_configurations"
    )
    frequently_used_configurations = []
    if (
        frequently_used_cached_vars
        and frequently_used_cached_vars.decode("utf-8") != "null"
    ):
        frequently_used_configurations = string_to_array_converter(
            frequently_used_cached_vars.decode("utf-8")
        )
    return {
        "status_code": status.HTTP_200_OK,
        "status": True,
        "message": "version is available",
        "data": version.base_configuration_value,
        "frequently_used_configurations": frequently_used_configurations,
        "is_update_available": (
            bool(
                is_update_available
                and is_update_available.base_configuration_value == "Yes"
            )
        ),
        "is_update_btn_enable": (
            bool(
                is_update_btn_enable
                and is_update_btn_enable.base_configuration_value == "Yes"
            )
        ),
        "under_maintenance_status": (
            bool(
                under_maintenance_status
                and under_maintenance_status.base_configuration_value == "Yes"
            )
        ),
        "under_maintenance_message": (
            under_maintenance_message.base_configuration_value
            if (
                under_maintenance_message
                and len(under_maintenance_message.base_configuration_value)
            )
            else (UNDER_MAINTENANCE_DEFAULT_MESSAGE)
        ),
        "is_3ds_available": (
            bool(
                is_3ds_available
                and is_3ds_available.base_configuration_value == "Yes"
            )
            if (
                is_3ds_available
                and len(is_3ds_available.base_configuration_value)
            )
            else (IS_3DS_AVAILABLE)
        ),
    }


@authentication_classes([])
@permission_classes([])
class AppUpdateAndUnderMaintenanceChecker(APIView):
    """app updates and under maintenance status checker"""

    @classmethod
    def get(cls, build_check_version):
        """post method to get build version,
        and app update and maintenance status"""
        try:
            os_type = build_check_version.query_params.get("os_type")
            if os_type:
                try:
                    version = BaseConfigurations.objects.filter(
                        base_configuration_key=os_type
                    ).first()
                    is_update_available = BaseConfigurations.objects.filter(
                        base_configuration_key="is_update_available"
                    ).first()
                    is_update_btn_enable = BaseConfigurations.objects.filter(
                        base_configuration_key="is_update_btn_enable"
                    ).first()
                    under_maintenance_status = (
                        BaseConfigurations.objects.filter(
                            base_configuration_key="under_maintenance_status"
                        ).first()
                    )
                    under_maintenance_message = (
                        BaseConfigurations.objects.filter(
                            base_configuration_key="under_maintenance_message"
                        ).first()
                    )
                    is_3ds_available = BaseConfigurations.objects.filter(
                        base_configuration_key="is_3ds_available"
                    ).first()
                    if version:
                        return Response(
                            return_app_update_version_formatted_data(
                                version,
                                is_update_available,
                                is_update_btn_enable,
                                under_maintenance_status,
                                under_maintenance_message,
                                is_3ds_available,
                            )
                        )
                except ObjectDoesNotExist:
                    return Response(
                        {
                            "status_code": status.HTTP_404_NOT_FOUND,
                            "status": False,
                            "message": "version history not available",
                        }
                    )
            return Response(
                {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "status": False,
                    "message": "os_type key is required",
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"App Update And Under Maintenance Checker failed due to \
                    exception -> {exception}"
            )
            return API_ERROR_OBJECT


@authentication_classes([])
@permission_classes([])
class BuildValue(APIView):
    """mobile build version update and create"""

    @classmethod
    def post(cls, build_value_request):
        """post method to check username uniquness"""
        try:
            os_type = build_value_request.data.get("os_type")
            version = build_value_request.data.get("version")
            if os_type and version:
                try:
                    config_exist = BaseConfigurations.objects.filter(
                        base_configuration_key=os_type
                    )
                    if config_exist.first():
                        config_exist.update(
                            base_configuration_value=version,
                            updated_date=timezone.localtime(timezone.now()),
                        )
                        return Response(
                            {
                                "status_code": status.HTTP_200_OK,
                                "status": True,
                                "message": os_type
                                + " version successfully updated.",
                            }
                        )
                    BaseConfigurations.objects.create(
                        base_configuration_key=os_type,
                        base_configuration_value=version,
                        created_date=timezone.localtime(timezone.now()),
                    )
                    return Response(
                        {
                            "status_code": status.HTTP_200_OK,
                            "status": True,
                            "message": os_type
                            + "  version sucessfully added.",
                        }
                    )
                except ObjectDoesNotExist:
                    return Response(
                        {
                            "status_code": status.HTTP_404_NOT_FOUND,
                            "status": False,
                            "message": "version history not available",
                        }
                    )
            else:
                return Response(
                    {
                        "status_code": status.HTTP_404_NOT_FOUND,
                        "status": False,
                        "message": "os_type and version key is required.",
                    }
                )
        except COMMON_ERRORS as exception:
            print(
                f"Build Value API failed due to exception -> {exception}"
            )
            return API_ERROR_OBJECT
