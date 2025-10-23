from rest_framework import serializers
from sharedServices.constants import ConstantMessage, IS_MFG_KEYS
from sharedServices.model_files.station_models import Stations

class ChargePointSerializer(serializers.Serializer):
    ampeco_charge_point_id = serializers.CharField(required=False, default="")
    ampeco_charge_point_name = serializers.CharField(required=False, default="")

class BackOfficeSerializer(serializers.Serializer):
    back_office = serializers.CharField(required=True)
    location_id = serializers.CharField(required=True)

class AddStationRequestSerializer(serializers.Serializer):
    station_id = serializers.CharField(required=True)
    station_name = serializers.CharField(required=True)
    station_type = serializers.CharField(required=True)
    brand = serializers.CharField(required=True)
    owner = serializers.CharField(required=True)
    latitude = serializers.FloatField(required=True)
    longitude = serializers.FloatField(required=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    ampeco_site_id = serializers.CharField(required=False, allow_blank=True)
    ampeco_site_title = serializers.CharField(required=False, allow_blank=True)
    images = serializers.ListField(child=serializers.CharField(), required=False, default=[])
    chargepoints = ChargePointSerializer(many=True, required=False, default=[])
    backoffice = BackOfficeSerializer(many=True, required=False, default=[])
    address_line1 = serializers.CharField(required=True)
    address_line2 = serializers.CharField(required=False, allow_blank=True)
    address_line3 = serializers.CharField(required=False, allow_blank=True)
    town = serializers.CharField(required=True)
    postal_code = serializers.CharField(required=True)
    country = serializers.CharField(required=True)
    status = serializers.CharField(required=True)
    overstay_fee = serializers.FloatField(required=False, default=0)
    valeting = serializers.CharField(required=False, default="NO")
    parking_details = serializers.CharField(required=False, allow_blank=True)
    site_id = serializers.CharField(required=False, allow_blank=True)
    site_title = serializers.CharField(required=False, allow_blank=True)
    operation_region = serializers.CharField(required=False, allow_blank=True)
    region = serializers.CharField(required=False, allow_blank=True)
    regional_manager = serializers.CharField(required=False, allow_blank=True)
    area = serializers.CharField(required=False, allow_blank=True)
    area_regional_manager = serializers.CharField(required=False, allow_blank=True)
    receipt_hero_site_name = serializers.CharField(required=False, allow_blank=True)
    valeting_site_id = serializers.CharField(required=False, allow_blank=True)
    payment_terminal = serializers.ListField(child=serializers.CharField(), required=False, default=[])

    # Validation: station ID unique
    def validate_station_id(self, value):
        if Stations.objects.filter(station_id=value).exists():
            raise serializers.ValidationError(ConstantMessage.STATION_ALREADY_EXISTS)
        return value

    # Validation: EV Power must have chargepoints
    def validate(self, attrs):
        if attrs.get("station_type") in IS_MFG_KEYS and attrs.get("brand") == "EV Power":
            if not attrs.get("chargepoints"):
                raise serializers.ValidationError(ConstantMessage.NO_CHARGEPOINTS_PROVIDED)
        return attrs


class UploadSheetRequestSerializer(serializers.Serializer):
    file = serializers.FileField(required=True)


from rest_framework import serializers


class StationListRequestSerializer(serializers.Serializer):
    """Request serializer for station list API."""

    page = serializers.IntegerField(required=False, default=1)
    brand = serializers.CharField(required=False, allow_blank=True)
    station_type = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(required=False, allow_blank=True)
    search = serializers.CharField(required=False, allow_blank=True)
    order_by_station = serializers.CharField(required=False, allow_blank=True)


class StationListResponseSerializer(serializers.Serializer):
    """Response serializer for station list."""
    station_id = serializers.CharField()
    station_name = serializers.CharField()
    brand = serializers.CharField()
    station_type = serializers.CharField()
    status = serializers.CharField()
    address = serializers.SerializerMethodField()

    def get_address(self, obj):
        """Get full formatted address using model helper."""
        return obj.get_full_address() if hasattr(obj, "get_full_address") else ""
    


class ViewStationRequestSerializer(serializers.Serializer):
    """Request serializer for viewing a station."""
    station_pk = serializers.CharField(required=True)


class ViewStationResponseSerializer(serializers.Serializer):
    """Response serializer for full station details."""
    station_id = serializers.CharField()
    station_name = serializers.CharField()
    brand = serializers.CharField()
    station_type = serializers.CharField()
    status = serializers.CharField()
    address = serializers.SerializerMethodField()
    amenities = serializers.ListField(child=serializers.CharField(), required=False)
    food_services = serializers.ListField(child=serializers.CharField(), required=False)
    retails = serializers.ListField(child=serializers.CharField(), required=False)
    images = serializers.ListField(child=serializers.CharField(), required=False)
    payment_terminals = serializers.ListField(child=serializers.CharField(), required=False)
    valeting_machines = serializers.ListField(required=False)
    promotions = serializers.ListField(required=False)
    tariffs = serializers.DictField(required=False)
    back_offices = serializers.DictField(required=False)

    def get_address(self, obj):
        """Combine station address fields into one string."""
        return obj.get_full_address() if hasattr(obj, "get_full_address") else ""


class StationSerializer(serializers.Serializer):
    station_id = serializers.CharField(max_length=100)
    station_name = serializers.CharField(max_length=255)
    station_address1 = serializers.CharField(max_length=255, allow_blank=True)
    station_address2 = serializers.CharField(max_length=255, allow_blank=True)
    station_address3 = serializers.CharField(max_length=255, allow_blank=True)
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    town = serializers.CharField(max_length=100, allow_blank=True)
    postal_code = serializers.CharField(max_length=20, allow_blank=True)
    country = serializers.CharField(max_length=50)
    status = serializers.CharField(max_length=50)
    brand = serializers.CharField(max_length=100, allow_blank=True)
    owner = serializers.CharField(max_length=100, allow_blank=True)
    email = serializers.EmailField(allow_blank=True)
    phone = serializers.CharField(max_length=50, allow_blank=True)
    station_type = serializers.CharField(max_length=50)
    payment_terminals = serializers.ListField(child=serializers.CharField(), required=False)
    valeting = serializers.CharField(max_length=10)
    site_id = serializers.CharField(max_length=100, allow_blank=True)
    receipt_hero_site_name = serializers.CharField(max_length=255, allow_blank=True)
    ampeco_site_id = serializers.CharField(max_length=100, allow_blank=True)
    ampeco_site_title = serializers.CharField(max_length=255, allow_blank=True)
    overstay_fee = serializers.FloatField(required=False)
    parking_details = serializers.CharField(max_length=255, allow_blank=True)
    operation_region = serializers.CharField(max_length=100, allow_blank=True)
    region = serializers.CharField(max_length=100, allow_blank=True)
    area = serializers.FloatField(required=False)
    regional_manager = serializers.CharField(max_length=100, allow_blank=True)
    area_regional_manager = serializers.CharField(max_length=100, allow_blank=True)


from rest_framework import serializers

class UpdateStationRequestSerializer(serializers.Serializer):
    """Validate request data for updating a station."""

    station_pk = serializers.CharField(required=True)

    station_name = serializers.CharField(required=False, allow_blank=True)
    station_address1 = serializers.CharField(required=False, allow_blank=True)
    station_address2 = serializers.CharField(required=False, allow_blank=True)
    station_address3 = serializers.CharField(required=False, allow_blank=True)
    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)
    country = serializers.CharField(required=False)
    town = serializers.CharField(required=False)
    postal_code = serializers.CharField(required=False)
    status = serializers.CharField(required=False)
    brand = serializers.CharField(required=False)
    owner = serializers.CharField(required=False)
    email = serializers.EmailField(required=False, allow_blank=True)
    phone = serializers.CharField(required=False, allow_blank=True)
    station_type = serializers.CharField(required=False)
    payment_terminals = serializers.ListField(
        child=serializers.CharField(), required=False, allow_empty=True
    )
    valeting = serializers.CharField(required=False)
    site_id = serializers.CharField(required=False, allow_blank=True)
    receipt_hero_site_name = serializers.CharField(required=False, allow_blank=True)
    ampeco_site_id = serializers.CharField(required=False, allow_blank=True)
    ampeco_site_title = serializers.CharField(required=False, allow_blank=True)
    overstay_fee = serializers.FloatField(required=False)
    parking_details = serializers.CharField(required=False, allow_blank=True)

    amenities = serializers.ListField(
        child=serializers.DictField(), required=False
    )
    retail = serializers.ListField(
        child=serializers.DictField(), required=False
    )
    food = serializers.ListField(
        child=serializers.DictField(), required=False
    )
    chargepoints = serializers.ListField(
        child=serializers.DictField(), required=False
    )
    working_hours = serializers.ListField(
        child=serializers.DictField(), required=False
    )
    valeting_terminals = serializers.ListField(
        child=serializers.DictField(), required=False
    )
    valeting_machines = serializers.ListField(
        child=serializers.DictField(), required=False
    )

