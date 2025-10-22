"""gift card helper functions"""
# Date - 11/08/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file contains gift card helper functions.
#   Name            - Gift card helper functions
#   Modified by     - Manish Pawar
#   Modified date   - 30/11/2022


# These are all the imports that we are exporting from
# different module's from project or library.

from django.utils import timezone as tz

# pylint:disable=import-error
from sharedServices.models import BaseConfigurations, TransactionsTracker


def validate_form(data):
    """validated data from frontend"""
    error = {}
    is_valid = True
    for key, value in data.items():
        if value is None:
            error[key] = "required"
            is_valid = False
    return error, is_valid


def get_user_wallet_max(user):
    """get voucher exceeded statuses"""
    max_month_vouchers = BaseConfigurations.objects.filter(
        base_configuration_key="max_month_user_vouchers"
    ).first()
    max_year_vouchers = BaseConfigurations.objects.filter(
        base_configuration_key="max_year_user_vouchers"
    ).first()
    if max_month_vouchers:
        max_month_vouchers = int(max_month_vouchers.base_configuration_value)
    else:
        max_month_vouchers = 10

    if max_year_vouchers:
        max_year_vouchers = int(max_year_vouchers.base_configuration_value)
    else:
        max_year_vouchers = 20
    year = tz.now().year
    month = tz.now().month
    user_voucher_monthly_count = TransactionsTracker.objects.filter(
        user_id=user, created_date__year=year, created_date__month=month
    ).count()
    user_voucher_yearly_count = TransactionsTracker.objects.filter(
        user_id=user, created_date__year=year
    ).count()
    return (
        user_voucher_monthly_count >= max_month_vouchers,
        user_voucher_yearly_count >= max_year_vouchers,
    )
