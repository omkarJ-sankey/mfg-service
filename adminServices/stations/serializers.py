from rest_framework import serializers
from sharedServices.constants import ConstantMessage, IS_MFG_KEYS
from sharedServices.model_files.station_models import Stations

class ConnectorSerializer(serializers.Serializer):
    connector_type = serializers.ChoiceField(
        choices=['AC', 'Rapid', 'Ultra-Rapid'],
        required=True,
        help_text="Type of connector"
    )
    connector_id = serializers.CharField(required=True, help_text="Connector ID")
    connector_name = serializers.CharField(required=True, help_text="Connector Name")
    status = serializers.CharField(required=True, help_text="Connector Status")
    plug_type_name = serializers.CharField(required=True, help_text="Plug Type Name")
    maximum_charge_rate = serializers.FloatField(required=True, help_text="Maximum Charge Rate in kWh")
    tariff_amount = serializers.FloatField(required=True, help_text="Tariff Amount")
    tariff_currency = serializers.CharField(required=True, help_text="Currency for Tariff")
    connector_sort_order = serializers.IntegerField(required=True, help_text="Sort Order")
    evse_uid = serializers.CharField(required=True, help_text="OCPI EVSE UID")
    ocpi_connector_id = serializers.CharField(required=True, help_text="OCPI Connector ID")

class ChargePointSerializer(serializers.Serializer):
    charge_point_id = serializers.CharField(required=True, help_text="Charge Point ID")
    charge_point_name = serializers.CharField(required=True, help_text="Charge Point Name")
    status = serializers.CharField(required=True, help_text="Charge Point Status")
    device_id = serializers.CharField(required=True, help_text="Device ID")
    payter_terminal_id = serializers.CharField(required=True, help_text="Payter Terminal ID")
    ampeco_charge_point_id = serializers.CharField(required=False, default="", help_text="Ampeco Charge Point ID")
    ampeco_charge_point_name = serializers.CharField(required=False, default="", help_text="Ampeco Charge Point Name")

    connectors = ConnectorSerializer(
        many=True,
        required=False,
        default=[],
        help_text="List of connectors for this charge point"
    )

class BackOfficeSerializer(serializers.Serializer):
    back_office = serializers.CharField(required=True)
    location_id = serializers.CharField(required=True)

class ServiceSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=True)
    service_name = serializers.CharField(required=True)
    image_path = serializers.CharField(required=True)
    service_type = serializers.CharField(required=True)

class ValetingTerminalSerializer(serializers.Serializer):
    payter_serial_number = serializers.CharField(required=True, help_text="Payter Serial Number")
    valeting_amenities = serializers.CharField(required=True, help_text="Valeting Amenities")
    status = serializers.CharField(required=True, help_text="Terminal Status (Active/Inactive)")

class ValetingMachineSerializer(serializers.Serializer):
    machine_id = serializers.IntegerField(required=True, help_text="Machine ID")
    machine_name = serializers.CharField(required=True, help_text="Machine Name")
    machine_number = serializers.CharField(required=True, help_text="Machine Number")
    status = serializers.CharField(required=True, help_text="Machine Status (Active/Inactive)")

class DayWorkingHoursSerializer(serializers.Serializer):
    full_hours = serializers.BooleanField(required=True, help_text="Is the station open 24 hours for this day?")
    start_time = serializers.CharField(required=False, allow_blank=True, help_text="Start time if not full hours, e.g., 08:00")
    end_time = serializers.CharField(required=False, allow_blank=True, help_text="End time if not full hours, e.g., 18:00")


class WorkingHoursSerializer(serializers.Serializer):
    monday_friday = DayWorkingHoursSerializer(required=True, help_text="Working hours for Monday to Friday")
    saturday = DayWorkingHoursSerializer(required=True, help_text="Working hours for Saturday")
    sunday = DayWorkingHoursSerializer(required=True, help_text="Working hours for Sunday")



class AddStationRequestSerializer(serializers.Serializer):

    station_id = serializers.CharField(required=True, help_text="Enter Station ID")
    station_name = serializers.CharField(required=True, help_text="Enter Station Name")

    address_line1 = serializers.CharField(required=True, help_text="Address Line 1")
    address_line2 = serializers.CharField(required=False, allow_blank=True, help_text="Address Line 2")
    address_line3 = serializers.CharField(required=False, allow_blank=True, help_text="Address Line 3")
    latitude = serializers.FloatField(required=True, help_text="Latitude")
    longitude = serializers.FloatField(required=True, help_text="Longitude")
    town = serializers.CharField(required=True, help_text="Enter Town")
    postal_code = serializers.CharField(required=True, help_text="Enter Postal Code")
    country = serializers.CharField(required=True, help_text="Country")
    working_hours = WorkingHoursSerializer(required=False, help_text="Working hours per day")
    status = serializers.CharField(required=True, help_text="Active/Inactive/Coming Soon")
    brand = serializers.CharField(required=True, help_text="Select Brand")
    owner = serializers.CharField(required=True, help_text="Select Owner")
    email = serializers.EmailField(required=False, allow_blank=True, help_text="Enter Email")
    phone = serializers.CharField(required=False, allow_blank=True, help_text="Enter Phone")
    station_type = serializers.CharField(required=True, help_text="MFG EV / Forecourt")
    payment_terminal = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=[],
        help_text="e.g. ['Payter', 'Receipt Hero']"
    )
    receipt_hero_site_name = serializers.CharField(required=False, allow_blank=True, help_text="Receipt Hero Site Name")
    valeting = serializers.CharField(required=False, default="NO", help_text="Yes/No")
    valeting_terminals = ValetingTerminalSerializer(many=True, required=False, default=[], help_text="List of valeting terminal details")
    valeting_machines = ValetingMachineSerializer(many=True, required=False, default=[], help_text="List of valeting machine details")

    site_id = serializers.CharField(required=False, allow_blank=True, help_text="Driivz Site ID")
    ampeco_site_id = serializers.CharField(required=False, allow_blank=True, help_text="Ampeco Site ID")
    ampeco_site_title = serializers.CharField(required=False, allow_blank=True, help_text="Ampeco Site Title")

    overstay_fee = serializers.FloatField(required=False, default=0, help_text="Enter Overstay Fee")
    parking_details = serializers.CharField(required=False, allow_blank=True, help_text="Enter Parking Details")
    site_title = serializers.CharField(required=False, allow_blank=True, help_text="Enter Site Title")
    operation_region = serializers.CharField(required=False, allow_blank=True)
    region = serializers.CharField(required=False, allow_blank=True)
    regional_manager = serializers.CharField(required=False, allow_blank=True)
    area = serializers.CharField(required=False, allow_blank=True)
    area_regional_manager = serializers.CharField(required=False, allow_blank=True)
    backoffice = BackOfficeSerializer(
        many=True,
        required=False,
        default=[],
        help_text="List of back office objects with back_office & location_id"
    )
    chargepoints = ChargePointSerializer(
        many=True,
        required=False,
        default=[],
        help_text="List of chargepoint objects"
    )
    station_images = serializers.ListField(
        child=serializers.DictField(child=serializers.CharField()),
        required=False,
        default=[],
        help_text="List of image details"
    )
    amenities = ServiceSerializer(
        many=True,
        required=False,
        default=[],
        help_text="List of amenities"
    )

    retails = ServiceSerializer(
        many=True,
        required=False,
        default=[],
        help_text="List of retail stores"
    )

    food_to_go = ServiceSerializer(
        many=True,
        required=False,
        default=[],
        help_text="List of food-to-go stores"
    )
    def validate_station_id(self, value):
        if Stations.objects.filter(station_id=value).exists():
            raise serializers.ValidationError(ConstantMessage.STATION_ALREADY_EXISTS)
        return value

    def validate(self, attrs):
        if attrs.get("station_type") in IS_MFG_KEYS and attrs.get("brand") == "EV Power":
            if not attrs.get("chargepoints"):
                raise serializers.ValidationError(ConstantMessage.NO_CHARGEPOINTS_PROVIDED)
        if "Receipt Hero" in attrs.get("payment_terminal", []):
            if not attrs.get("receipt_hero_site_name"):
                raise serializers.ValidationError("Receipt Hero Site Name is required when using Receipt Hero terminal.")

        if attrs.get("valeting", "NO").upper() == "YES":
            if not attrs.get("valeting_terminals"):
                raise serializers.ValidationError("Valeting terminal details required when valeting is enabled.")
            if not attrs.get("valeting_machines"):
                raise serializers.ValidationError("Valeting machine details required when valeting is enabled.")

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


class DeleteStationRequestSerializer(serializers.Serializer):
    """Serializer for validating station deletion request."""
    station_pk = serializers.CharField(required=True)