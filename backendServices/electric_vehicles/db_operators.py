"""DB operators (create, update)"""
# Date - 23/11/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused db operations
#                       such as create and update.
#   Name            - Db operators
#   Modified by     - Manish Pawar
#   Modified date   - 14/12/2021

# imports required to create views
import io
from PIL import Image
from django.shortcuts import get_object_or_404
from django.db import transaction

# pylint:disable=import-error
from sharedServices.model_files.vehicle_models import ElectricVehicleDatabase
from sharedServices.common import array_to_string_converter
from sharedServices.image_optimization_funcs import optimize_image
from sharedServices.sentry_tracers import traced_request
from sharedServices.constants import (
    EV_DETAIL_IMAGE,
    EV_THUMBNAIL_IMAGE,
    REQUEST_API_TIMEOUT,
    GET_REQUEST,
)


def insert_ev_details_func(ev_array):
    """insert ev data in db"""
    ElectricVehicleDatabase.objects.bulk_create(ev_array)


def update_ev_details_func(ev_array):
    """update ev details in bulk"""

    with transaction.atomic():
        for ev_vehicle in ev_array:
            ElectricVehicleDatabase.objects.filter(
                vehicle_id=ev_vehicle["Vehicle_ID"]
            ).update(
                misc_body=ev_vehicle["Misc_Body"],
                vehicle_make=ev_vehicle["Vehicle_Make"],
                vehicle_model=ev_vehicle["Vehicle_Model"],
                vehicle_model_version=ev_vehicle["Vehicle_Model_Version"],
                range_real=ev_vehicle["Range_Real"],
                battery_capacity_useable=ev_vehicle[
                    "Battery_Capacity_Useable"
                ],
                charge_plug=ev_vehicle["Charge_Plug"],
                fastcharge_plug=ev_vehicle["Fastcharge_Plug"],
                fastcharge_chargespeed=ev_vehicle["Fastcharge_ChargeSpeed"],
                max_charge_speed=ev_vehicle["Fastcharge_Power_Max"],
                electric_vehicle_object=array_to_string_converter(
                    [ev_vehicle]
                ),
            )


def upload_ev_images_to_blob(ev_images_array):
    """update ev images to blob storage"""
    for ev_image in ev_images_array:
        ev_exists = ElectricVehicleDatabase.objects.filter(
            vehicle_id=ev_image["vehicle_id"]
        )
        if ev_exists.first():
            if len(ev_image["images"]) > 0:
                if ev_exists.first().ev_image:
                    ev_exists.first().ev_image.delete()
                if ev_exists.first().ev_thumbnail_image:
                    ev_exists.first().ev_thumbnail_image.delete()

                image_req = traced_request(GET_REQUEST, ev_image["images"][0], timeout=REQUEST_API_TIMEOUT)
                image = Image.open(io.BytesIO(image_req.content))
                ev_detail_image = optimize_image(
                    image,
                    ev_image["images"][0].split("/")[-1],
                    EV_DETAIL_IMAGE,
                )
                ev_thumbnail_image = optimize_image(
                    image,
                    ev_image["images"][0].split("/")[-1],
                    EV_THUMBNAIL_IMAGE,
                )
                ev_imageupload = get_object_or_404(
                    ElectricVehicleDatabase, id=ev_exists.first().id
                )
                ev_imageupload.ev_image = ev_detail_image
                ev_imageupload.ev_thumbnail_image = ev_thumbnail_image
                ev_imageupload.save()
            else:
                ev_exists.update(ev_image=None, ev_thumbnail_image=None)
