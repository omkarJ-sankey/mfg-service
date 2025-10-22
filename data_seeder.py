"""This file helps to delete entire data from database
and reimport the neccessary data."""
import json
import os
import sys
import django

from decouple import config
from django.core import serializers

# pylint:disable=import-error
from sharedServices.model_files.config_models import (
    BaseConfigurations,
    MapMarkerConfigurations,
    ConnectorConfiguration,
    ServiceConfiguration,
)
from sharedServices.model_files.station_models import (
    Stations,
    StationWorkingHours,
    ChargePoint,
    StationConnector,
    StationImages,
    StationServices,
    Bookmarks,
)
from sharedServices.model_files.admin_user_models import (
    Content,
    RoleAccessTypes,
    AdminUser,
    AdminAuthorization,
    LoginRecords,
)
from sharedServices.model_files.app_user_models import (
    MFGUserEV,
    Profile,
    EmailVerification,
)
from sharedServices.model_files.promotions_models import (
    Promotions,
    PromotionsAvailableOn,
    PromotionImages,
)
from sharedServices.model_files.transaction_models import (
    Transactions,
    TransactionsDetails,
)
from sharedServices.model_files.review_models import Reviews, ReviewLikes
from sharedServices.model_files.bulk_models import (
    BulkUploadProgress,
    BulkUploadErrorMessages,
)
from sharedServices.model_files.card_models import Cards
from sharedServices.model_files.trip_models import Trips
from sharedServices.model_files.charging_session_models import (
    ChargingSession,
    SwarcoDynamicData,
)
from sharedServices.model_files.audit_models import AuditTrail
from sharedServices.model_files.vehicle_models import ElectricVehicleDatabase

from sharedServices.sentry_tracers import traced_request
from sharedServices.constants import REQUEST_API_TIMEOUT, GET_REQUEST


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backendServices.settings")
django.setup()
# fetching rquired  data

BACKUP_FOLDER_NAME = "Backup"
DATABASE_BACKUP_FILE_NAME = "db_data_mfg"


def fetching_data():
    """fetching all data from db"""
    print("Data fetching started...")
    base_configurations_entries = BaseConfigurations.objects.all()

    content_entries = Content.objects.all()

    role_access_types = RoleAccessTypes.objects.all()

    first_user = AdminUser.objects.filter().first()

    admin_user_entry = AdminUser.objects.filter(id=first_user.id)

    admin_authorization_entry = AdminAuthorization.objects.filter(
        user_id_id=first_user.id
    )

    admin_login_record_entry = LoginRecords.objects.filter(
        user_id_id=first_user.id
    )

    map_marker_congigurations_entries = MapMarkerConfigurations.objects.all()

    print("Fetched all required data...")
    return [
        base_configurations_entries,
        content_entries,
        role_access_types,
        admin_user_entry,
        admin_authorization_entry,
        admin_login_record_entry,
        map_marker_congigurations_entries,
    ]


# serializing data (converting querysets to json objects)


def serializing_data():
    """serializing data"""
    print("Json file creation in progress...")
    try:
        data_entries = fetching_data()
        (
            base_configurations_query_set,
            content_query_set,
            role_access_type_query_set,
            admin_user_query_set,
            admin_authorization_query_set,
            admin_login_record_query_set,
            map_marker_congigurations_query_set,
        ) = data_entries

        data_to_be_exported = []

        base_configurations_json_data = serializers.serialize(
            "json", base_configurations_query_set
        )
        data_to_be_exported = data_to_be_exported + json.loads(
            base_configurations_json_data
        )

        content_json_data = serializers.serialize("json", content_query_set)
        data_to_be_exported = data_to_be_exported + json.loads(
            content_json_data
        )

        role_access_type_json_data = serializers.serialize(
            "json", role_access_type_query_set
        )
        data_to_be_exported = data_to_be_exported + json.loads(
            role_access_type_json_data
        )

        admin_user_json_data = serializers.serialize(
            "json", admin_user_query_set
        )
        data_to_be_exported = data_to_be_exported + json.loads(
            admin_user_json_data
        )

        admin_authorization_json_data = serializers.serialize(
            "json", admin_authorization_query_set
        )
        data_to_be_exported = data_to_be_exported + json.loads(
            admin_authorization_json_data
        )

        admin_login_record_json_data = serializers.serialize(
            "json", admin_login_record_query_set
        )
        data_to_be_exported = data_to_be_exported + json.loads(
            admin_login_record_json_data
        )

        map_marker_congigurations_json_data = serializers.serialize(
            "json", map_marker_congigurations_query_set
        )
        data_to_be_exported = data_to_be_exported + json.loads(
            map_marker_congigurations_json_data
        )

        print("Preparing file to download.")
        local_path = f"./{BACKUP_FOLDER_NAME}"

        file_name = f"{DATABASE_BACKUP_FILE_NAME}.json"
        upload_file_path = os.path.join(local_path, file_name)

        print("Checking previous file whether it's exists or not")
        if os.path.exists(upload_file_path):
            print(
                "File exists on machine,  so deleting the old\
                    file to create new one."
            )
            os.remove(upload_file_path)
            os.rmdir("Backup")
        else:
            print("The file does not exist")

        os.mkdir(local_path)
        # pylint:disable=unspecified-encoding
        with open(upload_file_path, mode="w") as file:
            file.write(json.dumps(data_to_be_exported))
        # pylint:enable=unspecified-encoding

        print("Downloaded json file successfully...")

        print("....")
        print("Json file uploading on blob storage ....")
        print("Successfully uploaded  json file  to azure...")
        return True

    # pylint:disable=broad-except
    except Exception as error:
        print("Failed to serialize data , due to ->", str(error))
    return False
    # pylint:enable=broad-except


def delete_objects():
    """delete all data"""
    try:
        BaseConfigurations.objects.all().delete()

        Content.objects.all().delete()

        RoleAccessTypes.objects.all().delete()

        AdminUser.objects.all().delete()

        AdminAuthorization.objects.all().delete()

        LoginRecords.objects.all().delete()

        MapMarkerConfigurations.objects.all().delete()

        ConnectorConfiguration.objects.all().delete()

        ServiceConfiguration.objects.all().delete()

        Stations.objects.all().delete()

        StationWorkingHours.objects.all().delete()

        ChargePoint.objects.all().delete()

        StationConnector.objects.all().delete()

        StationImages.objects.all().delete()

        StationServices.objects.all().delete()

        MFGUserEV.objects.all().delete()

        Profile.objects.all().delete()

        EmailVerification.objects.all().delete()

        Cards.objects.all().delete()

        Bookmarks.objects.all().delete()

        Promotions.objects.all().delete()

        PromotionsAvailableOn.objects.all().delete()

        PromotionImages.objects.all().delete()

        Transactions.objects.all().delete()

        TransactionsDetails.objects.all().delete()

        Reviews.objects.all().delete()

        ReviewLikes.objects.all().delete()

        Trips.objects.all().delete()

        ChargingSession.objects.all().delete()

        AuditTrail.objects.all().delete()

        SwarcoDynamicData.objects.all().delete()

        ElectricVehicleDatabase.objects.all().delete()

        BulkUploadProgress.objects.all().delete()

        BulkUploadErrorMessages.objects.all().delete()
        print("Successfuly deleted all data!!")
    except (TimeoutError) as error:
        print("Failed to delete data , due to->", str(error))


# deleting all data
def delete_all_data():
    """delete all data"""
    local_path = f"./{BACKUP_FOLDER_NAME}"
    file_name = f"{DATABASE_BACKUP_FILE_NAME}.json"
    json_file_path = os.path.join(local_path, file_name)
    can_be_deleted = False
    print(
        "Checking whether backup file is there or not to\
            load data in database after deletion..."
    )
    if os.path.exists(json_file_path):
        can_be_deleted = True
    else:
        blob_request_response = traced_request(
            GET_REQUEST,
            f"{config('DJANGO_APP_BLOB_STORAGE_URL')}"
            + BACKUP_FOLDER_NAME
            + "/"
            + DATABASE_BACKUP_FILE_NAME
            + ".json",
            timeout=REQUEST_API_TIMEOUT
        )

        if blob_request_response.status_code == 200:
            can_be_deleted = True
    if can_be_deleted:
        print("Found backup initializing delete process...")
        delete_objects()
    else:
        print("No backup found in order to reload data after deletion.")


def load_data_in_database():
    """load data from db"""
    print("Reading file to load data in database...")

    local_path = f"./{BACKUP_FOLDER_NAME}"

    file_name = f"{DATABASE_BACKUP_FILE_NAME}.json"
    json_file_path = os.path.join(local_path, file_name)

    print("Checking whether file is availale on machine or not")
    if os.path.exists(json_file_path):
        print("File exists on machine,  so loading json data from json file.")

        with open(json_file_path, "rb") as fixture:
            objects = serializers.deserialize(
                "json", fixture, ignorenonexistent=True
            )
            for obj in objects:
                obj.save()

        print("*****  -- Data loaded successfully! --  *****")
    else:
        print(
            "The file does not exists on machine, \
                downloading data from azure blob storage..."
        )
        blob_request_response = traced_request(
            GET_REQUEST,
            f"{config('DJANGO_APP_BLOB_STORAGE_URL')}"
            + BACKUP_FOLDER_NAME
            + "/"
            + DATABASE_BACKUP_FILE_NAME
            + ".json",
            timeout=REQUEST_API_TIMEOUT
        )

        if blob_request_response.status_code == 200:
            print("Successfully fetched data from blob storage")

            objects = serializers.deserialize(
                "json", blob_request_response.content, ignorenonexistent=True
            )
            for obj in objects:
                obj.save()

            print("*****  -- Data loaded successfully! --  *****")
        else:
            print(
                "Data loading process failed as file is\
                    available on blob storage."
            )


if __name__ == "__main__":
    if "load_data" in sys.argv:
        print("Loading data in progress")
        load_data_in_database()

    if "reset_data" in sys.argv:
        print("Reseting data in progress")
        SERIALIZED_RESULT = serializing_data()
        if SERIALIZED_RESULT:
            delete_all_data()
            load_data_in_database()

    if "delete_all_data" in sys.argv:
        delete_all_data()
    else:
        print()
        print("############    ----     #############")
        print()
        print()
        print(
            'To load data in new database run command  \
                "py data_seeder.py load_data"'
        )
        print()
        print("&")
        print()
        print(
            'To delete existing data and load new data run command \
                "py data_seeder.py reset_data"'
        )
        print()
        print("&")
        print()
        print('To delete all data run "py data_seeder.py delete_all_data"')
        print()
        print()
        print("############    ----     #############")
