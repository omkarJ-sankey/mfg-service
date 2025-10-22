"""loyalty common functions"""

# Date - 11/08/2021


# File details-
#   Author          - Shivkumar Kunmbhar
#   Description     - This file contains loyalty common functions.
#   Name            - loyalty common functions
#   Modified by     - Shivkumar Kunmbhar
#   Modified date   - 1/12/2023

from datetime import datetime, timedelta
from django.utils import timezone
from decimal import Decimal
import json
import ast
from django.db.models import Q
from rest_framework import status
import concurrent.futures
from django.core.cache import cache
import threading
from django.db.models import Value, BooleanField, Q, F, ExpressionWrapper, IntegerField
from django.forms.models import model_to_dict


from sharedServices.models import (
    ChargingSession,
    Loyalty,
    UserLoyaltyTransactions,
    LoyaltyTransactions,
    PushNotifications,
    Profile,
)
from sharedServices.common import (
    array_to_string_converter,
    string_to_array_converter,
    send_push,
    remove_all_cache,
)
from sharedServices.shared_station_serializer import (
    caching_station_finder_data,
)
from sharedServices.common import custom_round_function

from sharedServices.constants import (
    PURCHASED,
    REDEEMED,
    REDEEMED_ACTION_CODE,
    ACTIVE,
    COSTA_COFFEE,
    FREE_LOYALTY,
    BURNED,
    REWARD_UNLOCK,
    REWARD_EXPIRY,
    NO,
    DEFAULT_NOTIFICATION_IMAGE_URL,
    REGISTERED_USERS,
    ALL_USERS,
)
from sharedServices.model_files.ocpi_sessions_models import OCPISessions


def assign_loyalty_reward_and_send_notification(
    loyalty, user_ids, notification_identifier=REWARD_EXPIRY
):
    "This functions creates loyalty transactions reward and send notifications"
    number_of_issued_vouchers = (
        loyalty.number_of_issued_vouchers
        if loyalty.number_of_issued_vouchers
        else 0
    )
    print(f"[DEBUG] number_of_issued_vouchers: {number_of_issued_vouchers}")
    if notification_identifier == REWARD_UNLOCK:
        Loyalty.objects.filter(id=loyalty.id).update(
            number_of_issued_vouchers=number_of_issued_vouchers + 1,
        )
        if (
            number_of_issued_vouchers + 1
            == loyalty.number_of_total_issuances
        ):
            UserLoyaltyTransactions.objects.filter(
                Q(expired_on=None)
                | Q(expired_on__lte=timezone.localtime(timezone.now())),
                action_code=PURCHASED,
                loyalty_id=loyalty,
            ).update(
                action_code=BURNED,
                updated_date=timezone.localtime(timezone.now()),
            )
            cache.expire("cache_loyalties", timeout=0)
            start_caching_promotions_data = threading.Thread(
                target=caching_station_finder_data,
                daemon=True
            )
            start_caching_promotions_data.start()
            start_removing_promotions_cached_data = threading.Thread(
                target=remove_all_cache,
                daemon=True
            )
            start_removing_promotions_cached_data.start()
    print(f"[DEBUG] notification_identifier: {notification_identifier}")

    reward_unlocked_or_expiry_notification_data = (
        PushNotifications.objects.filter(
            id=(
                loyalty.reward_unlocked_notification_id.id
                if notification_identifier == REWARD_UNLOCK
                else loyalty.reward_expiration_notification_id.id
            )
        )
    )
    print(f"[DEBUG] reward_unlocked_or_expiry_notification_data: {reward_unlocked_or_expiry_notification_data}")
    user_profile = Profile.objects.filter(
        loyalty_preference_status=True,
        fcm_device_token__isnull=False,
        user_id__in=user_ids,
    )
    print(f"[DEBUG] user_profile: {user_profile}")
    if user_profile:
        registration_tokens = list(
            user_profile.values_list("fcm_device_token", flat=True)
        )
        print(f"[DEBUG] registration_tokens: {registration_tokens}")
        if reward_unlocked_or_expiry_notification_data and registration_tokens:
            notification_data = (
                reward_unlocked_or_expiry_notification_data.first()
            )
            success_count = send_push(
                notification_data.subject,
                notification_data.description,
                registration_tokens,
                (
                    notification_data.get_push_notification_image()
                    if notification_data.image
                    else DEFAULT_NOTIFICATION_IMAGE_URL.split("static/")[1]
                ),
                notification_data.screens,
                notification_data.inapp_notification,
                str(loyalty.id),
            )
            print(f"[DEBUG] success_count: {success_count}")
            delivered_time = timezone.localtime(timezone.now())
            if success_count:
                user_notifications_update_array = []
                inapp_notification_object = {
                    "id": int(delivered_time.timestamp()),
                    "subject": notification_data.subject,
                    "description": notification_data.description,
                    "image": (
                        str(notification_data.image)
                        if notification_data.image
                        else DEFAULT_NOTIFICATION_IMAGE_URL.split("static/")[1]
                    ),
                    "delivered_time": delivered_time.strftime(
                        "%Y-%m-%dT%H:%M:%S"
                    ),
                    "screens": notification_data.screens,
                    "read_status": False,
                    "expiry_in_hours": (
                        loyalty.reward_activated_notification_expiry
                        if notification_identifier == REWARD_UNLOCK
                        else loyalty.reward_expiration_notification_expiry
                    ),
                    "reference_id": loyalty.id,
                }
                print(f"[DEBUG] inapp_notification_object: {inapp_notification_object}")
                is_inapp_notification = (
                    notification_data.inapp_notification
                    and notification_data.inapp_notification == "true"
                )
                print(f"[DEBUG] is_inapp_notification: {is_inapp_notification}")

                def update_notifications_data(user_id):
                    "This function is notification data update helper"
                    user_notifications_update_array.append(
                        {
                            "user_id": user_id,
                            "delivered_time": delivered_time.strftime(
                                "%Y-%m-%dT%H:%M:%S"
                            ),
                        }
                    )
                    if is_inapp_notification:
                        user_profile = Profile.objects.filter(user_id=user_id)
                        prev_inapp_notifications = (
                            string_to_array_converter(
                                user_profile.first().inapp_notification_object
                            )
                            if user_profile.first().inapp_notification_object
                            else []
                        )
                        prev_inapp_notifications = [
                            inapp_notification_object
                        ] + prev_inapp_notifications
                        user_profile.update(
                            inapp_notification_object=array_to_string_converter(
                                prev_inapp_notifications
                            )
                        )

                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=50
                ) as executor:
                    executor.map(
                        update_notifications_data,
                        user_ids,
                    )
                reward_unlocked_or_expiry_notification_data.update(
                    assign_to=array_to_string_converter(
                        string_to_array_converter(
                            reward_unlocked_or_expiry_notification_data.first().assign_to
                        )
                        + user_notifications_update_array
                        if reward_unlocked_or_expiry_notification_data.first().assign_to
                        else user_notifications_update_array
                    )
                )


def save_user_loyalty_details(
    loyalty,
    user,
    number_of_paid_purchases,
    timestamp,
    purchased_quantity_or_amount,
    redeemed_product_sales_amount=None,
    invalid_transactions=None,
    number_of_loyalty_transaction=None,
    qr_code=None,
    transaction_details=None,
    station=None,
    qr_action_code=None,
    charging_session_db_id=None,
):
    """this function saves the user loyalty data to database"""
    print("************ purchased_quantity_or_amount", purchased_quantity_or_amount)
    print("************ loyalty.number_of_paid_purchases", loyalty.number_of_paid_purchases)
    print("************ loyalty.transaction_count_for_costa_kwh_consumption", loyalty.transaction_count_for_costa_kwh_consumption)
    if loyalty.loyalty_type == COSTA_COFFEE and purchased_quantity_or_amount < loyalty.number_of_paid_purchases and (loyalty.transaction_count_for_costa_kwh_consumption or 0) > 0:
        return {
                "status_code": status.HTTP_201_CREATED,
                "status": True,
                "message": "Transaction submitted successfully!",
                "invalid_transactions": invalid_transactions,
            }
    user_loyalty_transactions = UserLoyaltyTransactions.objects.filter(
        action_code=PURCHASED,
        loyalty_id=loyalty,
        user_id=user,
    )
    print("**1**",user_loyalty_transactions)
    if (
        loyalty.loyalty_type == COSTA_COFFEE
        and qr_action_code != REDEEMED_ACTION_CODE and loyalty.transaction_count_for_costa_kwh_consumption is None
    ):
        print("**2**")
        user_loyalty_transactions = user_loyalty_transactions.filter(
            number_of_transactions__lt=number_of_paid_purchases,
            start_date__gt=timezone.localtime(
                timezone.now()
                - timedelta(days=int(float(loyalty.cycle_duration)))
            ),
        )
        print("**3**", user_loyalty_transactions)
    if (
        loyalty.loyalty_type == COSTA_COFFEE
        and qr_action_code != REDEEMED_ACTION_CODE and (loyalty.transaction_count_for_costa_kwh_consumption or 0) > 0 
    ):
        print("**2**")
        user_loyalty_transactions = user_loyalty_transactions.filter(
            start_date__gt=timezone.localtime(
                timezone.now()
                - timedelta(days=int(float(loyalty.cycle_duration)))
            ),
        )
        
        first_transaction = user_loyalty_transactions.first()

        if first_transaction and first_transaction.transaction_ids:
            previous_transactions = string_to_array_converter(first_transaction.transaction_ids)
            if len(previous_transactions) < loyalty.transaction_count_for_costa_kwh_consumption:
                pass
            else:
                user_loyalty_transactions = user_loyalty_transactions.none()
        else:
            user_loyalty_transactions = user_loyalty_transactions.none()
    transaction_type = PURCHASED
    if user_loyalty_transactions:
        if loyalty.loyalty_type == FREE_LOYALTY:
            create_free_loyalty = LoyaltyTransactions.objects.create(
                loyalty_id=loyalty,
                user_id=user,
                station_id=station,
                transaction_response=array_to_string_converter(
                    [transaction_details]
                ),
                qr_code=qr_code,
                transaction_time=timezone.localtime(timezone.now()),
                created_date=timezone.localtime(timezone.now()),
                transaction_type=REDEEMED,
                updated_date=timezone.localtime(timezone.now()),
                count_of_transactions=1,
            )
            user_loyalty_transactions.update(
                action_code=REDEEMED,
                number_of_transactions=1,
                transaction_ids=array_to_string_converter(
                    [create_free_loyalty.id]
                ),
                end_date=timezone.localtime(timezone.now()),
                updated_date=timezone.localtime(timezone.now()),
            )
            return {
                "status_code": status.HTTP_201_CREATED,
                "status": True,
                "message": "Transaction submitted successfully!",
                "invalid_transactions": invalid_transactions,
            }
        user_prev_loyalty_transaction_id = user_loyalty_transactions.first().id
        print("**4**", user_prev_loyalty_transaction_id)
        # user have previous transactions for the loyalty
        previous_tranactions = string_to_array_converter(
            user_loyalty_transactions.first().transaction_ids
        )
        print("**5**", previous_tranactions)
        number_of_transactions = (
            user_loyalty_transactions.first().number_of_transactions
        )
        print("**6**", number_of_transactions)
        # valid request
        if (
            ((number_of_transactions >= number_of_paid_purchases) and loyalty.transaction_count_for_costa_kwh_consumption is None) or ((len(previous_tranactions) >= (loyalty.transaction_count_for_costa_kwh_consumption or 0)) and (number_of_transactions >= number_of_paid_purchases))
            and qr_action_code
            and qr_action_code == REDEEMED_ACTION_CODE
        ):
            transaction_type = REDEEMED
        if not (
            loyalty.loyalty_type == COSTA_COFFEE
            and transaction_type == PURCHASED
        ):
            create_transaction = LoyaltyTransactions.objects.create(
                loyalty_id=loyalty,
                user_id=user,
                station_id=station,
                transaction_response=array_to_string_converter(
                    [transaction_details]
                ),
                qr_code=qr_code,
                transaction_time=timezone.localtime(timezone.now()),
                created_date=timezone.localtime(timezone.now()),
                transaction_type=transaction_type,
                updated_date=timezone.localtime(timezone.now()),
                count_of_transactions=(
                    number_of_loyalty_transaction
                    if transaction_type == PURCHASED
                    else 1
                ),
            )
        if (
            qr_action_code == REDEEMED_ACTION_CODE
            and loyalty.loyalty_type == COSTA_COFFEE
        ):
            user_loyalty_transactions.update(
                action_code=REDEEMED,
                transaction_ids=array_to_string_converter(
                    previous_tranactions + [f"Reward-{create_transaction.id}"]
                ),
                end_date=timezone.localtime(timezone.now()),
            )
            return {
                "status_code": status.HTTP_201_CREATED,
                "status": True,
                "message": "Transaction submitted successfully!",
                "invalid_transactions": invalid_transactions,
            }
        previous_tranactions.append(
            charging_session_db_id
            if charging_session_db_id
            else create_transaction.id
        )
        previous_tranactions = array_to_string_converter(previous_tranactions)
        if (
            loyalty.loyalty_type != COSTA_COFFEE
            and number_of_transactions >= number_of_paid_purchases
        ):
            user_loyalty_transactions.update(
                number_of_transactions=number_of_paid_purchases
                + (
                    1
                    if loyalty.redeem_type == "Count"
                    else redeemed_product_sales_amount
                ),
                transaction_ids=previous_tranactions,
                end_date=timezone.localtime(timezone.now()),
                action_code=REDEEMED,
            )
            if number_of_transactions - number_of_paid_purchases > 0:
                UserLoyaltyTransactions.objects.create(
                    action_code=PURCHASED,
                    loyalty_id=loyalty,
                    user_id=user,
                    number_of_transactions=number_of_transactions
                    - number_of_paid_purchases,
                    transaction_ids=array_to_string_converter(
                        [f"Ref-{user_prev_loyalty_transaction_id}"]
                    ),
                    expired_on=(
                        datetime.strptime(timestamp, "%Y-%m-%d%H:%M:%S:%f")
                        + timedelta(days=loyalty.expiry_in_days)
                        if number_of_transactions - number_of_paid_purchases
                        >= number_of_paid_purchases
                        else None
                    ),
                    start_date=timezone.localtime(timezone.now()),
                    created_date=timezone.localtime(timezone.now()),
                    updated_date=timezone.localtime(timezone.now()),
                )
        else:
            user_loyalty_transactions.update(
                number_of_transactions=custom_round_function(number_of_transactions, 2)
                + custom_round_function(purchased_quantity_or_amount, 2),
                transaction_ids=previous_tranactions,
                expired_on=(
                    datetime.strptime(timestamp, "%Y-%m-%d%H:%M:%S:%f")
                    + timedelta(days=loyalty.expiry_in_days)
                    if (
                        (number_of_transactions + purchased_quantity_or_amount)
                        >= number_of_paid_purchases
                    )
                    else None
                ),
            )
            if loyalty.loyalty_type == COSTA_COFFEE:
                if (
                    loyalty.number_of_paid_purchases is not None
                    and loyalty.transaction_count_for_costa_kwh_consumption is not None
                ):
                    threshold = (
                        loyalty.number_of_paid_purchases
                        * loyalty.transaction_count_for_costa_kwh_consumption
                    )

                    if (
                        len(previous_tranactions) >= (loyalty.transaction_count_for_costa_kwh_consumption or 0)
                        and (number_of_transactions + purchased_quantity_or_amount) >= threshold
                    ):
                        assign_loyalty_reward_and_send_notification(
                            loyalty, [user.id], REWARD_UNLOCK
                        )                
                    else:
                        return {
                            "status_code": status.HTTP_201_CREATED,
                            "status": True,
                            "message": "Transaction submitted successfully!",
                            "invalid_transactions": invalid_transactions,
                        }

                else:
                    threshold = number_of_paid_purchases
                    if (number_of_transactions + purchased_quantity_or_amount) >= threshold:
                        assign_loyalty_reward_and_send_notification(
                            loyalty, [user.id], REWARD_UNLOCK
                        )

    else:
        # user dont have previous transactions for loyalty
        if not (
            loyalty.loyalty_type == COSTA_COFFEE
            and transaction_type == PURCHASED
        ):
            create_transaction = LoyaltyTransactions.objects.create(
                loyalty_id=loyalty,
                user_id=user,
                station_id=station,
                transaction_response=array_to_string_converter(
                    [transaction_details]
                ),
                transaction_type=PURCHASED,
                qr_code=qr_code,
                transaction_time=timezone.localtime(timezone.now()),
                created_date=timezone.localtime(timezone.now()),
                updated_date=timezone.localtime(timezone.now()),
                count_of_transactions=number_of_loyalty_transaction,
            )
            if not create_transaction:
                print("Transaction create process failed!.", qr_code)
                print("invalid_transactions", invalid_transactions)
                return {
                    "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                    "status": False,
                    "message": "Transaction create process failed!",
                    "invalid_transactions": invalid_transactions,
                }
        UserLoyaltyTransactions.objects.create(
            loyalty_id=loyalty,
            user_id=user,
            number_of_transactions=custom_round_function(purchased_quantity_or_amount, 2),
            transaction_ids=array_to_string_converter(
                [
                    (
                        charging_session_db_id
                        if charging_session_db_id
                        else create_transaction.id
                    )
                ]
            ),
            expired_on=(
                datetime.strptime(timestamp, "%Y-%m-%d%H:%M:%S:%f")
                + timedelta(days=loyalty.expiry_in_days)
                if purchased_quantity_or_amount >= number_of_paid_purchases
                else None
            ),
            start_date=timezone.localtime(timezone.now()),
            action_code=PURCHASED,
            created_date=timezone.localtime(timezone.now()),
            updated_date=timezone.localtime(timezone.now()),
        )
        if loyalty.loyalty_type == COSTA_COFFEE:
            if (
                loyalty.number_of_paid_purchases is not None
                and loyalty.transaction_count_for_costa_kwh_consumption is not None
            ):
                print(f"[DEBUG] number_of_paid_purchases: {loyalty.number_of_paid_purchases}")
                print(f"[DEBUG] transaction_count_for_costa_kwh_consumption: {loyalty.transaction_count_for_costa_kwh_consumption}")
                threshold = (
                    loyalty.number_of_paid_purchases
                    * loyalty.transaction_count_for_costa_kwh_consumption
                )
                print(f"[DEBUG] threshold: {threshold}")
                if (
                    loyalty.transaction_count_for_costa_kwh_consumption == 1
                    and purchased_quantity_or_amount >= threshold
                ):
                    print(f"[DEBUG] purchased_quantity_or_amount >= threshold: {purchased_quantity_or_amount >= threshold}")
                    assign_loyalty_reward_and_send_notification(
                        loyalty, [user.id], REWARD_UNLOCK
                    )
                else:
                    return {
                        "status_code": status.HTTP_201_CREATED,
                        "status": True,
                        "message": "Transaction submitted successfully!",
                        "invalid_transactions": invalid_transactions,
                    }

            else:
                print(f"[DEBUG] number_of_paid_purchases: {number_of_paid_purchases}")
                threshold = number_of_paid_purchases
                if purchased_quantity_or_amount >= threshold:
                    assign_loyalty_reward_and_send_notification(
                        loyalty, [user.id], REWARD_UNLOCK
                    )


    print("Transaction submitted successfully!", qr_code)
    return {
        "status_code": status.HTTP_201_CREATED,
        "status": True,
        "message": "Transaction submitted successfully!",
        "invalid_transactions": invalid_transactions,
    }

def is_session_in_trigger_sites(charging_session, loyalty):
    """ This function checks if the charging session is in the trigger sites of the loyalty program."""

    # print("charging_session.station_id:", getattr(charging_session, "station_id", None))
    # print("loyalty.trigger_sites (raw):", getattr(loyalty, "trigger_sites", None))

    if not loyalty or not hasattr(loyalty, "trigger_sites") or not loyalty.trigger_sites:
        return False
    trigger_sites = loyalty.trigger_sites
    if isinstance(trigger_sites, str):
        try:
            trigger_sites = json.loads(trigger_sites)
            # print(f"Parsed trigger sites: {trigger_sites}")
        except Exception:
            trigger_sites = [s.strip() for s in trigger_sites.split(",") if s.strip()]
            # print(f"Fallback parsed trigger sites: {trigger_sites}")
    else:
        print(f"Trigger sites as list: {trigger_sites}")

    station_id = str(getattr(charging_session, "station_id", ""))
    print("Checking if station_id", station_id, "is in", trigger_sites, station_id in [str(s) for s in trigger_sites])
    return station_id in [str(s) for s in trigger_sites]

def handle_user_costa_loyalty(user, charging_session_db_id,is_ocpi = True):
    """this function handles user conta loyalty"""
    loyalty = Loyalty.objects.filter(
        loyalty_type=COSTA_COFFEE,
        status=ACTIVE,
        deleted=NO,
        valid_from_date__lte=timezone.localtime(timezone.now()),
        valid_to_date__gte=timezone.localtime(timezone.now()),
        visibility__in=[REGISTERED_USERS, ALL_USERS],
    ).first()

    if loyalty:
        print(f"Current Costa Active loyalty : {model_to_dict(loyalty)}")
    energy_consumed = 0
    if is_ocpi:
        charging_session = OCPISessions.objects.filter(
            id=(charging_session_db_id)
        ).annotate(
            is_ocpi=Value(True, output_field=BooleanField()),
            total_cost=ExpressionWrapper(
                F('total_cost_incl') * 100,
                output_field=IntegerField()
            ),
            start_time = F("start_datetime")
        ).first()
        # start_datetime = charging_session.start_time
    else:
        print("charging_session_db_id:", charging_session_db_id)
        charging_session = ChargingSession.objects.filter(
                id=(charging_session_db_id)
            ).annotate(
                is_ocpi=Value(True, output_field=BooleanField())
            ).first()
    print("charging_session:", charging_session)
    if not (charging_session and is_session_in_trigger_sites(charging_session, loyalty)):
        print("Charging session is not in trigger sites, skipping.")
        return
    
    start_datetime = charging_session.start_time
    if start_datetime:
        energy_consumed = float(
            string_to_array_converter(charging_session.charging_data)[0][
                "totalEnergy"
            ]
        )
    if (
        loyalty
        and start_datetime >= loyalty.valid_from_date
        and loyalty.number_of_total_issuances
        and (
            loyalty.number_of_issued_vouchers is None
            or (
                loyalty.number_of_issued_vouchers
                and loyalty.number_of_total_issuances
                > loyalty.number_of_issued_vouchers
            )
        )
    ):
        helper_date = timezone.localtime(
            timezone.now() - timedelta(days=int(float(loyalty.cycle_duration)))
        )
        user_loyalty_transactions = UserLoyaltyTransactions.objects.filter(
            loyalty_id=loyalty,
            user_id=user,
        )
        if loyalty.loyalty_type == COSTA_COFFEE:
            previous_uncooled_cycle = False
            print(f"[DEBUG] loyalty_type: {loyalty.loyalty_type}")

            if (
                loyalty.number_of_paid_purchases is not None
                and loyalty.transaction_count_for_costa_kwh_consumption is not None
            ):
                print(f"[DEBUG] number_of_paid_purchases: {loyalty.number_of_paid_purchases}")
                print(f"[DEBUG] transaction_count_for_costa_kwh_consumption: {loyalty.transaction_count_for_costa_kwh_consumption}")

                threshold = (
                    loyalty.number_of_paid_purchases
                    * loyalty.transaction_count_for_costa_kwh_consumption
                )
                print(f"[DEBUG] threshold: {threshold}")

                if user_loyalty_transactions:
                    previous_tranactions = string_to_array_converter(
                        user_loyalty_transactions.last().transaction_ids
                    )
                    print(f"[DEBUG] previous_tranactions: {previous_tranactions} (len={len(previous_tranactions)})")

                    number_of_transactions = (
                        user_loyalty_transactions.last().number_of_transactions
                    )
                    print(f"[DEBUG] number_of_transactions: {number_of_transactions}")

                    purchased_quantity_or_amount = energy_consumed
                    print(f"[DEBUG] purchased_quantity_or_amount: {purchased_quantity_or_amount}")

                    meets_threshold = (
                        len(previous_tranactions) >= (loyalty.transaction_count_for_costa_kwh_consumption or 0)
                        and (number_of_transactions + purchased_quantity_or_amount) >= threshold
                    )
                    print(f"[DEBUG] meets_threshold: {meets_threshold}")

                    action_codes = user_loyalty_transactions.last().action_code
                    print(f"[DEBUG] action_codes: {action_codes}")

                    if meets_threshold and action_codes == PURCHASED:
                        previous_uncooled_cycle = True 
                        print(f"[DEBUG] Condition met → previous_uncooled_cycle set to True")
                else:
                    previous_uncooled_cycle = False 
                    print(f"[DEBUG] Condition not met → previous_uncooled_cycle remains False")

            print(f"[DEBUG] Final previous_uncooled_cycle: {previous_uncooled_cycle}")

        else:
            previous_uncooled_cycle = user_loyalty_transactions.filter(
                Q(start_date__gt=helper_date)
                | Q(expired_on__gt=timezone.localtime(timezone.now())),
                action_code__in=[REDEEMED, BURNED],
            )
        if loyalty.transaction_count_for_costa_kwh_consumption is not None:
            user_loyalty_transactions = user_loyalty_transactions.filter(
                Q(action_code=PURCHASED),
                Q(start_date__gt=helper_date),
                Q(
                    Q(expired_on__gte=timezone.localtime(timezone.now())) &
                    Q(end_date=None)
                )
            )

            first_transaction = user_loyalty_transactions.first()
            previous_transactions = []

            if first_transaction and first_transaction.transaction_ids:
                previous_transactions = string_to_array_converter(first_transaction.transaction_ids)

            if (
                user_loyalty_transactions
                and len(previous_transactions) <= (loyalty.transaction_count_for_costa_kwh_consumption or 0)
                and charging_session_db_id not in previous_transactions
            ):
                user_loyalty_transactions = False
        else:
            user_loyalty_transactions = user_loyalty_transactions.filter(
                Q(action_code=PURCHASED),
                Q(
                    Q(number_of_transactions__gte=loyalty.number_of_paid_purchases)
                    & Q(start_date__gt=helper_date)
                )
                | Q(
                    Q(expired_on__gte=timezone.localtime(timezone.now()))
                    & Q(end_date=None)
                ),
            )
        if not user_loyalty_transactions and not previous_uncooled_cycle:
            save_user_loyalty_details(
                loyalty,
                user,
                loyalty.number_of_paid_purchases,
                f'{timezone.localtime(timezone.now()).date().strftime("%Y-%m-%d")}{timezone.localtime(timezone.now()).time().strftime("%H:%M:%S:%f")}',
                energy_consumed,
                charging_session_db_id=charging_session_db_id,
            )
