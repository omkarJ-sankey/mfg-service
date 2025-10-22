"""stations app level constants"""
# pylint:disable=import-error
from sharedServices.constants import (
    EMAIL_ADDRESS,
    FUEL_BRANDS,
    LOC_LONG,
    OPS_REGION,
    REGIONAL_MANAGERS,
    STATION_ID,
    LOC_LAT,
)


NO_CHARGEPOINTS_PROVIDED_MESSAGE = "In order to assign station type as \
    MFG EV ,make sure you have provided chargepoints for this site"

STATIONS_LIST_OF_FIELDS = [
    STATION_ID,
    LOC_LAT,
    LOC_LONG,
    FUEL_BRANDS,
    "Postcode",
    "Valeting",
    "Payment Terminal",
]

STATIONS_IERATION_LIST_OF_FIELDS = [
    STATION_ID,
    FUEL_BRANDS,
    "Address Line 1",
    "Station Name",
    "Address Line 2",
    "Address Line 3",
    "Postcode",
    LOC_LAT,
    LOC_LONG,
    "Phone Number",
    "Monday - Friday Opening Status",
    "Monday - Friday Closing Time",
    "Monday - Friday Opening Time",
    "Saturday Opening Status",
    "Saturday Opening Time",
    "Saturday Closing Time",
    "Sunday Opening Status",
    "Sunday Opening Time",
    "Sunday Closing Time",
    "Services",
    # "Image",
    "Site Id",
    "Valeting",
    "Payment Terminal",
    "RH Site Name",
    "Overstay Fee",
    "Ampeco Site ID",
    "Ampeco Site Title",
    "Back Office",
    "Location ID",
    "Parking Details"
]

DEVICES_LIST_OF_FIELDS = [
    STATION_ID,
    "Charge point ID",
    "Chargepoint name",
    "Chargepoint activation status",
    "Connecter Id",
    "Socket name",
    "Connecter Plug type",
    "Power in kw",
    "Connector Sort order",
    "Tariff amount",
    "Tariff currency",
    "Connector Type",
    # "Back-office",
    "Device ID",
    "Payter Terminal ID",
    "Worldline Terminal ID",
    "Evse UID",
    "Ocpi Connector ID",
]

DEVICES_LIST_OF_FIELDS_EXPORT = [
    STATION_ID,
    "Charge point ID",
    "Chargepoint name",
    "Chargepoint activation status",
    "Connecter Id",
    "Socket name",
    "Connecter Plug type",
    "Power in kw",
    "Connector Sort order",
    "Tariff amount",
    "Tariff currency",
    "Connector Type",
    # "Back-office",
    "Device ID",
    "Payter Terminal ID",
    "Worldline Terminal ID",
    "Ampeco Chargepoint ID",
    "Ampeco Chargepoint Name",
    "Evse UID",
    "Ocpi Connector ID",
]

DEVICES_LIST_OF_FIELDS_CHARGEPOINT = ["ID"] + DEVICES_LIST_OF_FIELDS_EXPORT

DEVICES_ITERATION_LIST_OF_FIELDS = [
    STATION_ID,
    "Charge point ID",
    "Chargepoint name",
    "Chargepoint activation status",
    "Connecter Id",
    "Socket name",
    "Connecter Plug type",
    "Power in kw",
    "Connector Sort order",
    "Tariff amount",
    "Tariff currency",
    "Connector Type",
    # "Back-office",
    "Device ID",
    "Payter Terminal ID",
    "Worldline Terminal ID",
    "Evse UID",
    "Ocpi Connector ID" 
]

SITE_DETAILS_LIST_OF_FIELDS = [
    STATION_ID,
    OPS_REGION,
    "Region",
    REGIONAL_MANAGERS,
    "Area",
    "ARM",
    "Title",
    EMAIL_ADDRESS,
    "Country",
]

SITE_DETAILS_ITERATION_LIST_OF_FIELDS = [
    STATION_ID,
    OPS_REGION,
    "Region",
    REGIONAL_MANAGERS,
    "Area",
    "ARM",
    "Title",
    EMAIL_ADDRESS,
    "Country",
    "Food to Go",
    "Retail",
]

VALETING_TERMINALS_ITERATION_LIST_OF_FIELDS = (
    VALETING_TERMINALS_LIST_OF_FIELDS
) = [
    STATION_ID,
    "Payter Serial Number",
    "Status",
    "Amenities",
]

LOCATION_MAPPING_ITERATION_LIST_OF_FIELDS = (
    LOCATION_MAPPING_LIST_OF_FIELDS
) = [
    STATION_ID,
    "Back Office",
    "Location ID",
]

VALETING_TERMINAL_LIST_OF_FIELDS = [
    "ID"
] + VALETING_TERMINALS_ITERATION_LIST_OF_FIELDS
ZERO, ONE, TWO, THREE, FOUR, FIVE = [0, 1, 2, 3, 4, 5]

STATIONS_EXPORT = [
    "ID",
    STATION_ID,
    "Station Name",
    FUEL_BRANDS,
    "Owner",
    "Address Line 1",
    "Address Line 2",
    "Address Line 3",
    "Postcode",
    LOC_LAT,
    LOC_LONG,
    "Phone Number",
    "Monday - Friday Opening Status",
    "Monday - Friday Opening Time",
    "Monday - Friday Closing Time",
    "Saturday Opening Status",
    "Saturday Opening Time",
    "Saturday Closing Time",
    "Sunday Opening Status",
    "Sunday Opening Time",
    "Sunday Closing Time",
    "Is MFG",
    "Is EV",
    "Services",
    "Created date",
    # "Image",
    "Site Id",
    "Valeting",
    "Payment Terminal",
    "RH Site Name",
    "Overstay Fee",
    # "Valeting Site ID",
    "Ampeco Site ID",
    "Ampeco Site Title",
    "Back Office",
    "Location ID",
    "Parking Details"
]
STATIONS_EXPORT_DETAILS = [
    STATION_ID,
    "Site Name",
    OPS_REGION,
    "Region",
    "Area",
    REGIONAL_MANAGERS,
    "ARM",
    "Title",
    "Station type",
    "Status",
    EMAIL_ADDRESS,
    "Country",
    "Food to Go",
    "Retail",
]

NON_EV_STATION_TYPE = ["MFG Forecourt", "Non MFG"]

DRIIVZ_PAGINATION_PAGE_SIZE = 1000
DRIIVZ_PAGINATION_FIRST_PAGE_INDEX = 0
DRIIVZ_FETCH_CHARGER_MODELS_ENDPOINT = "/api-gateway/v1/charger-models/filter"
DRIIVZ_FETCH_CHARGERS_ENDPOINT = "/api-gateway/v1/chargers/profiles/filter"

VALETING_MACHINES_LIST_OF_FIELDS = [
    "Machine ID",
    "Station ID",
    "Machine Name",
    "Machine Number",
    "Active"
]