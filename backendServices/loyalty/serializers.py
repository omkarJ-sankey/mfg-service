"""Loyalties serializers"""

# Date - 10/01/2022

# File details-
#   Author          - Manish Pawar
#   Description     - This file contains Serializers to make operation
#                       on database, to restrict fields of database.
#   Name            - Loyalty Serializers
#   Modified by     - Manish Pawar
#   Modified date   - 10/01/2022


# imports required for serializers

from datetime import timedelta
from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

# pylint:disable=import-error
from sharedServices.common import string_to_array_converter
from sharedServices.models import (
    Loyalty,
    Stations,
    UserLoyaltyTransactions,
    LoyaltyOccurrences
)
from sharedServices.shared_station_serializer import (
    StationDetailsLogoSerializer,
)
from sharedServices.constants import (
    COUNT_CONST,
    COSTA_COFFEE,
    PURCHASED,
    FREE_LOYALTY,
    GENERIC_OFFERS,
)
from sharedServices.common import custom_round_function

# pylint:enable=import-error
# This serializer returns the detailed info about loyalty.


class LoyaltiesSerializers(serializers.ModelSerializer):
    """loyalty detail serializer"""

    station_details = serializers.SerializerMethodField("get_stations_details")

    def get_stations_details(self, _):
        """get loyalty station details"""
        if self.context["station_id"]:
            station_exists = Stations.objects.filter(
                id=int(self.context["station_id"])
            )
            if station_exists.first():
                serializer = StationDetailsLogoSerializer(
                    station_exists.first(), read_only=True
                )
                return serializer.data
        return None

    # Following code defines the meta data for serializer.
    class Meta:
        """meta data"""

        model = Loyalty
        fields = [
            "offer_details",
            "terms_and_conditions",
            "station_details",
            "qr_refresh_time",
        ]


class LoyaltyDetailsSerializersV4(serializers.ModelSerializer):
    """loyalty detail serializer"""

    image = serializers.SerializerMethodField("get_image")
    is_offer = serializers.SerializerMethodField("get_is_offer_status")
    loyalty_progress = serializers.SerializerMethodField(
        "get_loyalty_progress"
    )
    redeem_available = serializers.SerializerMethodField(
        "get_redeem_available"
    )
    valid_till = serializers.SerializerMethodField("get_valid_till")

    @classmethod
    def get_image(cls, loyalty):
        """get loyalty image"""
        return (loyalty.get_loyalty_image()) if loyalty.image else None

    @classmethod
    def get_is_offer_status(cls, loyalty):
        """get offer status"""
        return loyalty.offer_type == GENERIC_OFFERS

    def get_valid_till(self, loyalty):
        """get validity of loyalty"""
        user_loyalty_transaction = (
            self.context["user_loyalties"].filter(loyalty_id=loyalty).first()
        )
        redeem_available = loyalty.loyalty_type == FREE_LOYALTY or (
            user_loyalty_transaction
            and user_loyalty_transaction.number_of_transactions
            and loyalty.number_of_paid_purchases
            and user_loyalty_transaction.number_of_transactions
            >= loyalty.number_of_paid_purchases
        )
        if loyalty.occurance_status == 'Yes' and loyalty.show_occurrence_offer and not redeem_available:
            loyalty_occurrence = LoyaltyOccurrences.objects.filter(
                loyalty_id=loyalty,
                date__date=timezone.localtime(timezone.now()).date()
            ).first()
            if loyalty_occurrence:
                return (
                    f'Valid until {timezone.localtime(timezone.now()).strftime("%d/%m/%Y")} '+
                    f'{str(loyalty_occurrence.end_time.hour).zfill(2)}:{str(loyalty_occurrence.end_time.minute).zfill(2)}'
                )
        if redeem_available:
            if user_loyalty_transaction and user_loyalty_transaction.expired_on:
                min = timezone.localtime(user_loyalty_transaction.expired_on) if user_loyalty_transaction.expired_on < loyalty.valid_to_date else loyalty.valid_to_date
                return (
                    f'Valid until {min.strftime("%d/%m/%Y")} '+
                    f'{str(min.hour).zfill(2)}:{str(min.minute).zfill(2)}'
                )
        if (
            loyalty.offer_type != GENERIC_OFFERS and
            loyalty.loyalty_type in [COSTA_COFFEE, FREE_LOYALTY]
        ):
            return get_valid_till_date(
                loyalty,
                self.context["user"],
                is_detail_screen=True,
                user_purchased_loyalty_transactions=self.context[
                    "user_loyalties"
                ],
                message_ending='',
                is_v4=True
            )
        return f'Valid until {loyalty.valid_to_date.strftime("%d/%m/%Y %H:%M")}'

    def get_loyalty_progress(self, loyalty):
        """this function returns loyalty purchase progress for user"""
        if loyalty.offer_type == GENERIC_OFFERS:
            return None
        def get_costa_coffee_progress(loyalty, user_loyalty=None):
            """
            Returns purchase progress for COSTA_COFFEE when both 
            number_of_paid_purchases and transaction_count_for_costa_kwh_consumption exist.
            """
            total_required = loyalty.transaction_count_for_costa_kwh_consumption

            if user_loyalty:
                purchases_done = len(string_to_array_converter(user_loyalty.transaction_ids))
            else:
                purchases_done = 0

            purchases_to_go = max(total_required - purchases_done, 0)
            return {
                "purchases_done": custom_round_function(purchases_done*loyalty.number_of_paid_purchases, 2),
                "puchases_to_go": custom_round_function(purchases_to_go*loyalty.number_of_paid_purchases, 2),
            }

        if (
            loyalty.loyalty_type == COSTA_COFFEE
            and loyalty.number_of_paid_purchases is not None
            and loyalty.transaction_count_for_costa_kwh_consumption is not None
        ):
            user_loyalty = None
            if self.context["user_loyalties"]:
                user_loyalty = self.context["user_loyalties"].filter(loyalty_id=loyalty).first()
            return get_costa_coffee_progress(loyalty, user_loyalty)

        purchase_progress = {
            "purchases_done": 0,
            "puchases_to_go": custom_round_function(
                loyalty.number_of_paid_purchases, 2
            ),
        }
        if self.context["user_loyalties"]:
            loyalty_used_by_user = self.context["user_loyalties"].filter(
                loyalty_id=loyalty
            )
            if loyalty.loyalty_type == COSTA_COFFEE:
                loyalty_used_by_user = loyalty_used_by_user.filter(
                    start_date__gt=timezone.localtime(
                        timezone.now()
                        # - timedelta(days=int(float(loyalty.cycle_duration)))
                    ),
                )
            if loyalty_used_by_user.first():
                if loyalty.redeem_type == COUNT_CONST:
                    purchase_progress["purchases_done"] = custom_round_function(
                        loyalty_used_by_user.first().number_of_transactions
                        if (
                            loyalty.number_of_paid_purchases
                            >= loyalty_used_by_user.first().number_of_transactions
                        )
                        else loyalty.number_of_paid_purchases,
                        2
                    )
                    purchase_progress["puchases_to_go"] = custom_round_function(
                        loyalty.number_of_paid_purchases
                        - loyalty_used_by_user.first().number_of_transactions
                        if (
                            loyalty.number_of_paid_purchases
                            >= loyalty_used_by_user.first().number_of_transactions
                        )
                        else 0,
                        2
                    )
                else:
                    purchase_progress["purchases_done"] = (
                        custom_round_function(
                            loyalty_used_by_user.first().number_of_transactions,
                            2,
                        )
                        if loyalty.number_of_paid_purchases
                        >= loyalty_used_by_user.first().number_of_transactions
                        else custom_round_function(
                            loyalty.number_of_paid_purchases, 2
                        )
                    )
                    purchase_progress["puchases_to_go"] = (
                        custom_round_function(
                            loyalty.number_of_paid_purchases
                            - purchase_progress["purchases_done"],
                            2,
                        )
                    )
        return purchase_progress

    def get_redeem_available(self, loyalty):
        """this function returns whether redeem is available
        for loyalty or not"""
        if loyalty.offer_type == GENERIC_OFFERS:
            return None
        user_loyalty_transaction = (
            self.context["user_loyalties"].filter(loyalty_id=loyalty).first()
        )
        if (
            loyalty.loyalty_type == COSTA_COFFEE
            and loyalty.number_of_paid_purchases is not None
            and loyalty.transaction_count_for_costa_kwh_consumption is not None
            and user_loyalty_transaction
            and user_loyalty_transaction.transaction_ids
        ):
            transaction_count = len(string_to_array_converter(user_loyalty_transaction.transaction_ids))
            return transaction_count >= loyalty.transaction_count_for_costa_kwh_consumption
        else:
            return loyalty.loyalty_type == FREE_LOYALTY or (
                user_loyalty_transaction
                and user_loyalty_transaction.number_of_transactions
                and loyalty.number_of_paid_purchases
                and user_loyalty_transaction.number_of_transactions
                >= loyalty.number_of_paid_purchases
            )

    # Following code defines the meta data for serializer.
    class Meta:
        """meta data"""

        model = Loyalty
        fields = [
            "id",
            "offer_details",
            "terms_and_conditions",
            "qr_refresh_time",
            "loyalty_title",
            "loyalty_progress",
            "redeem_available",
            "valid_till",
            "redeem_product_promotional_code",
            "scheme_bar_code",
            "image",
            "is_offer",
            "loyalty_type",
            "steps_to_redeem"
        ]


def get_valid_till_date(
    loyalty,
    user,
    is_detail_screen=False,
    is_station_details_screen=False,
    user_purchased_loyalty_transactions=None,
    message_ending='.',
    is_v4=False
):
    """this function formats the valid till date for loyalties"""
    message = (
        "Valid until "
        if is_detail_screen
        else "" if is_station_details_screen else "*Offer valid till "
    )
    date_format = "%d/%m/%Y" if is_station_details_screen or is_v4 is False else "%d/%m/%Y %H:%M"
    if (
        loyalty.loyalty_type == FREE_LOYALTY
        and user_purchased_loyalty_transactions
    ):
        min_date = timezone.localtime(user_purchased_loyalty_transactions.first().expired_on) if user_purchased_loyalty_transactions.first().expired_on < loyalty.valid_to_date else loyalty.valid_to_date
        return message + (
            (min_date.strftime(date_format) + message_ending
        ))
    active_costa_cycle = UserLoyaltyTransactions.objects.filter(
        Q(
            start_date__gt=timezone.localtime(
                timezone.now()
                # - timedelta(days=int(float(loyalty.cycle_duration)))
            )
        )
        | (
            Q(expired_on__gt=timezone.localtime(timezone.now()))
            & Q(action_code=PURCHASED)
        ),
        loyalty_id=loyalty,
        user_id=user,
    )
    if active_costa_cycle:
        cycle_expiry = active_costa_cycle.first().start_date
        if (
            active_costa_cycle.first().action_code == PURCHASED
            and active_costa_cycle.first().expired_on
        ):
            return message + (
                timezone.localtime(
                    active_costa_cycle.first().expired_on
                ).strftime(date_format) + message_ending
            )
        return message + (
            timezone.localtime(cycle_expiry).strftime(date_format) + message_ending
            if cycle_expiry < loyalty.valid_to_date
            else (loyalty.valid_to_date).strftime(date_format)
        )
    return message + (loyalty.valid_to_date).strftime(date_format) + message_ending


class LoyaltiesListSerializers(serializers.ModelSerializer):
    """loyalty list serializer"""

    image = serializers.SerializerMethodField("get_image")
    valid_till = serializers.SerializerMethodField("get_valid_till")
    loyalty_shops_and_amenities = serializers.SerializerMethodField(
        "get_loyalty_shops_and_amenities"
    )
    loyalty_progress = serializers.SerializerMethodField(
        "get_loyalty_progress"
    )
    redeem_available = serializers.SerializerMethodField(
        "get_redeem_available"
    )
    expiry_date = serializers.SerializerMethodField("get_expiry_date")
    expired_status = serializers.SerializerMethodField("get_expired_status")
    redeem_product_detail = serializers.SerializerMethodField(
        "get_redeem_product_detail"
    )

    @classmethod
    def get_image(cls, loyalty):
        """get loyalty image"""
        return (loyalty.get_loyalty_image()) if loyalty.image else None

    @classmethod
    def get_redeem_product_detail(cls, loyalty):
        """get loyalty redeem product detail"""
        return loyalty.redeem_product

    def get_valid_till(self, loyalty):
        """get validity of loyalty"""
        user_loyalty_transaction = (
            self.context["user_loyalties"].filter(loyalty_id=loyalty).first()
        )
        redeem_available = loyalty.loyalty_type == FREE_LOYALTY or (
            user_loyalty_transaction
            and user_loyalty_transaction.number_of_transactions
            and loyalty.number_of_paid_purchases
            and user_loyalty_transaction.number_of_transactions
            >= loyalty.number_of_paid_purchases
        )
        if loyalty.occurance_status == 'Yes' and loyalty.show_occurrence_offer and not redeem_available:
            loyalty_occurrence = LoyaltyOccurrences.objects.filter(
                loyalty_id=loyalty,
                date__date=timezone.localtime(timezone.now()).date()
            ).first()
            if loyalty_occurrence:
                return (
                    f'Valid until {timezone.localtime(timezone.now()).strftime("%d/%m/%Y")} '+
                    f'{str(loyalty_occurrence.end_time.hour).zfill(2)}:{str(loyalty_occurrence.end_time.minute).zfill(2)}'
                )
        if loyalty.occurance_status == 'No' and redeem_available:
            if user_loyalty_transaction and user_loyalty_transaction.expired_on:
                min = user_loyalty_transaction.expired_on if user_loyalty_transaction.expired_on < loyalty.valid_to_date else loyalty.valid_to_date
                return (
                    f'Valid until {min.strftime("%d/%m/%Y")} '+
                    f'{str(min.hour).zfill(2)}:{str(min.minute).zfill(2)}'
                )
        if loyalty.loyalty_type in [COSTA_COFFEE, FREE_LOYALTY]:
            return get_valid_till_date(
                loyalty,
                self.context["user"],
                is_detail_screen=bool("is_detail_screen" in self.context),
                user_purchased_loyalty_transactions=self.context[
                    "user_loyalties"
                ],
            )
        return f'*Offer valid till {loyalty.valid_to_date.strftime("%d/%m/%Y")}.'

    def get_loyalty_progress(self, loyalty):
        """this function returns loyalty purchase progress for user"""
        purchase_progress = {
            "purchases_done": 0,
            "puchases_to_go": custom_round_function(
                loyalty.number_of_paid_purchases, 2
            ),
        }
        if self.context["user_loyalties"]:
            loyalty_used_by_user = self.context["user_loyalties"].filter(
                loyalty_id=loyalty
            )
            if loyalty.loyalty_type == COSTA_COFFEE:
                loyalty_used_by_user = loyalty_used_by_user.filter(
                    start_date__gt=timezone.localtime(
                        timezone.now()
                        # - timedelta(days=int(float(loyalty.cycle_duration)))
                    ),
                )
            if loyalty_used_by_user.first():
                if loyalty.redeem_type == COUNT_CONST:
                    purchase_progress["purchases_done"] = (
                        loyalty_used_by_user.first().number_of_transactions
                        if (
                            loyalty.number_of_paid_purchases
                            >= loyalty_used_by_user.first().number_of_transactions
                        )
                        else loyalty.number_of_paid_purchases
                    )
                    purchase_progress["puchases_to_go"] = (
                        loyalty.number_of_paid_purchases
                        - loyalty_used_by_user.first().number_of_transactions
                        if (
                            loyalty.number_of_paid_purchases
                            >= loyalty_used_by_user.first().number_of_transactions
                        )
                        else 0
                    )
                else:
                    purchase_progress["purchases_done"] = (
                        custom_round_function(
                            loyalty_used_by_user.first().number_of_transactions,
                            2,
                        )
                        if loyalty.number_of_paid_purchases
                        >= loyalty_used_by_user.first().number_of_transactions
                        else custom_round_function(
                            loyalty.number_of_paid_purchases, 2
                        )
                    )
                    purchase_progress["puchases_to_go"] = (
                        custom_round_function(
                            loyalty.number_of_paid_purchases
                            - purchase_progress["purchases_done"],
                            2,
                        )
                    )
        return purchase_progress

    def get_redeem_available(self, loyalty):
        """this function returns whether redeem is available
        for loyalty or not"""
        user_loyalty_transaction = (
            self.context["user_loyalties"].filter(loyalty_id=loyalty).first()
        )
        if (
            loyalty.loyalty_type == COSTA_COFFEE
            and loyalty.number_of_paid_purchases is not None
            and loyalty.transaction_count_for_costa_kwh_consumption is not None
            and user_loyalty_transaction
            and user_loyalty_transaction.transaction_ids
        ):
            transaction_count = len(string_to_array_converter(user_loyalty_transaction.transaction_ids))
            return transaction_count >= loyalty.transaction_count_for_costa_kwh_consumption
        else:
            return loyalty.loyalty_type == FREE_LOYALTY or (
                user_loyalty_transaction
                and user_loyalty_transaction.number_of_transactions
                and loyalty.number_of_paid_purchases
                and user_loyalty_transaction.number_of_transactions
                >= loyalty.number_of_paid_purchases
            )

    def get_expiry_date(self, loyalty):
        """get expiry date for loyalty reward redemption"""
        user_loyalty_transaction = (
            self.context["user_loyalties"].filter(loyalty_id=loyalty).first()
        )
        return (
            (
                "*Reward expires on "
                + (
                    timezone.localtime(
                        self.context["user_loyalties"]
                        .filter(loyalty_id=loyalty)
                        .first()
                        .expired_on
                    ).strftime("%d/%m/%Y %H:%M")
                ) + '.'
                if user_loyalty_transaction
                and user_loyalty_transaction.expired_on
                else ""
            )
            if loyalty.loyalty_type in [COSTA_COFFEE, FREE_LOYALTY]
            else "*Reward expires on "
            + loyalty.valid_to_date.strftime("%d/%m/%Y %H:%M") + '.'
        )

    def get_expired_status(self, loyalty):
        """get status of loyalty expiration"""
        user_loyalty_transcation = (
            self.context["user_loyalties"].filter(loyalty_id=loyalty).first()
        )
        return bool(
            user_loyalty_transcation
            and user_loyalty_transcation.expired_on
            and user_loyalty_transcation.expired_on
            <= timezone.localtime(timezone.now())
        )

    @classmethod
    def get_loyalty_shops_and_amenities(cls, loyalty):
        """this fuction returns array of shops added for loyalty"""
        return (
            string_to_array_converter(loyalty.shop_ids)
            if loyalty.shop_ids
            else []
        )

    # Following code defines the meta data for serializer.
    class Meta:
        """meta data"""

        model = Loyalty
        fields = [
            "id",
            "valid_till",
            "image",
            "loyalty_title",
            "loyalty_progress",
            "redeem_available",
            "loyalty_shops_and_amenities",
            "expiry_date",
            "expired_status",
            "redeem_product_detail",
            "loyalty_type",
            "loyalty_list_footer_message",
        ]


class LoyaltiesClubsListSerializersV4(serializers.ModelSerializer):
    """loyalty list serializer"""

    image = serializers.SerializerMethodField("get_image")
    is_offer = serializers.SerializerMethodField("get_is_offer_status")
    loyalty_progress = serializers.SerializerMethodField(
        "get_loyalty_progress"
    )
    redeem_available = serializers.SerializerMethodField(
        "get_redeem_available"
    )

    @classmethod
    def get_image(cls, loyalty):
        """get loyalty image"""
        return (loyalty.get_loyalty_image()) if loyalty.image else None

    @classmethod
    def get_is_offer_status(cls, _):
        """get offer status"""
        return False


    def get_loyalty_progress(self, loyalty):
        """this function returns loyalty purchase progress for user"""
        purchase_progress = {
            "purchases_done": 0,
            "puchases_to_go": custom_round_function(
                loyalty.number_of_paid_purchases, 2
            ),
        }
        def get_costa_coffee_progress(loyalty, user_loyalty=None):
            """
            Returns purchase progress for COSTA_COFFEE when both 
            number_of_paid_purchases and transaction_count_for_costa_kwh_consumption exist.
            """
            total_required = loyalty.transaction_count_for_costa_kwh_consumption

            if user_loyalty:
                purchases_done = len(string_to_array_converter(user_loyalty.transaction_ids))
                print(len(string_to_array_converter(user_loyalty.transaction_ids)))
            else:
                purchases_done = 0

            purchases_to_go = max(total_required - purchases_done, 0)
            return {
                "purchases_done": custom_round_function(purchases_done*loyalty.number_of_paid_purchases, 2),
                "puchases_to_go": custom_round_function(purchases_to_go*loyalty.number_of_paid_purchases, 2),
            }

        if (
            loyalty.loyalty_type == COSTA_COFFEE
            and loyalty.number_of_paid_purchases is not None
            and loyalty.transaction_count_for_costa_kwh_consumption is not None
        ):
            user_loyalty = None
            if self.context["user_loyalties"]:
                user_loyalty = self.context["user_loyalties"].filter(loyalty_id=loyalty).first()
            return get_costa_coffee_progress(loyalty, user_loyalty)

        if self.context["user_loyalties"]:
            loyalty_used_by_user = self.context["user_loyalties"].filter(
                loyalty_id=loyalty
            )
            if loyalty.loyalty_type == COSTA_COFFEE:
                loyalty_used_by_user = loyalty_used_by_user.filter(
                    start_date__gt=timezone.localtime(
                        timezone.now()
                        # - timedelta(days=int(float(loyalty.cycle_duration)))
                    ),
                )
            if loyalty_used_by_user.first():
                if loyalty.redeem_type == COUNT_CONST:
                    purchase_progress["purchases_done"] = (
                        loyalty_used_by_user.first().number_of_transactions
                        if (
                            loyalty.number_of_paid_purchases
                            >= loyalty_used_by_user.first().number_of_transactions
                        )
                        else loyalty.number_of_paid_purchases
                    )
                    purchase_progress["puchases_to_go"] = (
                        loyalty.number_of_paid_purchases
                        - loyalty_used_by_user.first().number_of_transactions
                        if (
                            loyalty.number_of_paid_purchases
                            >= loyalty_used_by_user.first().number_of_transactions
                        )
                        else 0
                    )
                else:
                    purchase_progress["purchases_done"] = (
                        custom_round_function(
                            loyalty_used_by_user.first().number_of_transactions,
                            2,
                        )
                        if loyalty.number_of_paid_purchases
                        >= loyalty_used_by_user.first().number_of_transactions
                        else custom_round_function(
                            loyalty.number_of_paid_purchases, 2
                        )
                    )
                    purchase_progress["puchases_to_go"] = (
                        custom_round_function(
                            loyalty.number_of_paid_purchases
                            - purchase_progress["purchases_done"],
                            2,
                        )
                    )
        return purchase_progress

    def get_redeem_available(self, loyalty):
        """this function returns whether redeem is available
        for loyalty or not"""
        user_loyalty_transaction = (
            self.context["user_loyalties"].filter(loyalty_id=loyalty).first()
        )
        if (
            loyalty.loyalty_type == COSTA_COFFEE
            and loyalty.number_of_paid_purchases is not None
            and loyalty.transaction_count_for_costa_kwh_consumption is not None
            and user_loyalty_transaction
            and user_loyalty_transaction.transaction_ids
        ):
            transaction_count = len(string_to_array_converter(user_loyalty_transaction.transaction_ids))
            return transaction_count >= loyalty.transaction_count_for_costa_kwh_consumption
        else:
            return loyalty.loyalty_type == FREE_LOYALTY or (
                user_loyalty_transaction
                and user_loyalty_transaction.number_of_transactions
                and loyalty.number_of_paid_purchases
                and user_loyalty_transaction.number_of_transactions
                >= loyalty.number_of_paid_purchases
            )


    # Following code defines the meta data for serializer.
    class Meta:
        """meta data"""

        model = Loyalty
        fields = [
            "id",
            "image",
            "loyalty_title",
            "loyalty_progress",
            "redeem_available",
            "loyalty_list_footer_message",
            "is_offer",
            "loyalty_type"
        ]


class OffersListSerializersV4(serializers.ModelSerializer):
    """loyalty list serializer"""

    image = serializers.SerializerMethodField("get_image")
    is_offer = serializers.SerializerMethodField("get_is_offer_status")
    is_free_loyalty = serializers.SerializerMethodField("get_free_loyalty_status")
    valid_till = serializers.SerializerMethodField("get_valid_till")

    @classmethod
    def get_image(cls, loyalty):
        """get loyalty image"""
        return (loyalty.get_loyalty_image()) if loyalty.image else None

    @classmethod
    def get_is_offer_status(cls, _):
        """get offer status"""
        return True

    @classmethod
    def get_free_loyalty_status(cls, loyalty):
        """get offer status"""
        return loyalty.loyalty_type == FREE_LOYALTY

    def get_valid_till(self, loyalty):
        """get validity of loyalty"""
        user_loyalty_transaction = (
            self.context["user_loyalties"].filter(loyalty_id=loyalty).first()
        )
        redeem_available = loyalty.loyalty_type == FREE_LOYALTY or (
            user_loyalty_transaction
            and user_loyalty_transaction.number_of_transactions
            and loyalty.number_of_paid_purchases
            and user_loyalty_transaction.number_of_transactions
            >= loyalty.number_of_paid_purchases
        )
        if loyalty.occurance_status == 'Yes' and loyalty.show_occurrence_offer and not redeem_available:
            loyalty_occurrence = LoyaltyOccurrences.objects.filter(
                loyalty_id=loyalty,
                date__date=timezone.localtime(timezone.now()).date()
            ).first()
            if loyalty_occurrence:
                return (
                    f'Valid until {timezone.localtime(timezone.now()).strftime("%d/%m/%Y")} '+
                    f'{str(loyalty_occurrence.end_time.hour).zfill(2)}:{str(loyalty_occurrence.end_time.minute).zfill(2)}'
                )
        if  loyalty.offer_type != GENERIC_OFFERS and loyalty.loyalty_type == FREE_LOYALTY:
            return get_valid_till_date(
                loyalty,
                self.context["user"],
                is_detail_screen=True,
                user_purchased_loyalty_transactions=self.context[
                    "user_loyalties"
                ].filter(loyalty_id=loyalty),
                message_ending='',
                is_v4=True
            )
        return f'Valid until {loyalty.valid_to_date.strftime("%d/%m/%Y %H:%M")}'

    # Following code defines the meta data for serializer.
    class Meta:
        """meta data"""

        model = Loyalty
        fields = [
            "id",
            "valid_till",
            "image",
            "loyalty_title",
            "is_offer",
            "is_free_loyalty"
        ]
