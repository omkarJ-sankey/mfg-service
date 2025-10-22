"""Promotions serializers"""
# Date - 26/06/2021

# File details-
#   Author          - Manish Pawar
#   Description     - This file contains Serializers to make operation
#                        on database, to restrict fields of database.
#   Name            - Promotion Serializers
#   Modified by     - Manish Pawar
#   Modified date   - 26/06/2021


# imports required for serializers
from rest_framework import serializers

# pylint:disable=import-error
from sharedServices.common import string_to_array_converter
from sharedServices.model_files.promotions_models import Promotions
from sharedServices.model_files.station_models import Stations
from sharedServices.shared_station_serializer import (
    StationDetailsLogoSerializer,
)

# This serializer returns the detailed info about promotion.


class PromotionsSerializers(serializers.ModelSerializer):
    """promotion detail serializer"""

    image = serializers.SerializerMethodField("get_image")
    offer_by = serializers.SerializerMethodField("get_offer_by")
    valid_till = serializers.SerializerMethodField("get_valid_till")
    station_details = serializers.SerializerMethodField("get_stations_details")

    @classmethod
    def get_image(cls, promotion):
        """get promotion image"""
        return (promotion.get_promotion_image()) if promotion.image else None

    @classmethod
    def get_offer_by(cls, promotion):
        """get offer by"""
        shops = string_to_array_converter(promotion.shop_ids)
        return shops[0] if len(shops) > 0 else False

    @classmethod
    def get_valid_till(cls, promotion):
        """get validity of promotion"""
        return promotion.end_date.date().strftime("%d/%m/%Y")

    def get_stations_details(self, _):
        """get station details"""
        if self.context["station_id"]:
            station_exists = Stations.objects.filter(
                id=int(self.context["station_id"])
            )
            if station_exists.first():
                serializer = StationDetailsLogoSerializer(
                    station_exists.first(), read_only=True
                )
                return serializer.data
        return None

    # Following code defines the meta data for serializer.
    class Meta:
        """meta data"""

        model = Promotions
        fields = [
            "id",
            "unique_code",
            "retail_barcode",
            "offer_by",
            "valid_till",
            "product",
            "promotion_title",
            "available_for",
            "image",
            "offer_details",
            "terms_and_conditions",
            "station_details",
        ]
