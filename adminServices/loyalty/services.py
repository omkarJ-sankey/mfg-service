from datetime import timedelta
import json
from io import StringIO
import traceback
from django.http import JsonResponse
from django.utils import timezone
from django.urls import reverse
from types import SimpleNamespace
from django.db.models import Q

from adminServices.dashboard.app_level_constants import DASHBOARD_DATA_DAYS_LIMIT, DEFAULT_DASHBOARD_DATA_DAYS_LIMIT
from adminServices.loyalty.db_operators import add_loyalty_notification_data, get_stations_object, update_loyalty_notification_data
from adminServices.loyalty.loyalty_helper_functions import export_loyalty_data, remove_loyalties_cached_data, return_amenities_from_configurations, return_loyalty_data, return_loyalty_list, return_shops_from_configurations
from adminServices.stations.stations_helper_functions import remove_stations_cached_data
from sharedServices.common import date_formater_for_frontend_date, end_date_formater_for_frontend_date, filter_function_for_base_configuration, filter_url, image_converter, order_by_function, randon_string_generator, search_validator
from sharedServices.common_audit_trail_functions import add_audit_data, audit_data_formatter
from sharedServices.constants import ACTIVE, AUDIT_ADD_CONSTANT, AUDIT_DELETE_CONSTANT, AUDIT_UPDATE_CONSTANT, BURNED, COSTA_COFFEE, IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN, LOYALTY_CONST, LOYALTY_IMAGE, LOYALTY_REWARD_IMAGE, LOYALTY_TYPES, NO, PROMOTION_IMAGE, PURCHASED, YES, ConstantMessage
from sharedServices.image_optimization_funcs import optimize_image
from sharedServices.model_files.audit_models import AuditTrail
from sharedServices.model_files.loyalty_models import Loyalty, LoyaltyAvailableOn, LoyaltyOccurrences, LoyaltyProducts, UserLoyaltyTransactions
from sharedServices.model_files.notifications_module_models import PushNotifications


def add_loyalty_service(data, user):
    """Service to handle loyalty creation."""
    try:
        data = SimpleNamespace(**data)
        image = None
        station_loyalty_card_image = None
        reward_image = None
        user = {
            "id": 1,
            "full_name": "Test User",
            "role_id": {"role_name": "Admin"}
        }

        # === Validation logic ===
        if data.loyalty_type == COSTA_COFFEE:
            costa_loyalty_exists = Loyalty.objects.filter(
                loyalty_type=COSTA_COFFEE,
                status=ACTIVE,
                deleted=NO
            ).exists()
            if costa_loyalty_exists:
                return {
                    "status": 0,
                    "message": ConstantMessage.COSTA_COFFEE_ALREADY_EXISTS,
                    "data": {},
                }

        if Loyalty.objects.filter(unique_code=data.unique_code).exists():
            return {
                "status": 0,
                "message": ConstantMessage.LOYALTY_DUPLICATE_CODE,
                "data": {},
            }

        # === Image Handling ===
        if getattr(data, "promotion_image", None):
            image_data = image_converter(data.promotion_image)
            image = optimize_image(
                image_data[0],
                f"{data.loyalty_title}.jpg",
                "LOYALTY_IMAGE",
            )
            station_loyalty_card_image = optimize_image(
                image_data[0],
                f"{data.loyalty_title}_card.jpg",
                "PROMOTION_IMAGE",
            )

        if getattr(data, "reward_image", None):
            reward_image_data = image_converter(data.reward_image)
            reward_image = optimize_image(
                reward_image_data[0],
                f"{data.loyalty_title}_reward.jpg",
                "LOYALTY_REWARD_IMAGE",
                reward_image_data[0]
            )

        # === Prepare shop ids as string ===
        string_converter = StringIO()
        json.dump(data.shop, string_converter)
        shops = string_converter.getvalue()

        start_date = date_formater_for_frontend_date(data.start_date)
        end_date = end_date_formater_for_frontend_date(data.end_date)

        # === Create Loyalty ===
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
            redeem_product_promotional_code=data.redeem_product_promotional_code,
            expiry_in_days=data.expiry_in_days,
            image=image,
            station_loyalty_card_image=station_loyalty_card_image,
            reward_image=reward_image,
            shop_ids=shops,
            created_date=timezone.localtime(timezone.now()),
            updated_by=user["full_name"],
            offer_type=data.offer_type,
            loyalty_list_footer_message=data.loyalty_list_footer_message.strip(),
            trigger_sites=data.trigger_sites,
            transaction_count_for_costa_kwh_consumption=data.transaction_count_for_costa_kwh_consumption or None,
            detail_site_check=data.detail_site_check,
            is_car_wash=data.is_car_wash,
            visibility=data.visibility,
            display_on_charging_screen=data.display_on_charging_screen,
        )

        # === Optional: Notifications ===
        if data.loyalty_type in LOYALTY_TYPES:
            add_loyalty_notification_data(data, user, loyalty.id)

        # === Bulk Create Related Data ===
        loyalty_products = [
            LoyaltyProducts(
                loyalty_id_id=loyalty.loyalty_id,
                product_plu=p["product_plu"],
                product_bar_code=p["product_bar_code"],
                price=p["price"],
                redeem_product_promotion_price=p["redeem_product_promotion_price"],
                status=p["status"],
                desc=p["product"],
                created_date=timezone.localtime(timezone.now()),
                updated_by=user["full_name"],
            )
            for p in data.loyalty_products
        ]
        if loyalty_products:
            LoyaltyProducts.objects.bulk_create(loyalty_products)

        loyalty_occurrences = [
            LoyaltyOccurrences(
                loyalty_id_id=loyalty.loyalty_id,
                date=date_formater_for_frontend_date(o["date"]),
                start_time=o["start_time"],
                end_time=o["end_time"],
                created_date=timezone.localtime(timezone.now()),
                updated_by=user["full_name"],
            )
            for o in data.occurrences
        ]
        if loyalty_occurrences:
            LoyaltyOccurrences.objects.bulk_create(loyalty_occurrences)

        # === Link Loyalty to Stations ===
        stations_data = get_stations_object()
        if stations_data:
            loyalty_stations = [
                LoyaltyAvailableOn(
                    loyalty_id_id=loyalty.loyalty_id,
                    station_id_id=stations_data[s]["id"],
                    station_name=stations_data[s]["station_name"],
                    operation_region=stations_data[s]["operation_region"],
                    region=stations_data[s]["region"],
                    area=stations_data[s]["area"],
                    updated_date=timezone.localtime(timezone.now()),
                    updated_by=user["full_name"],
                )
                for s in list(set(data.stations))
            ]
        if loyalty_stations:
            LoyaltyAvailableOn.objects.bulk_create(loyalty_stations)

        # === Audit Trail ===
        new_data = audit_data_formatter(LOYALTY_CONST, loyalty.loyalty_id)
        add_audit_data(
            user,
            f"{loyalty.unique_code}, {loyalty.loyalty_title}",
            f"{LOYALTY_CONST}-{loyalty.loyalty_id}",
            AUDIT_ADD_CONSTANT,
            LOYALTY_CONST,
            new_data,
            None,
        )

        # === Cache Cleanup ===
        remove_loyalties_cached_data()

        return {
            "status": 1,
            "message": ConstantMessage.LOYALTY_ADDED_SUCCESS,
            "data": {},
        }

    except Exception as e:
        return {
            "status": 0,
            "message": f"{ConstantMessage.SOMETHING_WENT_WRONG}: {str(e)}",
            "data": {},
        }



def update_single_loyalty_service(data, loyalty, loyalty_pk, shops, user):
    """Service to update single loyalty (same business logic preserved)."""
    try:
        start_date = date_formater_for_frontend_date(data.start_date)
        end_date = end_date_formater_for_frontend_date(data.end_date)

        if data.loyalty_type == COSTA_COFFEE:
            costa_loyalty_exists = Loyalty.objects.filter(
                ~Q(id=loyalty_pk),
                loyalty_type=COSTA_COFFEE,
                status=ACTIVE,
                deleted=NO,
            )
            if costa_loyalty_exists.exists():
                return JsonResponse({
                    "status": 0,
                    "message": "It’s not possible to add another Costa Coffee loyalty as one Costa Coffee loyalty is active.",
                    "url": reverse("station_list"),
                })

        # --- Unique code check ---
        loyalty_exists = Loyalty.objects.filter(
            ~Q(id=loyalty_pk), unique_code=data.unique_code
        )
        if loyalty_exists.exists():
            return JsonResponse({
                "status": 0,
                "message": "Loyalty with provided unique code already exists",
                "url": reverse("station_list"),
            })

        old_data = audit_data_formatter(LOYALTY_CONST, loyalty_pk)

        # --- Image updates (promotion + reward) ---
        image_data = None
        if data.promotion_image:
            if data.promotion_image != loyalty["image"]:
                image_data = image_converter(data.promotion_image)
        else:
            if Loyalty.objects.filter(id=loyalty_pk).first().image:
                Loyalty.objects.filter(id=loyalty_pk).first().image.delete()
                Loyalty.objects.filter(id=loyalty_pk).update(image=None)

        if image_data:
            existing_loyalty = Loyalty.objects.filter(id=loyalty_pk).first()
            if existing_loyalty.image:
                existing_loyalty.image.delete()

            image = optimize_image(
                image_data[IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN],
                f"{data.loyalty_title}_{randon_string_generator()}.{image_data[1]}",
                LOYALTY_IMAGE,
            )
            station_loyalty_card_image = optimize_image(
                image_data[IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN],
                f"{data.loyalty_title}_station_loyalty_card_image_{randon_string_generator()}.{image_data[1]}",
                PROMOTION_IMAGE,
            )

            existing_loyalty.image = image
            existing_loyalty.station_loyalty_card_image = station_loyalty_card_image
            existing_loyalty.save()

        # --- Reward image update ---
        reward_image_data = None
        if data.reward_image:
            if data.reward_image != loyalty["reward_image"]:
                reward_image_data = image_converter(data.reward_image)
        else:
            if Loyalty.objects.filter(id=loyalty_pk).first().reward_image:
                Loyalty.objects.filter(id=loyalty_pk).first().reward_image.delete()
                Loyalty.objects.filter(id=loyalty_pk).update(reward_image=None)

        if reward_image_data:
            existing_loyalty = Loyalty.objects.filter(id=loyalty_pk).first()
            if existing_loyalty.reward_image:
                existing_loyalty.reward_image.delete()

            reward_image = optimize_image(
                reward_image_data[IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN],
                f"{data.loyalty_title}_reward_image_{randon_string_generator()}.{reward_image_data[1]}",
                LOYALTY_REWARD_IMAGE,
                reward_image_data[0],
            )
            existing_loyalty.reward_image = reward_image
            existing_loyalty.save()

        # --- Update main loyalty record ---
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
            redeem_product_promotional_code=data.redeem_product_promotional_code,
            expiry_in_days=data.expiry_in_days,
            shop_ids=shops,
            loyalty_type=data.loyalty_type,
            number_of_total_issuances=data.number_of_total_issuances,
            reward_activated_notification_expiry=data.reward_activated_notification_expiry,
            reward_expiration_notification_expiry=data.reward_expiration_notification_expiry,
            expire_reward_before_x_number_of_days=data.reward_expiration_notification_before_x_number_of_days,
            reward_expiry_notification_trigger_time=data.reward_expiry_notification_trigger_time,
            offer_type=data.offer_type,
            updated_date=timezone.localtime(timezone.now()),
            updated_by=user.full_name,
            loyalty_list_footer_message=data.loyalty_list_footer_message.strip(),
            trigger_sites=data.trigger_sites,
            transaction_count_for_costa_kwh_consumption=data.transaction_count_for_costa_kwh_consumption or None,
            detail_site_check=data.detail_site_check,
            visibility=data.loyalty_visibility,
            is_car_wash=data.is_car_wash,
            display_on_charging_screen=data.display_on_charging_screen,
        )

        # --- Notification updates ---
        if data.loyalty_type in LOYALTY_TYPES:
            if (
                loyalty["reward_expiration_notification_id_id"]
                and loyalty["reward_unlocked_notification_id_id"]
            ):
                update_loyalty_notification_data(data, loyalty, user)
            else:
                add_loyalty_notification_data(data, user, loyalty["id"])

        # --- Loyalty Products ---
        for loyalty_product in data.loyalty_products:
            if loyalty_product.lp_id:
                old_product = LoyaltyProducts.objects.filter(id=loyalty_product.lp_id)
                if loyalty_product.deleted:
                    old_product.update(
                        deleted=YES,
                        updated_date=timezone.localtime(timezone.now()),
                        updated_by=user.full_name,
                    )
                else:
                    old_product.update(
                        product_plu=loyalty_product.product_plu,
                        product_bar_code=loyalty_product.product_bar_code,
                        price=loyalty_product.price,
                        redeem_product_promotion_price=loyalty_product.redeem_product_promotion_price,
                        status=loyalty_product.status,
                        desc=loyalty_product.product,
                        updated_date=timezone.localtime(timezone.now()),
                        updated_by=user.full_name,
                    )
            else:
                if not loyalty_product.deleted:
                    LoyaltyProducts.objects.create(
                        loyalty_id_id=loyalty_pk,
                        product_plu=loyalty_product.product_plu,
                        product_bar_code=loyalty_product.product_bar_code,
                        price=loyalty_product.price,
                        redeem_product_promotion_price=loyalty_product.redeem_product_promotion_price,
                        status=loyalty_product.status,
                        desc=loyalty_product.product,
                        created_date=timezone.localtime(timezone.now()),
                        updated_by=user.full_name,
                    )

        # --- Loyalty Occurrences ---
        for occurrence in data.occurrences:
            if occurrence.occurrence_id:
                old_occurrence = LoyaltyOccurrences.objects.filter(id=occurrence.occurrence_id)
                if occurrence.deleted:
                    old_occurrence.update(
                        deleted=YES,
                        updated_date=timezone.localtime(timezone.now()),
                        updated_by=user.full_name,
                    )
                else:
                    old_occurrence.update(
                        date=date_formater_for_frontend_date(occurrence.date),
                        start_time=occurrence.start_time,
                        end_time=occurrence.end_time,
                        updated_date=timezone.localtime(timezone.now()),
                        updated_by=user.full_name,
                    )
            else:
                if not occurrence.deleted:
                    LoyaltyOccurrences.objects.create(
                        loyalty_id_id=loyalty_pk,
                        date=date_formater_for_frontend_date(occurrence.date),
                        start_time=occurrence.start_time,
                        end_time=occurrence.end_time,
                        created_date=timezone.localtime(timezone.now()),
                        updated_by=user.full_name,
                    )

        # --- Station Updates ---
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

        stations_to_delete = [
            station_id
            for station_id in loyalty["station_ids"]
            if station_id not in stations_list
        ]
        if stations_to_delete:
            LoyaltyAvailableOn.objects.filter(
                loyalty_id_id=loyalty_pk,
                station_id__station_id__in=stations_to_delete,
            ).update(
                deleted=YES,
                updated_date=timezone.localtime(timezone.now()),
                updated_by=user.full_name,
            )

        # --- Audit trail ---
        new_data = audit_data_formatter(LOYALTY_CONST, loyalty_pk)
        if old_data != new_data:
            loyalty_record = Loyalty.objects.filter(id=loyalty_pk).first()
            add_audit_data(
                user,
                f"{loyalty_record.unique_code}, {loyalty_record.loyalty_title}",
                f"{LOYALTY_CONST}-{loyalty_pk}",
                AUDIT_UPDATE_CONSTANT,
                LOYALTY_CONST,
                new_data,
                old_data,
            )

        return None  # Success, handled by view

    except Exception as e:
        traceback.print_exc()
        return JsonResponse({
            "status": 0,
            "message": f"Loyalty update failed: {str(e)}",
            "url": reverse("loyalties_list"),
        })

def get_loyality_list(validated_data):
    """
    Service function that handles business logic for fetching loyalty list.
    """

    from_date = validated_data.get("from_date", "")
    to_date = validated_data.get("to_date", "")
    search = validated_data.get("search", "")
    status_val = validated_data.get("status", None)
    order_by_start_date = validated_data.get("order_by_start_date", None)
    order_by_end_date = validated_data.get("order_by_end_date", None)
    do_export = validated_data.get("export", None)

    dashboard_data_days_limit = int(
        filter_function_for_base_configuration(
            DASHBOARD_DATA_DAYS_LIMIT, DEFAULT_DASHBOARD_DATA_DAYS_LIMIT
        )
    )
    loyalty_list = return_loyalty_list()
    updated_url = ""

    # -----------------------------
    # 🕓 Date Validation Logic
    # -----------------------------
    if (
        to_date != ""
        and (
            date_formater_for_frontend_date(to_date)
            - (
                date_formater_for_frontend_date(from_date)
                if from_date
                else date_formater_for_frontend_date(to_date)
                - timedelta(days=dashboard_data_days_limit)
            )
        ).days
        < 0
    ):
        to_date = ""

    current_and_from_date_difference = 0
    if from_date:
        current_and_from_date_difference = (
            timezone.now() - date_formater_for_frontend_date(from_date)
        ).days

    to_date_and_from_date_difference = (
        current_and_from_date_difference
        if to_date == ""
        else (
            date_formater_for_frontend_date(to_date)
            - (
                date_formater_for_frontend_date(from_date)
                if from_date
                else date_formater_for_frontend_date(to_date)
                - timedelta(days=dashboard_data_days_limit)
            )
        ).days
    )

    # Adjust if beyond allowed range
    if to_date_and_from_date_difference > dashboard_data_days_limit:
        to_date = (
            date_formater_for_frontend_date(from_date)
            + timedelta(days=dashboard_data_days_limit)
        ).strftime("%d/%m/%Y")

    if from_date:
        loyalty_list = loyalty_list.filter(
            valid_from_date__gte=date_formater_for_frontend_date(from_date)
        )
        updated_url += f"&from_date={from_date}"

    if to_date:
        formatted_to_date = date_formater_for_frontend_date(to_date)
        loyalty_list = loyalty_list.filter(valid_from_date__lte=formatted_to_date)
        updated_url += f"&to_date={to_date}"

    if search:
        loyalty_list = loyalty_list.filter(loyalty_title__icontains=search)

    if status_val and status_val != "All":
        loyalty_list = loyalty_list.filter(status=status_val)

    ordered_loyalties = order_by_function(
        loyalty_list,
        [
            {"valid_from_date": ["order_by_start_date", order_by_start_date]},
            {"valid_to_date": ["order_by_end_date", order_by_end_date]},
        ],
    )
    loyalty_list = ordered_loyalties["ordered_table"]
    export_response = None
    if do_export == YES:
        export_response = export_loyalty_data({"filtered_table_for_export": loyalty_list})
    
    return {
        "loyalties": loyalty_list,              
        "updated_url": updated_url,              
        "export_response": export_response,     
        "dashboard_limit": dashboard_data_days_limit,
        "from_date": from_date,
        "to_date": to_date,
    }



def delete_loyalty_service(loyalty_pk, user):
    """Service to perform soft deletion of loyalty and its related objects."""
    # Fetch loyalty
    loyalty = Loyalty.objects.filter(id=loyalty_pk).first()
    if not loyalty:
        raise ValueError("Loyalty not found")

    Loyalty.objects.filter(id=loyalty_pk).update(
        deleted=YES,
        updated_date=timezone.localtime(timezone.now()),
        updated_by=user.full_name,
    )

    if loyalty.loyalty_type == COSTA_COFFEE:
        UserLoyaltyTransactions.objects.filter(
            Q(expired_on=None)
            | Q(expired_on__lte=timezone.localtime(timezone.now())),
            action_code=PURCHASED,
            loyalty_id=loyalty,
        ).update(
            action_code=BURNED,
            updated_date=timezone.localtime(timezone.now()),
        )

        PushNotifications.objects.filter(
            id__in=[
                loyalty.reward_unlocked_notification_id.id,
                loyalty.reward_expiration_notification_id.id,
            ]
        ).update(deleted=YES)

    LoyaltyAvailableOn.objects.filter(loyalty_id_id=loyalty_pk).update(
        deleted=YES,
        updated_date=timezone.localtime(timezone.now()),
        updated_by=user.full_name,
    )

    prev_audit_data = AuditTrail.objects.filter(
        data_db_id=f"{LOYALTY_CONST}-{loyalty_pk}"
    ).last()

    if prev_audit_data and prev_audit_data.new_data:
        add_audit_data(
            user,
            (loyalty.unique_code + ", " + loyalty.loyalty_title),
            f"{LOYALTY_CONST}-{loyalty_pk}",
            AUDIT_DELETE_CONSTANT,
            LOYALTY_CONST,
            None,
            prev_audit_data.new_data,
        )

    # Clear cache
    remove_loyalties_cached_data()
    remove_stations_cached_data()

    return {
        "loyalty_id": loyalty.id,
        "loyalty_code": loyalty.unique_code,
        "deleted_by": user.full_name,
        "deleted_at": timezone.localtime(timezone.now()),
    }

def change_loyalty_status(loyalty_id, status_value, user):
    """Service to change loyalty status and manage related updates."""
    loyalty = Loyalty.objects.filter(id=loyalty_id).first()
    if not loyalty:
        raise ValueError("Loyalty not found")

    old_data = audit_data_formatter(LOYALTY_CONST, loyalty_id)

    # Check for existing active Costa loyalty
    costa_loyalty_exists = Loyalty.objects.filter(
        ~Q(id=loyalty_id),
        loyalty_type=COSTA_COFFEE,
        status=ACTIVE,
        deleted=NO,
    ).first()

    # Validation logic
    if (
        status_value != "Active"
        or loyalty.loyalty_type != COSTA_COFFEE
        or (
            loyalty.loyalty_type == COSTA_COFFEE
            and status_value == "Active"
            and costa_loyalty_exists is None
        )
    ):
        # Update loyalty status
        Loyalty.objects.filter(id=loyalty_id).update(
            status=status_value,
            updated_date=timezone.localtime(timezone.now()),
        )

        new_data = audit_data_formatter(LOYALTY_CONST, loyalty_id)

        if old_data != new_data:
            add_audit_data(
                user,
                (loyalty.unique_code + ", " + loyalty.loyalty_title),
                f"{LOYALTY_CONST}_{loyalty_id}",
                AUDIT_UPDATE_CONSTANT,
                LOYALTY_CONST,
                new_data,
                old_data,
            )

        remove_loyalties_cached_data()

        return {"status": True, "message": "Successfully updated loyalty status!"}

    else:
        return {"status": False, "message": "Another Costa loyalty is already active!"}
    
def return_shop_and_amenity_list():
    """this function returns list of shops and amenities"""
    shops_list = [
        [i["id"], i["service_name"]]
        for i in return_shops_from_configurations()
    ]
    amenities_list = [
        [i["id"], i["service_name"]]
        for i in return_amenities_from_configurations()
    ]
    return [shops_list, amenities_list]

def get_loyalty_details(loyalty_pk, user):
    """Service to fetch loyalty details with shops and amenities."""
    loyalty_obj = Loyalty.objects.filter(id=loyalty_pk).values().first()
    if not loyalty_obj:
        raise ValueError("Loyalty not found")

    # Get raw data
    loyalty = return_loyalty_data(loyalty_obj, loyalty_pk, False)

    # Shops and amenities lists
    shops_list, amenities_list = return_shop_and_amenity_list()
    shops = [shop[1] for shop in shops_list if shop[1] in loyalty.get("shop", [])]
    amenities = [a[1] for a in amenities_list if a[1] in loyalty.get("shop", [])]

    url_data = filter_url(user.role_id.access_content.all(), LOYALTY_CONST)

    return {
        "loyalty": loyalty,
        "shops": shops,
        "amenities": amenities,
        "url_data": url_data
    }
