"""stations api serializers"""
# Date - 21/06/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file contains Serializers to make
#                       operation on database, to restrict
#                       fields of database.
#   Name            - Station Finder Serializers
#   Modified by     - Manish Pawar
#   Modified date   - 21/06/2021


# imports required for serializers
from rest_framework import serializers

# pylint:disable=import-error
from sharedServices.model_files.config_models import (
    ServiceConfiguration,
)
from sharedServices.model_files.station_models import (
    Bookmarks,
)

from sharedServices.model_files.review_models import ReviewLikes, Reviews

# Bookmark serializer


class BookmarksSerializer(serializers.ModelSerializer):
    """bookmark serializer"""

    # Following code defines the meta data for serializer
    # such as Which database and it's
    # fields are going to used to do oprations.
    class Meta:
        """meta data"""

        model = Bookmarks
        fields = (
            "user_id",
            "bookmarked_station_id",
            "bookmark_status",
            "created_date",
            "updated_date",
        )

    # This function inserts a data row in a table.
    @classmethod
    def create(cls, validated_data):
        """add bookmark method"""
        boomark = Bookmarks.objects.create(**validated_data)
        return boomark


# Review create serializer
class ReviewsSerializer(serializers.ModelSerializer):
    """Review serializers"""

    # Following code defines the meta data for serializer.
    class Meta:
        """meta data"""

        model = Reviews
        fields = (
            "user_id",
            "station_id",
            "review",
            "flag",
            "status",
            "img_url",
            "post_date",
        )

    # This function inserts a data row in a table.
    @classmethod
    def create(cls, validated_data):
        return Reviews.objects.create(**validated_data)


# Review like and dislike serializer (create)


class ReviewLikesSerializer(serializers.ModelSerializer):
    """Review likes serializer"""

    # Following code defines the meta data for serializer.
    class Meta:
        """meta data"""

        model = ReviewLikes
        fields = ["user_id", "review_id", "review_response"]

    # This function inserts a data row in a table.
    @classmethod
    def create(cls, validated_data):
        response = ReviewLikes.objects.create(**validated_data)
        return response


class ServiceConfigurationSerializers(serializers.ModelSerializer):
    """service configuration serializer"""

    # Following code defines the meta data for serializer.
    image = serializers.SerializerMethodField("get_image")

    @classmethod
    def get_image(cls, service):
        """get image of service"""
        queryset = ServiceConfiguration.objects.filter(id=service.id)
        return (
            queryset.first().get_image_path() if queryset.count() > 0 else ""
        )

    class Meta:
        """meta data"""

        model = ServiceConfiguration
        fields = ["service_name", "service_type", "image"]
