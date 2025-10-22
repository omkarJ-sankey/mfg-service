"""dashboard views"""
#  File details-
#   Author      - Shubham Dhumal
#   Description - This file is mainly focused on show data and
#                   visualize Dashboard users.
#   Name        - Dashboard View
#   Modified by - Vismay Raul

# These are all the imports that we are exporting from
# different module's from project or library.
import json
from itertools import groupby
from datetime import timedelta, datetime
import pytz

from django.shortcuts import render
from django.db.models import Q, F, Sum, Count
from django.db.models.functions import ExtractYear
from django.utils import timezone
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.views.decorators.http import require_http_methods
from django.core.cache import cache
from django.conf import settings
from django.db.models.expressions import RawSQL
from django.db.models import OuterRef, Subquery, F, Value
from collections import defaultdict
import traceback
from itertools import chain
# from myapp.models import Data, Location

# pylint:disable=import-error
from sharedServices.model_files.ocpi_locations_models import OCPILocation
from sharedServices.decorators import authenticated_user
from sharedServices.model_files.app_user_models import MFGUserEV
from sharedServices.model_files.station_models import Stations
from sharedServices.model_files.charging_session_models import (
    ChargingSession, ThreeDSCheckLogs
)
from sharedServices.model_files.loyalty_models import LoyaltyTransactions
from sharedServices.model_files.ocpi_sessions_models import OCPISessions
from sharedServices.model_files.ocpi_charge_detail_records_models import OCPIChargeDetailRecords
from sharedServices.common import (
    filter_url,
    date_formater_for_frontend_date,
    string_to_array_converter,
    date_difference_function,
    filter_function_for_base_configuration,
)
from sharedServices.constants import (
    DASHBOARD_CONST,
    NO,
    GET_METHOD_ALLOWED,
    POST_METHOD_ALLOWED,
    COMMON_ERRORS,
    ERROR_TEMPLATE_URL,
)

from adminServices.stations.views import station_site_locations_list

from .date_utils import (
    return_days_from_sessions_dates,
    return_months_from_sessions_dates,
    return_weeks_from_sessions_dates,
    return_days_from_user_created_dates,
    return_months_from_user_created_dates,
    return_weeks_from_user_created_dates,
    days_in_month,
)

from .app_level_constants import (
    DAY_POSITION_IN_DAYS_ARRAY,
    MONTH_POSITION_IN_DAYS_ARRAY,
    YEAR_POSITION_IN_DAYS_ARRAY,
    WEEK_POSITION_IN_WEEKS_ARRAY,
    YEAR_POSITION_IN_WEEKS_ARRAY,
    MONTH_POSITION_IN_MONTHS_ARRAY,
    YEAR_POSITION_IN_MONTHS_ARRAY,
    MONTHS_LIST,
    ONE_STAR_REVIEWS,
    TWO_STAR_REVIEWS,
    THREE_STAR_REVIEWS,
    FOUR_STAR_REVIEWS,
    FIVE_STAR_REVIEWS,
    SWARCO,
    DRIIVZ,
    DASHBOARD_DATA_DAYS_LIMIT,
    DEFAULT_DASHBOARD_DATA_DAYS_LIMIT,
    COMMON_SESSION_FIELDS,
)


CACHE_TTL = getattr(settings, "CACHE_TTL", DEFAULT_TIMEOUT)

# This method render Dashboard


def dashboard_url_maker(filter_object):
    """dashboard url maker"""
    url = ""
    graph_urls = ""
    for key, value in filter_object.items():
        if key == "type_of_change":
            if value:
                url += f"&type_of_change={value}"
                graph_urls += f"&type_of_change={value}"
            else:
                url += "&type_of_change=Daily"
                graph_urls += "&type_of_change=Daily"
        elif key == "active_chart_tab":
            if value:
                url += f"&active_chart_tab={value}"
            else:
                url += "&active_chart_tab=Sales"
        else:
            if value:
                url += f"&{key}={value}"
                graph_urls += f"&{key}={value}"
    return [url, graph_urls]


def total_power_calculator(array):
    """total power calculator"""
    sum_of_power = 0
    for i in array:
        if i is not None and i.charging_data:
            charging_data = string_to_array_converter(i.charging_data)
            if i.back_office == SWARCO and "kwh" in list(
                charging_data[0].keys()
            ):
                sum_of_power += float(charging_data[0]["kwh"])
            if i.back_office == DRIIVZ and "totalEnergy" in list(
                charging_data[0].keys()
            ):
                sum_of_power += float(charging_data[0]["totalEnergy"])
    return sum_of_power


def total_sales_calculator(array,is_ocpi):
    """total sales calculator"""
    if is_ocpi:
        sales_data = array.values_list("id",flat=True)
        cdrs_cost = OCPIChargeDetailRecords.objects.filter(charging_session_id__in = sales_data).values_list("total_cost",flat=True)
        return (
        sum(
            [
                float(json.loads(charge_data)['incl_vat'])
                for charge_data in cdrs_cost
                if json.loads(charge_data)['incl_vat']
            ]
        )
    )

    return (
        sum(
            [
                float(charge_data.total_cost)
                for charge_data in array
                if charge_data.total_cost
            ]
        )
        / 100
    )


def day_month_year_joiner(*arg):
    """this functions formats dates in a valid format for graphs"""
    return "/".join([f"{el}" for el in arg])


def ratings_counter_function(ratings_data):
    """this functions returns reviews counts for particular stars"""
    ratings_count = (
        sum(d["ratings"] for d in ratings_data[ONE_STAR_REVIEWS])
        + sum(d["ratings"] for d in ratings_data[TWO_STAR_REVIEWS])
        + sum(d["ratings"] for d in ratings_data[THREE_STAR_REVIEWS])
        + sum(d["ratings"] for d in ratings_data[FOUR_STAR_REVIEWS])
        + sum(d["ratings"] for d in ratings_data[FIVE_STAR_REVIEWS])
    )
    positive_rating_count = sum(
        d["ratings"] for d in ratings_data[FOUR_STAR_REVIEWS]
    ) + sum(d["ratings"] for d in ratings_data[FIVE_STAR_REVIEWS])
    neutral_rating_count = sum(
        d["ratings"] for d in ratings_data[THREE_STAR_REVIEWS]
    )
    negative_rating_count = sum(
        d["ratings"] for d in ratings_data[ONE_STAR_REVIEWS]
    ) + sum(d["ratings"] for d in ratings_data[TWO_STAR_REVIEWS])

    return [
        ratings_count,
        positive_rating_count,
        neutral_rating_count,
        negative_rating_count,
    ]


def rating_key_func(elment):
    """function to return rating key for group by"""
    return elment.rating


def get_month_year_label(year, month):
    return f"{MONTHS_LIST[int(month)-1]}/{year}"


def get_daily_loyalty_transaction_data(
    loyalty_transactions,
    transaction_type,
):
    loyalty_transactions = loyalty_transactions.filter(
        transaction_type=transaction_type,
    )
    redeemed_or_purchaseed_qr_code_array = list(
        loyalty_transactions.values(date=F("transaction_time__date"))
        .annotate(Sum("count_of_transactions"))
        .order_by("transaction_time__date")
    )
    redeemed_or_purchaseed_qr_code_count = (
        loyalty_transactions.aggregate(Sum("count_of_transactions"))
    )["count_of_transactions__sum"]

    return (
        redeemed_or_purchaseed_qr_code_array,
        redeemed_or_purchaseed_qr_code_count,
    )


def get_weekly_loyalty_transaction_data(
    loyalty_transactions,
    transaction_type,
):
    loyalty_transactions = loyalty_transactions.filter(
        transaction_type=transaction_type,
    )
    redeemed_or_purchaseed_qr_code_array = []
    redeemed_or_purchaseed_qr_code_count = (
        loyalty_transactions.aggregate(Sum("count_of_transactions"))
    )["count_of_transactions__sum"]
    for year in sorted(
        set(
            loyalty_transactions.annotate(
                year=ExtractYear("transaction_time")
            ).values_list("year", flat=True)
        ),
    ):
        weekly_data_yearwise = (
            loyalty_transactions.filter(transaction_time__year=str(year))
            .values(date=F("transaction_time__week"))
            .annotate(Sum("count_of_transactions"))
            .order_by("transaction_time__week")
        )
        for week_data_yearwise in list(weekly_data_yearwise):
            week_data_yearwise["date"] = f'{week_data_yearwise["date"]}/{year}'
        redeemed_or_purchaseed_qr_code_array += list(weekly_data_yearwise)
    return [
        redeemed_or_purchaseed_qr_code_array,
        redeemed_or_purchaseed_qr_code_count,
    ]


def get_monthly_loyalty_transaction_data(
    loyalty_transactions,
    transaction_type,
):
    loyalty_transactions = loyalty_transactions.filter(
        transaction_type=transaction_type,
    )
    redeemed_or_purchaseed_qr_code_array = []
    redeemed_or_purchaseed_qr_code_count = (
        loyalty_transactions.aggregate(Sum("count_of_transactions"))
    )["count_of_transactions__sum"]
    for year in sorted(
        set(
            loyalty_transactions.annotate(
                year=ExtractYear("transaction_time")
            ).values_list("year", flat=True)
        ),
    ):
        monthly_data_yearwise = (
            loyalty_transactions.filter(transaction_time__year=str(year))
            .values(date=F("transaction_time__month"))
            .annotate(Sum("count_of_transactions"))
            .order_by("transaction_time__month")
        )
        for month_data_yearwise in list(monthly_data_yearwise):
            month_data_yearwise["date"] = get_month_year_label(
                year, month_data_yearwise["date"]
            )
        redeemed_or_purchaseed_qr_code_array += list(monthly_data_yearwise)
    return [
        redeemed_or_purchaseed_qr_code_array,
        redeemed_or_purchaseed_qr_code_count,
    ]


def get_loyalty_transaction_data(type_of_change, loyalty_transactions):
    if type_of_change == "Daily":
        (
            purchased_qr_data,
            purchased_qr_count,
        ) = get_daily_loyalty_transaction_data(
            loyalty_transactions, "Purchased"
        )
        (
            redeemed_qr_data,
            redeemed_qr_count,
        ) = get_daily_loyalty_transaction_data(
            loyalty_transactions, "Redeemed"
        )
    elif type_of_change == "Monthly":
        (
            purchased_qr_data,
            purchased_qr_count,
        ) = get_monthly_loyalty_transaction_data(
            loyalty_transactions, "Purchased"
        )
        (
            redeemed_qr_data,
            redeemed_qr_count,
        ) = get_monthly_loyalty_transaction_data(
            loyalty_transactions, "Redeemed"
        )

    else:
        (
            purchased_qr_data,
            purchased_qr_count,
        ) = get_weekly_loyalty_transaction_data(
            loyalty_transactions, "Purchased"
        )
        (
            redeemed_qr_data,
            redeemed_qr_count,
        ) = get_weekly_loyalty_transaction_data(
            loyalty_transactions, "Redeemed"
        )
    return [
        purchased_qr_data,
        purchased_qr_count,
        redeemed_qr_data,
        redeemed_qr_count,
    ]


def get_daily_3ds_logs_data(three_ds_logs, status):
    """this function returns the daily 3DS logs data"""
    return list(
        three_ds_logs.filter(
            status=status,
        ).values(date=F("created_date__date"))
        .annotate(Count("id"))
        .order_by("created_date__date")
    )


def get_weekly_3ds_logs_data(three_ds_logs, status):
    """this function returns the weekly 3DS logs data"""
    three_ds_logs = three_ds_logs.filter(
        status=status,
    )
    three_ds_logs_array = []
    for year in sorted(
        set(
            three_ds_logs.annotate(
                year=ExtractYear("created_date")
            ).values_list("year", flat=True)
        ),
    ):
        weekly_data_yearwise = (
            three_ds_logs.filter(created_date__year=str(year))
            .values(date=F("created_date__week"))
            .annotate(Count("id"))
            .order_by("created_date__week")
        )
        for week_data_yearwise in list(weekly_data_yearwise):
            week_data_yearwise["date"] = f'{week_data_yearwise["date"]}/{year}'
        three_ds_logs_array += list(weekly_data_yearwise)
    return three_ds_logs_array


def get_monthly_3ds_logs_data(three_ds_logs, status):
    """this function returns the monthly 3DS logs data"""
    three_ds_logs = three_ds_logs.filter(
        status=status,
    )
    three_ds_logs_array = []
    for year in sorted(
        set(
            three_ds_logs.annotate(
                year=ExtractYear("created_date")
            ).values_list("year", flat=True)
        ),
    ):
        monthly_data_yearwise = (
            three_ds_logs.filter(created_date__year=str(year))
            .values(date=F("created_date__month"))
            .annotate(Count("id"))
            .order_by("created_date__month")
        )
        for month_data_yearwise in list(monthly_data_yearwise):
            month_data_yearwise["date"] = get_month_year_label(
                year, month_data_yearwise["date"]
            )
        three_ds_logs_array += list(monthly_data_yearwise)
    return three_ds_logs_array


def get_3ds_logs_data(type_of_change, three_ds_logs):
    """this function returns 3DS logs data"""
    if type_of_change == "Daily":
        successful_3ds_checks = get_daily_3ds_logs_data(three_ds_logs, "Successful")
        failed_3ds_checks = get_daily_3ds_logs_data(three_ds_logs, "Failed")
    elif type_of_change == "Monthly":
        successful_3ds_checks = get_monthly_3ds_logs_data(three_ds_logs, "Successful")
        failed_3ds_checks = get_monthly_3ds_logs_data(three_ds_logs, "Failed")
    else:
        successful_3ds_checks = get_weekly_3ds_logs_data(three_ds_logs, "Successful")
        failed_3ds_checks = get_weekly_3ds_logs_data(three_ds_logs, "Failed")
    return [
        successful_3ds_checks,
        failed_3ds_checks
    ]


def get_sessions_and_users_data_for_dashboard(type_of_change, sessions, users,is_ocpi):
    """this function generates dahboard data"""

    charging_sessions_count = 0
    user_list_count = 0
    charging_sessions_array = []
    charging_power_array = []
    charging_sales_array = []
    user_list = []
    ratings_data = [[], [], [], [], []]

    def appender(iterator, table):
        charging_sessions_array.append(
            {"date": iterator, "no_of_sessions": len(table)}
        )
        charging_power_array.append(
            {"date": iterator, "power": total_power_calculator(table)}
        )
        charging_sales_array.append(
            {"date": iterator, "sales": total_sales_calculator(table,is_ocpi)}
        )
        table = sorted(table.filter(~Q(rating=0)), key=rating_key_func)

        for key, value in groupby(table, rating_key_func):
            ratings_data[key - 1].append(
                {"date": iterator, "ratings": len(list(value))}
            )

    if type_of_change == "Daily":
        graph_x_axis_lable = "Day's"
        session_days = return_days_from_sessions_dates(sessions)
        for day in session_days:
            session_date = day_month_year_joiner(
                day[DAY_POSITION_IN_DAYS_ARRAY],
                day[MONTH_POSITION_IN_DAYS_ARRAY],
                day[YEAR_POSITION_IN_DAYS_ARRAY],
            )
            filtered_sessions = sessions.filter(
                payment_completed_at__range=[
                    timezone.localtime(
                        datetime.strptime(session_date, "%d/%m/%Y").replace(
                            tzinfo=pytz.UTC
                        )
                    ),
                    timezone.localtime(
                        datetime.strptime(session_date, "%d/%m/%Y").replace(
                            tzinfo=pytz.UTC
                        )
                        + timedelta(hours=23, minutes=59, seconds=59)
                    ),
                ]
            )
            charging_sessions_count += len(filtered_sessions)
            appender(
                session_date,
                filtered_sessions,
            )

        user_created_dates = return_days_from_user_created_dates(users)
        for day in user_created_dates:
            filtered_users = users.filter(
                timestamp__day__exact=day[DAY_POSITION_IN_DAYS_ARRAY],
                timestamp__month__exact=day[MONTH_POSITION_IN_DAYS_ARRAY],
                timestamp__year__exact=day[YEAR_POSITION_IN_DAYS_ARRAY],
            )
            user_list_count += len(filtered_users)
            user_list.append(
                {
                    "date": day_month_year_joiner(
                        day[DAY_POSITION_IN_DAYS_ARRAY],
                        day[MONTH_POSITION_IN_DAYS_ARRAY],
                        day[YEAR_POSITION_IN_DAYS_ARRAY],
                    ),
                    "count": len(filtered_users),
                }
            )
    if type_of_change == "Monthly":
        graph_x_axis_lable = "Months"
        months = return_months_from_sessions_dates(sessions)
        for month in months:
            session_month = (
                "1/"
                + str(month[MONTH_POSITION_IN_MONTHS_ARRAY])
                + "/"
                + str(month[YEAR_POSITION_IN_MONTHS_ARRAY])
            )
            filtered_sessions = sessions.filter(
                payment_completed_at__range=[
                    timezone.localtime(
                        datetime.strptime(session_month, "%d/%m/%Y").replace(
                            tzinfo=pytz.UTC
                        )
                    ),
                    timezone.localtime(
                        datetime.strptime(session_month, "%d/%m/%Y").replace(
                            tzinfo=pytz.UTC
                        )
                        + timedelta(
                            days=days_in_month(
                                month[YEAR_POSITION_IN_MONTHS_ARRAY],
                                month[MONTH_POSITION_IN_MONTHS_ARRAY],
                            )
                            - 1,
                            hours=23,
                            minutes=59,
                            seconds=59,
                        )
                    ),
                ]
            )
            charging_sessions_count += len(filtered_sessions)
            appender(
                day_month_year_joiner(
                    MONTHS_LIST[month[MONTH_POSITION_IN_MONTHS_ARRAY] - 1],
                    month[YEAR_POSITION_IN_MONTHS_ARRAY],
                ),
                filtered_sessions,
            )

        user_created_dates = return_months_from_user_created_dates(users)
        for month in user_created_dates:
            filtered_users = users.filter(
                timestamp__month__exact=month[MONTH_POSITION_IN_MONTHS_ARRAY],
                timestamp__year__exact=month[YEAR_POSITION_IN_MONTHS_ARRAY],
            )
            user_list_count += len(filtered_users)
            user_list.append(
                {
                    "date": day_month_year_joiner(
                        MONTHS_LIST[month[MONTH_POSITION_IN_MONTHS_ARRAY] - 1],
                        month[YEAR_POSITION_IN_MONTHS_ARRAY],
                    ),
                    "count": len(filtered_users),
                }
            )
    if type_of_change == "Weekly":
        graph_x_axis_lable = "Weeks"
        weeks = return_weeks_from_sessions_dates(sessions)
        for week in weeks:
            week_date = datetime.strptime(
                f"{week[YEAR_POSITION_IN_WEEKS_ARRAY]}"
                + "-W"
                + f"{week[WEEK_POSITION_IN_WEEKS_ARRAY]}"
                + "-1",
                "%Y-W%W-%w",
            )
            filtered_sessions = sessions.filter(
                payment_completed_at__range=[
                    timezone.localtime(week_date.replace(tzinfo=pytz.UTC)),
                    timezone.localtime(
                        week_date.replace(tzinfo=pytz.UTC)
                        + timedelta(days=6, hours=23, minutes=59, seconds=59)
                    ),
                ]
            )
            charging_sessions_count += len(filtered_sessions)
            appender(
                str(week_date.day)
                + "/"
                + str(week_date.month)
                + "/"
                + str(week_date.year),
                filtered_sessions,
            )

        user_created_dates = return_weeks_from_user_created_dates(users)
        for week in user_created_dates:
            filtered_users = users.filter(
                timestamp__week__exact=week[WEEK_POSITION_IN_WEEKS_ARRAY],
                timestamp__year__exact=week[YEAR_POSITION_IN_WEEKS_ARRAY],
            )
            user_list_count += len(filtered_users)
            week = datetime.strptime(
                f"{week[YEAR_POSITION_IN_WEEKS_ARRAY]}"
                + "-W"
                + f"{week[WEEK_POSITION_IN_WEEKS_ARRAY]}"
                + "-1",
                "%Y-W%W-%w",
            )
            user_list.append(
                {
                    "date": f"{week.day}/{week.month}/{week.year}",
                    "count": len(filtered_users),
                }
            )
    
    # total user and sessions count
    user_count = user_list_count
    total_charging_sessions = charging_sessions_count
    return [
        ratings_data,
        charging_sessions_array,
        charging_power_array,
        charging_sales_array,
        user_list,
        user_count,
        total_charging_sessions,
        graph_x_axis_lable,
    ]


def stations_area_regions_extractor(ops_region, region, area, station):
    """
    this function returns operation regions ,
    regions and area from stations
    """
    # Side navbar field values are fetched by following logic
    prev_ops_region = None
    prev_region = None
    prev_area = None
    # station_for_filteration = Stations.objects.filter(deleted=NO)
    # cache.set(
    #     "cache_station_for_filteration",
    #     station_for_filteration,
    #     timeout=CACHE_TTL,
    # )

    if "cache_station_for_filteration" in cache:
        # get results from cache
        station_for_filteration = cache.get("cache_station_for_filteration")
    else:
        station_for_filteration = Stations.objects.filter(deleted=NO).only(
            "id", "station_id", "operation_region", "region", "area"
        )
        # station_for_filteration = Stations.objects.filter(deleted=NO)
        cache.set(
            "cache_station_for_filteration",
            station_for_filteration,
            timeout=CACHE_TTL,
        )
    if ops_region and ops_region != "All":
        if "$" in ops_region:
            ops_region = ops_region.replace("$", "&")
        prev_ops_region = ops_region
        station_for_filteration = station_for_filteration.filter(
            operation_region=ops_region
        )
        regions = station_for_filteration.values("region").distinct()
        if "&" in ops_region:
            ops_region = ops_region.replace("&", "$")
    else:
        regions = station_for_filteration.values("region").distinct()
    if region and region != "All":
        if "$" in region:
            region = region.replace("$", "&")
        prev_region = region
        station_for_filteration = station_for_filteration.filter(region=region)
        areas = station_for_filteration.values("area").distinct()
        if "&" in region:
            region = region.replace("&", "$")
    else:
        areas = station_for_filteration.values("area").distinct()
    if area and area != "All":
        if "$" in area:
            area = area.replace("$", "&")
        prev_area = area
        station_for_filteration = station_for_filteration.filter(area=area)

        if "&" in area:
            area = area.replace("&", "$")
    station_for_session_filteration = station_for_filteration
    if station and station != "All":
        station_for_session_filteration = station_for_filteration.filter(
            station_id=station
        )
    return [
        station_for_session_filteration,
        station_for_filteration,
        regions,
        areas,
        prev_ops_region,
        prev_region,
        prev_area,
    ]

# def aggregate_chart_data(chart_data):
#     aggregated = defaultdict(int)
#     for entry in chart_data:
#         aggregated[entry['date']] += entry['no_of_sessions']
#     # Convert back to list of dicts, sorted by date
#     return [{'date': k, 'no_of_sessions': v} for k, v in sorted(aggregated.items(), key=lambda x: datetime.strptime(x[0], "%d/%m/%Y"))]
def aggregate_chart_data(chart_data):
    aggregated = defaultdict(int)
    for entry in chart_data:
        if "no_of_sessions" in entry:
            aggregated[entry['date']] += entry["no_of_sessions"]
            value_key = "no_of_sessions"
        elif "power" in entry:
            aggregated[entry['date']] += entry["power"]
            value_key = "power"
        elif "sales" in entry:
            aggregated[entry['date']] += entry["sales"]
            value_key = "sales"
    
    # Convert back to list of dicts, sorted by date
    return [{'date': k, value_key: v} for k, v in sorted(aggregated.items(), key=lambda x: datetime.strptime(x[0], "%d/%m/%Y"))]

# pylint: disable-msg=too-many-locals
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
def form_dashboard(request):
    """dashboard view"""
    try:
        dashboard_data_days_limit = int(
            filter_function_for_base_configuration(
                DASHBOARD_DATA_DAYS_LIMIT, DEFAULT_DASHBOARD_DATA_DAYS_LIMIT
            )
        )
        from_date = request.GET.get(
            "from_date",
            ((timezone.now() - timedelta(days=dashboard_data_days_limit)).strftime("%d/%m/%Y")),
        )
        if from_date == "":
            from_date = (timezone.now() - timedelta(days=dashboard_data_days_limit)).strftime(
                "%d/%m/%Y"
            )
        to_date = request.GET.get("to_date", "")

        if (
            to_date != ""
            and (
                date_formater_for_frontend_date(to_date)
                - date_formater_for_frontend_date(from_date)
            ).days
            < 0
        ):
            to_date = ""

        current_and_from_date_difference = (
            timezone.now() - date_formater_for_frontend_date(from_date)
        ).days
        if (
            current_and_from_date_difference <= dashboard_data_days_limit
            and to_date == ""
        ):
            to_date = timezone.now().strftime("%d/%m/%Y")

        maximum_to_date = 0

        to_date_and_from_date_diffrence = (
            current_and_from_date_difference
            if to_date == ""
            else (
                date_formater_for_frontend_date(to_date)
                - date_formater_for_frontend_date(from_date)
            ).days
        )
        if to_date_and_from_date_diffrence > dashboard_data_days_limit:
            to_date = (
                date_formater_for_frontend_date(from_date)
                + timedelta(days=dashboard_data_days_limit)
            ).strftime("%d/%m/%Y")
            maximum_to_date = (
                abs(
                    (
                        timezone.now()
                        - date_formater_for_frontend_date(from_date)
                    ).days
                )
                - dashboard_data_days_limit
            )
        elif (
            to_date != ""
            and current_and_from_date_difference > dashboard_data_days_limit
        ):
            maximum_to_date = (
                abs(
                    (
                        timezone.now()
                        - date_formater_for_frontend_date(from_date)
                    ).days
                )
                - dashboard_data_days_limit
            )

        type_of_change = request.GET.get("type_of_change", "Daily")
        ops_region = request.GET.get("ops_region", None)
        region = request.GET.get("region", None)
        area = request.GET.get("area", None)
        station = request.GET.get("station", None)
        date_difference = 0
        # from_date = request.GET.get(
        #     "from_date",
        #     ((timezone.now() - timedelta(days=30)).strftime("%d/%m/%Y")),
        # )
        # to_date = request.GET.get("to_date", "")
        active_chart_tab = request.GET.get("active_chart_tab", "Sales")

        if len(list(dict(request.GET).keys())) > 0:
            query_params_str = list(dict(request.GET).keys())[0]
            if query_params_str == "ops_region":
                region = None
                area = None
                station = None
            elif query_params_str == "region":
                area = None
                station = None
            elif query_params_str == "area":
                station = None

        # logic to extract charging sessions
        (
            station_for_session_filteration,
            station_for_filteration,
            regions,
            areas,
            prev_ops_region,
            prev_region,
            prev_area,
        ) = stations_area_regions_extractor(ops_region, region, area, station)

        station_ids = [
            station.id for station in station_for_session_filteration
        ]

        loyalty_transactions = LoyaltyTransactions.objects.filter(
            ~Q(transaction_time=None),
            station_id_id__in=station_ids,
        )

        if (
            (ops_region and ops_region != "All")
            or (region and region != "All")
            or (area and area != "All")
            or (station and station != "All")
        ):
            charging_sessions = ChargingSession.objects.filter(
                ~Q(payment_completed_at=None),
                station_id_id__in=station_ids,
                paid_status="paid",
            ).only(*COMMON_SESSION_FIELDS, 'total_cost','start_time')

            ocpi_sessions = OCPISessions.objects.filter(
                ~Q(payment_completed_at=None),
                station_id_id__in=station_ids,
                paid_status="paid",
            ).annotate(
                total_cost=F('total_cost_incl'),
                start_time=F('start_datetime'),
            ).only(*COMMON_SESSION_FIELDS)
        else:
            charging_sessions = ChargingSession.objects.filter(
                ~Q(payment_completed_at=None),
                paid_status="paid",
            ).only(*COMMON_SESSION_FIELDS,'total_cost','start_time')

            ocpi_sessions = OCPISessions.objects.filter(
                ~Q(payment_completed_at=None),
                paid_status="paid",
            #)
            #.select_related('location_id')
            ).annotate(
                total_cost=F('total_cost_incl'),
                start_time=F('start_datetime'),
            ).only(*COMMON_SESSION_FIELDS,"total_cost_incl","total_cost_excl","location_id")
            # ocpi_sessions = OCPISessions.objects.annotate(
            #     back_office=F('location_id__evse_id__connector__back_office'),
            #     # region=F('location__location_id')
            # ).annotate(
            #     location_id=Subquery(
            #         Location.objects.extra(
            #             where=[
            #                 "JSON_VALUE(places_json, CONCAT('$.', %s)) = %s"
            #             ],
            #             params=[OuterRef('back_office')]
            #         ).values('id')[:1]
            #     )
            # )
            # data - session
            # place_id = location_id
            # place  location

            # cp - evse
            # location - stations
        #sessions = charging_sessions#.union(ocpi_sessions)
        users = MFGUserEV.objects.filter(~Q(user_email="")).only(
            "id", "timestamp"
        )
        three_ds_logs = ThreeDSCheckLogs.objects.filter()


        if from_date != "":
            filter_start_date = date_formater_for_frontend_date(
                from_date
            )
            charging_sessions = charging_sessions.filter(
                payment_completed_at__gte=filter_start_date
            )
            ocpi_sessions = ocpi_sessions.filter(
                payment_completed_at__gte=filter_start_date
            )
            users = users.filter(
                timestamp__gte=filter_start_date
            )
            loyalty_transactions = loyalty_transactions.filter(
                transaction_time__gte=filter_start_date
            )
            three_ds_logs = three_ds_logs.filter(
                created_date__gte=filter_start_date
            )
        to_date_provided = False
        if to_date != "":
            to_date_provided = True
            fomatted_to_date = date_formater_for_frontend_date(to_date)
            fomatted_to_date = fomatted_to_date + timedelta(days=1)
            charging_sessions = charging_sessions.filter(
                payment_completed_at__lte=fomatted_to_date
            )
            ocpi_sessions = ocpi_sessions.filter(
                payment_completed_at__lte=fomatted_to_date
            )
            users = users.filter(timestamp__lte=fomatted_to_date)
            loyalty_transactions = loyalty_transactions.filter(
                transaction_time__lte=fomatted_to_date
            )
            three_ds_logs = three_ds_logs = three_ds_logs.filter(
                created_date__lte=fomatted_to_date
            )
            formatted_to_date = date_formater_for_frontend_date(to_date)
            date_difference = date_difference_function(from_date,formatted_to_date)

        (
            ratings_data,
            charging_sessions_array,
            charging_power_array,
            charging_sales_array,
            user_list,
            user_count,
            total_charging_sessions,
            graph_x_axis_lable,
        ) = get_sessions_and_users_data_for_dashboard(
            type_of_change,
            charging_sessions,
            users,
            False
        )

        (
            ocpi_ratings_data,
            ocpi_charging_sessions_array,
            ocpi_charging_power_array,
            ocpi_charging_sales_array,
            ocpi_user_list,
            _,
            ocpi_total_charging_sessions,
            _,
        ) = get_sessions_and_users_data_for_dashboard(
            type_of_change,
            ocpi_sessions,
            users,
            True
        )

        # get loaylty data
        (
            purchased_qr_data,
            purchased_qr_count,
            redeemed_qr_data,
            redeemed_qr_count,
        ) = get_loyalty_transaction_data(type_of_change, loyalty_transactions)

        # ratings data
        (
            ratings_count,
            positive_rating_count,
            neutral_rating_count,
            negative_rating_count,
        ) = ratings_counter_function(ratings_data)
        (
            ocpi_ratings_count,
            ocpi_positive_rating_count,
            ocpi_neutral_rating_count,
            ocpi_negative_rating_count,
        ) = ratings_counter_function(ocpi_ratings_data)

        (
            successful_3ds_checks,
            failed_3ds_checks,
        ) = get_3ds_logs_data(type_of_change, three_ds_logs)

        urls = dashboard_url_maker(
            {
                "type_of_change": type_of_change,
                "ops_region": ops_region,
                "region": region,
                "area": area,
                "station": station,
                "from_date": from_date,
                "to_date": to_date,
                "active_chart_tab": active_chart_tab,
            }
        )
        url = urls[0]
        graph_urls = urls[1]

        graph_navigation = [
            {"name": "Sales", "state": ""},
            {"name": "Users", "state": ""},
            {"name": "Ratings", "state": ""},
            {"name": "Loyalty", "state": ""},
            {"name": "3DS", "state": ""},
        ]
        for graph_nav in graph_navigation:
            if active_chart_tab:
                if graph_nav["name"] == active_chart_tab:
                    graph_nav["state"] = "active"
            else:
                graph_navigation[0]["state"] = "active"

        time_difference = 0
        if from_date:
            time_difference = (
                abs(
                    (
                        date_formater_for_frontend_date(from_date)
                        - timezone.now()
                    ).days
                )
                - 1
            )
        # total_ev_users_count = len(
        old_users_session_list = charging_sessions.filter(
            ~Q(user_id__user_email=""),
            user_id__in=users
            ).values_list(
                "user_id"
                ).distinct()
        # )
        new_user_session_list = ocpi_sessions.filter(
            ~Q(user_id__user_email=""), 
            user_id__in=users
            ).values_list(
                "user_id"
                ).distinct()
        
        total_ev_users_count = len(set(old_users_session_list).union(set(new_user_session_list)))
        total_non_ev_users_count = len(users) - total_ev_users_count
        # Pass data to page for render
        context = {
            "to_date_difference_from_current_date": date_difference,
            "to_date_provided": to_date_provided,
            "time_difference": time_difference,
            "chart": graph_navigation,
            "chart_active_tab": active_chart_tab,
            "type_of_changes": ["Daily", "Weekly", "Monthly"],
            "chart_data": sorted(aggregate_chart_data(list(chain(charging_sessions_array, ocpi_charging_sessions_array))), key=lambda s: datetime.strptime(s["date"], "%d/%m/%Y")),
            "power_data": sorted(aggregate_chart_data(list(chain(charging_power_array, ocpi_charging_power_array))), key=lambda s: datetime.strptime(s["date"], "%d/%m/%Y")),
            "total_ev_users_count": total_ev_users_count,
            "total_non_ev_users_count": (total_non_ev_users_count),
            "ratings_data": ratings_data + ocpi_ratings_data,
            "user_list": user_list + ocpi_user_list,
            "sales_data": sorted(aggregate_chart_data(list(chain(charging_sales_array, ocpi_charging_sales_array))), key=lambda s: datetime.strptime(s["date"], "%d/%m/%Y")),
            "ops_regions": station_site_locations_list()[0],
            "regions": regions,
            "area": areas,
            "stations": station_for_filteration,
            "prev_type_of_change": type_of_change,
            "x_axis_lable": graph_x_axis_lable,
            "prev_from_date": from_date,
            "prev_to_date": to_date,
            "prev_station_id": station,
            "prev_area": prev_area,
            "prev_region": prev_region,
            "prev_ops_region": prev_ops_region,
            "updated_url_params": url,
            "graph_urls": graph_urls,
            "usr_count": user_count,
            "total_charging_sessions": total_charging_sessions+ocpi_total_charging_sessions,
            "ratings_count": ratings_count+ocpi_ratings_count,
            "positive_rating_count": positive_rating_count+ocpi_positive_rating_count,
            "neutral_rating_count": neutral_rating_count + ocpi_neutral_rating_count,
            "negative_rating_count": negative_rating_count + ocpi_negative_rating_count,
            "purchased_qr_data": purchased_qr_data,
            "purchased_qr_count": purchased_qr_count if purchased_qr_count else 0,
            "redeemed_qr_data": redeemed_qr_data,
            "redeemed_qr_count": redeemed_qr_count if redeemed_qr_count else 0,
            "successful_3ds_checks": successful_3ds_checks,
            "failed_3ds_checks": failed_3ds_checks,
            "maximum_to_date": maximum_to_date,
            "dashboard_data_days_limit":dashboard_data_days_limit,
            "data": filter_url(
                request.user.role_id.access_content.all(), DASHBOARD_CONST
            ),
        }
        return render(request, "dashboard/dashboard.html", context)
    except Exception:#COMMON_ERRORS:
        traceback.print_exc()
        return render(request, ERROR_TEMPLATE_URL)
