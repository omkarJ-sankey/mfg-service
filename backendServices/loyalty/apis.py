"""loyalty apis"""

# Date - 04/1/2022


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on APIs related to loyalty.
#   Name            - Loyalty APIs
#   Modified by     - Shivkumar Kumbhar
#   Modified date   - 30/03/2023


# These are all the imports that we are exporting from
# different module's from project or library.
import json
from datetime import timedelta, datetime
import threading
import pytz
from passlib.hash import django_pbkdf2_sha256 as handler
import traceback

from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.response import Response

# pylint:disable=import-error
from sharedServices.common import (
    array_to_string_converter,
    handle_concurrent_user_login,
    get_distance,
    remove_extra_spaces,
    string_to_array_converter,
)
from sharedServices.loyalty_common_functions import (
    assign_loyalty_reward_and_send_notification,
)
from sharedServices.model_files.loyalty_models import (
    Loyalty,
    UserLoyaltyTransactions,
    LoyaltyAvailableOn,
    LoyaltyBulkUpload,
)
from sharedServices.model_files.third_party_users_models import (
    ThirdPartyCredentials,
)
from sharedServices.model_files.station_models import (
    Stations,
    ServiceConfiguration,
)
from sharedServices.model_files.config_models import (
    BaseConfigurations
)
from sharedServices.model_files.charging_session_models import (
    ChargingSession,
)
from sharedServices.constants import (
    DEFAULT_LATITUDE_FOR_PROMOTIONS_AND_STATION_FINDER,
    DEFAULT_LONGITUDE_FOR_PROMOTIONS_AND_STATION_FINDER,
    NO,
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    LOYALTY_TYPE,
    MFGEVCONNECT_CONSTANT,
    PURCHASED_ACTION_CODE,
    QR_CODE_ELEMENTS_ARRAY_SIZE,
    REDEEMED,
    PURCHASED,
    REDEEMED_ACTION_CODE,
    BURNED,
    COSTA_COFFEE,
    REGULAR_LOYALTY,
    FREE_LOYALTY,
    ACTIVE,
    SECRET_KEY_IN_VALID,
    SECRET_KEY_NOT_PROVIDED,
    DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET,
    REWARD_UNLOCK,
    BEARER_CONSTANT_STRING,
    GENERIC_OFFERS,
    GUEST_USERS,
    ALL_USERS,
    REGISTERED_USERS,
    GUEST_SIGN_IN
)
from backendServices.backend_app_constants import (
    MULTIPLE_LOGIN,
    UNAUTHORIZED,
)

# pylint:enable=import-error
from .serializers import (
    LoyaltiesSerializers,
    LoyaltiesListSerializers,
    get_valid_till_date,
)
from .loyalty_helper_functions import (
    submit_transaction,
    submit_transactions_in_bulk,
)


@csrf_exempt
def upload_loyalty_transaction_in_bulk(request):
    """post request to accept all transactions"""
    try:
        if 'HTTP_AUTHORIZATION' not in request.META:
            return JsonResponse(
                {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "status": False,
                    "message": "Not authorized!",
                }
            )
        if not request.body:
            return JsonResponse(
                {
                    "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                    "status": False,
                    "message": "Invalid request body provided",
                }
            )
        request_data = json.loads(request.body.decode("utf-8"))
        request_token = request.META['HTTP_AUTHORIZATION']
        request_token_from_db = BaseConfigurations.objects.filter(
            base_configuration_key="token_secret_for_tlm"
        ).first().base_configuration_value
        if BEARER_CONSTANT_STRING in request_token and handler.verify(
            request_token.split(BEARER_CONSTANT_STRING)[1],
            request_token_from_db
        ):
            transactions = request_data.get("transaction_data", None)
            if not transactions:
                return JsonResponse(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "transactions data not provided",
                    }
                )
            submit_transactions = LoyaltyBulkUpload.objects.create(
                transaction_bulk_data=array_to_string_converter(transactions),
                transaction_data_size=len(transactions),
                user=ThirdPartyCredentials.objects.filter(
                    token=request_token
                ).first(),
                created_date=timezone.localtime(timezone.now()),
                updated_date=timezone.localtime(timezone.now()),
            )
            if submit_transactions:
                start_bulk_processing_of_transactions = threading.Thread(
                    target=submit_transactions_in_bulk,
                    args=[submit_transactions.id],
                )
                start_bulk_processing_of_transactions.daemon = True
                start_bulk_processing_of_transactions.start()
                return JsonResponse(
                    {
                        "status_code": status.HTTP_201_CREATED,
                        "status": True,
                        "message": "Transactions submitted successfully!",
                    }
                )
            return JsonResponse(
                {
                    "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                    "status": False,
                    "message": "Failed to submit transactions!",
                }
            )
        return JsonResponse(
            {
                "status_code": status.HTTP_401_UNAUTHORIZED,
                "status": False,
                "message": "Not authorized!",
            }
        )
    except COMMON_ERRORS as exception:
        print(
            f"Upload Loyalty Transaction In Bulk failed due to exception\
                    -> {exception}"
        )
        return JsonResponse(
            {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": False,
                "message": "Something went wrong",
            }
        )


@csrf_exempt
def loyalty_transaction_submission_api(request):
    """This api accepts user loyalty transactions to save in database,
    API asks for QR code which consists of 13 elements.
    List of 13 elements - > customer id , type,bar code std,scheme bar code,
    product bar code,number of units purchased,valid from date,
    valid to date,timed expiration,expiration minutes,timestamp,actioncode,
    site id
    """
    try:
        if 'HTTP_AUTHORIZATION' not in request.META:
            return JsonResponse(
                {
                    "status_code": status.HTTP_401_UNAUTHORIZED,
                    "status": False,
                    "message": "Not authorized!",
                }
            )
        if not request.body:
            return JsonResponse(
                {
                    "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                    "status": False,
                    "message": "Invalid request body provided",
                }
            )
        print("Token provided in the request body.")
        request_data = json.loads(request.body.decode("utf-8"))
        request_token = request.META['HTTP_AUTHORIZATION']
        request_token_from_db = BaseConfigurations.objects.filter(
            base_configuration_key="token_secret_for_tlm"
        ).first().base_configuration_value
        if BEARER_CONSTANT_STRING in request_token and handler.verify(
            request_token.split(BEARER_CONSTANT_STRING)[1],
            request_token_from_db
        ):
            print("Token matches with the token stored in base configurations.")
            qr_code = request_data.get("qr_code", None)
            transaction_details = request_data.get("transaction_details", None)
            print(f"[DEBUG] transaction_details: {transaction_details}")
            if not qr_code:
                print("Transaction failed:- Qr code not provided")
                return JsonResponse(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "status": False,
                        "message": "QR code not provided!",
                    }
                )
            return JsonResponse(
                submit_transaction(
                    {
                        "qr_code": qr_code,
                        "transaction_details": transaction_details,
                    }
                )
            )
        return JsonResponse(
            {
                "status_code": status.HTTP_401_UNAUTHORIZED,
                "status": False,
                "message": "Not authorized!",
            }
        )
    except COMMON_ERRORS as exception:
        print(
            f"Loyalty Transaction Submission API failed due to exception\
                    -> {exception}"
        )
        return JsonResponse(
            {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "status": False,
                "message": "Something went wrong",
            }
        )


def qr_code_generator(*args):
    """This function returns qr code for loyalty in a format needed for
    scanning and verification"""
    qr_code_generation, loyalty, user_loyalty, station = args
    action_code = PURCHASED_ACTION_CODE
    if user_loyalty.first() and (
        int(loyalty.first().number_of_paid_purchases)
        <= int(user_loyalty.first().number_of_transactions)
    ) or (
        loyalty.first().loyalty_type == FREE_LOYALTY and
        loyalty.first().offer_type != GENERIC_OFFERS
    ):
        action_code = REDEEMED_ACTION_CODE
    if action_code == REDEEMED_ACTION_CODE:
        product_bar_code = (
            loyalty.first().redeem_product_promotional_code
            if loyalty.first().redeem_product_promotional_code
            else ""
        )
    else:
        product_bar_code = (
            loyalty.first().loyalty_products.first().product_bar_code
            if loyalty.first().loyalty_products.first()
            else ""
        )
    list_of_elements = [
        f"{qr_code_generation.user.id}",
        LOYALTY_TYPE,
        loyalty.first().bar_code_std,
        loyalty.first().unique_code,
        product_bar_code,
        (
            f"{user_loyalty.first().number_of_transactions}"
            if user_loyalty.first()
            else "0"
        ),
        timezone.localtime(loyalty.first().valid_from_date)
        .date()
        .strftime("%Y-%m-%d"),
        (
            timezone.localtime(
                user_loyalty.first().expired_on
                if loyalty.first().loyalty_type
                in [COSTA_COFFEE, REGULAR_LOYALTY]
                and user_loyalty.first()
                and user_loyalty.first().expired_on
                else loyalty.first().valid_to_date
            )
            + timedelta(days=1)
        )
        .date()
        .strftime("%Y-%m-%d"),
        "Y",
        f"{loyalty.first().qr_refresh_time}",
        remove_extra_spaces(
            timezone.localtime(timezone.now()).date().strftime("%Y-%m-%d")
            + timezone.localtime(timezone.now()).time().strftime("%H:%M:%S:%f")
        ),
        action_code,
        station.first().station_id,
    ]
    return MFGEVCONNECT_CONSTANT + "_".join(
        [str(element) for element in list_of_elements]
    )


def get_user_loyalty_transaction_wrt_loyalty(
    loyalty_id, user_loyalty_transaction, number_of_paid_purchases
):
    """this function will return user loyalty transactions for loyalties"""
    user_loyalty_transaction = user_loyalty_transaction.filter(
        loyalty_id_id=loyalty_id
    ).first()
    return bool(
        user_loyalty_transaction
        and user_loyalty_transaction.number_of_transactions
        and number_of_paid_purchases
        and user_loyalty_transaction.number_of_transactions
        >= number_of_paid_purchases
    )


def return_station_loyalties(
    loyalty_id, station_id, user, is_loyalty_details=True
):
    """this function returns station loyalties"""
    loyalties = Loyalty.objects.filter(
        ~Q(id=loyalty_id),
        ~Q(image=None),
        station_available_loyalties__station_id_id=station_id,
        station_available_loyalties__deleted=NO,
        deleted=NO,
        status="Active",
        valid_from_date__lte=timezone.localtime(timezone.now()),
    ).distinct()
    user_loyalty_transaction = UserLoyaltyTransactions.objects.filter(
        Q(expired_on__gte=timezone.localtime(timezone.now())),
        action_code=PURCHASED,
        loyalty_id__in=[loyalty.id for loyalty in loyalties],
        user_id=user,
    )
    return [
        (
            {
                "id": loyalty.id,
                "image": loyalty.get_loyalty_image(),
                "loyalty_type": loyalty.loyalty_type,
                "redeem_available": (
                    (
                        loyalty.loyalty_type == FREE_LOYALTY
                        or (loyalty.loyalty_type == COSTA_COFFEE)
                        and get_user_loyalty_transaction_wrt_loyalty(
                            loyalty.id,
                            user_loyalty_transaction,
                            loyalty.number_of_paid_purchases,
                        )
                    )
                ),
            }
            if is_loyalty_details
            else {
                "id": loyalty.id,
                "image": (
                    str(loyalty.station_loyalty_card_image)
                    if loyalty.station_loyalty_card_image
                    else str(loyalty.image)
                ),
                "end_date": (
                    loyalty.valid_to_date.date().strftime("%d/%m/%Y")
                    if loyalty.loyalty_type != COSTA_COFFEE
                    else get_valid_till_date(
                        loyalty, user, is_station_details_screen=True
                    )
                ),
            }
        )
        for loyalty in loyalties
        if (
            (
                is_loyalty_details is False
                and loyalty.station_loyalty_card_image
            )
            or loyalty.image
        )
        and (
            (
                loyalty.loyalty_type == REGULAR_LOYALTY
                and loyalty.valid_to_date >= timezone.localtime(timezone.now())
            )
            or (
                loyalty.loyalty_type in [COSTA_COFFEE, FREE_LOYALTY]
                and get_active_loyalty_status(loyalty, user)
                and (
                    (
                        user_loyalty_transaction.filter(
                            Q(
                                expired_on__gte=timezone.localtime(
                                    timezone.now()
                                )
                            ),
                            end_date=None,
                            loyalty_id=loyalty,
                        )
                    )
                    or (
                        loyalty.valid_to_date
                        >= timezone.localtime(timezone.now())
                        and (
                            loyalty.number_of_issued_vouchers is None
                            or loyalty.number_of_total_issuances
                            > loyalty.number_of_issued_vouchers
                        )
                    )
                )
            )
        )
    ]


class LoyaltyDetailsAPI(APIView):
    """loyalty details viewset"""

    # Permission classes are used to restrict the user
    permission_classes = [permissions.IsAuthenticated]

    def get(self, loyalty_details_request):
        """get method to fetch lolyalty details"""
        try:
            if not loyalty_details_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                loyalty_details_request.user.id, loyalty_details_request.auth
            ):
                return MULTIPLE_LOGIN
            loyalty_id = self.request.query_params.get("loyalty_id", None)

            user_latitude = self.request.query_params.get("latitude", False)
            user_longitude = self.request.query_params.get("longitude", False)

            queryset = Loyalty.objects.filter(
                id__exact=int(loyalty_id),
                status="Active",
                valid_from_date__lte=timezone.localtime(timezone.now()),
                deleted=NO,
            )

            if user_latitude and user_longitude:
                user_latitude = float(user_latitude)
                user_longitude = float(user_longitude)
            else:
                user_latitude = float(
                    DEFAULT_LATITUDE_FOR_PROMOTIONS_AND_STATION_FINDER
                )
                user_longitude = float(
                    DEFAULT_LONGITUDE_FOR_PROMOTIONS_AND_STATION_FINDER
                )

            if not loyalty_id:
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "status": False,
                        "message": "Loyalty id or station id not provided",
                    }
                )
            loyalties = []
            loyalty_stations = LoyaltyAvailableOn.objects.filter(
                loyalty_id_id=loyalty_id, deleted=NO
            ).values(
                "station_id_id",
                "station_id__latitude",
                "station_id__longitude",
            )

            def get_station_distance(station):
                """this function calculates distance between \
                        station and usr location"""
                distance = get_distance(
                    {
                        "latitude": station["station_id__latitude"],
                        "longitude": station["station_id__longitude"],
                    },
                    {
                        "latitude": user_latitude,
                        "longitude": user_longitude,
                    },
                )
                return distance

            loyalty_stations = sorted(
                loyalty_stations, key=get_station_distance
            )
            station_id = None
            if len(loyalty_stations) > 0:
                station_id = loyalty_stations[0]["station_id_id"]
                loyalties = return_station_loyalties(
                    queryset.first().id,
                    station_id,
                    loyalty_details_request.user,
                )
            if station_id is None:
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Offer is unavailble on nearest site.",
                    }
                )
            # user loyalty progress and qr code
            user_loyalty = UserLoyaltyTransactions.objects.filter(
                action_code=PURCHASED,
                user_id_id=loyalty_details_request.user.id,
                loyalty_id_id=loyalty_id,
            )
            serializer_one = LoyaltiesListSerializers(
                queryset.first(),
                context={
                    "user_loyalties": user_loyalty,
                    "user": loyalty_details_request.user,
                    "is_detail_screen": True,
                },
            )
            serializer_two = LoyaltiesSerializers(
                queryset.first(),
                context={
                    "station_id": station_id,
                    "user_loyalties": user_loyalty,
                    "is_details_screen": True,
                },
            )
            qr_data = qr_code_generator(
                loyalty_details_request,
                queryset,
                user_loyalty,
                Stations.objects.filter(id=int(station_id)),
            )
            loyalty_data = {
                **serializer_one.data,
                **serializer_two.data,
            }
            loyalty_data["redeem_status_message"] = None
            if user_loyalty.first() is None:
                loyalty_data["redeem_status_message"] = "Get started"
            if (
                user_loyalty.first()
                and user_loyalty.first().number_of_transactions
                >= queryset.first().number_of_paid_purchases
            ):
                loyalty_data["redeem_status_message"] = "Redeem now"
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Successfully fetched loyalty data",
                    "data": {
                        "loyalty_data": loyalty_data,
                        "qr_code": qr_data,
                        "user_loyalty_transaction_cycle_id": (
                            user_loyalty.first().id if user_loyalty else None
                        ),
                        "other_loyalties": loyalties,
                    },
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Loyalty Details API failed for user -> \
                    {loyalty_details_request.user.id} due to exception \
                    -> {exception}"
            )
            return API_ERROR_OBJECT


class LoyaltyFilters(APIView):
    """loyalty filters viewset"""

    permission_classes = [permissions.IsAuthenticated]

    @classmethod
    def get(cls, _):
        """get api to fetch filters"""
        try:
            services = ServiceConfiguration.objects.filter(
                ~Q(image_path=None),
            )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "successfully fetched promotion filters",
                    "data": {
                        "shops": [
                            {
                                "shop_name": service.service_name,
                                "image": service.get_image_path(),
                            }
                            for service in services
                            if service.service_type != "Amenity"
                        ],
                        "amenities": [
                            {
                                "shop_name": service.service_name,
                                "image": service.get_image_path_with_text(),
                            }
                            for service in services
                            if service.service_type == "Amenity"
                            and service.image_path_with_text is not None
                        ],
                    },
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Loyalty filters API failed due to exception\
                      -> {exception}"
            )
            return API_ERROR_OBJECT


def return_loyalty_availale_stations_list():
    """this functions return stations on which loyalty is available"""
    current_time = timezone.localtime(timezone.now())
    return (
        Stations.objects.filter(
            deleted=NO,
            station_loyalties__loyalty_id__status="Active",
            station_loyalties__deleted=NO,
            station_loyalties__loyalty_id__deleted=NO,
            station_loyalties__loyalty_id__valid_to_date__gte=current_time,
            station_loyalties__loyalty_id__valid_from_date__lte=current_time,
        )
        .values("id", "station_name", "latitude", "longitude")
        .distinct()
    )


def valid_to_date_helper_function_for_free_loyalties(valid_to_date):
    "this function is helper function to modify date for free loyalty cooldown"
    valid_to_date = datetime.strptime(
        valid_to_date.strftime("%d/%m/%Y %H:%M"), "%d/%m/%Y %H:%M"
    )
    bst_valid_to_date = timezone.localtime(
        timezone.make_aware(
            valid_to_date, timezone=timezone.get_current_timezone()
        )
    )
    utc_valid_to_date = timezone.localtime(
        bst_valid_to_date
    ).replace(tzinfo=pytz.UTC)
    return timezone.localtime(utc_valid_to_date)


def get_active_loyalty_status(loyalty, user):
    "this function return active costa loyalty status"
    user_transactions = UserLoyaltyTransactions.objects.filter(
        user_id=user,
        loyalty_id=loyalty,
    )
    if user_transactions:
        user_last_costa_transaction = user_transactions.last()
        if user_last_costa_transaction.action_code in [
            REDEEMED,
            BURNED,
        ] and (
            (
                loyalty.loyalty_type == COSTA_COFFEE
                and user_last_costa_transaction.start_date
                > timezone.localtime(
                    timezone.now()
                    # - timedelta(days=int(float(loyalty.cycle_duration)))
                )
            )
            or (loyalty.loyalty_type != COSTA_COFFEE
                and user_last_costa_transaction.expired_on
                and user_last_costa_transaction.expired_on
                > timezone.localtime(timezone.now())
            )
        ):
            return False

        # if loyalty.loyalty_type == COSTA_COFFEE:
        #     previous_transaction_ids = string_to_array_converter(
        #         user_last_costa_transaction.transaction_ids
        #     )
        #     total_energy_consumed = 0

        #     charging_sessions = ChargingSession.objects.filter(
        #         id__in=[t_id for t_id in previous_transaction_ids if str(t_id).isdigit()]
        #     )

        #     for session in charging_sessions:
        #         if session.start_time:
        #             try:
        #                 total_energy_consumed += float(
        #                     string_to_array_converter(session.charging_data)[0]["totalEnergy"]
        #                 )
        #             except (KeyError, ValueError, TypeError):
        #                 pass

        #     if not (
        #         len(previous_transaction_ids) >= loyalty.transaction_count_for_costa_kwh_consumption
        #         and total_energy_consumed >= loyalty.number_of_paid_purchases
        #     ):
        #         return False

    number_of_issued_vouchers = (
        loyalty.number_of_issued_vouchers
        if loyalty.number_of_issued_vouchers
        else 0
    )
    if (
        loyalty.loyalty_type == FREE_LOYALTY
        and number_of_issued_vouchers < loyalty.number_of_total_issuances
        and loyalty.valid_to_date >= timezone.localtime(timezone.now())
        and not user_transactions.filter(action_code=PURCHASED)
    ):
        expired_on_date = timezone.localtime(
            timezone.now().replace(tzinfo=pytz.UTC)
        ) + timedelta(days=loyalty.expiry_in_days)
        UserLoyaltyTransactions.objects.create(
            action_code=PURCHASED,
            loyalty_id=loyalty,
            user_id=user,
            number_of_transactions=0,
            expired_on=(
                valid_to_date_helper_function_for_free_loyalties(
                    loyalty.valid_to_date
                )
                if expired_on_date >= loyalty.valid_to_date
                else expired_on_date
            ),
            start_date=timezone.localtime(timezone.now()),
            created_date=timezone.localtime(timezone.now()),
            updated_date=timezone.localtime(timezone.now()),
        )
        assign_loyalty_reward_and_send_notification(
            loyalty, [user.id], REWARD_UNLOCK
        )
    return True

class LoyaltyListViewset(APIView):
    """loyalties list API"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, loyalty_list_request):
        """get all loyalty list"""
        try:
            if not loyalty_list_request.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                loyalty_list_request.user.id, loyalty_list_request.auth
            ):
                return MULTIPLE_LOGIN
            loyalties = (
                Loyalty.objects.filter(
                    ~Q(image=None),
                    status="Active",
                    valid_from_date__lte=timezone.localtime(timezone.now()),
                    deleted=NO,
                )
                .order_by("-valid_from_date")
                .distinct()
            )
            if loyalty_list_request.user.sign_in_method == GUEST_SIGN_IN:
                loyalties = loyalties.filter(visibility__in = [GUEST_USERS, ALL_USERS])
            else:
                loyalties = loyalties.filter(visibility__in = [REGISTERED_USERS, ALL_USERS])

            car_wash = self.request.query_params.get("car_wash", "").lower()

            if car_wash == "true":
                loyalties = loyalties.filter(is_car_wash = True)
            else:
                loyalties = loyalties.filter(is_car_wash = False)
            
            user_loyalties = UserLoyaltyTransactions.objects.filter(
                action_code=PURCHASED,
                loyalty_id__in=[loyalty.id for loyalty in loyalties],
                user_id_id=loyalty_list_request.user.id,
            )

            loyalty_list_data = LoyaltiesListSerializers(
                [
                    loyalty
                    for loyalty in loyalties
                    if loyalty.image
                    and (
                        (
                            loyalty.loyalty_type == REGULAR_LOYALTY
                            and loyalty.valid_to_date
                            >= timezone.localtime(timezone.now())
                        )
                        or (
                            loyalty.loyalty_type
                            in [COSTA_COFFEE, FREE_LOYALTY]
                            and get_active_loyalty_status(
                                loyalty, loyalty_list_request.user
                            )
                            and (
                                (
                                    user_loyalties.filter(
                                        Q(
                                            expired_on__gte=timezone.localtime(
                                                timezone.now()
                                            )
                                        ),
                                        end_date=None,
                                        loyalty_id=loyalty,
                                    )
                                )
                                or (
                                    loyalty.valid_to_date
                                    >= timezone.localtime(timezone.now())
                                    and (
                                        loyalty.number_of_issued_vouchers
                                        is None
                                        or loyalty.number_of_total_issuances
                                        > loyalty.number_of_issued_vouchers
                                    )
                                )
                            )
                        )
                    )
                ],
                many=True,
                context={
                    "user_loyalties": UserLoyaltyTransactions.objects.filter(
                        Q(expired_on__gte=timezone.localtime(timezone.now()))
                        | Q(expired_on=None),
                        action_code=PURCHASED,
                        loyalty_id__in=[loyalty.id for loyalty in loyalties],
                        user_id_id=loyalty_list_request.user.id,
                    ),
                    "user": loyalty_list_request.user,
                },
            )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "successfully loaded loyalties",
                    "data": {
                        # "available_loyalties": loyalties.distinct().count()
                        # - user_loyalties.filter(action_code=REDEEMED)
                        # .distinct()
                        # .count(),
                        # "used_loyalties": user_loyalties.filter(
                        #     action_code=REDEEMED
                        # )
                        # .distinct()
                        # .count(),
                        "loyalties": loyalty_list_data.data,
                    },
                }
            )
        except COMMON_ERRORS as exception:
            traceback.print_exc()
            print(
                f"Loyalty List Viewset API failed for user -> \
                {loyalty_list_request.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


class QRCodeGeneratorAPIForLoyalty(APIView):
    """this api is used to generate QR code for every five minutes"""

    permission_classes = [permissions.IsAuthenticated]

    @classmethod
    def post(cls, qr_code_generation):
        """generate qr code api"""
        try:
            if not qr_code_generation.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                qr_code_generation.user.id, qr_code_generation.auth
            ):
                return MULTIPLE_LOGIN
            loyalty_id = qr_code_generation.data.get("loyalty_id", None)
            station_id = qr_code_generation.data.get("station_id", None)

            loyalty = Loyalty.objects.filter(id=loyalty_id)
            station = Stations.objects.filter(id=station_id)
            if loyalty.first() is None or station.first() is None:
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "status": False,
                        "message": "Invalid data provided",
                    }
                )
            user_loyalty = UserLoyaltyTransactions.objects.filter(
                action_code=PURCHASED,
                user_id_id=qr_code_generation.user.id,
                loyalty_id_id=loyalty_id,
            )
            qr_data = qr_code_generator(
                qr_code_generation, loyalty, user_loyalty, station
            )

            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "successfully loaded promotions",
                    "data": {"qr_code": qr_data},
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"QR Code Generator API For Loyalty failed for user -> \
                {qr_code_generation.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


def get_confirm_purchase_status(
    user_loyalties,
    user_loyalty_transaction_id,
    current_loyalty_progress,
    qr_action_code,
):
    """confirm purchase status"""
    if not user_loyalty_transaction_id:
        return bool(user_loyalties.filter(action_code=PURCHASED).first())
    user_last_cycle = user_loyalties.filter(
        id=user_loyalty_transaction_id
    ).last()
    if qr_action_code == PURCHASED_ACTION_CODE:
        return bool(
            user_last_cycle
            and user_last_cycle.number_of_transactions
            > float(current_loyalty_progress)
        )
    return bool(user_last_cycle and user_last_cycle.action_code == REDEEMED)


class ConfirmPurchasedAPI(APIView):
    """this api returns whether user purchased is successful or not"""

    @classmethod
    def post(cls, user_purchase_check):
        """check user purchase"""
        try:
            if not user_purchase_check.auth:
                return UNAUTHORIZED

            if not handle_concurrent_user_login(
                user_purchase_check.user.id, user_purchase_check.auth
            ):
                return MULTIPLE_LOGIN
            qr_code = user_purchase_check.data.get("qr_code", None)
            current_loyalty_progress = user_purchase_check.data.get(
                "current_loyalty_progress", None
            )
            user_loyalty_transaction_cycle_id = user_purchase_check.data.get(
                "user_loyalty_transaction_cycle_id", None
            )
            if qr_code is None or current_loyalty_progress is None:
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "status": False,
                        "message": (
                            "Qr code or current progress not not provided"
                        ),
                    }
                )

            qr_elements = qr_code.split("_")
            if len(qr_elements) != QR_CODE_ELEMENTS_ARRAY_SIZE:
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "status": False,
                        "message": "Invalid QR code.",
                    }
                )
            (
                _,
                _,
                _,
                _,
                scheme_bar_code,
                _,
                _,
                _,
                _,
                _,
                _,
                _,
                qr_action_code,
                site_id,
            ) = qr_elements
            user_loyalties = UserLoyaltyTransactions.objects.filter(
                loyalty_id__unique_code=scheme_bar_code,
                user_id_id=user_purchase_check.user.id,
            )
            station = Stations.objects.filter(station_id=site_id)
            if user_loyalties.first() is None:
                return Response(
                    {
                        "status_code": status.HTTP_400_BAD_REQUEST,
                        "status": False,
                        "message": "Thank you for your purchase, "
                        + "your loyalty plan will be updated once verified.",
                    }
                )

            serializer_one = LoyaltiesListSerializers(
                user_loyalties.first().loyalty_id,
                context={
                    "station_id": station.first().id,
                    "user_loyalties": user_loyalties.filter(
                        action_code=PURCHASED
                    ),
                    "user": user_purchase_check.user,
                },
            )
            serializer_two = LoyaltiesSerializers(
                user_loyalties.first().loyalty_id,
                context={
                    "station_id": station.first().id,
                    "user_loyalties": user_loyalties,
                },
            )

            loyalty_data = {
                **serializer_one.data,
                **serializer_two.data,
            }
            loyalty_data["reward_image"] = (
                (user_loyalties.first().loyalty_id.get_loyalty_reward_image())
                if user_loyalties.first().loyalty_id.reward_image
                else None
            )
            loyalty_data["redeem_status_message"] = None
            if user_loyalties.first() is None:
                loyalty_data["redeem_status_message"] = "Get started"
            if (
                user_loyalties.filter(action_code=PURCHASED).first()
                and user_loyalties.filter(action_code=PURCHASED)
                .first()
                .number_of_transactions
                >= user_loyalties.filter(action_code=PURCHASED)
                .first()
                .loyalty_id.number_of_paid_purchases
            ):
                loyalty_data["redeem_status_message"] = "Redeem now"

            if user_loyalties.filter(action_code=PURCHASED).first() is None:
                loyalty_data["redeem_status_message"] = "Purchase completed"

            qr_data = qr_code_generator(
                user_purchase_check,
                Loyalty.objects.filter(
                    id=user_loyalties.first().loyalty_id.id
                ),
                user_loyalties,
                station,
            )
            # loyalties = return_station_loyalties(
            #     user_loyalties.first().loyalty_id.id,
            #     station.first().id,
            #     user_purchase_check.user,
            # )
            confirm_purchase_status = get_confirm_purchase_status(
                user_loyalties,
                user_loyalty_transaction_cycle_id,
                current_loyalty_progress,
                qr_action_code,
            )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": confirm_purchase_status,
                    "message": (
                        "Thank you for your purchase, your "
                        + "loyalty plan has been updated"
                        if confirm_purchase_status
                        else "Thank you for your purchase, "
                        + "your loyalty plan will be updated once verified."
                    ),
                    "data": {
                        "loyalty_data": loyalty_data,
                        "qr_code": qr_data,
                        # "other_loyalties": loyalties,
                    },
                }
            )

        except COMMON_ERRORS as exception:
            print(
                f"Confirm Purchased API failed for user -> \
                {user_purchase_check.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


def burn_down_loyalty_rewards():
    "This function burns the loyalty rewards"
    non_regular_loyalties = Loyalty.objects.filter(
        loyalty_type__in=[COSTA_COFFEE, FREE_LOYALTY],
        status=ACTIVE,
        deleted=NO,
    )
    if non_regular_loyalties:
        UserLoyaltyTransactions.objects.filter(
            action_code=PURCHASED,
            expired_on__lte=timezone.localtime(timezone.now()),
            loyalty_id__in=non_regular_loyalties,
        ).update(
            action_code=BURNED,
        )
        for loyalty in non_regular_loyalties:
            if loyalty.loyalty_type == COSTA_COFFEE:
                UserLoyaltyTransactions.objects.filter(
                    action_code=PURCHASED,
                    expired_on=None,
                    start_date__lte=timezone.localtime(
                        timezone.now()
                        - timedelta(days=int(float(loyalty.cycle_duration)))
                    ),
                    loyalty_id=loyalty,
                ).update(
                    action_code=BURNED,
                )


class LoyaltyRewardBurnDownCRONJobAPI(APIView):
    """cronjonb API"""

    @classmethod
    def post(cls, cron_job_request):
        """post method to initialize cron job api"""
        try:
            secret_key_azure = cron_job_request.data.get("secret_key", None)
            if secret_key_azure is None:
                return SECRET_KEY_NOT_PROVIDED
            if not handler.verify(
                secret_key_azure, DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET
            ):
                return SECRET_KEY_IN_VALID

            start_time = threading.Thread(
                target=burn_down_loyalty_rewards(),
                daemon=True
            )
            start_time.start()

            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Cron job initiated.",
                }
            )
        except COMMON_ERRORS:
            return API_ERROR_OBJECT


class CheckUserActiveReward(APIView):
    """This api checks if user has any active costa reward"""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, loyalty_request):
        """generate qr code api"""
        try:
            if not loyalty_request.auth:
                return UNAUTHORIZED
            if not handle_concurrent_user_login(
                loyalty_request.user.id, loyalty_request.auth
            ):
                return MULTIPLE_LOGIN
            loyalty_id = self.request.query_params.get("loyalty_id", None)
            if not loyalty_id:
                Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "active_reward": False,
                    }
                )
            loyalty = Loyalty.objects.filter(
                id=int(loyalty_id),
            )
            if loyalty:
                active_loyalty = loyalty.filter(
                    status=ACTIVE,
                    deleted=NO,
                ).first()
                if active_loyalty:
                    active_reward = UserLoyaltyTransactions.objects.filter(
                        action_code=PURCHASED,
                        user_id=loyalty_request.user,
                        loyalty_id=active_loyalty,
                        expired_on__gt=timezone.localtime(timezone.now()),
                        end_date=None,
                    )
                    if active_reward.first():
                        return Response(
                            {
                                "status_code": status.HTTP_200_OK,
                                "active_reward": True,
                            }
                        )
            return Response(
                {
                    "status_code": status.HTTP_404_NOT_FOUND,
                    "active_reward": False,
                }
            )

        except COMMON_ERRORS as exception:
            print(
                f"Check User Active Loyalty Reward API failed for user -> \
                {loyalty_request.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


def send_loyalty_reward_reminder_notification():
    """This function send the reminder notification for loyalty reward"""
    try:
        loyalties = Loyalty.objects.filter(
            loyalty_type__in=[COSTA_COFFEE, FREE_LOYALTY],
            status=ACTIVE,
            deleted=NO,
        )
        for loyalty in loyalties:
            if loyalty and loyalty.reward_expiry_notification_trigger_time:
                current_date_time = timezone.localtime(timezone.now())
                (
                    reward_expiry_hours,
                    reward_expiry_minutes,
                ) = loyalty.reward_expiry_notification_trigger_time.strip().split(
                    ":"
                )
                minutes_representation_of_trigger_time = int(
                    reward_expiry_hours
                ) * 60 + int(reward_expiry_minutes)
                current_minutes = (
                    current_date_time.hour * 60 + current_date_time.minute
                )
                if (
                    current_minutes - minutes_representation_of_trigger_time
                    > 0
                    and current_minutes
                    - minutes_representation_of_trigger_time
                    <= 5
                ):
                    active_rewards_users = UserLoyaltyTransactions.objects.filter(
                        action_code=PURCHASED,
                        loyalty_id=loyalty,
                        expired_on__date=(
                            current_date_time
                            + timedelta(
                                days=loyalty.expire_reward_before_x_number_of_days
                            )
                        ).date(),
                    ).values_list(
                        "user_id", flat=True
                    )
                    if active_rewards_users:
                        assign_loyalty_reward_and_send_notification(
                            loyalty, active_rewards_users
                        )
    except Exception as error:
        print(error)


class SendLoyaltyRewardReminderNotificationCronJob(APIView):
    """Loyalty Reward BurnDown CRONJob API"""

    @classmethod
    def post(cls, cron_job_request):
        """post method to initialize cron job api"""
        try:
            secret_key_azure = cron_job_request.data.get("secret_key", None)
            if secret_key_azure is None:
                return SECRET_KEY_NOT_PROVIDED
            if not handler.verify(
                secret_key_azure, DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET
            ):
                return SECRET_KEY_IN_VALID

            start_time = threading.Thread(
                target=send_loyalty_reward_reminder_notification(),
                daemon=True
            )
            start_time.start()

            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Cron job initiated.",
                }
            )

        except COMMON_ERRORS:
            return API_ERROR_OBJECT
