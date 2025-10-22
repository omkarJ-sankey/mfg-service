"""models"""
# Date - 21/06/2021
# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on
#                       creating database tables for
#                       all modules.
#   Name            - Authentication related models
#   Modified by     - Manish Pawar
#   Modified date   - 26/06/2021


# Imports required to make models are below
from django.db import models
from ..constants import YES, NO
from .station_models import Stations
from .app_user_models import MFGUserEV


# reviews models
class Reviews(models.Model):
    """reviews model"""

    conditions = ((YES, YES), (NO, NO))
    review_id = models.AutoField
    user_id = models.ForeignKey(
        MFGUserEV, null=True, on_delete=models.SET_NULL
    )
    station_id = models.ForeignKey(
        Stations,
        null=True,
        on_delete=models.SET_NULL,
        related_name="station_reviews",
        related_query_name="station_reviews",
    )
    review = models.CharField(max_length=200, blank=True, null=True)
    status = models.CharField(
        max_length=100, blank=True, default="pending", null=True
    )
    flag = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    post_date = models.DateTimeField(max_length=100, blank=True, null=False)
    img_url = models.ImageField(upload_to="images", null=True, blank=True)
    update_date = models.DateTimeField(null=True, blank=True)
    update_by = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return str(self.station_id)


# this ReviewsLikes model contain informmation of responses on reviews


class ReviewLikes(models.Model):
    """review likes/dislikes model"""

    res = (("like", "like"), ("disLike", "disLike"))
    user_id = models.ForeignKey(
        MFGUserEV, null=True, on_delete=models.SET_NULL
    )
    review_id = models.ForeignKey(
        Reviews,
        null=True,
        on_delete=models.SET_NULL,
        related_name="review_response",
        related_query_name="review_response",
    )
    review_response = models.CharField(max_length=100, blank=True, choices=res)
    created_date = models.DateTimeField(null=True, blank=True)
    update_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        """meta data"""

        db_table = "review_likes"

    def __str__(self):
        return str(self.review_response)
