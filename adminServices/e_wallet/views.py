"""gift card views"""
# Date - 11/08/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file contains gift card views.
#   Name            - Gift card views
#   Modified by     - Manish Pawar
#   Modified date   - 30/11/2022


# These are all the imports that we are exporting from
# different module's from project or library.
import json
import concurrent.futures
import threading
from decouple import config
from cryptography.fernet import Fernet

from django.shortcuts import render, redirect
from django.views.decorators.http import require_http_methods
from django.http import HttpResponse, JsonResponse
from django.db.models import Q
from django.contrib import messages

# pylint:disable=import-error
from sharedServices.models import (
    TransactionsTracker,
    MFGUserEV,
    Profile,
    RoleAccessTypes,
    BaseConfigurations,
)
from sharedServices.decorators import allowed_users, authenticated_user
from sharedServices.common_audit_trail_functions import (
    audit_data_formatter,
    add_audit_data,
)
from sharedServices.gift_card_common_functions import (
    create_customer_gift_card
)
from sharedServices.constants import (
    GET_METHOD_ALLOWED,
    POST_METHOD_ALLOWED,
    EWALLET,
    AUDIT_ADD_CONSTANT,
    AUDIT_UPDATE_CONSTANT,
    YES,
    NO,
    POST_REQUEST,
    COMMON_ERRORS,
    ERROR_TEMPLATE_URL
)
from sharedServices.common import (
    date_formater_for_frontend_date,
    filter_url,
    order_by_function,
    pagination_and_filter_func,
    hasher,
    date_difference_function,
    search_validator,
)
from sharedServices.payments_helper_function import (
    make_request,
)
from .helper import validate_form, get_user_wallet_max
from .handle_gift_cards import (
    gift_card_activity_handler,
    get_wallet_amount_details_for_user,
)
from .app_level_constants import PROCESSED_BY_ADMIN


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=EWALLET)
def wallet(request):
    """wallet transactions list function"""
    page_num = request.GET.get("page", 1)
    search = request.GET.get("search", "")
    search = search_validator(search, "search and email accepted")
    role = request.GET.get("role_id", None)
    withdrawn_status = request.GET.get("is_withdrawn", None)
    from_date = request.GET.get("from_date", "")
    to_date = request.GET.get("to_date", "")
    date_difference = 0
    # Sorting parameters
    order_by_receiver = request.GET.get("order_by_receiver", None)
    order_by_assigned = request.GET.get("order_by_assigned", None)
    order_by_role = request.GET.get("order_by_role", None)
    order_by_amount = request.GET.get("order_by_amount", None)
    page_num = int(page_num)
    updated_url = ""
    filter_user_management = [
        {
            "search": search,
            "search_array": [
                "user_id__username__icontains",
                "transaction_amount__icontains",
                "driivz_account_number__icontains",
            ],
        },
        {"is_withdrawn": withdrawn_status},
        {"assigned_by__role_id__role_name": role},
    ]
    transaction_details = TransactionsTracker.objects.filter(
        reference_current_status="Successful", processed_by=PROCESSED_BY_ADMIN
    ).order_by("-id")
    if from_date:
        transaction_details = transaction_details.filter(
            created_date__gte=date_formater_for_frontend_date(from_date)
        )
        updated_url += f"&from_date={from_date}"
    if to_date:
        transaction_details = transaction_details.filter(
            created_date__lte=date_formater_for_frontend_date(to_date)
        )
        updated_url += f"&to_date={to_date}"
        formatted_to_date = date_formater_for_frontend_date(to_date)
        date_difference = date_difference_function(from_date,formatted_to_date)
    ordered_transaction = order_by_function(
        transaction_details,
        [
            {"user_id__username": ["order_by_receiver", order_by_receiver]},
            {
                "assigned_by__full_name": [
                    "order_by_assigned",
                    order_by_assigned,
                ]
            },
            {
                "assigned_by__role_id__role_name": [
                    "order_by_role",
                    order_by_role,
                ]
            },
            {"transaction_amount": ["order_by_amount", order_by_amount]},
        ],
    )
    filtered_data = pagination_and_filter_func(
        page_num, ordered_transaction["ordered_table"], filter_user_management
    )
    total_amount = sum(
        [
            transaction.transaction_amount
            for transaction in filtered_data["filtered_table_for_export"]
        ]
    )

    total_withdrawn_amount = sum(
        [
            transaction.transaction_amount
            for transaction in filtered_data["filtered_table_for_export"]
            if transaction.is_withdrawn == YES
        ]
    )
    roles = RoleAccessTypes.objects.all()
    context = {
        "to_date_difference_from_current_date": date_difference,
        "data": filter_url(request.user.role_id.access_content.all(), EWALLET),
        "transaction_data": filtered_data["filtered_table"],
        "data_count": filtered_data["data_count"],
        "next": filtered_data["next_page"],
        "first_data_number": filtered_data["first_record_number"],
        "last_data_number": filtered_data["last_record_number"],
        "update_url_param": filtered_data["url"]
        + ordered_transaction["url"]
        + updated_url,
        "pagination_num_list": filtered_data["number_list"],
        "current_page": int(page_num),
        "prev": filtered_data["prev_page"],
        "prev_search": search,
        "prev_role": role,
        "prev_withdrawn_status": withdrawn_status,
        "prev_from_date": from_date,
        "prev_to_date": to_date,
        "total_amount": total_amount / 100,
        "total_vouchers": len(filtered_data["filtered_table_for_export"]),
        "total_withdrawn_amount": total_withdrawn_amount / 100,
        "order_by_receiver": order_by_receiver,
        "order_by_assigned": order_by_assigned,
        "order_by_role": order_by_role,
        "order_by_amount": order_by_amount,
        "roles": roles,
        "withdrawn_statuses": [YES, NO],
    }
    return render(request, "e_wallet/ewallet.html", context)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=EWALLET)
def wallet_details(request, transaction_id):
    """get wallet transaction details"""
    data = None
    try:
        data = (
            TransactionsTracker.objects.filter(payment_id=transaction_id)
            .values(
                "id",
                "assigned_by__full_name",
                "assigned_by__role_id__role_name",
                "assigned_by__id",
                "created_date",
                "user_id__username",
                "comments",
                "transaction_amount",
                "driivz_account_number",
                "payment_id",
                "user_updated_balance",
                "is_withdrawn",
                "updated_by",
                "updated_date",
            )
            .first()
        )
    except (KeyError, AttributeError):
        data = {}
    context = {
        "user_data": data,
        "data": filter_url(request.user.role_id.access_content.all(), EWALLET),
    }
    return render(request, "e_wallet/ewallet_details.html", context)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=EWALLET)
def list_email(request):
    """list all wallet transactions"""
    if request.method == "GET":
        search = request.GET.get("search", None)
        payload = []
        if search:
            user_data = MFGUserEV.objects.filter(
                user_email=hasher(search)
            ).first()
            if user_data:
                payload.append(
                    {
                        "user_id": user_data.id,
                        "username": user_data.username,
                        "email": user_data.get_dec_email(),
                    }
                )
        return JsonResponse({"data": payload})


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=EWALLET)
def get_receiver_data(request):
    """get user driivz_account_number"""
    if request.method == "GET":
        user_id = request.GET.get("user_id")
        user_data = {"driivz_account_number": None}
        if user_id:
            try:
                user_data = Profile.objects.filter(
                    user=MFGUserEV.objects.filter(id=user_id).first()
                ).first()
                user_data = {
                    "driivz_account_number": user_data.driivz_account_number
                }
            except (KeyError, AttributeError):
                user_data = {"driivz_account_number": None}
        return JsonResponse(user_data)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=EWALLET)
def assign_amount(request):
    """add new user"""
    if request.method == "POST":
        user = None
        user_id = None
        description = None
        amount = None
        data = json.loads(request.body.decode("utf-8"))
        try:
            user_id = data["userId"]
            description = data["description"]
            amount = float(data["amount"])
            expiry_days = data["expiryDays"]
        except KeyError:
            return HttpResponse(status=400)

        error, is_valid = validate_form(data)
        if not is_valid:
            return HttpResponse(error, status=400)
        try:
            if amount <= 0:
                return HttpResponse(
                    "Amount must be greater than 0", status=400
                )
            user = MFGUserEV.objects.filter(id=user_id).first()
            profile = Profile.objects.filter(user_id=user_id).first()
            if profile.driivz_account_number is None:
                return HttpResponse("Driivz id not found", status=404)
            pay_body = {
                "amount_money": {
                    "amount": amount,
                    "currency": config("DJANGO_APP_PAYMENT_CURRENCY"),
                },
                "description": description,
            }
            (
                monthly_vouchers_exceed,
                yearly_vouchers_exceed,
            ) = get_user_wallet_max(user.id)

            if monthly_vouchers_exceed:
                return HttpResponse(
                    "Monthly voucher limit exceeded", status=400
                )

            if yearly_vouchers_exceed:
                return HttpResponse(
                    "Yearly voucher limit exceeded", status=400
                )

            max_amount_for_voucher = BaseConfigurations.objects.filter(
                base_configuration_key="max_amount_for_voucher"
            ).first()
            if max_amount_for_voucher:
                max_amount_for_voucher = int(
                    max_amount_for_voucher.base_configuration_value
                )
            else:
                max_amount_for_voucher = 10

            if amount > max_amount_for_voucher:
                return HttpResponse(
                    f"Can not add amount more than {max_amount_for_voucher} "
                    + "GBP in single voucher",
                    status=400,
                )
            response = gift_card_activity_handler(
                user, profile, amount, pay_body, request.user, expiry_days
            )
            if response["status"]:
                wallet_transaction = TransactionsTracker.objects.filter(
                    payment_id=response["payment_id"]
                ).first()
                if wallet_transaction:
                    new_data = audit_data_formatter(
                        EWALLET, wallet_transaction.id
                    )
                    add_audit_data(
                        request.user,
                        (
                            str(wallet_transaction.user_id.username)
                            + ", "
                            + str(wallet_transaction.driivz_account_number)
                        ),
                        f"{EWALLET}-{wallet_transaction.id}",
                        AUDIT_ADD_CONSTANT,
                        EWALLET,
                        new_data,
                        None,
                    )
                return HttpResponse(response["msg"], status=200)
            else:
                return HttpResponse(response["msg"], status=400)
        except (KeyError, AttributeError):
            return HttpResponse("User not found", status=404)


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
@allowed_users(section=EWALLET)
def withdraw_wallet_amount(request):
    """withdraw wallet amount"""
    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        try:
            wallet_transaction = TransactionsTracker.objects.filter(
                id=int(data["transaction_id"])
            )
        except KeyError:
            return HttpResponse(status=400)

        if wallet_transaction.first():
            old_data = audit_data_formatter(
                EWALLET, wallet_transaction.first().id
            )
            transaction_status = get_wallet_amount_details_for_user(
                wallet_transaction, request.user
            )
            if transaction_status:
                return HttpResponse(transaction_status, status=400)
            new_data = audit_data_formatter(
                EWALLET, wallet_transaction.first().id
            )
            add_audit_data(
                request.user,
                (
                    str(wallet_transaction.first().user_id.username)
                    + ", "
                    + str(wallet_transaction.first().driivz_account_number)
                ),
                f"{EWALLET}-{wallet_transaction.first().id}",
                AUDIT_UPDATE_CONSTANT,
                EWALLET,
                new_data,
                old_data,
            )
            return HttpResponse("Withdrawal successful!")
        return HttpResponse("User not found", status=404)


def create_user_square_account(user):
    """this function create user square account"""
    decrypter = Fernet(user.first().key)
    customer_req_body = {
        "given_name": user.first().username,
        "reference_id": user.first().username,
        "email_address": decrypter.decrypt(user.first().encrypted_email).decode(),
    }
    create_customer_result = make_request(
        POST_REQUEST,
        f'/customers',
        None,
        data=customer_req_body,
        module="Square create customer API"
    )
    if create_customer_result.status_code == 200:
        customer_data = json.loads(create_customer_result.content)
        if "customer" in customer_data:
            return customer_data["customer"]["id"]
    return None


def create_user_gift_card(user_id):
    """this function creates gift card for user"""
    try:
        user = MFGUserEV.objects.filter(id=user_id)
        customer_id = user.first().customer_id
        if customer_id is None:
            create_customer_account=create_user_square_account(user)
            if create_customer_account:
                customer_id=create_customer_account
                user.update(customer_id=create_customer_account)
        if customer_id:
            result = create_customer_gift_card(
                customer_id,
                user.first()
            )
            if result is not None:
                print(
                    f'Failed to create gift card for user with id {user_id}, due to " {result} "'
                )
        else:
            print(f"User with id {user_id} doesn't have square customer id")
    except Exception as error:
        print(error)


def gift_card_creation_function(count, users_not_having_gift_cards):
    """this function creates gift cards for users in background"""
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        executor.map(
            create_user_gift_card,
            users_not_having_gift_cards[:count]
            if count < len(users_not_having_gift_cards)
            else users_not_having_gift_cards
        )


@require_http_methods([GET_METHOD_ALLOWED, POST_METHOD_ALLOWED])
@authenticated_user
# @allowed_users(section=EWALLET)
def create_gift_cards_for_old_users(request):
    """create gift card for old users"""
    try:
        if request.user.role_id.role_name != "Super admin":
            return redirect("dashboard")
        users_having_gift_cards = Profile.objects.filter(
            ~Q(user_gift_card_id=None, user__user_email="")
        ).values_list('user_id', flat=True)
        users_not_having_gift_cards = Profile.objects.filter(
            ~Q(user__user_email=""),
            user_gift_card_id=None
        ).values_list('user_id', flat=True)
        if request.method == "POST":
            create_gift_card_user_count = request.POST.get("create_gift_card_user_count", 0)
            create_gift_card_user_count = (
                int(create_gift_card_user_count)
                if create_gift_card_user_count and create_gift_card_user_count.isnumeric()
                else 0
            )
            if create_gift_card_user_count > 0:
                create_gift_card_users = threading.Thread(
                    target=gift_card_creation_function,
                    args=[create_gift_card_user_count, users_not_having_gift_cards],
                    daemon=True
                )
                create_gift_card_users.start()
                messages.success(
                    request,
                    "Gift card creation process has been started for "
                    + f"{create_gift_card_user_count} users."
                )
            else:
                messages.warning(
                    request,
                    "Invalid batch size provided."
                )
        context = {
            "users_having_gift_cards_count": len(users_having_gift_cards),
            "users_not_having_gift_cards_count": len(users_not_having_gift_cards),
            "data": filter_url(
                request.user.role_id.access_content.all(), EWALLET
            ),
        }
        return render(request, "e_wallet/create_gift_cards_for_old_users.html", context)
    except COMMON_ERRORS:
        return render(request, ERROR_TEMPLATE_URL)
