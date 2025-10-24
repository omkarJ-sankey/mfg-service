import json
from io import StringIO
import traceback
from django.http import JsonResponse
from django.utils import timezone
from django.urls import reverse
from types import SimpleNamespace

from adminServices.loyalty.db_operators import add_loyalty_notification_data, get_stations_object, update_loyalty_notification_data
from adminServices.loyalty.loyalty_helper_functions import remove_loyalties_cached_data
from sharedServices.common import date_formater_for_frontend_date, end_date_formater_for_frontend_date, image_converter, randon_string_generator
from sharedServices.common_audit_trail_functions import add_audit_data, audit_data_formatter
from sharedServices.constants import ACTIVE, AUDIT_ADD_CONSTANT, AUDIT_UPDATE_CONSTANT, COSTA_COFFEE, IMAGE_OBJECT_POSITION_IN_IMG_CONVRTER_FUN, LOYALTY_CONST, LOYALTY_IMAGE, LOYALTY_REWARD_IMAGE, LOYALTY_TYPES, NO, PROMOTION_IMAGE, YES, ConstantMessage
from sharedServices.image_optimization_funcs import optimize_image
from sharedServices.model_files.loyalty_models import Loyalty, LoyaltyAvailableOn, LoyaltyOccurrences, LoyaltyProducts


def add_loyalty_service(data, user):
    """Service to handle loyalty creation."""
    try:
        data = SimpleNamespace(**data)
        image = None
        station_loyalty_card_image = None
        reward_image = None

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
        if data.promotion_image:
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

        if data.reward_image:
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
            updated_by=user.full_name,
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
                loyalty_id_id=loyalty.id,
                product_plu=p["product_plu"],
                product_bar_code=p["product_bar_code"],
                price=p["price"],
                redeem_product_promotion_price=p["redeem_product_promotion_price"],
                status=p["status"],
                desc=p["product"],
                created_date=timezone.localtime(timezone.now()),
                updated_by=user.full_name,
            )
            for p in data.loyalty_products
        ]
        if loyalty_products:
            LoyaltyProducts.objects.bulk_create(loyalty_products)

        loyalty_occurrences = [
            LoyaltyOccurrences(
                loyalty_id_id=loyalty.id,
                date=date_formater_for_frontend_date(o["date"]),
                start_time=o["start_time"],
                end_time=o["end_time"],
                created_date=timezone.localtime(timezone.now()),
                updated_by=user.full_name,
            )
            for o in data.occurrences
        ]
        if loyalty_occurrences:
            LoyaltyOccurrences.objects.bulk_create(loyalty_occurrences)

        # === Link Loyalty to Stations ===
        stations_data = get_stations_object()
        loyalty_stations = [
            LoyaltyAvailableOn(
                loyalty_id_id=loyalty.id,
                station_id_id=stations_data[s]["id"],
                station_name=stations_data[s]["station_name"],
                operation_region=stations_data[s]["operation_region"],
                region=stations_data[s]["region"],
                area=stations_data[s]["area"],
                updated_date=timezone.localtime(timezone.now()),
                updated_by=user.full_name,
            )
            for s in list(set(data.stations))
        ]
        if loyalty_stations:
            LoyaltyAvailableOn.objects.bulk_create(loyalty_stations)

        # === Audit Trail ===
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
