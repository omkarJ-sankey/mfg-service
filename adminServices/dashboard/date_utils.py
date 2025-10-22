"""dashboard dateutils"""
from datetime import datetime
from django.db.models.functions import (
    ExtractMonth,
    ExtractWeek,
    ExtractYear,
    ExtractDay,
)

# pylint:disable=import-error
from .app_level_constants import (
    DAY_POSITION_IN_DAYS_ARRAY,
    MONTH_POSITION_IN_DAYS_ARRAY,
    YEAR_POSITION_IN_DAYS_ARRAY,
    WEEK_POSITION_IN_WEEKS_ARRAY,
    YEAR_POSITION_IN_WEEKS_ARRAY,
    MONTH_POSITION_IN_MONTHS_ARRAY,
    YEAR_POSITION_IN_MONTHS_ARRAY,
)

from .app_level_constants import DAYS_IN_MONTH


def return_months_from_sessions_dates(sessions):
    """this function returns list of months from charging_sessions
    payment_completed_at dates"""
    months = [
        [month, year]
        for year in sessions.filter(session_status="completed")
        .annotate(year=ExtractYear("payment_completed_at"))
        .values_list("year", flat=True)
        .distinct()
        for month in sessions.filter(
            payment_completed_at__year__exact=year, session_status="completed"
        )
        .annotate(month=ExtractMonth("payment_completed_at"))
        .values_list("month", flat=True)
        .distinct()
    ]
    return sorted(
        months,
        key=lambda month: datetime.strptime(
            (
                "1"
                + "/"
                + str(month[MONTH_POSITION_IN_MONTHS_ARRAY])
                + "/"
                + str(month[YEAR_POSITION_IN_MONTHS_ARRAY])
            ),
            "%d/%m/%Y",
        ),
    )


def return_days_from_sessions_dates(sessions):
    """this function returns list of days from charging_sessions
    payment_completed_at dates"""
    days = [
        [day, month, year]
        for year in sessions.filter(session_status="completed")
        .annotate(year=ExtractYear("payment_completed_at"))
        .values_list("year", flat=True)
        .distinct()
        for month in sessions.filter(
            payment_completed_at__year__exact=year, session_status="completed"
        )
        .annotate(month=ExtractMonth("payment_completed_at"))
        .values_list("month", flat=True)
        .distinct()
        for day in sessions.filter(
            payment_completed_at__month__exact=month,
            payment_completed_at__year__exact=year,
            session_status="completed",
        )
        .annotate(day=ExtractDay("payment_completed_at"))
        .values_list("day", flat=True)
        .distinct()
    ]
    return sorted(
        days,
        key=lambda day: datetime.strptime(
            (
                str(day[DAY_POSITION_IN_DAYS_ARRAY])
                + "/"
                + str(day[MONTH_POSITION_IN_DAYS_ARRAY])
                + "/"
                + str(day[YEAR_POSITION_IN_DAYS_ARRAY])
            ),
            "%d/%m/%Y",
        ),
    )


def return_weeks_from_sessions_dates(sessions):
    """this function returns list of weeks from charging_sessions
    payment_completed_at dates"""
    weeks = [
        [week, year]
        for year in sessions.filter(session_status="completed")
        .annotate(year=ExtractYear("payment_completed_at"))
        .values_list("year", flat=True)
        .distinct()
        for week in sessions.filter(
            payment_completed_at__year__exact=year, session_status="completed"
        )
        .annotate(week=ExtractWeek("payment_completed_at"))
        .values_list("week", flat=True)
        .distinct()
    ]
    return sorted(
        weeks,
        key=lambda week: datetime.strptime(
            f"{week[YEAR_POSITION_IN_WEEKS_ARRAY]}"
            + "-W"
            + f"{week[WEEK_POSITION_IN_WEEKS_ARRAY]}"
            + "-1",
            "%Y-W%W-%w",
        ),
    )


def return_months_from_user_created_dates(users):
    """this function returns list of months from user created dates"""
    months = [
        [month, year]
        for year in users.filter()
        .annotate(year=ExtractYear("timestamp"))
        .values_list("year", flat=True)
        .distinct()
        for month in users.filter(timestamp__year__exact=year)
        .annotate(month=ExtractMonth("timestamp"))
        .values_list("month", flat=True)
        .distinct()
    ]
    return sorted(
        months,
        key=lambda month: datetime.strptime(
            (
                "1"
                + "/"
                + str(month[MONTH_POSITION_IN_MONTHS_ARRAY])
                + "/"
                + str(month[YEAR_POSITION_IN_MONTHS_ARRAY])
            ),
            "%d/%m/%Y",
        ),
    )


def return_days_from_user_created_dates(users):
    """this function returns list of days from user created dates"""
    days = [
        [day, month, year]
        for year in users.filter()
        .annotate(year=ExtractYear("timestamp"))
        .values_list("year", flat=True)
        .distinct()
        for month in users.filter(timestamp__year__exact=year)
        .annotate(month=ExtractMonth("timestamp"))
        .values_list("month", flat=True)
        .distinct()
        for day in users.filter(
            timestamp__month__exact=month,
            timestamp__year__exact=year,
        )
        .annotate(day=ExtractDay("timestamp"))
        .values_list("day", flat=True)
        .distinct()
    ]
    return sorted(
        days,
        key=lambda day: datetime.strptime(
            (
                str(day[DAY_POSITION_IN_DAYS_ARRAY])
                + "/"
                + str(day[MONTH_POSITION_IN_DAYS_ARRAY])
                + "/"
                + str(day[YEAR_POSITION_IN_DAYS_ARRAY])
            ),
            "%d/%m/%Y",
        ),
    )


def return_weeks_from_user_created_dates(users):
    """this function returns list of weeks from user created dates"""
    weeks = [
        [week, year]
        for year in users.filter()
        .annotate(year=ExtractYear("timestamp"))
        .values_list("year", flat=True)
        .distinct()
        for week in users.filter(
            timestamp__year__exact=year,
        )
        .annotate(week=ExtractWeek("timestamp"))
        .values_list("week", flat=True)
        .distinct()
    ]
    return sorted(
        weeks,
        key=lambda week: datetime.strptime(
            f"{week[YEAR_POSITION_IN_WEEKS_ARRAY]}"
            + "-W"
            + f"{week[WEEK_POSITION_IN_WEEKS_ARRAY]}"
            + "-1",
            "%Y-W%W-%w",
        ),
    )


def _is_leap(year):
    "year -> 1 if leap year, else 0."
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def days_in_month(year, month):
    "year, month -> number of days in that month in that year."
    try:
        if not (1 <= month <= 12):
            raise ValueError("Month must be between 1 and 12 inclusive.")
        
        if month == 2 and _is_leap(year):
            return 29
        
        return DAYS_IN_MONTH[month]
    except KeyError:
        # Handle the case where DAYS_IN_MONTH does not have an entry for the given month
        raise ValueError("Invalid month") from None
    # assert 1 <= month <= 12, month
    # if month == 2 and _is_leap(year):
    #     return 29
    # return DAYS_IN_MONTH[month]
