"""audit trail common functions"""
import json
from io import StringIO

from django.utils import timezone
from django.db.models import Q, OuterRef, Subquery, F, Value

from sharedServices.model_files.valeting_models import ValetingMachine
import traceback
# pylint:disable=import-error
from .model_files.audit_models import AuditTrail
from .model_files.station_models import (
    Stations,
    StationWorkingHours,
    ChargePoint,
    StationConnector,
    StationServices,
    StationImages,
    ValetingTerminals,
)
from .model_files.charging_session_models import (
    ChargingSession,
)
from .model_files.app_user_models import Profile
from .model_files.promotions_models import Promotions, PromotionsAvailableOn
from .model_files.loyalty_models import (
    Loyalty,
    LoyaltyAvailableOn,
    LoyaltyProducts,
    LoyaltyOccurrences
)
from .model_files.config_models import (
    ServiceConfiguration,
    ConnectorConfiguration,
    MapMarkerConfigurations,
    BaseConfigurations,
)
from .model_files.notifications_module_models import (
    EmailNotifications,
    PushNotifications,
)
from .model_files.transaction_models import TransactionsTracker
from .model_files.admin_user_models import AdminUser, LoginRecords
from .model_files.review_models import Reviews
from .common import array_to_string_converter, string_to_array_converter
from .constants import (
    NO,
    YES,
    ON_CONST,
    BLANK_SPACE_CONST,
    SITES_CONST,
    PROMOTIONS_CONST,
    LOYALTY_CONST,
    REVIEW_CONST,
    USER_MANAGEMENT_CONST,
    CONNECTORS_CONST,
    SERVICES_CONST,
    BASE_CONFIG_CONST,
    MAP_MARKERS_CONST,
    AZURE_BLOB_STORAGE_URL,
    EWALLET,
    PAYMENT_CONST,
    NOTIFICATION_CONST,
    PUSH_NOTIFICATION_CONST,
    HOLD_PAYMENT_CONST,
    THREE_DS_CONFIG_CONST,
    LOYALTY_TYPES,
    THREE_DS_FOR_ALL_CONFIG_CONST,
    OCPI_CONFIG_CONST
)
from sharedServices.model_files.ocpi_credentials_models import OCPICredentials,OCPIModuleDetails
from sharedServices.model_files.ocpi_locations_models import OCPILocation,OCPIConnector,OCPIEVSE
from sharedServices.ocpi_common_functions import get_location_backoffice

def add_audit_data(*args):
    """this function is used to add audit data"""
    (
        user_data,
        module_id,
        data_db_id,
        action,
        module,
        new_data,
        old_data,
    ) = args
    audit_created = AuditTrail.objects.create(
        user_id=user_data.get("id"),
        user_name = user_data.get("full_name"),
        user_role = user_data.get("role_id", {}).get("role_name"),
        action=action,
        module=module,
        module_id=module_id,
        data_db_id=data_db_id,
        new_data=new_data,
        previous_data=old_data,
        created_date=timezone.now(),
    )
    return audit_created.id


def add_references_to_audit_data(audit_data_ids, reference_id):
    """this function adds references to audit data"""
    AuditTrail.objects.filter(id__in=audit_data_ids).update(
        changes_reference_id=reference_id
    )


# This function categorizes services in different categories.


def date_formatter_for_json(offer_date, is_offer_date=True):
    """this function formats date"""
    if offer_date is not None:
        return (
            offer_date.strftime("%d/%m/%Y %H:%M")
            if is_offer_date
            else (timezone.localtime(offer_date).strftime("%d/%m/%Y %H:%M"))
        )
    return "-"


def services_categorization_function():
    """service categorization function"""
    # Database call to fetch all services from configurations.
    services = ServiceConfiguration.objects.all().values(
        "id", "service_name", "image_path", "service_type"
    )

    for service in services:
        service[
            "image_path"
        ] = f"{AZURE_BLOB_STORAGE_URL}{service['image_path']}"

    # Dividing services according to their types.
    filter_retail = filter(
        lambda service: service["service_type"] == "Retail", services
    )
    retail_data = list(filter_retail)

    filter_food_to_go_data = filter(
        lambda service: service["service_type"] == "Food To Go", services
    )
    food_to_go_data = list(filter_food_to_go_data)

    filter_amenity_data = filter(
        lambda service: service["service_type"] == "Amenity", services
    )
    amenity_data = list(filter_amenity_data)

    return [retail_data, food_to_go_data, amenity_data]


def get_valeting_amenities_names(valeting_amenities_ids, station_amenities):
    valeting_amenities_names = ""
    for count, valeting_amenities_id in enumerate(valeting_amenities_ids):
        for station_amenity in station_amenities:
            if station_amenity["id"] == valeting_amenities_id:
                valeting_amenities_names += (
                    station_amenity["service_name"]
                    if count == len(valeting_amenities_ids) - 1
                    else f"""{station_amenity["service_name"]},"""
                )
    return valeting_amenities_names


def format_data_for_stations(station_id):
    """this function formates data for station"""
    station_details_object = {}
    station_basic_data = (
        Stations.objects.filter(id=station_id).values().first()
    )
    if station_basic_data is None:
        return None
    
    location = OCPILocation.objects.filter(station_mapping_id = station_basic_data["id"] ).first()
    back_office = get_location_backoffice(location)
    station_details_object = {
        "Station ID": station_basic_data["station_id"],
        "Station Name": station_basic_data["station_name"],
        "Station Address 1": station_basic_data["station_address1"],
        "Station Address 2": station_basic_data["station_address2"],
        "Station Address 3": station_basic_data["station_address3"],
        "Town": station_basic_data["town"],
        "Post Code": station_basic_data["post_code"],
        "Country": station_basic_data["country"],
        "Brand": station_basic_data["brand"],
        "Owner": station_basic_data["owner"],
        "Latitude": station_basic_data["latitude"],
        "Longitude": station_basic_data["longitude"],
        "Email": station_basic_data["email"],
        "Phone": station_basic_data["phone"],
        "Status": station_basic_data["status"],
        "Station Type": station_basic_data["station_type"],
        "Site Title": station_basic_data["site_title"],
        "Operation Region": station_basic_data["operation_region"],
        "Region": station_basic_data["region"],
        "Regional Manager": station_basic_data["regional_manager"],
        "Area": station_basic_data["area"],
        "Area Retail Manager": station_basic_data["area_regional_manager"],
        "Overstay Fee": station_basic_data["overstay_fee"],
        "Valeting": station_basic_data["valeting"],
        "Payment Temrinal":station_basic_data["payment_terminal"],
        "RH Site Name":station_basic_data["receipt_hero_site_name"],
        "Valeting Site ID":station_basic_data["valeting_site_id"] if station_basic_data["valeting_site_id"] else None,
        "Ampeco Site ID":station_basic_data["ampeco_site_id"],
        "Ampeco Site Title":station_basic_data["ampeco_site_title"],
        "Back Office": back_office,
        "Location ID":location.location_id if location is not None else None,
        "Parking Details": station_basic_data["parking_details"]
    }

    working_hours_details = (
        StationWorkingHours.objects.filter(station_id_id=station_id)
        .values("monday_friday", "saturday", "sunday")
        .first()
    )

    if working_hours_details:
        station_details_object["working_hours"] = {
            "Monday - Friday": working_hours_details["monday_friday"],
            "Saturday": working_hours_details["saturday"],
            "Sunday": working_hours_details["sunday"],
        }
    devices_data = []

    charge_points = ChargePoint.objects.filter(
        station_id_id=station_id, deleted=NO
    ).values()

    evses = OCPIEVSE.objects.filter(chargepoint_mapping_id__in = charge_points )

    connector_id_query = Subquery(OCPIConnector.objects.filter(
        connector_mapping_id=OuterRef('id')
        ).values('connector_id'))
    
    evse_id_query = Subquery(OCPIConnector.objects.filter(
        connector_mapping_id=OuterRef('id')
        ).values('evse_id__uid'))
    

    for charge_point in charge_points:
        connectors = [
            {
                "id": station_connector["id"],
                "Connector Type": station_connector["connector_type"],
                "Connector ID": station_connector["connector_id"],
                "Connector Name": station_connector["connector_name"],
                "Status": station_connector["status"],
                "Plug Type Name": station_connector["plug_type_name"],
                "Maximum Charge Rate": station_connector["max_charge_rate"],
                "Tariff Amount": station_connector["tariff_amount"],
                "Tariff Currency": station_connector["tariff_currency"],
                "Evse UID":station_connector["evse_uid"],
                "Ocpi Connector ID":station_connector["ocpi_connector_id"],
            }
            for station_connector in StationConnector.objects.filter(
                station_id_id=station_id,
                charge_point_id_id=charge_point["id"],
                deleted=NO,
            ).values().annotate(
                evse_uid = Subquery(evse_id_query),
                ocpi_connector_id =  Subquery(connector_id_query)
            )
        ]
        devices_data.append(
            {
                "id": charge_point["id"],
                "Charge Point ID": charge_point["charger_point_id"],
                "Charge Point Name": charge_point["charger_point_name"],
                "Status": charge_point["charger_point_status"],
                # "Back-office": charge_point["back_office"],
                "Device id": charge_point["device_id"],
                "Payter terminal id": charge_point["payter_terminal_id"],
                "Worldline terminal id": charge_point["worldline_terminal_id"],
                "connectors": connectors,
            }
        )
    station_details_object["charge_points"] = devices_data

    station_details_object["station_images"] = [
        {"id": image.id, "image_path": image.get_image()}
        for image in StationImages.objects.filter(
            station_id=station_id, deleted=NO
        )
    ]
    # Fetching services from a function which is common for this sites module
    (
        retails_services,
        food_to_go_services,
        amenities_services,
    ) = services_categorization_function()
    # Fetching amenities available on station.
    amenities_ids = [
        service.service_id.id
        for service in StationServices.objects.filter(
            station_id=station_id, service_name="Amenity", deleted=NO
        )
        if service.service_id
    ]
    # Fetching retail shops available on station.
    retail_ids = [
        service.service_id.id
        for service in StationServices.objects.filter(
            station_id=station_id, service_name="Retail", deleted=NO
        )
        if service.service_id
    ]
    # Fetching food services available on station.
    foods_ids = [
        service.service_id.id
        for service in StationServices.objects.filter(
            station_id=station_id, service_name="Food To Go", deleted=NO
        )
        if service.service_id
    ]
    # Matching station services with configuration services
    # to filter station services.
    station_details_object["amenities"] = [
        service
        for service in amenities_services
        if service["id"] in amenities_ids
    ]
    station_details_object["retails"] = [
        service for service in retails_services if service["id"] in retail_ids
    ]
    station_details_object["food_to_go"] = [
        service
        for service in food_to_go_services
        if service["id"] in foods_ids
    ]
    valeting_terminals = ValetingTerminals.objects.filter(
        station_id=station_id
    )
    valeting_machines = ValetingMachine.objects.filter(
        station_id=station_id
    )
    station_details_object["valating_terminals_data"] = [
        {
            "id": valating_terminal.id,
            "payter_serial_number": valating_terminal.payter_serial_number,
            "amenities": get_valeting_amenities_names(
                string_to_array_converter(valating_terminal.amenities),
                station_details_object["amenities"],
            ),
            "status": valating_terminal.status,
            "deleted": valating_terminal.deleted,
        }
        for valating_terminal in valeting_terminals
    ]
    station_details_object["valeting_machines_data"] = [
        {
            "machine_id": valeting_machine.machine_id,
            "machine_name": valeting_machine.machine_name,
            "machine_number": valeting_machine.machine_number,
            "is_active": valeting_machine.is_active
        }
        for valeting_machine in valeting_machines
    ]
    return array_to_string_converter([station_details_object])


def return_station_objects(station):
    """this function returns station object"""
    return {
        "id": station.id,
        "Operation Region": station.operation_region,
        "Region": station.region,
        "Area": station.area,
        "Station ID": station.station_id,
        "Station Name": station.station_name,
    }


def format_data_for_promotions(promotion_id):
    """this function formates data for promotion"""
    promotion_details_object = {}
    promotion_basic_data = (
        Promotions.objects.filter(id=promotion_id).values().first()
    )
    if promotion_basic_data is None:
        return None

    promotion_stations = PromotionsAvailableOn.objects.filter(
        promotion_id_id=promotion_id, deleted=NO
    )

    shops_from_configurations = ServiceConfiguration.objects.filter(
        ~Q(service_type="Amenity")
    ).values("id", "service_name", "image_path", "service_type")
    shops = []
    input_output = StringIO(promotion_basic_data["shop_ids"])
    shop_ids = (
        json.load(input_output) if promotion_basic_data["shop_ids"] else []
    )
    for shop in shops_from_configurations:
        if (
            str(shop["service_name"]) in shop_ids
            or str(shop["id"]) in shop_ids
        ):
            shops.append(shop["service_name"])
    promotion_details_object = {
        "Unique Code / Barcode": promotion_basic_data["unique_code"],
        "Retail Barcode": promotion_basic_data["retail_barcode"],
        "Product": promotion_basic_data["product"],
        "Promotions Title": promotion_basic_data["promotion_title"],
        "M Code": promotion_basic_data["m_code"],
        "Status": promotion_basic_data["status"],
        "Available For": promotion_basic_data["available_for"],
        "Start Date": date_formatter_for_json(
            promotion_basic_data["start_date"]
        ),
        "End Date": date_formatter_for_json(promotion_basic_data["end_date"]),
        "Price": promotion_basic_data["price"],
        "Quantity": promotion_basic_data["quantity"],
        "Londis Code": promotion_basic_data["londis_code"],
        "Budgen Code": promotion_basic_data["budgen_code"],
        "Offer Details": promotion_basic_data["offer_details"],
        "Terms And Conditions": promotion_basic_data["terms_and_conditions"],
        "Shop": ", ".join(shops),
        "Operation Regions": ", ".join(
            promotion_stations.values_list(
                "operation_region", flat=True
            ).distinct()
        ),
        "Regions": ", ".join(
            promotion_stations.values_list("region", flat=True).distinct()
        ),
        "Areas": ", ".join(
            promotion_stations.values_list("area", flat=True).distinct()
        ),
        "Stations": ", ".join(
            promotion_stations.values_list(
                "station_id__station_id", flat=True
            ).distinct()
        ),
        "Image": (
            (AZURE_BLOB_STORAGE_URL + promotion_basic_data["image"])
            if promotion_basic_data["image"]
            else ""
        ),
    }
    return array_to_string_converter([promotion_details_object])


def format_data_for_loyalties(loyalty_id):
    """this function formats data for loyalty"""
    loyalty_details_object = {}
    loyalty_basic_data = Loyalty.objects.filter(loyalty_id=loyalty_id).values().first()
    if loyalty_basic_data is None:
        return None
    loyalty_stations = LoyaltyAvailableOn.objects.filter(
        loyalty_id_id=loyalty_id, deleted=NO
    )

    shops_from_configurations = ServiceConfiguration.objects.filter(
        ~Q(service_type="Amenity")
    ).values("service_id", "service_name", "image_path", "service_type")
    shops = []
    input_output = StringIO(loyalty_basic_data["shop_ids"])
    shop_ids = (
        json.load(input_output) if loyalty_basic_data["shop_ids"] else []
    )
    for shop in shops_from_configurations:
        if (
            str(shop["service_name"]) in shop_ids
            or str(shop["service_id"]) in shop_ids
        ):
            shops.append(shop["service_name"])
    loyalty_details_object = {
        "Category": loyalty_basic_data["category"],
        "Loyalty Title": loyalty_basic_data["loyalty_title"],
        "Loyalty Type": loyalty_basic_data["loyalty_type"],
        "Offer Type": loyalty_basic_data["offer_type"],
        "Occurance Status": loyalty_basic_data["occurance_status"],
        "Status": loyalty_basic_data["status"],
        "Start Date": date_formatter_for_json(
            loyalty_basic_data["valid_from_date"]
        ),
        "End Date": date_formatter_for_json(
            loyalty_basic_data["valid_to_date"]
        ),
        "Number Of Purchases": loyalty_basic_data["number_of_paid_purchases"],
        "Number Of Issuances": loyalty_basic_data["number_of_total_issuances"],
        "Bar Code Std": loyalty_basic_data["bar_code_std"],
        "Product Code": loyalty_basic_data["redeem_product_code"],
        "Product": loyalty_basic_data["redeem_product"],
        "Promotional QR code": loyalty_basic_data[
            "redeem_product_promotional_code"
        ],
        "QR Code Expiry (In mins.)": loyalty_basic_data["qr_refresh_time"],
        "User Cycle Duration (In Days)": loyalty_basic_data["cycle_duration"],
        "Redeem Type": loyalty_basic_data["redeem_type"],
        "Loyalty Unique Code": loyalty_basic_data["unique_code"],
        "Offer Details": loyalty_basic_data["offer_details"],
        "Terms And Conditions": loyalty_basic_data["terms_and_conditions"],
        "Steps to Redeem": loyalty_basic_data["steps_to_redeem"],
        "Cooldown / Expiry (In Days)": loyalty_basic_data["expiry_in_days"],
        "Shop": ", ".join(shops),
        "Operation Regions": ", ".join(
            loyalty_stations.values_list(
                "operation_region", flat=True
            ).distinct()
        ),
        "Regions": ", ".join(
            loyalty_stations.values_list("region", flat=True).distinct()
        ),
        "Areas": ", ".join(
            loyalty_stations.values_list("area", flat=True).distinct()
        ),
        "Stations": ", ".join(
            loyalty_stations.values_list(
                "station_id__station_id", flat=True
            ).distinct()
        ),
        "Image": (
            (AZURE_BLOB_STORAGE_URL + loyalty_basic_data["image"])
            if loyalty_basic_data["image"]
            else ""
        ),
        "Reward Image": (
            (AZURE_BLOB_STORAGE_URL + loyalty_basic_data["reward_image"])
            if loyalty_basic_data["reward_image"]
            else ""
        )
    }
    # if loyalty_basic_data["loyalty_type"] in LOYALTY_TYPES:
    #     reward_activated_notification_data = PushNotifications.objects.filter(
    #         id=loyalty_basic_data["reward_unlocked_notification_id_id"]
    #     ).values().first()
    #     if reward_activated_notification_data:
    #         loyalty_details_object["reward_activated_notification_content"] = {
    #             "Title": reward_activated_notification_data["subject"],
    #             "Description": reward_activated_notification_data["description"],
    #             "Expiry": loyalty_basic_data["reward_activated_notification_expiry"],
    #             "Screens": reward_activated_notification_data["screens"],
    #             "Type of notification": "In-App Notification" if (
    #                 reward_activated_notification_data["inapp_notification"] == 'true'
    #             ) else "Push Notification",
    #             "Image": (
    #                 (AZURE_BLOB_STORAGE_URL + reward_activated_notification_data["image"])
    #                 if reward_activated_notification_data["image"]
    #                 else ""
    #             )
    #         }

    #     reward_expiration_notification_data = PushNotifications.objects.filter(
    #         id=loyalty_basic_data["reward_expiration_notification_id_id"]
    #     ).values().first()
    #     if reward_expiration_notification_data:
    #         loyalty_details_object["reward_expiration_notification_content"] = {
    #             "Title": reward_expiration_notification_data["subject"],
    #             "Description": reward_expiration_notification_data["description"],
    #             "Expiry": loyalty_basic_data["reward_expiration_notification_expiry"],
    #             "Expire before X days": loyalty_basic_data["expire_reward_before_x_number_of_days"],
    #             "Notification trigger time": loyalty_basic_data["reward_expiry_notification_trigger_time"],
    #             "Screens": reward_expiration_notification_data["screens"],
    #             "Type of notification": "In-App Notification" if (
    #                 reward_expiration_notification_data["inapp_notification"] == 'true'
    #             ) else "Push Notification",
    #             "Image": (
    #                 (AZURE_BLOB_STORAGE_URL + reward_expiration_notification_data["image"])
    #                 if reward_expiration_notification_data["image"]
    #                 else ""
    #             )
    #         }
    loyalty_details_object["loyalty_products"] = [
        {
            "id": product.id,
            "Product PLU": product.product_plu,
            "Product code": product.product_bar_code,
            "Product": product.desc,
            "Price": product.price,
            "Price After Promotion": product.redeem_product_promotion_price,
            "Status": product.status,
        }
        for product in LoyaltyProducts.objects.filter(
            loyalty_id=loyalty_id, deleted=NO
        )
    ]
    loyalty_details_object["loyalty_occurrences"] = [
        {
            "id": occurrence.id,
            "Start Time": f"{str(occurrence.start_time.hour).zfill(2)}:{str(occurrence.start_time.minute).zfill(2)}",
            "End Time": f"{str(occurrence.end_time.hour).zfill(2)}:{str(occurrence.end_time.minute).zfill(2)}",
            "Date": date_formatter_for_json(occurrence.date),
        }
        for occurrence in LoyaltyOccurrences.objects.filter(
            loyalty_id=loyalty_id,
            deleted=NO
        )
    ]
    return array_to_string_converter([loyalty_details_object])


def review_data_formatter(review_id):
    """this function formats review data"""
    review_data = Reviews.objects.filter(id=review_id).first()
    if review_data is None:
        return review_data
    return array_to_string_converter(
        [
            {
                "Review ID": review_data.id,
                "Station ID": review_data.station_id.station_id,
                "Station Name": review_data.station_id.station_name,
                "Review": review_data.review,
                "Status": review_data.status,
                "Flagged": review_data.flag,
                "Date": date_formatter_for_json(review_data.post_date, False),
            }
        ]
    )


def user_management_data_formatter(user_id):
    """this function formats review data"""
    user_data = AdminUser.objects.filter(id=user_id).first()
    if user_data is None:
        return user_data
    return array_to_string_converter(
        [
            {
                "id": user_data.id,
                "Role": user_data.role_id.role_name,
                "First Name": user_data.full_name.split(" ")[0],
                "Last Name": user_data.full_name.split(" ")[1],
                "Username": user_data.user_name,
                "Email": user_data.email,
                "Picture": user_data.get_profile_picture(),
                "Status": LoginRecords.objects.filter(user_id=user_data)
                .first()
                .current_status,
            }
        ]
    )


def user_specific_3ds_configurations(user_id):
    """this function formats user specififc 3DS configurations data"""
    user_data = Profile.objects.filter(id=user_id).first()
    if user_data is None:
        return user_data
    configuration_data = (
        json.loads(user_data.user_specific_3ds_configurations)
        if user_data.user_specific_3ds_configurations else None
    )
    return array_to_string_converter(
        [
            {
                "id": user_id,
                "DRIIVZ Account Number": (
                    user_data.driivz_account_number
                    if user_data.driivz_account_number
                    else "Not available"
                ),
                "Status": configuration_data["status"] if configuration_data else None,
                "Triggered 3DS For All Transactions": (YES if configuration_data[
                    'triggered_3ds_for_all_transactions'
                ] else NO) if configuration_data else None,
            }
        ]
    )


def three_3ds_for_all_configurations(_):
    """this function formats 3DS configuration data"""
    three_ds_configurations_from_db = BaseConfigurations.objects.filter(
        base_configuration_key="3ds_configurations"
    ).first()
    if (
        three_ds_configurations_from_db is None or
        (
            three_ds_configurations_from_db and
            not three_ds_configurations_from_db.base_configuration_value
        )
    ):
        return None
    three_ds_configurations = json.loads(
        three_ds_configurations_from_db.base_configuration_value
    )
    return array_to_string_converter(
        [
            {
                "id": three_ds_configurations_from_db.id,
                "First condition enabled": YES if (
                    'kwh_consumed__condition_checkbox' in three_ds_configurations and
                    three_ds_configurations['kwh_consumed__condition_checkbox'] == ON_CONST
                ) else NO,
                "First condition": (
                    three_ds_configurations["kwh_consumed__trigger_value"] +
                    BLANK_SPACE_CONST +
                    "kWh consumed in" +
                    BLANK_SPACE_CONST +
                    three_ds_configurations["kwh_consumed__in_x_days__number_of_days"] +
                    BLANK_SPACE_CONST +
                    "days. Trigger 3DS for next" +
                    BLANK_SPACE_CONST +
                    three_ds_configurations["kwh_consumed__in_x_days__number_of_next_transactions"] +
                    BLANK_SPACE_CONST +
                    "Transactions"
                ),
                "First condition last updated on": three_ds_configurations[
                    "kwh_consumed__last_updated_on_date"
                ] if (
                    'kwh_consumed__last_updated_on_date' in three_ds_configurations
                ) else "Not available",
                "Second condition enabled": YES if (
                    'total_transactions__condition_checkbox' in three_ds_configurations and
                    three_ds_configurations['total_transactions__condition_checkbox'] == ON_CONST
                ) else NO,
                "Second condition": (
                    three_ds_configurations["total_transactions__trigger_value"] +
                    BLANK_SPACE_CONST +
                    "kWh consumed in" +
                    BLANK_SPACE_CONST +
                    three_ds_configurations["total_transactions__in_x_days__number_of_days"] +
                    BLANK_SPACE_CONST +
                    "days. Trigger 3DS for next" +
                    BLANK_SPACE_CONST +
                    three_ds_configurations["total_transactions__in_x_days__number_of_next_transactions"] +
                    BLANK_SPACE_CONST +
                    "Transactions"
                ),
                "Second condition last updated on": three_ds_configurations[
                    "total_transactions__last_updated_on_date"
                ] if (
                    'total_transactions__last_updated_on_date' in three_ds_configurations
                ) else "Not available",
                "Third condition enabled": YES if (
                    'kwh_consumed_within__condition_checkbox' in three_ds_configurations and
                    three_ds_configurations['kwh_consumed_within__condition_checkbox'] == ON_CONST
                ) else NO,
                "Third condition": (
                    three_ds_configurations["kwh_consumed_within__trigger_value"] +
                    BLANK_SPACE_CONST +
                    "kWh consumed in" +
                    BLANK_SPACE_CONST +
                    three_ds_configurations["kwh_consumed_within__x_days__number_of_days"] +
                    BLANK_SPACE_CONST +
                    "days. Trigger 3DS for next" +
                    BLANK_SPACE_CONST +
                    three_ds_configurations["kwh_consumed_within__x_days__number_of_next_transactions"] +
                    BLANK_SPACE_CONST +
                    "Transactions"
                ),
                "Third condition last updated on": three_ds_configurations[
                    "kwh_consumed_within__last_updated_on_date"
                ] if (
                    'kwh_consumed_within__last_updated_on_date' in three_ds_configurations
                ) else "Not available",
                "Fourth condition enabled": YES if (
                    'total_transactions_within__condition_checkbox' in three_ds_configurations and
                    three_ds_configurations['total_transactions_within__condition_checkbox'] == ON_CONST
                ) else NO,
                "Fourth condition": (
                    three_ds_configurations["total_transactions_within__trigger_value"] +
                    BLANK_SPACE_CONST +
                    "kWh consumed in" +
                    BLANK_SPACE_CONST +
                    three_ds_configurations["total_transactions_within__x_days__number_of_days"] +
                    BLANK_SPACE_CONST +
                    "days. Trigger 3DS for next" +
                    BLANK_SPACE_CONST +
                    three_ds_configurations["total_transactions_within__x_days__number_of_next_transactions"] +
                    BLANK_SPACE_CONST +
                    "Transactions"
                ),
                "Fourth condition last updated on": three_ds_configurations[
                    "total_transactions_within__last_updated_on_date"
                ] if (
                    'total_transactions_within__last_updated_on_date' in three_ds_configurations
                ) else "Not available",
            }
        ]
    )


def connnector_configurations_formatter(connector_id):
    """this function returns formatted data for connectors"""
    connector_data = ConnectorConfiguration.objects.filter(
        id=connector_id
    ).first()
    if connector_data is None:
        return connector_data
    return array_to_string_converter(
        [
            {
                "Connector Type": connector_data.connector_plug_type,
                "Sorting order": connector_data.sorting_order,
                "Image": connector_data.get_image_path(),
            }
        ]
    )


def service_configurations_formatter(service_id):
    """this function returns formatted data for connectors"""
    service_data = ServiceConfiguration.objects.filter(id=service_id).first()
    if service_data is None:
        return service_data
    service_data_object = {
        "Name": service_data.service_name,
        "Unique ID": service_data.service_unique_identifier,
        "Image Without Text": service_data.get_image_path(),
    }
    if service_data.service_type == "Amenity":
        service_data_object[
            "Image With Text"
        ] = service_data.get_image_path_with_text()
    return array_to_string_converter([service_data_object])


def base_configurations_formatter(base_configuration_id):
    """this function returns formatted data for connectors"""
    base_conf_data = BaseConfigurations.objects.filter(
        id=base_configuration_id
    ).first()
    if base_conf_data is None:
        return base_conf_data
    base_conf_object = {}
    if base_conf_data.base_configuration_image:
        base_conf_object = {
            "Variable Name": base_conf_data.base_configuration_key,
            "Database Variable Name": base_conf_data.base_configuration_name,
            "Image": base_conf_data.get_image(),
        }
    else:
        base_conf_object = {
            "Variable Name": base_conf_data.base_configuration_key,
            "Database Variable Name": base_conf_data.base_configuration_name,
            "Description": base_conf_data.description,
            "Value": base_conf_data.base_configuration_value,
            "Added to cache": base_conf_data.add_to_cache,
            "Frequently used": base_conf_data.frequently_used,
        }
    return array_to_string_converter([base_conf_object])

def ocpi_configurations_formatter(configuration_id):
    """this function returns formatted data for connectors"""
    ocpi_conf_data = OCPICredentials.objects.filter(
        id=configuration_id
    ).first()
    modules = OCPIModuleDetails.objects.filter(
        credential_id = ocpi_conf_data
    )
    if ocpi_conf_data is None or modules.first() is None:
        return ocpi_conf_data
    # ocpi_conf_data = {}
    ocpi_conf_object = {
        "name": ocpi_conf_data.name,
        "endpoint": ocpi_conf_data.endpoint,
        "cpo_token": ocpi_conf_data.cpo_token,
        "emsp_token": ocpi_conf_data.emsp_token,
    }
    for module in modules:
        ocpi_conf_object[module.identifier] = module.url
    return array_to_string_converter([ocpi_conf_object])


def map_markers_formatter(map_marker_id):
    """this function returns formatted data for connectors"""
    map_marker_data = MapMarkerConfigurations.objects.filter(
        id=map_marker_id
    ).first()
    if map_marker_data is None:
        return map_marker_data
    return array_to_string_converter(
        [
            {
                "Indicator Type": map_marker_data.map_marker_key,
                "Indicator Image": map_marker_data.get_image_path(),
            }
        ]
    )


def wallet_transactions_formatter(transaction_id):
    """this function returns formatted data for connectors"""
    transaction_data = TransactionsTracker.objects.filter(
        id=transaction_id
    ).first()
    if transaction_data is None:
        return transaction_data
    return array_to_string_converter(
        [
            {
                "Receiver": transaction_data.user_id.username,
                "Assigned by": transaction_data.assigned_by.full_name,
                "Assigned role": date_formatter_for_json(
                    transaction_data.created_date
                ),
                "Amount": str(
                    float(transaction_data.transaction_amount) / 100
                ),
                "DRIIVZ ID": transaction_data.driivz_account_number,
                "Description": transaction_data.comments,
                "Wallet balance": transaction_data.user_updated_balance,
                "Withdrawal done": transaction_data.is_withdrawn,
            }
        ]
    )


def payment_formatter(session_id):
    """this function returns formatted data for payment"""
    session_data = ChargingSession.objects.filter(id=session_id).first()
    profile_data = Profile.objects.filter(user=session_data.user_id.id).first()
    if session_data is None:
        return None
    return array_to_string_converter(
        [
            {
                "Preauth Collected By": session_data.preauth_collected_by,
                "Preauth Status": session_data.preauth_status,
                "Reviewed By": session_data.is_reviewed,
                "Due amount": profile_data.due_amount_data,
            }
        ]
    )


def email_notifications_formatter(email_notification_id):
    """this function returns formatted data for email notification"""
    email_notification_data = EmailNotifications.objects.filter(
        id=email_notification_id
    ).first()
    if email_notification_data is None:
        return email_notification_data
    email_notification_object = {
        "Assigned to": email_notification_data.assign_to,
        "Users": (
            email_notification_data.user_list
            if email_notification_data.user_list
            else "-"
        ),
        "Postcode": (
            email_notification_data.postcode
            if email_notification_data.postcode
            else "-"
        ),
        "Subject": email_notification_data.subject,
        "Email Preference": email_notification_data.email_preference,
        "Scheduled time": date_formatter_for_json(
            email_notification_data.scheduled_time
        ),
        "Delivered time": date_formatter_for_json(
            email_notification_data.delivered_time
        ),
        "Status": email_notification_data.status,
        "Description": email_notification_data.description,
    }
    attachment_list = list(
        email_notification_data.email_attachments.filter(
            deleted=NO
        ).values_list("attachment", flat=True)
    )
    email_notification_object["Attachments"] = attachment_list
    return array_to_string_converter([email_notification_object])


def push_notifications_formatter(push_notification_id):
    """this function returns formatted data for push notification"""
    push_notification_data = PushNotifications.objects.filter(
        id=push_notification_id
    ).first()
    if push_notification_data is None:
        return push_notification_data
    push_notification_object = {
        "Assigned to": push_notification_data.assign_to,
        "Regions": push_notification_data.regions,
        "Title": push_notification_data.subject,
        "Description": push_notification_data.description,
        "Category": push_notification_data.category,
        "Push Notification": push_notification_data.push_notification,
        "In App Notification": push_notification_data.inapp_notification,
        "Screen": push_notification_data.screens,
        "Scheduled time": date_formatter_for_json(
            push_notification_data.scheduled_time
        ),
        "Delivered time": date_formatter_for_json(
            push_notification_data.delivered_time
        ),
        "Status": push_notification_data.status,
        "Image": push_notification_data.get_push_notification_image(),
    }
    return array_to_string_converter([push_notification_object])

def hold_payments_formatter(session_db_id):
    """this function formats data for hold transactions"""
    charging_session=ChargingSession.objects.filter(id=session_db_id).first()
    if charging_session is None:
        return charging_session
    push_notification_object = {
        "Session ID": charging_session.emp_session_id,
        "Session Status":charging_session.session_status,
        "Payment Status":charging_session.paid_status,
        "Amount":charging_session.total_cost,
        "Payment ID":charging_session.payment_id,
        "Mail Status":charging_session.mail_status,
        "Charge Point ID":charging_session.chargepoint_id.charger_point_name,
        "Back Office":charging_session.back_office,
        "Start time": date_formatter_for_json(
            charging_session.start_time
        ),
        "End time": date_formatter_for_json(
            charging_session.end_time
        ),
        "Payment Completed time": date_formatter_for_json(
            charging_session.end_time
        ),
        "Station Name":charging_session.station_id.station_name,
        "Type of payment":charging_session.payment_method,
        "Payment Initiated By":charging_session.is_reviewed,
        "Driivz Account Number":charging_session.user_account_number,
        "Rating":charging_session.rating,
        "Feedback":charging_session.feedback,
    }
    return array_to_string_converter([push_notification_object])


def audit_data_formatter(module, data_id=None):
    """this function formats data for audit trail modules"""
    switcher = {
        SITES_CONST: format_data_for_stations,
        PROMOTIONS_CONST: format_data_for_promotions,
        LOYALTY_CONST: format_data_for_loyalties,
        REVIEW_CONST: review_data_formatter,
        USER_MANAGEMENT_CONST: user_management_data_formatter,
        CONNECTORS_CONST: connnector_configurations_formatter,
        SERVICES_CONST: service_configurations_formatter,
        BASE_CONFIG_CONST: base_configurations_formatter,
        MAP_MARKERS_CONST: map_markers_formatter,
        EWALLET: wallet_transactions_formatter,
        PAYMENT_CONST: payment_formatter,
        NOTIFICATION_CONST: email_notifications_formatter,
        PUSH_NOTIFICATION_CONST: push_notifications_formatter,
        HOLD_PAYMENT_CONST: hold_payments_formatter,
        THREE_DS_CONFIG_CONST: user_specific_3ds_configurations,
        THREE_DS_FOR_ALL_CONFIG_CONST: three_3ds_for_all_configurations,
        OCPI_CONFIG_CONST:ocpi_configurations_formatter
    }
    func = switcher.get(module, lambda _: None)
    return func(data_id)
