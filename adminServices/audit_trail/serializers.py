from rest_framework import serializers

from sharedServices.constants import ACTION_CHOICES, MODULE_CHOICES, ORDER_CHOICES, REVIEW_STATUS_CHOICES, USER_ROLE_CHOICES
from sharedServices.model_files.audit_models import AuditTrail


class AuditTrailListRequestSerializer(serializers.Serializer):
    user_name = serializers.CharField(required=False)
    user_role = serializers.ChoiceField(
        choices=USER_ROLE_CHOICES, required=False
    )
    action = serializers.ChoiceField(
        choices=ACTION_CHOICES, required=False
    )
    module = serializers.ChoiceField(
        choices=MODULE_CHOICES, required=False
    )
    reviewed = serializers.ChoiceField(
        choices=REVIEW_STATUS_CHOICES, required=False
    )
    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)

    order_by_id = serializers.ChoiceField(
        choices=ORDER_CHOICES,
        required=False,
        allow_null=True,
    )
    order_by_date = serializers.ChoiceField(
        choices=ORDER_CHOICES,
        required=False,
        allow_null=True,
    )

    page = serializers.IntegerField(required=False, default=1)
    page_size = serializers.IntegerField(required=False, default=10)



class AuditTrailListResponseSerializer(serializers.ModelSerializer):
    created_date = serializers.DateTimeField(format="%Y-%m-%dT%H:%M:%SZ")
    class Meta:
        model = AuditTrail
        fields = [
            "id",
            "user_name",
            "user_role",
            "action",
            "module",
            "review_status",
            "created_date",
        ]


class AuditTrailDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)