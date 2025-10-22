"""stations api serializers"""
# Date - 23/02/2023


# File details-
#   Author          - Vismay Raul
#   Description     - This file contains Serializers to make
#                       operation on database, to restrict
#                       fields of database.
#   Name            - Common Station Detail Related Serializers
#   Modified by     - Vismay Raul
#   Modified date   - 23/02/2023


# imports required for serializers

from rest_framework import serializers

from django.db.models import Q
from django.utils import timezone

# pylint:disable=import-error
from .constants import (
    PROMOTIONS_ARRAY_LIMIT,
    YES,
    NO,
    EV_POWER_EXTENSION_FOR_DEFAULT_IMAGES,
    MFG_BRANDS,
    COMING_SOON_CONST,
    COSTA_COFFEE,
    APP_VERSION_FOUR,
)
from .common import get_distance, get_session_api_call_time
from .model_files.config_models import (
    BaseConfigurations,
)
from .model_files.station_models import (
    StationImages,
    StationWorkingHours,
    Stations,
    StationConnector,
)
from .model_files.loyalty_models import Loyalty
from .model_files.promotions_models import Promotions
from .model_files.review_models import Reviews
from .model_files.app_user_models import MFGUserEV, Profile


def get_promotion_details_data(station, is_loyalty):
    """returns have promotion data"""
    if is_loyalty:
        data = Loyalty.objects.filter(
            station_available_loyalties__deleted=NO,
            station_available_loyalties__station_id=station,
            status="Active",
            valid_to_date__gte=timezone.localtime(timezone.now()),
            valid_from_date__lte=timezone.localtime(timezone.now()),
            deleted=NO,
        )
    else:
        data = Promotions.objects.filter(
            station_available_promotions__deleted=NO,
            station_available_promotions__station_id=station,
            status="Active",
            end_date__gte=timezone.localtime(timezone.now()),
            start_date__lte=timezone.localtime(timezone.now()),
            deleted=NO,
        )
    return data


# User serializer to get the user data
class UserSerializers(serializers.ModelSerializer):
    """user serializers"""

    # Following code defines the meta data for serializer
    # such as Which database and it's
    # fields are going to used to do oprations.

    profile_ficture = serializers.SerializerMethodField("get_profile_picture")

    @classmethod
    def get_profile_picture(cls, user):
        """get profile picture"""
        profile = Profile.objects.filter(user=user)
        return (
            profile.first().get_profile_picture()
            if profile.first() and profile.first().profile_picture
            else False
        )

    class Meta:
        """meta data"""

        model = MFGUserEV
        fields = ["username", "profile_ficture"]


# Reviews serializer for station station info page
class ReviewsSerializers(serializers.ModelSerializer):
    """Reviews serializers"""

    # Here the variables before equal to (=) are the names
    # to be passed in the API and the\
    # names passed in 'SerializerMethodField()' are the
    # name of functions which return the\
    # value for the respected variable.
    posted_date = serializers.SerializerMethodField("get_posted_date")

    # This function returns the review posted date in a suitable format.
    @classmethod
    def get_posted_date(cls, review):
        """get posted date of review"""
        review_posted_date = timezone.localtime(review.post_date)
        return (
            review_posted_date.date().strftime("%d/%m/%Y")
            + " "
            + review_posted_date.time().strftime("%H:%M")
        )

    # User serializer is called to get the information about
    # the user who posted the review.
    user_id = UserSerializers(read_only=True)

    # Following code defines the meta data for serializer.
    class Meta:
        """meta data"""

        model = Reviews
        fields = [
            "id",
            "user_id",
            "review",
            "posted_date",
            "flag",
            "status",
            "img_url",
        ]

        # This serializer returns the timing of station for particular day.


class StationWorkingHoursSerializers(serializers.ModelSerializer):
    """station working hours serializer"""

    # Following code defines the meta data for serializer.
    class Meta:
        """meta data"""

        model = StationWorkingHours
        fields = ["monday_friday", "saturday", "sunday"]


# This serializer returns the list of station images
class StationImagesSerializers(serializers.ModelSerializer):
    """station image serializer"""

    # Following code defines the meta data for serializer.
    image_path = serializers.SerializerMethodField("get_image")
    app_version = serializers.SerializerMethodField("get_app_version")

    @classmethod
    def get_image(cls, image):
        """get station image"""
        queryset = StationImages.objects.filter(id=image.id)
        return queryset.first().get_image() if queryset.count() > 0 else ""
    
    @classmethod
    def get_app_version(cls,image):
        """get app version"""
        return APP_VERSION_FOUR

    class Meta:
        """meta data"""

        model = StationImages
        fields = ["image_path","app_version"]


# This serializer returns the detailed information about station
class StationDetailSerializer(serializers.ModelSerializer):
    """station details serializer"""

    # Serializer calls to get data from other tables in
    # which station id is foreign key.
    working_hours_details = StationWorkingHoursSerializers(
        many=True, read_only=True
    )
    # Here the variables before equal to (=) are the names
    # to be passed in the API and the\
    # names passed in 'SerializerMethodField()'
    # are the name of functions which return the
    # value for the respected variable.
    open_now = serializers.SerializerMethodField("get_open_now")
    station_reviews = serializers.SerializerMethodField("get_station_reviews")
    api_time_interval = serializers.SerializerMethodField(
        "get_api_time_interval"
    )
    nearby_promotions = serializers.SerializerMethodField(
        "get_nearby_promotions"
    )
    image_url_list = serializers.SerializerMethodField("get_image_url_list")
    station_promotions = serializers.SerializerMethodField(
        "get_station_promotions"
    )
    station_connector_ids = serializers.SerializerMethodField(
        "get_station_connector_ids"
    )

    # This function returns the list all reviews available for station.
    @classmethod
    def get_station_reviews(cls, station):
        """returns station reviews"""
        reviews = Reviews.objects.filter(
            status="Approved", station_id=station, flag=NO
        ).order_by("-post_date")
        serializer = ReviewsSerializers(reviews, many=True)
        return serializer.data

    # This function return the opening status of station
    # (whether currently opend or closed)
    @classmethod
    def get_open_now(cls, station):
        """returns open now status"""
        if station.status == COMING_SOON_CONST:
            return COMING_SOON_CONST
        open_now_status = False
        # Getting the current day of week - current_date.today().weekday()
        # returns the day of week as a number.
        # eg - timezone.localtime(
        # timezone.now()).today().weekday() returns 6 for "sunday"
        day = timezone.localtime(timezone.now()).today().weekday()
        # Getting current time to make a comparison with station opening time.
        current_time = timezone.localtime(timezone.now()).strftime("%H:%M")
        # The following logic returns the opening status of station
        working_hour = StationWorkingHours.objects.filter(station_id=station)

        def checktiming(time_status):
            state = False
            if time_status == "24 hours":
                state = True
            elif time_status == "Closed":
                state = False
            else:
                if time_status[0:5] <= current_time <= time_status[6:11]:
                    state = True
            return state

        # Here 6 means sunday and 5 means saturday. For more
        # info read aboove comments
        # in this function itself.
        if working_hour.first() is not None:
            if day == 5:
                open_now_status = checktiming(working_hour.first().saturday)
            elif day == 6:
                open_now_status = checktiming(working_hour.first().sunday)
            else:
                open_now_status = checktiming(working_hour.first().monday_friday)
        return open_now_status

    @classmethod
    def get_image_url_list(cls, station):
        """returns station image list"""
        station_imgs = StationImages.objects.filter(station_id=station, deleted=NO)
        if station_imgs.count() > 0:
            serializer = StationImagesSerializers(station_imgs, many=True)
            return serializer.data
        search_text = (
            "_".join(station.brand.lower().split(" ")) + "_default_image"
        )
        if station.is_ev == YES and station.brand not in MFG_BRANDS:
            search_text = (
                "_".join(station.brand.lower().split(" "))
                + "_"
                + "_".join(
                    EV_POWER_EXTENSION_FOR_DEFAULT_IMAGES.lower().split(
                        " "
                    )
                )
                + "_default_image"
            )
        return [
            {
                "image_path": default_image.get_image(),
                "app_version": default_image.for_app_version
            }
            for default_image in  BaseConfigurations.objects.filter(
                base_configuration_key=search_text
            )
        ]

    @classmethod
    def get_api_time_interval(cls, _):
        """get api time interval to call third party APIs"""
        return {
            "dynamic_api_call_time": int(
                BaseConfigurations.objects.filter(
                    base_configuration_key="dynamic_api_call_time"
                )
                .first()
                .base_configuration_value
            ),
            "session_api_call_time": get_session_api_call_time(),
        }

    @classmethod
    def get_station_promotions(cls, station):
        """get station promotions"""
        promotion_available = (
            get_promotion_details_data(station, False)
            .values("id", "image", "end_date")
            .distinct()
        )
        promotion_available = [
            {
                "id": promotion["id"],
                "image": promotion["image"],
                "end_date": promotion["end_date"].date().strftime("%d/%m/%Y"),
            }
            for promotion in promotion_available
            if promotion["image"]
        ]

        return promotion_available

    # @classmethod
    # def get_station_loyalties(cls, station):
    #     """get station promotions"""
    #     return list(get_promotion_details_data(station, True).values_list(
    #         "id",
    #         flat=True
    #     ))

    # this function nearby promotions to station if it doesnt have it's own.

    @classmethod
    def get_nearby_promotions(cls, station):
        """get nearby promotions of station"""
        # Condition to check whether station has the promotions or not.
        station_available_promotion = (
            get_promotion_details_data(station, False)
            .values("id", "image")
            .distinct()
        )
        if len(station_available_promotion) > 0:
            return False
        local_time = timezone.localtime(timezone.now())
        # Logic to find nearby stations
        stations = Stations.objects.filter(
            ~Q(id=station.id),
            deleted=NO,
            station_promotions__promotion_id__status="Active",
            station_promotions__promotion_id__deleted=NO,
            station_promotions__promotion_id__end_date__gte=local_time,
            station_promotions__promotion_id__start_date__lte=local_time,
        ).distinct()
        # This function returns the distance between current station
        # instance and other nearby stations

        def func_order(nearby_station):
            """ordering stations"""
            distance = get_distance(
                {
                    "latitude": nearby_station.latitude,
                    "longitude": nearby_station.longitude,
                },
                {
                    "latitude": station.latitude,
                    "longitude": station.longitude,
                },
            )
            return distance

        # Sorting of stations according to distance.
        queryset = sorted(stations, key=func_order)
        nearest_station = None
        if len(queryset) > 0:
            nearest_station = queryset[0]
        # The following logic loops over the nearby stations,
        # and returns the promotions
        # if the one of the nearest  station have the promotions.
        # if one of the nearest station have the promotions then
        # we will terminate the loop and will return station's
        # promotions. else we will return 'No nearby promotions'

        promotion_available = (
            Promotions.objects.filter(
                ~Q(image=None),
                station_available_promotions__deleted=NO,
                station_available_promotions__station_id=nearest_station,
                status="Active",
                end_date__gte=timezone.localtime(timezone.now()),
                start_date__lte=timezone.localtime(timezone.now()),
                deleted=NO,
            )
            .values("id", "image")
            .distinct()
        )

        if len(promotion_available) > 0:
            if len(promotion_available) > PROMOTIONS_ARRAY_LIMIT:
                promotion_available = list(promotion_available)[
                    :PROMOTIONS_ARRAY_LIMIT
                ]
            return {
                "station_name": nearest_station.station_name,
                "promotions": list(promotion_available),
            }
        return []

    @classmethod
    def get_station_connector_ids(cls, station):
        """get station connector ids"""
        return [
            int(float(connector.connector_id))
            for connector in StationConnector.objects.filter(
                station_id=station,
                deleted=NO,
                status="Active",
                charge_point_id__deleted=NO,
                charge_point_id__charger_point_status="Active",
            )
        ]

    # Following code defines the meta data for serializer.

    class Meta:
        """meta data"""

        model = Stations
        fields = [
                "open_now",
                "working_hours_details",
                "image_url_list",
                "station_promotions",
                "nearby_promotions",
                "station_reviews",
                "api_time_interval",
                "station_connector_ids",
            ]
