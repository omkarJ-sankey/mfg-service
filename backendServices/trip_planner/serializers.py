"""trip planner serializers"""
# Date - 21/06/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file contains Serializers to make operation
#                       on database, to restrict fields of database.
#   Name            - Trip planner Serializers
#   Modified by     - Manish Pawar
#   Modified date   - 21/06/2021


# imports required for serializers
import googlemaps
from decouple import config

from rest_framework import serializers

# pylint:disable=import-error
from sharedServices.model_files.trip_models import Trips

gmaps = googlemaps.Client(key=config("DJANGO_APP_GOOGLE_API_KEY"))

# Trips serializer


class AddTripsSerializer(serializers.ModelSerializer):
    """add trip serializer to save and update trips"""

    # Following code defines the meta data for serializer
    # such as Which database and it's\
    # fields are going to used to do oprations.
    class Meta:
        """meta data"""

        model = Trips
        fields = (
            "user_id",
            "source",
            "destination",
            "miles",
            "duration",
            "ev_range",
            "ev_battery",
            "ev_current_battery",
            "favourite",
            "saved",
            "store_id",
            "amenity_id",
            "charging_types",
            "station_distance",
            "fuel_station_type",
            "trip_options_filter",
            "connector_type_id",
            "stations_data",
            "created_date",
            "updated_date",
            "add_stop_automatically",
            "add_spot_place_id",
        )

    # This function inserts a data row in a table.
    @classmethod
    def create(cls, validated_data):
        """create trip method"""
        trip = Trips.objects.create(**validated_data)
        return trip


# Trips serializer


class TripsSerializer(serializers.ModelSerializer):
    """trip serializer to fetch user trips"""

    # Following code defines the meta data for serializer
    # such as Which database and it's
    # fields are going to used to do oprations.

    start_location = serializers.SerializerMethodField("get_start_location")
    end_location = serializers.SerializerMethodField("get_end_location")

    @classmethod
    def get_start_location(cls, trip):
        """get trip start location"""
        return gmaps.reverse_geocode(trip.source)[0]["formatted_address"]

    @classmethod
    def get_end_location(cls, trip):
        """get trip end location"""
        return gmaps.reverse_geocode(trip.destination)[0]["formatted_address"]

    class Meta:
        """meta data"""

        model = Trips
        fields = ("id", "start_location", "end_location", "miles", "favourite")
