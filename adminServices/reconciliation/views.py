"""reconciliation views"""
# Date - 26/06/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on views(backend
#                       logic) related to reconciliation.
#   Name            - Reconciliation Views
#   Modified by     - Manish Pawar
#   Modified date   - 26/06/2021

# imports required to create views

from types import SimpleNamespace
from datetime import datetime
import json
import zipfile
import pytz
import pandas as pd

from django.shortcuts import render
from django.db.models import Sum
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

# pylint:disable=import-error
from sharedServices.decorators import allowed_users, authenticated_user
from sharedServices.common import (
    pagination_and_filter_func,
    filter_url,
    field_tracking_func,
    export_data_function,
    error_messages_object_formatter,
)
from sharedServices.model_files.station_models import Stations
from sharedServices.model_files.transaction_models import Transactions
from sharedServices.constants import (
    ORDER_ID,
    RECONCILIATION_CONST,
    SETTLEMENT_AMOUNT,
    TRANSACTION_AMOUNT,
    YES,
    GET_METHOD_ALLOWED,
    POST_METHOD_ALLOWED,
    COMMON_ERRORS,
    ERROR_TEMPLATE_URL,
    JSON_ERROR_OBJECT,
)
from adminServices.reconciliation.app_level_constants import (
    LIST_OF_FIELDS_FOR_RECONCILIATION,
    LIST_OF_FIELDS_FOR_RECONCILIATION_EXPORT,
)

UTC = pytz.UTC


# This function is used to filter the transactions
def filter_for_transactions(table, array_of_filters):
    """filter transaction"""
    filter_table = table

    url = ""
    for i in array_of_filters:

        for key_name, key_value in i.items():
            if key_value and key_value[0] and key_value[0] != "All":
                if "__" in key_name:
                    url += f"&{key_value[2]}={key_value[0]}"
                elif key_name == "datetime":
                    str_date = str(key_value[0].date()).split("-")
                    date_in_format = (
                        f"{str_date[1]}/{str_date[2]}/{str_date[0]}"
                    )
                    date = datetime.strptime(date_in_format, "%m/%d/%Y")
                    url += f"&{key_value[2]}={date}"
                else:
                    url += f"&{key_name}={key_value[0]}"
                if key_value[1] == "Equal":
                    filter_table = [
                        filter_key
                        for filter_key in filter_table
                        if filter_key[key_name] == key_value[0]
                    ]
                if key_value[1] == "Greater_than":
                    filter_table = [
                        filter_key
                        for filter_key in filter_table
                        if filter_key[key_name] >= key_value[0]
                    ]
                if key_value[1] == "Less_than":
                    filter_table = [
                        filter_key
                        for filter_key in filter_table
                        if filter_key[key_name] <= key_value[0]
                    ]
    return [filter_table, url]


def dates_retrieve(dates, transactions_all):
    """dates retrieve for transactions"""
    # Looping over uniques dates to fetch the transactions
    # for that particular date.
    for date in dates:
        # Fetching the transaction datewise
        transaction_date_wise = (
            Transactions.objects.filter(created_date=date["created_date"])
            .values("station_id__station_id", "station_id")
            .distinct()
        )
        # Looping over the transactions to separate them
        # according to payment method
        for transaction in transaction_date_wise:
            payment_methods = (
                Transactions.objects.filter(
                    station_id=transaction["station_id"]
                )
                .values("payment_method")
                .distinct()
            )

            # Looping over the payment_methods to calculate
            # transaction amount and
            # settlement amount for particular payment
            for pay_type in payment_methods:
                # Calculating total transaction amount
                # ( for particular payment method on\
                # station )
                station_total_transaction_amount = Transactions.objects.filter(
                    station_id=transaction["station_id"],
                    payment_method=pay_type["payment_method"],
                ).aggregate(Sum("transaction_amount"))
                # Calculating total settlement amount
                # ( for particular payment method on
                # station )
                station_total_settlement_amount = Transactions.objects.filter(
                    station_id=transaction["station_id"],
                    payment_method=pay_type["payment_method"],
                ).aggregate(Sum("settlement_amount"))

                # Comparing the total transaction
                # amount and total settlement amount and
                # assigning
                # status according to results.
                if (
                    station_total_settlement_amount["settlement_amount__sum"]
                    == station_total_transaction_amount[
                        "transaction_amount__sum"
                    ]
                ):
                    status_to_pass = "Exact"
                elif (
                    station_total_settlement_amount["settlement_amount__sum"]
                    < station_total_transaction_amount[
                        "transaction_amount__sum"
                    ]
                ):
                    status_to_pass = "Underpayment"
                else:
                    status_to_pass = "Overpayment"

                # Database call to station to fetch it'd ID and name
                station = Stations.objects.get(id=transaction["station_id"])

                transactions_all.append(
                    {
                        "station_db_id": transaction["station_id"],
                        "date": f"{date['created_date'].date()}",
                        "datetime": date["created_date"],
                        "station_id": station.station_id,
                        "station_name": station.station_name,
                        "payment_method": pay_type["payment_method"],
                        "transaction_total": round(
                            station_total_transaction_amount[
                                "transaction_amount__sum"
                            ],
                            2,
                        ),
                        "settlement_total": round(
                            station_total_settlement_amount[
                                "settlement_amount__sum"
                            ],
                            2,
                        ),
                        "status": status_to_pass,
                    }
                )
    return transactions_all


# This view returns the categorized list of
#   reconciliation status of stations
#   1. List will be categorized with respect to date
#   2. List will be also categorized with respect to
#       payment methods used for transaction
# ( Mastercard, Visa)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=RECONCILIATION_CONST)
def reconciliation_list(request):
    """reconciliation list according station and payment methods"""
    try:
        transactions_all = []
        # Declaration of all query params that helps in
        # filtering data and pagination.
        page_num = request.GET.get("page", 1)
        from_site = request.GET.get("from_site", None)
        to_site = request.GET.get("to_site", None)
        from_date = request.GET.get("from_date", "")
        to_date = request.GET.get("to_date", "")
        payment_method = request.GET.get("payment_method", None)
        status = request.GET.get("status", None)
        do_export = request.GET.get("export", None)
        update_url_param = ""

        # ordering parameters
        order_by_date = request.GET.get("order_by_date", None)
        order_by_station_id = request.GET.get("order_by_station_id", None)

        # Database call to fetch uniques dates from database.
        dates = Transactions.objects.values("created_date").distinct()
        transactions_all = dates_retrieve(dates, transactions_all)
        # Fetching station ids so that we cn use them in
        # "from site" and "to site" dropdown
        # for filteration.
        stations_list = Transactions.objects.values(
            "station_id__station_id", "station_id"
        ).distinct()

        filteration_array = [
            {"station_id": [from_site, "Greater_than"]},
            {"station_id": [to_site, "Less_than"]},
            {"payment_method": [payment_method, "Equal"]},
            {"status": [status, "Equal"]},
        ]
        if from_date != "":
            if len(from_date) > 10:
                str_date = from_date[:10].split("-")
                from_date = f"{str_date[1]}/{str_date[2]}/{str_date[0]}"
            filteration_array.append(
                {
                    "datetime": [
                        UTC.localize(datetime.strptime(from_date, "%m/%d/%Y")),
                        "Greater_than",
                        "from_date",
                    ]
                }
            )
        if to_date != "":
            if len(to_date) > 10:
                str_date = to_date[:10].split("-")
                to_date = f"{str_date[1]}/{str_date[2]}/{str_date[0]}"
            filteration_array.append(
                {
                    "datetime": [
                        UTC.localize(datetime.strptime(to_date, "%m/%d/%Y")),
                        "Less_than",
                        "to_date",
                    ]
                }
            )

        # All the filters are below. Called through the common function
        filtered_transactions = filter_for_transactions(
            transactions_all, filteration_array
        )

        # End of filters
        transactions_all = filtered_transactions[0]
        update_url_param = filtered_transactions[1]
        # Pagination function (which is common throughout the project)
        filtered_data_reconcile = pagination_and_filter_func(
            page_num, transactions_all, []
        )
        paginated_page = filtered_data_reconcile["filtered_table"]

        # Calculating total transaction amount and
        # settlement amount of all transaction
        # without any categoriztion.
        total_transaction_amount = Transactions.objects.aggregate(
            Sum("transaction_amount")
        )
        total_settlement_amount = Transactions.objects.aggregate(
            Sum("settlement_amount")
        )

        # If user clicked on export then this view will
        # return the sheet in response which
        # will be downloaded
        # automatically onec clicked by user.
        if do_export == YES:
            response_op = export_data_function(
                transactions_all,
                LIST_OF_FIELDS_FOR_RECONCILIATION,
                [
                    "date",
                    "station_id",
                    "station_name",
                    "payment_method",
                    "transaction_total",
                    "settlement_total",
                    "status",
                ],
                "ReconciliationSummary",
            )
            if response_op:
                return response_op

        # Here filter_url() function is used to filter
        # navbar elements so that we can render
        # only those navbar tabs
        # to which logged in user have access.
        if (
            total_transaction_amount["transaction_amount__sum"] is None
            or total_settlement_amount["settlement_amount__sum"] is None
        ):
            total_transaction_amount["transaction_amount__sum"] = 0
            total_settlement_amount["settlement_amount__sum"] = 0
        url_data = filter_url(
            request.user.role_id.access_content.all(), RECONCILIATION_CONST
        )
        context = {
            "stations": stations_list,
            "transactions": paginated_page,
            "Total_transactions": len(transactions_all),
            "Total_transaction_amount": round(
                total_transaction_amount["transaction_amount__sum"], 2
            ),
            "prev_from_site": from_site,
            "prev_to_site": to_site,
            "prev_from_date": from_date,
            "prev_to_date": to_date,
            "prev_payment": payment_method,
            "prev_status": status,
            "prev_order_by_date": order_by_date,
            "prev_order_by_station_id": order_by_station_id,
            "status_list": ["All", "Exact", "Overpayment", "Underpayment"],
            "payment_options": ["All", "Visa", "MasterCard"],
            "Total_settlement": round(
                total_settlement_amount["settlement_amount__sum"], 2
            ),
            "data_count": filtered_data_reconcile["data_count"],
            "first_data_number": filtered_data_reconcile[
                "first_record_number"
            ],
            "last_data_number": filtered_data_reconcile["last_record_number"],
            "update_url_param": update_url_param
            + filtered_data_reconcile["url"],
            "pagination_num_list": filtered_data_reconcile["number_list"],
            "current_page": int(page_num),
            "prev": filtered_data_reconcile["prev_page"],
            "next": filtered_data_reconcile["next_page"],
            "data": url_data,
        }
        return render(
            request, "reconciliation/reconciliation_list.html", context=context
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


# This View will be called with the help of
# ajax to import sheet into the backend
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
def import_reconciliation_data(request):
    """import reconciliation data"""
    try:
        # Post method to make queries securely.
        if request.method == "POST":

            # Used pandas library to decode the sheet coming from frontend.
            try:
                xls = pd.ExcelFile(request.body, engine="openpyxl")
            except zipfile.BadZipFile:
                response_op = {
                    "status": False,
                    "message": "Please provide excel sheet.",
                }
                return JsonResponse(response_op)

            # Rading the sheet and defining the coolumns that we required
            # to perform queries.
            try:
                sheet = pd.read_excel(xls, "reconciliation_Worldpay-Acquiri")
            except (AttributeError, KeyError):
                response_op = {
                    "status": False,
                    "message": "Sheet must include\
                        'reconciliation_Worldpay-Acquiri' tab",
                }
                return JsonResponse(response_op)

            field_tracker = []
            field_tracker = field_tracking_func(
                [
                    ORDER_ID,
                    SETTLEMENT_AMOUNT,
                    TRANSACTION_AMOUNT,
                    "Timestamp",
                    "Payment method",
                    "Issuing bank",
                ],
                sheet,
            )
            if len(field_tracker) > 0:
                response_op = {
                    "status": True,
                    "fields": True,
                    "data": field_tracker,
                }
                return JsonResponse(response_op)
            # Fetching order_ids from sheet so that we can check the
            # discrepancy for the particular transaction whose order_id
            # is one of the element in order_ids
            sheet_order_ids = sheet[ORDER_ID]
            errors = []
            # Looping over order_ids.
            for count, sheet_order_id in enumerate(sheet_order_ids):
                # Fetching particular transaction with the help of order_id
                status_to_upload = "-"
                if (
                    not pd.isna(sheet[ORDER_ID][count])
                    and not pd.isna(sheet[TRANSACTION_AMOUNT][count])
                    and not pd.isna(sheet[SETTLEMENT_AMOUNT][count])
                ):

                    filter_transaction = Transactions.objects.filter(
                        order_id=sheet_order_id
                    )

                    # Condition to check whether transaction with
                    # order_id present in database or not.
                    if filter_transaction.count() > 0:
                        sheet_row = ""

                        # Getting a row in sheet with respect to
                        # current order_id position.
                        if count == 0:
                            sheet_row = sheet[:1]
                        else:
                            sheet_row = sheet[count : (count + 1)]

                        # Calculating discrepancy in transaction
                        # amount and settlement
                        # amount and then assigning the
                        # status according to results.
                        if (
                            sheet_row[SETTLEMENT_AMOUNT][count]
                            == sheet_row[TRANSACTION_AMOUNT][count]
                        ):
                            status_to_upload = "Exact"
                        elif (
                            sheet_row[SETTLEMENT_AMOUNT][count]
                            < sheet_row[TRANSACTION_AMOUNT][count]
                        ):
                            status_to_upload = "Underpayment"
                        else:
                            status_to_upload = "Overpayment"

                        transaction_datetime = sheet_row["Timestamp"][count]
                        datetim = datetim.replace(
                            hour=0, minute=0, second=0, microsecond=0
                        )

                        # Updating the discrepancy status of transaction
                        filter_transaction.update(
                            settlement_amount=sheet_row[SETTLEMENT_AMOUNT][
                                count
                            ],
                            payment_method=sheet_row["Payment method"][count],
                            issuing_bank=sheet_row["Issuing bank"][count],
                            status=status_to_upload,
                            transaction_timestamp=sheet_row["Timestamp"][
                                count
                            ],
                            created_date=transaction_datetime,
                            updated_date=timezone.localtime(timezone.now()),
                        )
                else:
                    errors.append(
                        error_messages_object_formatter(
                            [ORDER_ID, "Transaction date"],
                            [
                                f"{sheet['Order ID'][count]}",
                                f"{sheet['Transaction date'][count].date()}",
                            ],
                        )
                    )

            # Response to request.
            response_op = {"status": True, "fields": False, "data": errors}
            return JsonResponse(response_op)
        return JsonResponse("Request method improper")
    except COMMON_ERRORS:
        return JSON_ERROR_OBJECT


# This view will be called in ajax to submit comment for
# the particular transaction.


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
def add_comment_to_transaction_view(request):
    """add comment to transaction"""
    # Post request to make comment securely.
    try:
        if request.method == "POST":
            post_data_from_front_end = json.loads(
                request.POST["getdata"],
                object_hook=lambda d: SimpleNamespace(**d),
            )

            # Database call to add or update the comment.
            Transactions.objects.filter(
                id__exact=int(post_data_from_front_end.transaction_id)
            ).update(comments=post_data_from_front_end.comment)

            response_op = {"status": 1, "message": "ok"}
            return JsonResponse(response_op)
        return JsonResponse("Request method improper")
    except COMMON_ERRORS:
        return JSON_ERROR_OBJECT


# This view returns the discrepancy status of all transactions
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=RECONCILIATION_CONST)
def reconciliation_transaction_list(request):
    """reconciliation all transaction list"""
    try:
        # Fetching all the transactions.
        transactions = Transactions.objects.values(
            "id",
            "order_id",
            "transaction_timestamp",
            "station_id__id",
            "station_id__station_id",
            "station_id__station_name",
            "payment_method",
            "transaction_amount",
            "settlement_amount",
            "status",
            "comments",
        )

        # Fetching station ids so that we cn use them
        #  in "from site" and "to site"
        # dropdown for filteration.
        station_list = Transactions.objects.values(
            "station_id__station_id", "station_id"
        ).distinct()

        # Declaration of all query params that helps
        # in filtering data and pagination.
        page_num = request.GET.get("page", 1)
        from_site = request.GET.get("from_site", None)

        to_site = request.GET.get("to_site", None)
        from_date = request.GET.get("from_date", None)

        to_date = request.GET.get("to_date", None)
        payment_method = request.GET.get("payment_method", None)

        status = request.GET.get("status", None)
        do_export = request.GET.get("export", None)

        update_url_param = ""
        # All the filters are below. Called through the common function
        filteration_array = [
            {
                "station_id__station_id": [
                    from_site,
                    "Greater_than",
                    "from_site",
                ]
            },
            {"station_id__station_id": [to_site, "Less_than", "to_site"]},
            {"payment_method": [payment_method, "Equal"]},
            {"status": [status, "Equal"]},
        ]
        if from_date:
            if len(from_date) > 10:
                str_date = from_date[:10].split("-")
                from_date = f"{str_date[1]}/{str_date[2]}/{str_date[0]}"
            filteration_array.append(
                {
                    "transaction_timestamp": [
                        UTC.localize(datetime.strptime(from_date, "%m/%d/%Y")),
                        "Greater_than",
                        "from_date",
                    ]
                }
            )
        if to_date:
            if len(to_date) > 10:
                str_date = to_date[:10].split("-")
                to_date = f"{str_date[1]}/{str_date[2]}/{str_date[0]}"
            filteration_array.append(
                {
                    "transaction_timestamp": [
                        UTC.localize(datetime.strptime(to_date, "%m/%d/%Y")),
                        "Less_than",
                        "to_date",
                    ]
                }
            )

        filtered_transactions = filter_for_transactions(
            transactions, filteration_array
        )

        transactions = filtered_transactions[0]
        update_url_param = filtered_transactions[1]
        # Calculating total transaction amount and settlement amount of
        # all transaction without any categoriztion.
        total_transaction_amount = Transactions.objects.aggregate(
            Sum("transaction_amount")
        )
        total_settlement_amount = Transactions.objects.aggregate(
            Sum("settlement_amount")
        )

        # Pagination function (which is common throughout the project)
        filtered_data_reconcile = pagination_and_filter_func(
            page_num, transactions, []
        )
        paginated_page = filtered_data_reconcile["filtered_table"]
        if from_date is None:
            from_date = ""
        if to_date is None:
            to_date = ""

        # If user clicked on export then this view will return the sheet in
        # response which will be downloaded
        # automatically onec clicked by user.
        if do_export == YES:
            response_op = export_data_function(
                transactions,
                LIST_OF_FIELDS_FOR_RECONCILIATION_EXPORT,
                [
                    "order_id",
                    "transaction_timestamp",
                    "station_id__station_id",
                    "station_id__station_name",
                    "payment_method",
                    "transaction_amount",
                    "settlement_amount",
                    "status",
                ],
                "ReconciliationTransactions",
            )
            if response_op:
                return response_op

        # Here filter_url() function is used to filter navbar
        # elements so that we can render only those navbar tabs
        # to which logged in user have access.
        url_data = filter_url(
            request.user.role_id.access_content.all(), RECONCILIATION_CONST
        )
        if (
            total_settlement_amount["settlement_amount__sum"] is None
            and total_transaction_amount["transaction_amount__sum"] is None
        ):
            total_transaction_amount["transaction_amount__sum"] = 0
            total_settlement_amount["settlement_amount__sum"] = 0
        return render(
            request,
            "reconciliation/reconciliation__transaction_list.html",
            context={
                "stations": station_list,
                "transactions": paginated_page,
                "Total_transactions": filtered_data_reconcile["data_count"],
                "Total_transaction_amount": round(
                    total_transaction_amount["transaction_amount__sum"], 2
                ),
                "Total_settlement": round(
                    total_settlement_amount["settlement_amount__sum"], 2
                ),
                "prev_from_date": from_date,
                "prev_to_date": to_date,
                "prev_from_site": from_site,
                "prev_to_site": to_site,
                "prev_payment": payment_method,
                "prev_status": status,
                "status_list": ["All", "Exact", "Overpayment", "Underpayment"],
                "payment_options": ["All", "Visa", "MasterCard"],
                "data_count": filtered_data_reconcile["data_count"],
                "first_data_number": filtered_data_reconcile[
                    "first_record_number"
                ],
                "last_data_number": filtered_data_reconcile[
                    "last_record_number"
                ],
                "update_url_param": update_url_param
                + filtered_data_reconcile["url"],
                "pagination_num_list": filtered_data_reconcile["number_list"],
                "current_page": int(page_num),
                "prev": filtered_data_reconcile["prev_page"],
                "next": filtered_data_reconcile["next_page"],
                "data": url_data,
            },
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


# This view returns the discrepancy status of
#  all transaction for a particular station
# on a particular
# date for a particular payment method.
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=RECONCILIATION_CONST)
def reconciliation_list_for_station(request, station_pk):
    """station wise reconciliation list"""
    try:
        # Fectching query params required to fetch the transaction
        # for a particular station on a particular  date for a
        # particular payment method.
        payment_method = request.GET.get("payment_type")
        date_to_filter = request.GET.get("date")

        page_num = request.GET.get("page", 1)

        # Fetching the station for which we have to fetch the transactions
        station = Stations.objects.get(id=station_pk)

        # Filtering transaction to get the transaction
        # for a particular station on a particular
        # date for a particular payment method.
        transactions = Transactions.objects.filter(
            station_id=station_pk,
            payment_method=payment_method,
            created_date=date_to_filter,
        ).values(
            "id",
            "order_id",
            "transaction_timestamp",
            "transaction_amount",
            "settlement_amount",
            "status",
            "comments",
        )

        # Pagination function (which is common throughout the project)
        filtered_data_reconcile = pagination_and_filter_func(
            page_num, transactions, []
        )
        paginated_page = filtered_data_reconcile["filtered_table"]

        # Calculating total transaction amount and
        # settlement amount or a particular
        # station on a particular
        # date for a particular payment method.
        total_transaction_amount = transactions.aggregate(
            Sum("transaction_amount")
        )
        total_settlement_amount = transactions.aggregate(
            Sum("settlement_amount")
        )

        # Here filter_url() function is used to filter navbar
        # elements so that we can
        # render only those navbar tabs
        # to which logged in user have access.
        url_data = filter_url(
            request.user.role_id.access_content.all(), RECONCILIATION_CONST
        )
        context = {
            "station": station,
            "date": date_to_filter,
            "payment_method": payment_method,
            "transactions": paginated_page,
            "Total_transactions": filtered_data_reconcile["data_count"],
            "status_list": ["All", "Exact", "Overpayment", "Underpayment"],
            "payment_options": ["All", "Visa", "MasterCard"],
            "data_count": filtered_data_reconcile["data_count"],
            "first_data_number": filtered_data_reconcile[
                "first_record_number"
            ],
            "last_data_number": filtered_data_reconcile["last_record_number"],
            "pagination_num_list": filtered_data_reconcile["number_list"],
            "current_page": int(page_num),
            "prev": filtered_data_reconcile["prev_page"],
            "next": filtered_data_reconcile["next_page"],
            "Total_transaction_amount": round(
                total_transaction_amount["transaction_amount__sum"], 2
            ),
            "Total_settlement": round(
                total_settlement_amount["settlement_amount__sum"], 2
            ),
            "data": url_data,
        }
        return render(
            request,
            "reconciliation/reconciliation_fromstations.html",
            context=context,
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)


# This view is used to return the details of transaction.
@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=RECONCILIATION_CONST)
def transaction_details(request, transaction_pk):
    """transaction detail view"""
    try:
        # Fetching the particular transction with
        # respect to transaction_pk which is
        # the transaction id sent from frontend request.
        transaction = Transactions.objects.filter(
            id__exact=transaction_pk
        ).values(
            "id",
            "order_id",
            "transaction_timestamp",
            "station_id__station_id",
            "station_id__station_name",
            "transaction_source",
            "payment_method",
            "transaction_amount",
            "settlement_amount",
            "status",
            "issuing_bank",
            "network",
            "transaction_currency",
            "comments",
        )

        # Here filter_url() function is used to filter
        # navbar elements so that we can
        # render only those navbar tabs to which
        # logged in user have access.
        url_data = filter_url(
            request.user.role_id.access_content.all(), RECONCILIATION_CONST
        )
        return render(
            request,
            "reconciliation/transaction_details.html",
            context={"transaction": transaction.first(), "data": url_data},
        )
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)
