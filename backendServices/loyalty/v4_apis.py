"""loyalty apis"""

# Date - 04/02/2024


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on APIs related to loyalty.
#   Name            - Loyalty APIs
#   Modified by     - Abhinav Shivalkar
#   Modified date   - 27/09/2025


# These are all the imports that we are exporting from
# different module's from project or library.

from passlib.hash import django_pbkdf2_sha256 as handler
from django.db.models import F

from django.utils import timezone
from django.db.models import Q
from rest_framework.views import APIView
from rest_framework import status, permissions
from rest_framework.response import Response

# pylint:disable=import-error
from sharedServices.common import (
    handle_concurrent_user_login,
    get_distance,
)
from sharedServices.model_files.loyalty_models import (
    Loyalty,
    UserLoyaltyTransactions,
    LoyaltyAvailableOn,
    LoyaltyOccurrences
)
from sharedServices.model_files.station_models import (
    Stations,
)
from sharedServices.constants import (
    NO,
    YES,
    COMMON_ERRORS,
    API_ERROR_OBJECT,
    PURCHASED,
    COSTA_COFFEE,
    REGULAR_LOYALTY,
    FREE_LOYALTY,
    GENERIC_OFFERS,
    DEFAULT_LATITUDE_FOR_PROMOTIONS_AND_STATION_FINDER,
    DEFAULT_LONGITUDE_FOR_PROMOTIONS_AND_STATION_FINDER,
    SECRET_KEY_IN_VALID,
    SECRET_KEY_NOT_PROVIDED,
    DJANGO_APP_AZURE_FUNCTION_CRON_JOB_SECRET,
    ACTIVE,
    BURNED,
    LOYALTY_OFFERS,
    GUEST_SIGN_IN,
    ALL_USERS,
    GUEST_USERS,
    REGISTERED_USERS
)
from backendServices.backend_app_constants import (
    MULTIPLE_LOGIN,
    UNAUTHORIZED,
)

# pylint:enable=import-error
from .serializers import (
    LoyaltiesClubsListSerializersV4,
    OffersListSerializersV4,
    LoyaltyDetailsSerializersV4
)

from .apis import (
    get_active_loyalty_status
)
from backendServices.stations.apis import NearestStation
from sharedServices.common import string_to_array_converter


class LoyaltyDetailsAPIV4(APIView):
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
            print('[DEBUG] user loc:', user_latitude, user_longitude)
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
            
            queryset = Loyalty.objects.filter(
                id__exact=int(loyalty_id),
                status="Active",
                valid_from_date__lte=timezone.localtime(timezone.now()),
                deleted=NO,
            )
            if queryset.first() and (
                loyalty_details_request.user.sign_in_method == GUEST_SIGN_IN and queryset.first().visibility == REGISTERED_USERS
                ) or (
                    loyalty_details_request.user.sign_in_method != GUEST_SIGN_IN and queryset.first().visibility == GUEST_USERS
                    ):
                return Response(
                    {
                        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                        "status": False,
                        "message": "Loyalty is not available for user type",
                    }
                )
            # if (queryset.first().number_of_issued_vouchers
            #     and queryset.first().number_of_total_issuances
            #     <= queryset.first().number_of_issued_vouchers):
            #     return Response(
            #         {
            #             "status_code": status.HTTP_406_NOT_ACCEPTABLE,
            #             "status": False,
            #             "message": "Loyalty is not available",
            #         }
            #     )

            loyalty_stations = LoyaltyAvailableOn.objects.filter(
                loyalty_id_id=loyalty_id, deleted=NO
            ).values(
                "station_id_id",
                "station_id__latitude",
                "station_id__longitude",
            )
            loyalty_first_item = queryset.first()
            def is_loyalty_redeemable(loyalty, user):
                user_loyalty_transaction = (
                    UserLoyaltyTransactions.objects.filter(
                        Q(expired_on__gte=timezone.localtime(timezone.now()))
                        | Q(expired_on=None),
                        action_code=PURCHASED,
                        user_id=user.id,
                        loyalty_id=loyalty.id,
                    ).first()
                )

                if (
                    loyalty.loyalty_type == COSTA_COFFEE
                    and loyalty.number_of_paid_purchases is not None
                    and loyalty.transaction_count_for_costa_kwh_consumption is not None
                    and user_loyalty_transaction
                    and user_loyalty_transaction.transaction_ids
                ):
                    transaction_count = len(
                        string_to_array_converter(user_loyalty_transaction.transaction_ids)
                    )
                    return transaction_count >= loyalty.transaction_count_for_costa_kwh_consumption
                return loyalty.loyalty_type == COSTA_COFFEE and (
                    user_loyalty_transaction
                    and user_loyalty_transaction.number_of_transactions
                    and loyalty.number_of_paid_purchases
                    and user_loyalty_transaction.number_of_transactions
                    >= loyalty.number_of_paid_purchases
                )


            if (
                loyalty_first_item
                and loyalty_first_item.loyalty_type == COSTA_COFFEE
                and loyalty_first_item.trigger_sites
                and not is_loyalty_redeemable(loyalty_first_item, loyalty_details_request.user)
            ):
                loyalty_stations = list(
                    Stations.objects.filter(station_id__in=loyalty_first_item.trigger_sites)
                    .annotate(
                        station_id_id=F("id"),
                        **{"station_id__latitude": F("latitude")},
                        **{"station_id__longitude": F("longitude")},
                    )
                    .values("station_id_id", "station_id__latitude", "station_id__longitude")
                )
            def get_nearest_site(data, key):
                return (
                    data.get(key, [None])[0]
                    if data and data.get(key)
                    else None
                )

            if queryset.first().offer_type == LOYALTY_OFFERS and queryset.first().detail_site_check:
                available_loyalty_stations = LoyaltyAvailableOn.objects.filter(
                    loyalty_id_id=loyalty_id, deleted=NO
                ).values(
                    "station_id_id",
                    "station_id__latitude",
                    "station_id__longitude",
                )
                print("[DEBUG] Redemption Site IDs:", [site['station_id_id'] for site in available_loyalty_stations])
                nearest_station_data = NearestStation.get_nearest_station(user_latitude, user_longitude, True, True)
                print(f"[DEBUG] nearest_station_data: {nearest_station_data}")

                ev_id = get_nearest_site(nearest_station_data, "is_ev_id")
                non_ev_id = get_nearest_site(nearest_station_data, "station_id")
                nearest_station_ids = [id_ for id_ in [ev_id, non_ev_id] if id_ is not None]
                loyalty_station_ids = [station['station_id_id'] for station in available_loyalty_stations]
                if not any(station_id in loyalty_station_ids for station_id in nearest_station_ids):
                    return Response(
                        {
                            "status_code": status.HTTP_406_NOT_ACCEPTABLE,
                            "status": False,
                            "message": "Offer is unavailable on your nearest site.",
                        }
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
                Q(expired_on__gte=timezone.localtime(timezone.now()))
                | Q(expired_on=None),
                action_code=PURCHASED,
                user_id_id=loyalty_details_request.user.id,
                loyalty_id_id=loyalty_id,
            )
            loyalty_data = LoyaltyDetailsSerializersV4(
                queryset.first(),
                context={
                    "user_loyalties": user_loyalty,
                    "user": loyalty_details_request.user,
                    "is_detail_screen": True,
                },
            ).data
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
                        **loyalty_data,
                        "station_id": station_id,
                        "loyalty_stations": [
                            station['station_id_id']
                            for station in loyalty_stations
                        ]
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


class LoyaltyListViewsetV4(APIView):
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
                    deleted=NO,
                    valid_from_date__lte=timezone.localtime(timezone.now())
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
            loyalty_list_data = LoyaltiesClubsListSerializersV4(
                [
                    loyalty
                    for loyalty in loyalties
                    if loyalty.image and
                        (
                            loyalty.offer_type != GENERIC_OFFERS and
                            loyalty.loyalty_type != FREE_LOYALTY
                        ) and (
                            loyalty.occurance_status == NO or
                            (
                                loyalty.occurance_status == YES and
                                (
                                    user_loyalties.filter(
                                        ~Q(expired_on=None),
                                        end_date=None,
                                        loyalty_id=loyalty
                                    ) or
                                    loyalty.show_occurrence_offer is True
                                )
                            )
                        ) and (
                        (
                            loyalty.loyalty_type == REGULAR_LOYALTY
                            and loyalty.valid_to_date
                            >= timezone.localtime(timezone.now())
                        )
                        or (
                            loyalty.loyalty_type == COSTA_COFFEE
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
            offers_list_data = OffersListSerializersV4(
                [
                    loyalty
                    for loyalty in loyalties
                    if (
                        loyalty.image and
                        (
                            (
                                loyalty.offer_type == GENERIC_OFFERS and
                                loyalty.valid_to_date >= timezone.localtime(timezone.now())
                            ) or
                            (
                                loyalty.offer_type != GENERIC_OFFERS and
                                loyalty.loyalty_type == FREE_LOYALTY and
                                (
                                    loyalty.occurance_status == NO or
                                    (
                                        loyalty.occurance_status == YES and
                                        (
                                            user_loyalties.filter(
                                                ~Q(expired_on=None),
                                                end_date=None,
                                                loyalty_id=loyalty
                                            ) or
                                            loyalty.show_occurrence_offer is True
                                        )
                                    )
                                ) and
                                get_active_loyalty_status(
                                    loyalty, loyalty_list_request.user
                                ) and (
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
                        "offers": offers_list_data.data,
                        "loyalties": loyalty_list_data.data,
                    },
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Loyalty List Viewset API failed for user -> \
                {loyalty_list_request.user.id} due to exception -> {exception}"
            )
            return API_ERROR_OBJECT


class EnableDailyLoyaltyAPI(APIView):
    """API to enable daily loyalties based on time added for the loyalty"""

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
            current_time = timezone.localtime(timezone.now()).time()
            loyalties_with_set_occurances = list(set(LoyaltyOccurrences.objects.filter(
                loyalty_id__status=ACTIVE,
                loyalty_id__deleted=NO,
                deleted=NO,
                date__date=timezone.localtime(timezone.now()).date(),
                start_time__lte=current_time,
                end_time__gte=current_time
            ).values_list('loyalty_id_id', flat=True)))

            Loyalty.objects.filter(
                id__in=loyalties_with_set_occurances
            ).update(
                show_occurrence_offer=True,
            )
            # Disabling
            remove_set_occurances = LoyaltyOccurrences.objects.filter(
                date__date=timezone.localtime(timezone.now()).date(),
                end_time__lt=current_time
            )
            Loyalty.objects.filter(
                id__in=[
                    remove_set_occurance.loyalty_id.id
                    for remove_set_occurance in remove_set_occurances
                ]
            ).update(
                show_occurrence_offer=False,
            )
            for remove_set_occurance in remove_set_occurances:
                UserLoyaltyTransactions.objects.filter(
                    action_code=PURCHASED,
                    expired_on=None,
                    start_date__date=timezone.localtime(timezone.now()).date(),
                    start_date__time__gte=remove_set_occurance.start_time,
                    start_date__time__lte=remove_set_occurance.end_time,
                    loyalty_id=remove_set_occurance.loyalty_id,
                ).update(
                    action_code=BURNED,
                )
            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Daily loyalty enabling process started.",
                }
            )
        except COMMON_ERRORS:
            return API_ERROR_OBJECT

def get_user_offers(user, station=None):
    """Get user offers data that can be reused across different APIs"""
    loyalties = (
        Loyalty.objects.filter(
            ~Q(image=None),
            status="Active",
            deleted=NO,
            valid_from_date__lte=timezone.localtime(timezone.now()),
            display_on_charging_screen=True,
        )
        .order_by("-valid_from_date")
        .distinct()
    )
    
    if station:
        loyalties = loyalties.filter(
            station_available_loyalties__station_id=station,
            station_available_loyalties__deleted=NO,
        )

    user_loyalties = UserLoyaltyTransactions.objects.filter(
        action_code=PURCHASED,
        loyalty_id__in=[loyalty.id for loyalty in loyalties],
        user_id_id=user.id,
    )

    offers_data = OffersListSerializersV4(
        [
            loyalty
            for loyalty in loyalties
            if (
                loyalty.image and
                (
                    (
                        loyalty.offer_type == GENERIC_OFFERS and
                        loyalty.valid_to_date >= timezone.localtime(timezone.now())
                    ) or
                    (
                        loyalty.offer_type != GENERIC_OFFERS and
                        loyalty.loyalty_type == FREE_LOYALTY and
                        (
                            loyalty.occurance_status == NO or
                            (
                                loyalty.occurance_status == YES and
                                (
                                    user_loyalties.filter(
                                        ~Q(expired_on=None),
                                        end_date=None,
                                        loyalty_id=loyalty
                                    ) or
                                    loyalty.show_occurrence_offer is True
                                )
                            )
                        ) and
                        get_active_loyalty_status(
                            loyalty, user
                        ) and (
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
            )
        ],
        many=True,
        context={
            "user_loyalties": UserLoyaltyTransactions.objects.filter(
                Q(expired_on__gte=timezone.localtime(timezone.now()))
                | Q(expired_on=None),
                action_code=PURCHASED,
                loyalty_id__in=[loyalty.id for loyalty in loyalties],
                user_id_id=user.id,
            ),
            "user": user,
        },
    ).data

    loyalty_list_data = LoyaltiesClubsListSerializersV4(
        [
            loyalty
            for loyalty in loyalties
            if loyalty.image and
                (
                    loyalty.offer_type != GENERIC_OFFERS and
                    loyalty.loyalty_type != FREE_LOYALTY
                ) and (
                    loyalty.occurance_status == NO or
                    (
                        loyalty.occurance_status == YES and
                        (
                            user_loyalties.filter(
                                ~Q(expired_on=None),
                                end_date=None,
                                loyalty_id=loyalty
                            ) or
                            loyalty.show_occurrence_offer is True
                        )
                    )
                ) and (
                (
                    loyalty.loyalty_type == REGULAR_LOYALTY
                    and loyalty.valid_to_date
                    >= timezone.localtime(timezone.now())
                )
                or (
                    loyalty.loyalty_type == COSTA_COFFEE
                    and get_active_loyalty_status(
                        loyalty, user
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
                user_id_id=user.id,
            ),
            "user": user,
        },
    ).data

    combined_ids = [item["id"] for item in offers_data + loyalty_list_data]
    print("combined_ids ::", combined_ids)
    return [
        {
            "id": offer["id"],
            "image": offer["image"],
            "offer_type": offer["offer_type"] == GENERIC_OFFERS
        }
        for offer in list((
            Loyalty.objects.filter(
                ~Q(image=None),
                id__in=combined_ids,
                station_available_loyalties__station_id=station,
                station_available_loyalties__deleted=NO,
                deleted=NO,
                status="Active",
                valid_from_date__lte=timezone.localtime(timezone.now()),
                valid_to_date__gte=timezone.localtime(timezone.now()),
            )
            .values("id", "image", "offer_type")
            .distinct()
        ))
    ]
