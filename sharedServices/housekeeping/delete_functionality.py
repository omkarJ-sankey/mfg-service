"""DELETE FUNCTION FOR HOUSEKEEPING"""
from datetime import datetime
from django.db.models import Q
from sharedServices.model_files.config_models import BaseConfigurations
from sharedServices.model_files.review_models import Reviews, ReviewLikes
from sharedServices.model_files.app_user_models import EmailVerification
from sharedServices.model_files.station_models import (
    ChargePoint,
    Stations,
    StationWorkingHours,
    Bookmarks,
    StationConnector,
    StationImages,
    StationServices,
)
from sharedServices.model_files.config_models import ServiceConfiguration
from sharedServices.model_files.promotions_models import Promotions, PromotionImages, PromotionsAvailableOn
from sharedServices.model_files.loyalty_models import Loyalty, LoyaltyAvailableOn, LoyaltyProducts
from sharedServices.common import YES
from dateutil.relativedelta import relativedelta

#this funcrion can be called as follows to delete the data as per requirements.
# delete_unused_data(["Promotions","StationWorkingHours","Bookmarks","StationImages","StationServices","Reviews","ReviewLikes","LoyaltyAvailableOn","LoyaltyProducts","PromotionsAvailableOn","PromotionImages","ServiceConfiguration","EmailVerification"])

def delete_unused_data(table_list):
    """This function will delete the unused data from the respective table"""

    #taking the retion period in months from base configuration
    retention_time = BaseConfigurations.objects.filter(
        base_configuration_key="data_retention_period"
    ).first().base_configuration_value if BaseConfigurations.objects.filter(
        base_configuration_key="data_retention_period"
    ).first() else "6"
    
    if "Stations" in table_list:
        Stations.objects.filter(
            Q(deleted=YES)
            & Q(
                updated_date__lte=datetime.now() - relativedelta(months=int(retention_time)
                )
            )
        ).delete()

    if "Promotions" in table_list:
        Promotions.objects.filter(
            Q(deleted=YES)
            & Q(
                end_date__lte=datetime.now() - relativedelta(months=int(retention_time)
                )
            )
        ).delete()

    if "Loyalty" in table_list:
        Loyalty.objects.filter(
            Q(
                Q(deleted=YES)
                & Q(
                    updated_date__lte=datetime.now() - relativedelta(months=int(retention_time))
                )
            )
            | Q(
                valid_to_date__lte=datetime.now() - relativedelta(months=int(retention_time)
                )
            )
        ).delete()

    "=============stations related tables============"
    if "ChargePoint" in table_list:
        ChargePoint.objects.filter(Q(Q(Q(station_id_id=None) | Q(station_id__deleted=YES)) | Q(deleted=YES))
            & Q(
                updated_date__lte=datetime.now() - relativedelta(months=int(retention_time))
            )
        ).delete()

    if "StationWorkingHours" in table_list:
        StationWorkingHours.objects.filter(
            Q(Q(Q(station_id_id=None) | Q(station_id__deleted=YES)) | Q(deleted=YES))
            & Q(
                updated_date__lte=datetime.now() - relativedelta(months=int(retention_time))
            )
        ).delete()

    if "Bookmarks" in table_list:
        Bookmarks.objects.filter(
            Q(
                Q(bookmark_status="bookmarked-removed")
                | Q(Q(bookmarked_station_id__deleted=YES)|Q(bookmarked_station_id_id=None))
            )& Q(
                updated_date__lte=datetime.now() - relativedelta(months=int(retention_time))
            )
        ).delete()

    if "StationConnector" in table_list:
        StationConnector.objects.filter(
            Q(Q(Q(station_id_id=None) | Q(station_id__deleted=YES)) | Q(deleted=YES))
            & Q(
                updated_date__lte=datetime.now() - relativedelta(months=int(retention_time))     
            )
        ).delete()

    if "StationImages" in table_list:
        StationImages.objects.filter(
            Q(Q(Q(station_id_id=None) | Q(station_id__deleted=YES)) | Q(deleted=YES))
            & Q(
                updated_date__lte=datetime.now() - relativedelta(months=int(retention_time))
            )
        ).delete()

    if "StationServices" in table_list:
        StationServices.objects.filter(
            Q(Q(deleted=YES) | Q(Q(station_id_id=None) | Q(station_id__deleted=YES)))
            & Q(
                updated_date__lte=datetime.now() - relativedelta(months=int(retention_time))
            )
        ).delete()
    "=============reviews related tables============"

    if "Reviews" in table_list:
        reviews = Reviews.objects.all()
        if bool(reviews) == True:
            reviews.filter(
                Q(Q(Q(station_id_id=None) | Q(station_id__deleted=YES)) | Q(status="Disapproved"))
                & Q(
                    post_date__lte=datetime.now() - relativedelta(months=int(retention_time))
                )
            ).delete()

    if "ReviewLikes" in table_list:
        review_likes = ReviewLikes.objects.all()
        if bool(review_likes) == True:
            review_likes.filter(
                Q(Q(review_id_id = None)| Q(review_id__deleted=YES))
                & Q(
                    update_date__lte=datetime.now() - relativedelta(months=int(retention_time))
                )
            ).delete()

    "=============Loyalty related tables============"

    if "LoyaltyAvailableOn" in table_list:
        LoyaltyAvailableOn.objects.filter(Q(Q(deleted=YES) | Q(Q(station_id_id=None) | Q(station_id__deleted=YES)))
                                        & Q(
            updated_date__lte=datetime.now() - relativedelta(months=int(retention_time))
        )).delete()

    if "LoyaltyProducts" in table_list:
        LoyaltyProducts.objects.filter(Q(Q(deleted=YES) | Q(Q(loyalty_id__deleted=YES)|Q(loyalty_id_id=None)))
            & Q(
            updated_date__lte=datetime.now() - relativedelta(months=int(retention_time))
        )).delete()

    "=============Promotions rekated tables============"

    if "PromotionsAvailableOn" in table_list:
        PromotionsAvailableOn.objects.filter(Q(Q(deleted=YES) | Q(Q(Q(station_id__deleted=YES)|Q(station_id_id = None)) | Q(promotion_id_id=None))) 
                                            & Q(
            updated_date__lte=datetime.now() - relativedelta(months=int(retention_time))
        )).delete()

    if "PromotionImages" in table_list:
        PromotionImages.objects.filter(Q(Q(deleted=YES) | Q(promotion_id_id=None))
                                    & Q(
            updated_date__lte=datetime.now() - relativedelta(months=int(retention_time))
        )).delete()

    "=============Config============"

    if "ServiceConfiguration" in table_list:
        ServiceConfiguration.objects.filter(Q(deleted=YES) & Q(updated_date__lte=
            datetime.now() - relativedelta(months=int(retention_time)))).delete()
    

    if "EmailVerification" in table_list:
        EmailVerification.objects.filter(
            Q(modified_date__lte=datetime.now() - relativedelta(months=int(retention_time)))
        ).delete()

    return "deleted successfull"
