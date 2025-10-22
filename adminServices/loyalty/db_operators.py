"""DB operators (create, update)"""
# Date - 23/11/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused db operations
#                       such as create and update.
#   Name            - Db operators
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 27/09/2025

# imports required to create views
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from django.urls import reverse
from django.shortcuts import get_object_or_404

# pylint:disable=import-error
from sharedServices.common import (
    image_converter,
    randon_string_generator,
    date_formater_for_frontend_date,
    end_date_formater_for_frontend_date,
)
from sharedServices.image_optimization_funcs import optimize_image
from sharedServices.common_audit_trail_functions import (
    add_audit_data,
    audit_data_formatter,
)
from sharedServices.constants import (
    YES,
    NO,
    LOYALTY_IMAGE,
    PROMOTION_IMAGE,
    IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN,
    LOYALTY_CONST,
    AUDIT_ADD_CONSTANT,
    AUDIT_UPDATE_CONSTANT,
    EV_NOTIFICATION_IMAGE,
    PUSH_NOTIFICATION_LOYALTY_TYPE,
    LOYALTY_REWARD_IMAGE,
    COSTA_COFFEE,
    ACTIVE,
    LOYALTY_TYPES,
)
from sharedServices.model_files.loyalty_models import (
    Loyalty,
    LoyaltyAvailableOn,
    LoyaltyProducts,
    LoyaltyOccurrences
)
from sharedServices.model_files.notifications_module_models import (
    PushNotifications
)
from sharedServices.model_files.station_models import (
    Stations,
)


# pylint:enable=import-error


def get_stations_object():
    """this function gives formatted station data"""
    stations_data = {}
    db_stations = Stations.objects.filter(deleted=NO).only(
        "id",
        "station_id",
        "operation_region",
        "region",
        "area",
        "station_name",
    )
    for station in db_stations:
        stations_data[station.station_id] = {
            "id": station.id,
            "station_id": station.station_id,
            "operation_region": station.operation_region,
            "region": station.region,
            "area": station.area,
            "station_name": station.station_name,
        }
    return stations_data


def add_loyalty_notification_data(data, user, loyalty_id):
    """this function adds loyalty notification data"""
    reward_activated_notification_image = None
    reward_expiration_notification_image = None
    if data.reward_activated_notification_image:
        reward_activated_notification_image_data = image_converter(
            data.reward_activated_notification_image
        )
        reward_activated_notification_image = optimize_image(
            reward_activated_notification_image_data[IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN],
            f"{data.reward_activated_notification_title}_{randon_string_generator()}"
            + "."
            + reward_activated_notification_image_data[1],
            EV_NOTIFICATION_IMAGE,
        )
    if data.reward_expiration_notification_image:
        reward_expiration_notification_image_data = image_converter(
            data.reward_expiration_notification_image
        )
        reward_expiration_notification_image = optimize_image(
            reward_expiration_notification_image_data[IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN],
            f"{data.reward_expiration_notification_title}_{randon_string_generator()}"
            + "."
            + reward_expiration_notification_image_data[1],
            EV_NOTIFICATION_IMAGE,
        )
    (
        reward_activated_notification_type_of_notification,
        reward_activated_notification_type_of_notification_status
    ) = data.reward_activated_notification_type_of_notification.split('-')
    reward_activation_notification = PushNotifications.objects.create(
        notification_for=PUSH_NOTIFICATION_LOYALTY_TYPE,
        subject=data.reward_activated_notification_title,
        description=data.reward_activated_notification_description,
        screens=data.reward_activated_notification_screen,
        category="Application",
        push_notification='true' if (
            (
                reward_activated_notification_type_of_notification == 'Push Notification' or
                reward_activated_notification_type_of_notification == 'In App Notification'
            ) and
            reward_activated_notification_type_of_notification_status == 'on'
        ) else 'false',
        inapp_notification='true' if (
            reward_activated_notification_type_of_notification == 'In App Notification' and
            reward_activated_notification_type_of_notification_status == 'on'
        ) else 'false',
        image=reward_activated_notification_image,
        created_date=timezone.localtime(timezone.now()),
        updated_by=user.full_name,
    )
    
    (
        reward_expiration_notification_type_of_notification,
        reward_expiration_notification_type_of_notification_status
    ) = data.reward_expiration_notification_type_of_notification.split('-')
    reward_expiration_notification = PushNotifications.objects.create(
        notification_for=PUSH_NOTIFICATION_LOYALTY_TYPE,
        subject=data.reward_expiration_notification_title,
        description=data.reward_expiration_notification_description,
        screens=data.reward_expiration_notification_screen,
        category="Application",
        push_notification='true' if (
            (
                reward_expiration_notification_type_of_notification == 'Push Notification' or
                reward_expiration_notification_type_of_notification == 'In App Notification'
            ) and
            reward_expiration_notification_type_of_notification_status == 'on'
        ) else 'false',
        inapp_notification='true' if (
            reward_expiration_notification_type_of_notification == 'In App Notification' and
            reward_expiration_notification_type_of_notification_status == 'on'
        ) else 'false',
        image=reward_expiration_notification_image,
        created_date=timezone.localtime(timezone.now()),
        updated_by=user.full_name,
    )
    Loyalty.objects.filter(
        id=loyalty_id
    ).update(
        number_of_total_issuances=data.number_of_total_issuances,
        reward_unlocked_notification_id=reward_activation_notification,
        reward_expiration_notification_id=reward_expiration_notification,
        reward_activated_notification_expiry=data.reward_activated_notification_expiry,
        reward_expiration_notification_expiry=data.reward_expiration_notification_expiry,
        expire_reward_before_x_number_of_days=data.reward_expiration_notification_before_x_number_of_days,
        reward_expiry_notification_trigger_time=data.reward_expiry_notification_trigger_time,
    )


# Looping over loyalty products sent from frontend
def update_notification_image(image_title,notification_id, new_image_data):
    notification = PushNotifications.objects.filter(
        id=notification_id
    ).first()
    if notification:
        if notification.image:
            notification.image.delete()
        if new_image_data:
            optimized_image = optimize_image(
                new_image_data[IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN],
                f"{image_title}_{randon_string_generator()}.{new_image_data[1]}",
                EV_NOTIFICATION_IMAGE,
            )
            notification.image = optimized_image
        else:
            notification.image = None
        notification.save()


def update_notification(
    notification_id,
    notification_title,
    notification_description,
    notification_screen,
    notification_type,
    user
):
    notification = PushNotifications.objects.filter(
        id=notification_id
    ).first()
    (
        notification_type_of_notification,
        notification_type_of_notification_status,
    ) = notification_type.split("-")
    notification.subject = notification_title
    notification.description = notification_description
    notification.screens = notification_screen
    notification.category = "Application"
    notification.push_notification = (
        "true"
        if (
            (
                notification_type_of_notification == "Push Notification"
                or notification_type_of_notification
                == "In App Notification"
            )
            and notification_type_of_notification_status == "on"
        )
        else "false"
    )
    notification.inapp_notification = (
        "true"
        if (
            notification_type_of_notification == "In App Notification"
            and notification_type_of_notification_status == "on"
        )
        else "false"
    )
    notification.updated_date = timezone.localtime(timezone.now())
    notification.updated_by = user.full_name
    notification.save()


def update_loyalty_notification_data(data, loyalty, user):
    """this function updates loyalty notification data"""
    # upadating notification content
    if data.reward_activated_notification_image != loyalty["reward_activated_notification_image"]:
        reward_activated_notification_image_data = (
            image_converter(data.reward_activated_notification_image)
            if data.reward_activated_notification_image
            else None
        )
        update_notification_image(
            data.reward_activated_notification_title,
            loyalty["reward_unlocked_notification_id_id"],
            reward_activated_notification_image_data,
        )

    if data.reward_expiration_notification_image != loyalty["reward_expiration_notification_image"]:
        reward_expiration_notification_image_data = (
            image_converter(data.reward_expiration_notification_image)
            if data.reward_expiration_notification_image
            else None
        )
        update_notification_image(
            data.reward_expiration_notification_title,
            loyalty["reward_expiration_notification_id_id"],
            reward_expiration_notification_image_data,
        )

    update_notification(
        loyalty["reward_unlocked_notification_id_id"],
        data.reward_activated_notification_title,
        data.reward_activated_notification_description,
        data.reward_activated_notification_screen,
        data.reward_activated_notification_type_of_notification,
        user
    )

    update_notification(
        loyalty["reward_expiration_notification_id_id"],
        data.reward_expiration_notification_title,
        data.reward_expiration_notification_description,
        data.reward_expiration_notification_screen,
        data.reward_expiration_notification_type_of_notification,
        user
    )

    Loyalty.objects.filter(id=loyalty["id"]).update(
        number_of_total_issuances=data.number_of_total_issuances,
        reward_activated_notification_expiry=data.reward_activated_notification_expiry,
        reward_expiration_notification_expiry=data.reward_expiration_notification_expiry,
        expire_reward_before_x_number_of_days=data.reward_expiration_notification_before_x_number_of_days,
        reward_expiry_notification_trigger_time=data.reward_expiry_notification_trigger_time,
    )


def create_single_loyalty(*args):
    """this function creates single loyalty"""
    data, shops, start_date, end_date, user = args
    image = None
    station_loyalty_card_image = None
    reward_image = None
    if data.loyalty_type == COSTA_COFFEE:
        costa_loyalty_exists = Loyalty.objects.filter(
            loyalty_type=COSTA_COFFEE,
            status=ACTIVE,
            deleted=NO
        )
        if costa_loyalty_exists.first():
            response = {
                "status": 0,
                "message": "It’s not possible to add another Costa Coffee loyalty as one costa coffee loyalty is active.",
                "url": reverse("station_list"),
            }
            return JsonResponse(response)
    loyalty_exists = Loyalty.objects.filter(unique_code=data.unique_code)
    if loyalty_exists.first():
        response = {
            "status": 0,
            "message": "Loyalty with provided unique code already exists",
            "url": reverse("station_list"),
        }
        return JsonResponse(response)

    if data.promotion_image:
        image_data = image_converter(data.promotion_image)
        if not (
            image_data[2] > 700
            or image_data[3] > 1400
            or image_data[2] < 400
            or image_data[3] < 700
        ):
            response = {
                "status": 0,
                "message": "Image with improper size is provided.",
                "url": reverse("station_list"),
            }
            return JsonResponse(response)
        image = optimize_image(
            image_data[IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN],
            f"{data.loyalty_title}_{randon_string_generator()}"
            + "."
            + image_data[1],
            LOYALTY_IMAGE,
        )
        station_loyalty_card_image = optimize_image(
            image_data[IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN],
            f"{data.loyalty_title}_station_loyalty_card_image_{randon_string_generator()}"
            + "."
            + image_data[1],
            PROMOTION_IMAGE,
        )

    if data.reward_image:
        reward_image_data = image_converter(data.reward_image)
        reward_image = optimize_image(
            reward_image_data[IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN],
            f"{data.loyalty_title}_reward_image_{randon_string_generator()}"
            + "."
            + reward_image_data[1],
            LOYALTY_REWARD_IMAGE,
            reward_image_data[0]
        )
    
    visibility = data.loyalty_visibility
    is_car_wash = data.is_car_wash
    # Loyalty insertion
    loyalty = Loyalty.objects.create(
        loyalty_title=data.loyalty_title,
        unique_code=data.unique_code,
        valid_from_date=start_date,
        valid_to_date=end_date,
        occurance_status=data.occurance_status,
        steps_to_redeem=data.steps_to_redeem,
        category=data.category,
        bar_code_std=data.bar_code_std,
        redeem_type=data.redeem_type,
        loyalty_type=data.loyalty_type,
        cycle_duration=data.cycle_duration,
        number_of_paid_purchases=data.number_of_paid_purchases,
        qr_refresh_time=data.qr_refresh_time,
        status=data.status,
        offer_details=data.offer_details,
        terms_and_conditions=data.terms_and_conditions,
        redeem_product_code=data.redeem_product_code,
        redeem_product=data.redeem_product,
        redeem_product_promotional_code=(data.redeem_product_promotional_code),
        expiry_in_days=data.expiry_in_days,
        image=image,
        station_loyalty_card_image=station_loyalty_card_image,
        reward_image=reward_image,
        shop_ids=shops,
        created_date=timezone.localtime(timezone.now()),
        updated_by=user.full_name,
        offer_type=data.offer_type,
        loyalty_list_footer_message=(data.loyalty_list_footer_message).strip(),
        trigger_sites=data.trigger_sites,
        transaction_count_for_costa_kwh_consumption = data.transaction_count_for_costa_kwh_consumption or None,
        detail_site_check=data.detail_site_check,
        is_car_wash = is_car_wash,
        visibility = visibility,
        display_on_charging_screen = data.display_on_charging_screen,
    )
    if data.loyalty_type in LOYALTY_TYPES:
        # adding notification content
        add_loyalty_notification_data(data, user, loyalty.id)
    bulk_create_products_data = [
        LoyaltyProducts(
            loyalty_id_id=loyalty.id,
            product_plu=loyalty_product.product_plu,
            product_bar_code=loyalty_product.product_bar_code,
            price=loyalty_product.price,
            redeem_product_promotion_price=(
                loyalty_product.redeem_product_promotion_price
            ),
            status=loyalty_product.status,
            desc=loyalty_product.product,
            created_date=timezone.localtime(timezone.now()),
            updated_by=user.full_name,
        )
        for loyalty_product in data.loyalty_products
    ]
    if bulk_create_products_data:
        LoyaltyProducts.objects.bulk_create(bulk_create_products_data)
    bulk_create_occurrences_data = [
        LoyaltyOccurrences(
            loyalty_id_id=loyalty.id,
            date=date_formater_for_frontend_date(occurrence.date),
            start_time=occurrence.start_time,
            end_time=occurrence.end_time,
            created_date=timezone.localtime(timezone.now()),    
            updated_by=user.full_name,
        )
        for occurrence in data.occurrences
    ]
    if bulk_create_occurrences_data:
        LoyaltyOccurrences.objects.bulk_create(bulk_create_occurrences_data)
    stations_data = get_stations_object()
    bulk_create_data = [
        LoyaltyAvailableOn(
            loyalty_id_id=loyalty.id,
            station_id_id=stations_data[station_id]["id"],
            station_name=stations_data[station_id]["station_name"],
            operation_region=stations_data[station_id]["operation_region"],
            region=stations_data[station_id]["region"],
            area=stations_data[station_id]["area"],
            updated_date=timezone.localtime(timezone.now()),
            updated_by=user.full_name,
        )
        for station_id in list(set(data.stations))
    ]
    if bulk_create_data:
        LoyaltyAvailableOn.objects.bulk_create(bulk_create_data)
    new_data = audit_data_formatter(LOYALTY_CONST, loyalty.id)
    add_audit_data(
        user,
        f"{loyalty.unique_code}, {loyalty.loyalty_title}",
        f"{LOYALTY_CONST}-{loyalty.id}",
        AUDIT_ADD_CONSTANT,
        LOYALTY_CONST,
        new_data,
        None,
    )
    return None


def update_single_loyalty(*args):
    """this function updates single loyalty"""
    data, loyalty, loyalty_pk, shops, user = args
    start_date = (
        date_formater_for_frontend_date(
            data.start_date
        )
    )
    end_date = (
        end_date_formater_for_frontend_date(
            data.end_date
        )
    )
    if data.loyalty_type == COSTA_COFFEE:
        costa_loyalty_exists = Loyalty.objects.filter(
            ~Q(id=loyalty_pk),
            loyalty_type=COSTA_COFFEE,
            status=ACTIVE,
            deleted=NO
        )
        if costa_loyalty_exists.first():
            response = {
                "status": 0,
                "message": "It’s not possible to add another Costa Coffee loyalty as one costa coffee loyalty is active.",
                "url": reverse("station_list"),
            }
            return JsonResponse(response)
    loyalty_exists = Loyalty.objects.filter(
        ~Q(id=loyalty_pk), unique_code=data.unique_code
    )
    if loyalty_exists.first():
        response = {
            "status": 0,
            "message": "Loyalty with provided unique code already exists",
            "url": reverse("station_list"),
        }
        return JsonResponse(response)
    old_data = audit_data_formatter(LOYALTY_CONST, loyalty_pk)
    image_data = None
    if data.promotion_image:
        if data.promotion_image != loyalty["image"]:
            image_data = image_converter(data.promotion_image)
    else:
        if Loyalty.objects.filter(id=loyalty_pk).first().image:
            Loyalty.objects.filter(id=loyalty_pk).first().image.delete()
            Loyalty.objects.filter(id=loyalty_pk).update(image=None)
    if image_data:
        if Loyalty.objects.filter(id=loyalty_pk).first().image:
            Loyalty.objects.filter(id=loyalty_pk).first().image.delete()
        image = optimize_image(
            image_data[IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN],
            f"{data.loyalty_title}_{randon_string_generator()}"
            + "."
            + image_data[1],
            LOYALTY_IMAGE,
        )
        station_loyalty_card_image = optimize_image(
            image_data[IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN],
            f"{data.loyalty_title}_station_loyalty_card_image_{randon_string_generator()}"
            + "."
            + image_data[1],
            PROMOTION_IMAGE,
        )
        loyalty_data = get_object_or_404(Loyalty, id=loyalty_pk)
        loyalty_data.image = image
        loyalty_data.station_loyalty_card_image = station_loyalty_card_image
        loyalty_data.save()
    reward_image_data = None
    if data.reward_image:
        if data.reward_image != loyalty["reward_image"]:
            reward_image_data = image_converter(data.reward_image)
    else:
        if Loyalty.objects.filter(id=loyalty_pk).first().reward_image:
            Loyalty.objects.filter(id=loyalty_pk).first().reward_image.delete()
            Loyalty.objects.filter(id=loyalty_pk).update(reward_image=None)
    if reward_image_data:
        if Loyalty.objects.filter(id=loyalty_pk).first().reward_image:
            Loyalty.objects.filter(id=loyalty_pk).first().reward_image.delete()
        reward_image = optimize_image(
            reward_image_data[IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN],
            f"{data.loyalty_title}_reward_image_{randon_string_generator()}"
            + "."
            + reward_image_data[1],
            LOYALTY_REWARD_IMAGE,
            reward_image_data[0]
        )
        loyalty_data = get_object_or_404(Loyalty, id=loyalty_pk)
        loyalty_data.reward_image = reward_image
        loyalty_data.save()
    # Update query on loyalties.
    Loyalty.objects.filter(id=loyalty_pk).update(
        loyalty_title=data.loyalty_title,
        unique_code=data.unique_code,
        category=data.category,
        bar_code_std=data.bar_code_std,
        valid_from_date=start_date,
        valid_to_date=end_date,
        occurance_status=data.occurance_status,
        steps_to_redeem=data.steps_to_redeem,
        redeem_type=data.redeem_type,
        cycle_duration=data.cycle_duration,
        number_of_paid_purchases=data.number_of_paid_purchases,
        qr_refresh_time=data.qr_refresh_time,
        status=data.status,
        offer_details=data.offer_details,
        terms_and_conditions=data.terms_and_conditions,
        redeem_product_code=data.redeem_product_code,
        redeem_product=data.redeem_product,
        redeem_product_promotional_code=(data.redeem_product_promotional_code),
        expiry_in_days=data.expiry_in_days,
        shop_ids=shops,
        loyalty_type=data.loyalty_type,
        number_of_total_issuances=data.number_of_total_issuances,
        reward_activated_notification_expiry=data.reward_activated_notification_expiry,
        reward_expiration_notification_expiry=data.reward_expiration_notification_expiry,
        expire_reward_before_x_number_of_days=(
            data.reward_expiration_notification_before_x_number_of_days
        ),
        reward_expiry_notification_trigger_time=(
            data.reward_expiry_notification_trigger_time
        ),
        offer_type=data.offer_type,
        updated_date=timezone.localtime(timezone.now()),
        updated_by=user.full_name,
        loyalty_list_footer_message=(data.loyalty_list_footer_message).strip(),
        trigger_sites=data.trigger_sites,
        transaction_count_for_costa_kwh_consumption = data.transaction_count_for_costa_kwh_consumption or None,
        detail_site_check=data.detail_site_check,
        visibility = data.loyalty_visibility,
        is_car_wash = data.is_car_wash,
        display_on_charging_screen = data.display_on_charging_screen,

    )
    if data.loyalty_type in LOYALTY_TYPES:
        if (
            loyalty["reward_expiration_notification_id_id"] and
            loyalty["reward_unlocked_notification_id_id"]
        ):
            update_loyalty_notification_data(data, loyalty, user)
        else:
            # adding notification content
            add_loyalty_notification_data(data, user, loyalty["id"])
    for loyalty_product in data.loyalty_products:
        # Condition to check whether loyalty product is already
        # present for loyalty in databse or newly added while updation
        if loyalty_product.lp_id:
            # Fetching loyalty product if product alredy exists for loyalty
            old_oroduct = LoyaltyProducts.objects.filter(
                id=loyalty_product.lp_id
            )
            if loyalty_product.deleted:
                old_oroduct.update(
                    deleted=YES,
                    updated_date=timezone.localtime(timezone.now()),
                    updated_by=user.full_name,
                )
            else:
                old_oroduct.update(
                    product_plu=loyalty_product.product_plu,
                    product_bar_code=loyalty_product.product_bar_code,
                    price=loyalty_product.price,
                    redeem_product_promotion_price=(
                        loyalty_product.redeem_product_promotion_price
                    ),
                    status=loyalty_product.status,
                    desc=loyalty_product.product,
                    updated_date=timezone.localtime(timezone.now()),
                    updated_by=user.full_name,
                )
        else:
            # If the loyalty product is added newly while updating the station
            # then we have to add it. Below are the queries to add
            # loyalty products.
            if not loyalty_product.deleted:
                LoyaltyProducts.objects.create(
                    loyalty_id_id=loyalty_pk,
                    product_plu=loyalty_product.product_plu,
                    product_bar_code=loyalty_product.product_bar_code,
                    price=loyalty_product.price,
                    redeem_product_promotion_price=(
                        loyalty_product.redeem_product_promotion_price
                    ),
                    status=loyalty_product.status,
                    desc=loyalty_product.product,
                    created_date=timezone.localtime(timezone.now()),
                    updated_by=user.full_name,
                )

    for loyalty_occurrence in data.occurrences:
        if loyalty_occurrence.occurrence_id:
            old_occurrence = LoyaltyOccurrences.objects.filter(
                id=loyalty_occurrence.occurrence_id
            )
            if loyalty_occurrence.deleted:
                old_occurrence.update(
                    deleted=YES,
                    updated_date=timezone.localtime(timezone.now()),
                    updated_by=user.full_name,
                )
            else:
                old_occurrence.update(
                    date=date_formater_for_frontend_date(loyalty_occurrence.date),
                    start_time=loyalty_occurrence.start_time,
                    end_time=loyalty_occurrence.end_time,
                    updated_date=timezone.localtime(timezone.now()),
                    updated_by=user.full_name,
                )
        else:
            # If the loyalty product is added newly while updating the station
            # then we have to add it. Below are the queries to add
            # loyalty products.
            if not loyalty_occurrence.deleted:
                LoyaltyOccurrences.objects.create(
                    loyalty_id_id=loyalty_pk,
                    date=date_formater_for_frontend_date(loyalty_occurrence.date),
                    start_time=loyalty_occurrence.start_time,
                    end_time=loyalty_occurrence.end_time,
                    created_date=timezone.localtime(timezone.now()),
                    updated_by=user.full_name,
                )

    # If station is not present previously in database for the station
    # then we have to create it.
    stations_list = list(set(data.stations))
    stations_data = get_stations_object()
    bulk_create_data = [
        LoyaltyAvailableOn(
            loyalty_id_id=loyalty_pk,
            station_id_id=stations_data[station_id]["id"],
            station_name=stations_data[station_id]["station_name"],
            operation_region=stations_data[station_id]["operation_region"],
            region=stations_data[station_id]["region"],
            area=stations_data[station_id]["area"],
            updated_date=timezone.localtime(timezone.now()),
            updated_by=user.full_name,
        )
        for station_id in stations_list
        if station_id not in loyalty["station_ids"]
    ]
    if bulk_create_data:
        LoyaltyAvailableOn.objects.bulk_create(bulk_create_data)
    # If station was present previously in database for the loyalty,
    # then we have to update it.
    stations_need_to_delete = [
        station_id
        for station_id in loyalty["station_ids"]
        if station_id not in stations_list
    ]
    if stations_need_to_delete:
        LoyaltyAvailableOn.objects.filter(
            loyalty_id_id=loyalty_pk,
            station_id__station_id__in=stations_need_to_delete,
        ).update(
            deleted=YES,
            updated_date=timezone.localtime(timezone.now()),
            updated_by=user.full_name,
        )
    new_data = audit_data_formatter(LOYALTY_CONST, loyalty_pk)
    loyalty_record = Loyalty.objects.filter(id=loyalty_pk)
    if old_data != new_data:
        add_audit_data(
            user,
            (
                loyalty_record.first().unique_code
                + ", "
                + loyalty_record.first().loyalty_title
            ),
            f"{LOYALTY_CONST}-{loyalty_pk}",
            AUDIT_UPDATE_CONSTANT,
            LOYALTY_CONST,
            new_data,
            old_data,
        )
    return None
