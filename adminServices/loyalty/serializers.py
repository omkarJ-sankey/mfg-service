import datetime
from rest_framework import serializers

from sharedServices.constants import BAR_CODE_STANDARDS, BAR_CODE_STD, BOOLEAN_CHOICES, CATEGORY_CHOICES, CYCLE_DURATIONS, LOYALTY_TYPES, NO, OFFER_TYPES, REDEEM_CHOICES, REDEEM_TYPES, STATUS_CHOICES, YES
from sharedServices.model_files.loyalty_models import Loyalty

class AddLoyaltyRequestSerializer(serializers.Serializer):
    """Request serializer for creating a new loyalty offer."""

    loyalty_title = serializers.CharField(required=True)
    unique_code = serializers.CharField(required=True)
    start_date = serializers.CharField(required=True)
    end_date = serializers.CharField(required=True)
    occurance_status = serializers.ChoiceField(choices=BOOLEAN_CHOICES, required=False)

    steps_to_redeem = serializers.CharField(required=True)
    category = serializers.ChoiceField(choices=CATEGORY_CHOICES, required=True)
    bar_code_std = serializers.ChoiceField(choices=BAR_CODE_STD, required=True)
    redeem_type = serializers.ChoiceField(choices=REDEEM_CHOICES, required=True)
    loyalty_type = serializers.ChoiceField(choices=LOYALTY_TYPES, required=True)
    cycle_duration = serializers.IntegerField(required=True)
    number_of_paid_purchases = serializers.IntegerField(required=True)
    qr_refresh_time = serializers.IntegerField(required=False, default=0)
    status = serializers.ChoiceField(choices=STATUS_CHOICES, required=True)
    offer_details = serializers.CharField(required=True)
    terms_and_conditions = serializers.CharField(required=True)
    redeem_product_code = serializers.CharField(required=True)
    redeem_product = serializers.CharField(required=True)
    redeem_product_promotional_code = serializers.CharField(required=True)
    expiry_in_days = serializers.IntegerField(required=True)
    loyalty_list_footer_message = serializers.CharField(required=False, allow_blank=True)
    trigger_sites = serializers.ListField(child=serializers.CharField(), required=False)
    transaction_count_for_costa_kwh_consumption = serializers.IntegerField(required=False, allow_null=True)
    detail_site_check = serializers.BooleanField(required=False, default=False)
    is_car_wash = serializers.BooleanField(required=False, default=False)
    visibility = serializers.CharField(required=True)
    display_on_charging_screen = serializers.BooleanField(required=False, default=False)
    offer_type = serializers.ChoiceField(choices=OFFER_TYPES, required=False, allow_blank=True)
    redeem_product_promotion_price = serializers.CharField(required=False, allow_blank=True)
    product = serializers.CharField(required=False, allow_blank=True)

    promotion_image = serializers.CharField(required=False, allow_blank=True)
    reward_image = serializers.CharField(required=False, allow_blank=True)
    shop = serializers.ListField(child=serializers.CharField(), required=False)
    amenities = serializers.ListField(child=serializers.CharField(),required=False)
    loyalty_products = serializers.ListField(child=serializers.DictField(), required=False)
    occurrences = serializers.ListField(child=serializers.DictField(), required=False)
    stations = serializers.ListField(child=serializers.CharField(), required=False)

    def validate(self, attrs):
        """Custom cross-field validation logic."""
        occurance_status = attrs.get("occurance_status")
        occurrences = attrs.get("occurrences")
        loyalty_products = attrs.get("loyalty_products")
        if occurance_status == "Yes":
            if not occurrences or not isinstance(occurrences, list) or len(occurrences) == 0:
                raise serializers.ValidationError({
                    "occurrences": "This field is required when occurance_status is 'Yes'."
                })

            for i, occ in enumerate(occurrences, start=1):
                missing_fields = [f for f in ["date", "start_time", "end_time"] if f not in occ or not occ[f]]
                if missing_fields:
                    raise serializers.ValidationError({
                        "occurrences": f"Occurrence is missing required fields: {', '.join(missing_fields)}."
                    })

        if loyalty_products:
            required_fields = [
                "product_plu",
                "product_bar_code",
                "price",
                "product",
                "status"
            ]
            for i, product in enumerate(loyalty_products, start=1):
                missing = [f for f in required_fields if f not in product or product[f] in [None, ""]]
                if missing:
                    raise serializers.ValidationError({
                        "loyalty_products": f"Product  is missing required fields: {', '.join(missing)}."
                    })

        return attrs



class EditLoyaltyRequestSerializer(serializers.Serializer):
    """
    Serializer to validate loyalty update requests.
    Used for PUT /edit-loyalties/<loyalty_pk>/
    """

    loyalty_pk = serializers.IntegerField(required=True)
    loyalty_title = serializers.CharField(max_length=255, required=True)
    unique_code = serializers.CharField(max_length=100, required=True)
    category = serializers.CharField(max_length=100, required=False, allow_blank=True)
    loyalty_type = serializers.ChoiceField(choices=LOYALTY_TYPES, required=True)
    offer_type = serializers.ChoiceField(choices=OFFER_TYPES, required=False, allow_blank=True)

    start_date = serializers.CharField(required=True)
    end_date = serializers.CharField(required=True)
    cycle_duration = serializers.ChoiceField(choices=CYCLE_DURATIONS, required=False, allow_blank=True)
    number_of_paid_purchases = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    expiry_in_days = serializers.IntegerField(required=False, allow_null=True, min_value=0)

    bar_code_std = serializers.ChoiceField(choices=BAR_CODE_STANDARDS, required=False, allow_blank=True)
    redeem_type = serializers.ChoiceField(choices=REDEEM_TYPES, required=False, allow_blank=True)
    redeem_product_code = serializers.CharField(max_length=100, required=False, allow_blank=True)
    redeem_product = serializers.CharField(max_length=255, required=False, allow_blank=True)
    redeem_product_promotional_code = serializers.CharField(max_length=100, required=False, allow_blank=True)

    promotion_image = serializers.CharField(required=False, allow_blank=True)
    reward_image = serializers.CharField(required=False, allow_blank=True)

    offer_details = serializers.CharField(required=False, allow_blank=True)
    terms_and_conditions = serializers.CharField(required=False, allow_blank=True)
    steps_to_redeem = serializers.CharField(required=False, allow_blank=True)
    loyalty_list_footer_message = serializers.CharField(required=False, allow_blank=True)

    reward_activated_notification_expiry = serializers.IntegerField(required=False, allow_null=True)
    reward_expiration_notification_expiry = serializers.IntegerField(required=False, allow_null=True)
    reward_expiration_notification_before_x_number_of_days = serializers.IntegerField(required=False, allow_null=True)
    reward_expiry_notification_trigger_time = serializers.CharField(required=False, allow_blank=True)

    occurance_status = serializers.ChoiceField(choices=[(YES, "Yes"), (NO, "No")], required=False, allow_blank=True)
    visibility = serializers.ChoiceField(choices=[(YES, "Visible"), (NO, "Hidden")], required=False)
    is_car_wash = serializers.BooleanField(required=False, default=False)
    display_on_charging_screen = serializers.BooleanField(required=False, default=False)
    status = serializers.ChoiceField(choices=STATUS_CHOICES, required=True)

    reward_activated_notification_title = serializers.CharField(required=False, allow_blank=True)
    reward_activated_notification_description = serializers.CharField(required=False, allow_blank=True)
    reward_expiration_notification_title = serializers.CharField(required=False, allow_blank=True)
    reward_expiration_notification_description = serializers.CharField(required=False, allow_blank=True)
    reward_activated_notification_screen = serializers.CharField(required=False, allow_blank=True)
    reward_expiration_notification_screen = serializers.CharField(required=False, allow_blank=True)

    shop = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )
    stations = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )

    loyalty_products = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True
    )

    occurrences = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        allow_empty=True
    )

    number_of_total_issuances = serializers.IntegerField(required=False, allow_null=True)
    trigger_sites = serializers.CharField(required=False, allow_blank=True)
    transaction_count_for_costa_kwh_consumption = serializers.IntegerField(required=False, allow_null=True)
    detail_site_check = serializers.BooleanField(required=False, default=False)

    def validate_start_date(self, value):
        try:
            datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            raise serializers.ValidationError("Invalid start_date format. Expected DD/MM/YYYY.")
        return value

    def validate_end_date(self, value):
        try:
            datetime.strptime(value, "%d/%m/%Y")
        except ValueError:
            raise serializers.ValidationError("Invalid end_date format. Expected DD/MM/YYYY.")
        return value

    def validate(self, data):
        """Cross-field validation."""
        start_date = datetime.strptime(data["start_date"], "%d/%m/%Y")
        end_date = datetime.strptime(data["end_date"], "%d/%m/%Y")

        if start_date >= end_date:
            raise serializers.ValidationError("End date must be greater than start date.")

        # Loyalty code uniqueness check
        loyalty_pk = data.get("loyalty_pk")
        existing = Loyalty.objects.filter(unique_code=data["unique_code"]).exclude(id=loyalty_pk)
        if existing.exists():
            raise serializers.ValidationError("Loyalty with this unique code already exists.")

        # Costa Coffee validation rule
        if data.get("loyalty_type") == "Costa Coffee":
            existing_costa = Loyalty.objects.filter(
                ~Loyalty.objects.filter(id=loyalty_pk),
                loyalty_type="Costa Coffee",
                status="Active",
                deleted="No",
            ).first()
            if existing_costa:
                raise serializers.ValidationError(
                    "Only one active Costa Coffee loyalty can exist at a time."
                )

        return data

class LoyaltyListRequestSerializer(serializers.Serializer):

    page = serializers.IntegerField(required=False, default=1)
    status = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    search = serializers.CharField(required=False, allow_blank=True, default="")
    from_date = serializers.CharField(required=False, allow_blank=True)
    to_date = serializers.CharField(required=False, allow_blank=True)
    order_by_start_date = serializers.CharField(required=False, allow_blank=True)
    order_by_end_date = serializers.CharField(required=False, allow_blank=True)
    export = serializers.CharField(required=False, allow_blank=True)

class LoyaltyListResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loyalty
        fields = [
            "id",
            "loyalty_title",
            "loyalty_type",
            "valid_from_date",
            "valid_to_date",
            "number_of_paid_purchases",
            "qr_refresh_time",
            "bar_code_std",
            "status",
            "category",
            "offer_details",
            "terms_and_conditions",
            "redeem_product_code",
            "redeem_product",
            "cycle_duration",
            "redeem_type",
            "number_of_total_issuances",
            "visibility",
            "is_car_wash",
            "display_on_charging_screen",
        ]


class DeleteLoyalitySerializer(serializers.Serializer):
    loyalty_pk = serializers.IntegerField(required=True)

class ChangeLoyaltyStatusSerializer(serializers.Serializer):
    loyalty_id = serializers.IntegerField(required=True)
    status = serializers.CharField(required=True)

class ViewLoyaltyDetailsSerializer(serializers.Serializer):
    loyalty_pk = serializers.IntegerField(required=True)