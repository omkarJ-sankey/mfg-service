"""OCPI common functions"""

# Date - 07/06/2025


# File details-
#   Author          - Abhinav Shivalkar
#   Description     - This file contains OCPI common functions.
#   Name            - OCPI common functions


import json

from .common import redis_connection
from .model_files.ocpi_credentials_models import OCPICredentials,OCPICredentialsRole
from .model_files.ocpi_tariffs_models import Tariffs,TariffElements,TariffRestrictions,TariffComponents
from .model_files.ocpi_tokens_models import OCPITokens
from .constants import OCPI_CREDENTIALS_CACHE_KEY
from datetime import datetime, timedelta
from .model_files.ocpi_charge_detail_records_models import OCPIChargeDetailRecords

def get_back_office_data(back_office):
    if back_office is None:
        return None,None
    back_office_data = redis_connection.get(
            OCPI_CREDENTIALS_CACHE_KEY
        )
    back_office_data = json.loads(back_office_data.decode('utf-8')) if back_office_data else None
    if back_office_data is None:
        back_office_data = OCPICredentials.objects.select_related('to_role').filter(name__iexact = back_office,status = "Active").only('to_role__country_code','to_role__party_id')
        if back_office_data.first() is None or back_office_data.first().to_role is None:
            return None,None
        country_code = back_office_data.first().to_role.country_code
        party_id = back_office_data.first().to_role.party_id
        return country_code,party_id
    elif back_office.upper() not in back_office_data:
        back_office_data = OCPICredentials.objects.select_related('to_role').filter(name__iexact = back_office,status = "Active").only('to_role__country_code','to_role__party_id')
        if back_office_data.first() is None or back_office_data.first().to_role is None:
            return None,None
        country_code = back_office_data.first().to_role.country_code
        party_id = back_office_data.first().to_role.party_id
    else:
        country_code = back_office_data[back_office.upper()]['to_role']['country_code']
        party_id = back_office_data[back_office.upper()]['to_role']['party_id']
    return country_code,party_id


def get_location_backoffice(location):
    if location is None:
        return None
    back_office = OCPICredentials.objects.filter(
        to_role__country_code = location.country_code,
        to_role__party_id = location.party_id,
        status = "Active"
    ).only("name").first()
    return back_office.name.upper() if back_office is not None else None

def get_user_token_details(mfg_user):
    """this function returns user token"""
    token_uid = OCPITokens.objects.filter(user_id = mfg_user).only('uid').first()
    return token_uid.uid if token_uid else None


def get_tariff_amount(tariff_ids, country_code, party_id, start_datetime):
    """This function is used to get tariff amount from tariff ids"""
    start_time = datetime.strftime(start_datetime,'HH:MM:SS')
    start_day = start_datetime.day
    tariffs = Tariffs.objects.filter(
        tariff_id__in = tariff_ids, country_code = country_code, party_id = party_id,
        tariff_element__tariff_restriction__day_of_week = start_day,
        tariff_element__tariff_restriction__start_time__lte = start_time,
        tariff_element__tariff_restriction__end_time__gte = start_time,
        
        ).prefetch_related('tariff_element').prefetch_related('tariff_restriction')
    tariff_arr = []
    for tariff in tariffs:
        tariff_arr.append(tariff.tariff_element.element_id)
    tariff_amount = TariffComponents.objects.filter(element_id__in = tariff_arr, type = 'ENERGY').only('price').first()
    if tariff_amount is not None:
        return tariff_amount.price
    return None

def get_cdr_cost(session_id):
    """Function to get cdrs for a session"""
    total_cost_incl_vat = 0
    total_cost_exc_vat = 0
    cdr_data = OCPIChargeDetailRecords.objects.filter(charging_session_id = session_id)
    cdr_energy = cdr_data.first().total_energy if cdr_data.first() else 0
    # if cdr_data is not None:
    for cdr in cdr_data:
        #total_energy_cost includes only energy cost including vat but it is an optional field
        #total_cost includes all cost including parking and reservation
        total_cost_incl_vat += json.loads(cdr.total_cost)['incl_vat']
        total_cost_exc_vat += json.loads(cdr.total_cost)['excl_vat']
    return total_cost_incl_vat,total_cost_exc_vat,cdr_energy