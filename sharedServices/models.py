"""models"""
# Date - 21/06/2021
# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on
#                       creating database tables for
#                       all modules.
#   Name            - Authentication related models
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 28/04/2021

# Imports required to make models are below
# pylint:disable=import-error
# pylint:disable=unused-import
from sharedServices.model_files.admin_user_models import (
    Content,
    RoleAccessTypes,
    AdminUser,
    AdminAuthorization,
    LoginRecords,
)
from sharedServices.model_files.app_user_models import (
    UserManager,
    MFGUserEV,
    Profile,
    EmailVerification,
)
from sharedServices.model_files.audit_models import AuditTrail
from sharedServices.model_files.bulk_models import (
    BulkUploadProgress,
    BulkUploadErrorMessages,
)
from sharedServices.model_files.card_models import Cards
from sharedServices.model_files.charging_session_models import (
    ChargingSession,
    SwarcoDynamicData,
    SessionTransactionStatusTracker,
    PaidPaymentLogs,
)
from sharedServices.model_files.config_models import (
    ConnectorConfiguration,
    ServiceConfiguration,
    BaseConfigurations,
    MapMarkerConfigurations,
)
from sharedServices.model_files.promotions_models import (
    Promotions,
    PromotionsAvailableOn,
    PromotionImages,
)
from sharedServices.model_files.review_models import Reviews, ReviewLikes
from sharedServices.model_files.station_models import (
    Stations,
    StationWorkingHours,
    ChargePoint,
    StationConnector,
    StationImages,
    StationServices,
    Bookmarks,
    ValetingTerminals,
)
from sharedServices.model_files.transaction_models import (
    Transactions,
    TransactionsDetails,
    TransactionsTracker,
)
from sharedServices.model_files.trip_models import Trips
from sharedServices.model_files.vehicle_models import ElectricVehicleDatabase
from sharedServices.model_files.loyalty_models import (
    Loyalty,
    LoyaltyAvailableOn,
    UserLoyaltyTransactions,
    LoyaltyTransactions,
    LoyaltyBulkUpload,
    LoyaltyProducts,
    LoyaltyOccurrences
)
from sharedServices.model_files.third_party_users_models import (
    ThirdPartyCredentials,
)
from sharedServices.model_files.notifications_module_models import (
    EmailNotifications,
    EmailAttachments,
    PushNotifications,
)
from .model_files.contactless_models import (
    ContactlessReceiptEmailTracking,
    ContactlessSessionsDownloadedReceipts,
    ThirdPartyServicesData,
    ValetingTransactionData,
)
from sharedServices.model_files.valeting_models import (
    ValetingMachine
)
from sharedServices.model_files.ocpi_credentials_models import (OCPICredentials,OCPICredentialsRole)

from sharedServices.model_files.ocpi_tariffs_models import (Tariffs,TariffElements,TariffComponents,TariffRestrictions)
from sharedServices.model_files.ocpi_locations_models import (OCPILocation,OCPIEVSE,OCPIConnector)
from sharedServices.model_files.ocpi_tokens_models import (OCPITokens)
from sharedServices.model_files.ocpi_sessions_models import (OCPISessions)
from sharedServices.model_files.ocpi_commands_models import (OCPICommands)
from sharedServices.model_files.ocpi_charge_detail_records_models import (OCPIChargeDetailRecords)