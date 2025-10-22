"""DB operators (create, update)"""
# Date - 23/11/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused db operations
#                       such as create and update.
#   Name            - Db operators
#   Modified by     - Manish Pawar
#   Modified date   - 23/11/2021

# imports required to create views
import json
from io import StringIO
from django.utils import timezone
from django.db import transaction
from django.db.models import Q

# pylint:disable=import-error
from sharedServices.model_files.promotions_models import (
    Promotions,
    PromotionsAvailableOn,
)
from adminServices.loyalty.db_operators import get_stations_object

from sharedServices.model_files.station_models import Stations
from sharedServices.model_files.bulk_models import BulkUploadProgress
from sharedServices.common import (
    date_formater_for_frontend_date,
    end_date_formater_for_frontend_date,
    image_converter,
    randon_string_generator,
)
from sharedServices.common_audit_trail_functions import (
    add_audit_data,
    audit_data_formatter,
)
from sharedServices.image_optimization_funcs import optimize_image
from sharedServices.constants import (
    YES,
    NO,
    PROMOTION_IMAGE,
    IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN,
    PROMOTIONS_CONST,
    AUDIT_ADD_CONSTANT,
    AUDIT_UPDATE_CONSTANT,
)


def create_promotion_func(promotions_array):
    """create promotion query in bulk"""
    promotion_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="promotions",
    )
    length_of_promotions_array = len(promotions_array)
    Promotions.objects.bulk_create(promotions_array)
    current_count = (
        int(promotion_bulk_upload_progress.first().uploaded_rows_count)
        + length_of_promotions_array
    )
    promotion_bulk_upload_progress.update(uploaded_rows_count=current_count)


def update_promotion_func(promotions_array):
    """bulk update promotions function"""
    promotion_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="promotions",
    )
    length_of_promotions_array = len(promotions_array)
    with transaction.atomic():
        for promotion in promotions_array:
            Promotions.objects.filter(
                unique_code=promotion["unique_code"]
            ).update(
                product=promotion["product"],
                retail_barcode=promotion["retail_barcode"],
                promotion_title=promotion["promotion_title"],
                m_code=promotion["m_code"],
                status=promotion["status"],
                start_date=promotion["start_date"],
                end_date=promotion["end_date"],
                available_for=promotion["available_for"],
                offer_type=promotion["offer_type"],
                londis_code=promotion["londis_code"],
                budgen_code=promotion["budgen_code"],
                price=promotion["price"],
                quantity=promotion["quantity"],
                offer_details=promotion["offer_details"],
                deleted=promotion["deleted"],
                terms_and_conditions=promotion["terms_and_conditions"],
                updated_date=promotion["updated_date"],
                updated_by=promotion["updated_by"],
            )
    current_count = (
        int(promotion_bulk_upload_progress.first().uploaded_rows_count)
        + length_of_promotions_array
    )
    promotion_bulk_upload_progress.update(uploaded_rows_count=current_count)


def handle_promotion_assignment(promotion_assignment_array):
    """handles promotion station assignment in bulk upload"""
    promotion_bulk_upload_progress = BulkUploadProgress.objects.filter(
        uploaded_for="promotions",
    )

    create_promotion_assignment = []
    for promotion_data in promotion_assignment_array:
        promotion_instance = Promotions.objects.filter(
            unique_code=promotion_data["promotion_instance_id"]
        )
        if promotion_instance.first():
            promotion_instance.update(shop_ids=promotion_data["shop_ids"])
            promotion = promotion_instance.first()
            user = promotion_data["user"]

            promotion_stations_id_list = PromotionsAvailableOn.objects.filter(
                ~Q(station_id=None), promotion_id=promotion
            ).values_list("station_id__station_id", flat=True)
            promotion_available_update_array = [
                station_id
                for station_id in promotion_data["station_ids"]
                if station_id in promotion_stations_id_list
            ]

            promotion_available_create_array = [
                station_id
                for station_id in promotion_data["station_ids"]
                if station_id not in promotion_stations_id_list
            ]

            promotion_available_delete_array = [
                station_id
                for station_id in promotion_stations_id_list
                if station_id not in promotion_data["station_ids"]
            ]
            PromotionsAvailableOn.objects.filter(
                station_id__station_id__in=promotion_available_update_array
            ).update(
                deleted=NO,
                updated_date=timezone.localtime(timezone.now()),
                updated_by=user.full_name,
            )

            PromotionsAvailableOn.objects.filter(
                station_id__station_id__in=promotion_available_delete_array
            ).update(
                deleted=YES,
                updated_date=timezone.localtime(timezone.now()),
                updated_by=user.full_name,
            )

            for station_id in promotion_available_create_array:
                station = Stations.objects.filter(station_id=station_id)
                if station.first():
                    create_promotion_assignment.append(
                        PromotionsAvailableOn(
                            promotion_id=promotion,
                            station_id=station.first(),
                            station_name=station.first().station_name,
                            operation_region=station.first().operation_region,
                            region=station.first().region,
                            area=station.first().area,
                            created_date=timezone.localtime(timezone.now()),
                            updated_date=timezone.localtime(timezone.now()),
                            updated_by=user.full_name,
                        )
                    )

    PromotionsAvailableOn.objects.bulk_create(create_promotion_assignment)

    current_count = int(
        promotion_bulk_upload_progress.first().uploaded_rows_count
    ) + len(promotion_assignment_array)
    promotion_bulk_upload_progress.update(uploaded_rows_count=current_count)


def add_single_promotion(
    post_data_from_front_end, user, shops_from_configurations
):
    """this function adds one pomotion"""

    # This logic helps us to store array of shop ids as a string in a database

    string_converter = StringIO()
    if "All" in post_data_from_front_end.shop:
        shops_array = [
            shop["service_name"] for shop in shops_from_configurations
        ]
        json.dump(shops_array, string_converter)
    else:
        json.dump(post_data_from_front_end.shop, string_converter)
    shops = string_converter.getvalue()

    start_date = date_formater_for_frontend_date(
        post_data_from_front_end.start_date
    )
    end_date = end_date_formater_for_frontend_date(
        post_data_from_front_end.end_date
    )
    image = None
    if len(post_data_from_front_end.images) > 0:
        image_data = image_converter(post_data_from_front_end.images[0])
        if (
            image_data[2] > 700
            or image_data[3] > 1400
            or image_data[2] < 400
            or image_data[3] < 700
        ):
            image = optimize_image(
                image_data[IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN],
                post_data_from_front_end.promotion_title
                + randon_string_generator()
                + "."
                + image_data[1],
                PROMOTION_IMAGE,
            )

    # Promotion insertion
    promotion = Promotions.objects.create(
        unique_code=post_data_from_front_end.unique_code,
        retail_barcode=post_data_from_front_end.retail_barcode,
        product=post_data_from_front_end.product,
        promotion_title=post_data_from_front_end.promotion_title,
        m_code=post_data_from_front_end.m_code,
        status=post_data_from_front_end.status,
        available_for=post_data_from_front_end.available_for,
        offer_type=post_data_from_front_end.offer_type,
        start_date=start_date,
        end_date=end_date,
        price=float(post_data_from_front_end.price),
        quantity=post_data_from_front_end.quantity,
        londis_code=post_data_from_front_end.londis_code,
        budgen_code=post_data_from_front_end.budgen_code,
        shop_ids=shops,
        offer_details=post_data_from_front_end.offer_details,
        image=image,
        terms_and_conditions=post_data_from_front_end.terms_and_conditions,
        created_date=timezone.localtime(timezone.now()),
        updated_by=user.full_name,
    )

    stations_data = get_stations_object()
    create_promotions_in_bulk = [
        PromotionsAvailableOn(
            promotion_id_id=promotion.id,
            station_id_id=stations_data[station_id]["id"],
            station_name=stations_data[station_id]["station_name"],
            operation_region=stations_data[station_id]["operation_region"],
            region=stations_data[station_id]["region"],
            area=stations_data[station_id]["area"],
            updated_date=timezone.localtime(timezone.now()),
            updated_by=user.full_name,
        )
        for station_id in list(set(post_data_from_front_end.stations))
    ]

    if create_promotions_in_bulk:
        PromotionsAvailableOn.objects.bulk_create(create_promotions_in_bulk)
    new_data = audit_data_formatter(PROMOTIONS_CONST, promotion.id)
    add_audit_data(
        user,
        f"{promotion.unique_code}, {promotion.promotion_title}",
        f"{PROMOTIONS_CONST}-{promotion.id}",
        AUDIT_ADD_CONSTANT,
        PROMOTIONS_CONST,
        new_data,
        None,
    )


def update_single_promotion(*args):
    """this function  updates single promotion"""
    (
        post_data_from_front_end,
        user,
        promotion_prev_stations,
        promotion_pk,
        start_date,
        end_date,
        shops,
        old_data,
    ) = args

    # Update query on promotions.
    Promotions.objects.filter(id=promotion_pk).update(
        unique_code=post_data_from_front_end.unique_code,
        retail_barcode=post_data_from_front_end.retail_barcode,
        product=post_data_from_front_end.product,
        promotion_title=post_data_from_front_end.promotion_title,
        m_code=post_data_from_front_end.m_code,
        status=post_data_from_front_end.status,
        available_for=post_data_from_front_end.available_for,
        offer_type=post_data_from_front_end.offer_type,
        start_date=start_date,
        end_date=end_date,
        price=float(post_data_from_front_end.price),
        quantity=float(post_data_from_front_end.quantity),
        londis_code=post_data_from_front_end.londis_code,
        budgen_code=post_data_from_front_end.budgen_code,
        shop_ids=shops,
        offer_details=post_data_from_front_end.offer_details,
        terms_and_conditions=post_data_from_front_end.terms_and_conditions,
        updated_date=timezone.localtime(timezone.now()),
        updated_by=user.full_name,
    )

    # If station is not present previously in database for
    # the promotion then we have to create it.
    promotion = Promotions.objects.filter(id=promotion_pk)
    stations_list = list(set(post_data_from_front_end.stations))
    stations_data = get_stations_object()
    create_promotions_in_bulk = [
        PromotionsAvailableOn(
            promotion_id_id=promotion_pk,
            station_id_id=stations_data[station_id]["id"],
            station_name=stations_data[station_id]["station_name"],
            operation_region=stations_data[station_id]["operation_region"],
            region=stations_data[station_id]["region"],
            area=stations_data[station_id]["area"],
            updated_date=timezone.localtime(timezone.now()),
            updated_by=user.full_name,
        )
        for station_id in stations_list
        if station_id not in promotion_prev_stations
    ]

    if create_promotions_in_bulk:
        PromotionsAvailableOn.objects.bulk_create(create_promotions_in_bulk)
    # If station was present previously in database for the promotion,
    # then we have to update it.
    stations_need_to_delete = [
        station_id
        for station_id in promotion_prev_stations
        if station_id not in stations_list
    ]
    if stations_need_to_delete:
        PromotionsAvailableOn.objects.filter(
            promotion_id_id=promotion_pk,
            station_id__station_id__in=stations_need_to_delete,
        ).update(
            deleted=YES,
            updated_date=timezone.localtime(timezone.now()),
            updated_by=user.full_name,
        )
    new_data = audit_data_formatter(PROMOTIONS_CONST, promotion_pk)
    if old_data != new_data:
        add_audit_data(
            user,
            (
                promotion.first().unique_code
                + ", "
                + promotion.first().promotion_title
            ),
            f"{PROMOTIONS_CONST}-{promotion_pk}",
            AUDIT_UPDATE_CONSTANT,
            PROMOTIONS_CONST,
            new_data,
            old_data,
        )
