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
from cryptography.fernet import Fernet
from decouple import config
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import RegexValidator
from django.db.models.signals import post_save
from ..constants import (
    YES,
    NO,
    EMAIL_SIGN_IN,
    APPLE_SIGN_IN,
    GOOGLE_SIGN_IN,
    GUEST_SIGN_IN
)

# Authentication models


class UserManager(BaseUserManager):
    """User manager"""

    def create_user(self, email, is_admin=False):
        """create user function"""
        if not email:
            raise ValueError("users must have a email number")
        user_obj = self.model(email=email)
        user_obj.set_unusable_password()
        user_obj.admin = is_admin
        user_obj.save(using=self._db)
        return user_obj


class MFGUserEV(AbstractBaseUser):
    """MFG user for App"""
    sign_in_methods = (
        (GOOGLE_SIGN_IN, GOOGLE_SIGN_IN),
        (APPLE_SIGN_IN, APPLE_SIGN_IN),
        (EMAIL_SIGN_IN, EMAIL_SIGN_IN),
        (GUEST_SIGN_IN, GUEST_SIGN_IN)
    )
    email = models.CharField(max_length=1000, unique=True, null=True,blank=True)
    user_email = models.CharField(max_length=1000, blank=True, null=True)
    password = models.CharField(max_length=1000, blank=True, null=True)
    first_name = models.BinaryField(blank=True, null=True)
    last_name = models.BinaryField(blank=True, null=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    post_code = models.BinaryField(blank=True, null=True)
    country = models.BinaryField(blank=True, null=True)
    key = models.BinaryField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    customer_id = models.CharField(max_length=1000, unique=False, null=True)
    encrypted_email = models.BinaryField(blank=True, null=True)
    phone_number = models.BinaryField(blank=True, null=True)
    hashed_phone_number = models.CharField(max_length=1000, unique=True, null=True)
    sign_in_method = models.CharField(
        max_length=1000,
        choices=sign_in_methods,
        null=True,
        blank=True
    )
    device_token = models.CharField(
        max_length=1000,
        null=True,
        blank=True
    )
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    class Meta:
        """meta data"""

        db_table = "mfg_user_ev"

    def __str__(self):
        return str(self.user_email)

    def get_username(self):
        """get user name"""
        return self.username

    def get_customer_id(self):
        """get cistomer id"""
        return self.customer_id

    def get_dec_email(self):
        """get decrypted email of user"""
        decrypt = Fernet(self.key)
        return decrypt.decrypt(self.encrypted_email).decode()


class AppUserThirdPartyRegistrationFailedAPILogs(models.Model):
    """App user third party registration failed api logs"""
    app_user = models.ForeignKey(
        MFGUserEV,
        on_delete=models.CASCADE,
        related_name="third_party_failed_api_log",
        related_query_name="third_party_failed_api_log",
        null=True,
    )
    url = models.CharField(
        max_length=1000,
        null=True,
        blank=True
    )
    response = models.TextField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return str(self.user.first_name)


class UserSelectedStationFinderFilters(models.Model):
    """user selected station finder filters"""
    user = models.OneToOneField(
        MFGUserEV,
        on_delete=models.CASCADE,
        related_name="user_selected_station_finder_filters",
        related_query_name="user_selected_station_finder_filters",
    )
    selected_filter_data = models.TextField(
        null=True,
        blank=True
    )
    created_date=models.DateTimeField(auto_now_add=True)
    updated_date=models.DateTimeField()

    def __str__(self):
        return str(self.user.first_name)


class Profile(models.Model):
    """user profile model"""

    conditions = ((YES, YES), (NO, NO))
    user_domain = ("normal_user", "normal_user")
    user = models.OneToOneField(
        MFGUserEV,
        on_delete=models.CASCADE,
        related_name="user_profile",
        related_query_name="user_profile",
    )
    profile_picture = models.ImageField(
        upload_to="images", blank=True, null=True
    )
    swarco_token = models.CharField(max_length=1000, null=True, blank=True)
    swarco_refresh_token = models.CharField(
        max_length=1000, null=True, blank=True
    )
    driivz_account_number = models.CharField(
        max_length=100, null=True, blank=True
    )
    driivz_virtual_card_id = models.CharField(
        max_length=100, null=True, blank=True
    )
    driivz_virtual_card_number = models.CharField(
        max_length=100, null=True, blank=True
    )
    user_gift_card_id = models.CharField(max_length=100, null=True, blank=True)
    user_gift_card_gan = models.CharField(
        max_length=100, null=True, blank=True
    )
    default_payment_method = models.CharField(
        max_length=1000, null=True, blank=True
    )
    app_access_token = models.CharField(max_length=1000, null=True, blank=True)
    user_token = models.CharField(max_length=1000, blank=True, null=True)
    user_ev_ids = models.CharField(max_length=3000, blank=True, null=True)
    default_ev_id = models.CharField(max_length=100, blank=True, null=True)
    have_amount_due = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    due_amount_data = models.TextField(null=True, blank=True)
    two_factor_done = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    wallet_balance = models.CharField(max_length=100, blank=True, null=True)
    updated_by = models.CharField(max_length=100, blank=True, null=True)
    fcm_device_token = models.CharField(max_length=1000, blank=True, null=True)
    region = models.CharField(max_length=100, blank=True, null=True)
    inapp_notification_object = models.TextField(blank=True, null=True)
    promotion_preference_status = models.BooleanField(default=True)
    loyalty_preference_status = models.BooleanField(default=True)
    other_preference_status = models.BooleanField(default=True)
    email_news_letter_preference_status = models.BooleanField(default=True)
    email_marketing_update_preference_status = models.BooleanField(
        default=True
    )
    email_promotion_preference_status = models.BooleanField(default=True)
    user_domain = models.CharField(max_length=100, default="normal_user")
    email_ev_updates_preference_status = models.BooleanField(default=True)

    # 3DS fields
    user_specific_3ds_set_by_admin = models.BooleanField(default=False, null=True)
    user_specific_3ds_configurations = models.TextField(blank=False, null=True)
    user_specific_3ds_configurations_updated_at = models.DateTimeField(null=True)
    is_3ds_check_active = models.BooleanField(default=False, null=True)

    def __str__(self):
        return str(self.user)

    def get_profile_picture(self):
        """get user profile picture"""
        if self.profile_picture:
            return f"{config('DJANGO_APP_CDN_BASE_URL')}{self.profile_picture}"
        return "abc.com"

    def get_driivz_account_number(self):
        """get drrivz account number"""
        if self.driivz_account_number:
            return self.driivz_account_number
        return ""


# pylint:disable=unused-argument
def user_created_receiver(sender, instance, created, *args, **kwargs):
    """user created receiver post save"""
    if created:
        # pylint:disable=no-member
        Profile.objects.get_or_create(user=instance)


post_save.connect(user_created_receiver, sender=MFGUserEV)


class EmailVerification(models.Model):
    """email verification model"""

    conditions = ((YES, YES), (NO, NO))
    email_regex = RegexValidator(
        regex=r"^(\w|\.|\_|\-)+[@](\w|\_|\-|\.)+[.]\w{2,3}$",
        message="Plase enter email in valid format!",
    )
    email = models.CharField(
        validators=[email_regex],
        max_length=1000,
        unique=True,
        blank=True,
        null=True,
    )
    verify_email = models.CharField(max_length=1000, blank=True, null=False)
    otp = models.CharField(max_length=9, blank=True, null=True)
    count = models.IntegerField(default=0, help_text="Number of otp sent")
    logged = models.CharField(
        max_length=100, choices=conditions, default=NO, blank=True, null=True
    )
    otp_type = models.CharField(max_length=20, blank=True, null=True)
    modified_date = models.DateTimeField()

    class Meta:
        """meta data"""

        db_table = "email_verification"

    def __str__(self):
        return str(self.otp) + " is sent to" + str(self.email)
