"""auths serializers"""
# Date - 26/06/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file contains Serializers to
#                       make operation on database, to
#                       restrict fields of database.
#   Name            - Authentication Serializers
#   Modified by     - Manish Pawar
#   Modified date   - 26/06/2021


# imports required for serializers
import decouple
from decouple import config
from cryptography.fernet import Fernet
from passlib.hash import django_pbkdf2_sha256 as handler

from rest_framework import serializers

from django.contrib.auth import authenticate
from django.contrib.auth.models import update_last_login
from django.contrib.auth import get_user_model

# pylint:disable=import-error

from sharedServices.model_files.vehicle_models import (
    UserEVs
)
from sharedServices.model_files.app_user_models import (
    MFGUserEV,
    Profile
)
from sharedServices.model_files.charging_session_models import ChargingSession
from sharedServices.model_files.config_models import BaseConfigurations

from sharedServices.custom_jwt_handler import jwt_payload_handler
from sharedServices.constants import YES

from .error_messages import USER_HAVE_RUNNING_SESSION_MESSAGE

User = get_user_model()

try:
    BLOB_CDN_URL = config("DJANGO_APP_CDN_BASE_URL")
except decouple.UndefinedValueError:
    BLOB_CDN_URL = "https://mfg-ev-qa.azureedge.net/media/33"
# This serializer is used to authenticate user and sends the
# token to access the other functionalities.


def return_loyalty_enabled_status():
    """this function returns status of whether loyalty is
    enabled or not"""
    return bool(
        BaseConfigurations.objects.filter(
            base_configuration_key="loyalty_enabled"
        ).first()
        and BaseConfigurations.objects.filter(
            base_configuration_key="loyalty_enabled"
        )
        .first()
        .base_configuration_value
        == YES
    )


def return_user_ev_list(user):
    """this function returns user evs"""
    user_evs = UserEVs.objects.filter(user_id=user).order_by('-created_date')
    user_evs_list = []
    if user_evs:
        user_default_ev_vehicle =  UserEVs.objects.filter(
            user_id=user,
            default=True
        ).first()
        for count, row_ev in enumerate(user_evs):
            user_evs_list.append(
                {
                    "id": row_ev.vehicle_id.id,
                    "user_vehicle_id": row_ev.id,
                    "default": bool(
                        user_default_ev_vehicle and row_ev.id == user_default_ev_vehicle.id
                        or (not user_default_ev_vehicle and count == 0)
                    ),
                    "vehicle_make": row_ev.vehicle_id.vehicle_make,
                    "vehicle_model": row_ev.vehicle_id.vehicle_model,
                    "vehicle_model_version": row_ev.vehicle_id.vehicle_model_version,
                    "battery_capacity_useable": row_ev.vehicle_id.battery_capacity_useable,
                    "fastcharge_chargespeed": row_ev.vehicle_id.fastcharge_chargespeed,
                    "vehicle_nickname": row_ev.vehicle_nickname,
                    "vehicle_registration_number": row_ev.vehicle_registration_number,
                    "ev_image": row_ev.vehicle_id.get_ev_image()
                }
            )
    return user_evs_list


# pylint:disable=abstract-method


class UserLoginSerializer(serializers.Serializer):
    """user login serializer"""

    email = serializers.CharField(max_length=255)
    token = serializers.CharField(max_length=255, read_only=True)
    password = serializers.CharField(max_length=255)
    user_token = serializers.CharField(max_length=255)
    user_evs = serializers.ListField(read_only=True)
    user_have_ev = serializers.BooleanField(read_only=True)
    loyalty_enabled = serializers.BooleanField(read_only=True)
    two_factor_auth_done = serializers.BooleanField(read_only=True)
    phone_number = serializers.CharField(max_length=255, read_only=True)
    driivz_account_number = serializers.CharField(
        max_length=100, read_only=True
    )
    sso_type = serializers.CharField(max_length=100)
    check_2fa = serializers.BooleanField()
    v3_registration = serializers.BooleanField()

    def validate(self, attrs):
        """validate user"""
        email = attrs.get("email", None)
        password = attrs.get("password", None)
        user_token = attrs.get("user_token", None)
        sso_type = attrs.get("sso_type", None)
        check_2fa = attrs.get("check_2fa", None)
        v3_registration = attrs.get("v3_registration", None)
        # authenticate user.
        # this authenticate is the custom authentication function,
        # which overrides django's default authentication function.
        user = (
            MFGUserEV.objects.filter(user_email=email).first()
            if sso_type and sso_type !="Email Sign In" else
            authenticate(email=email, password=password)
        )
        if user is None:
            raise serializers.ValidationError(
                "A user with this email not found"
            )
        user_profile = Profile.objects.filter(user=user)
        user_evs_list = return_user_ev_list(user)
        user_have_ev = True if len(user_evs_list) > 0 else False

        if user_profile.first().user_token:
            if not handler.verify(user_token, user_profile.first().user_token):
                user_charging_sessions = ChargingSession.objects.filter(
                    user_id=user, session_status="running"
                )
                if user_charging_sessions.first() is None:
                    user_profile.update(user_token=handler.hash(user_token))
                else:
                    raise serializers.ValidationError(
                        USER_HAVE_RUNNING_SESSION_MESSAGE
                    )
        else:
            user_profile.update(user_token=handler.hash(user_token))
        phone_number = "Not provided"
        if user.phone_number:
            decrypter = Fernet(user.key)
            phone_number = decrypter.decrypt(user.phone_number).decode()
        two_factor_auth_done = bool(
            user_profile.first().two_factor_done and
            user_profile.first().two_factor_done == YES
        )
        token = ""
        if two_factor_auth_done or check_2fa is False or v3_registration is True:
            try:
                token = jwt_payload_handler(user)
                user_profile.update(app_access_token=token)
                update_last_login(None, user)
            except User.DoesNotExist as user_does_not_exists:
                raise serializers.ValidationError(
                    "User with given email does not exists."
                ) from user_does_not_exists
        return {
            "email": user.user_email,
            "token": token,
            "password": "",
            "user_token": "",
            "user_evs": user_evs_list,
            "user_have_ev": user_have_ev,
            "loyalty_enabled": return_loyalty_enabled_status(),
            "two_factor_auth_done": two_factor_auth_done,
            "phone_number": phone_number,
            "driivz_account_number": (
                user_profile.first().get_driivz_account_number()
            ),
            "sso_type": "",
            "check_2fa": False,
            "v3_registration": v3_registration
        }


# pylint:enable=abstract-method

# This serializer is used to register  the new user
class CreateUserSerializer(serializers.ModelSerializer):
    """create user serializer"""

    # Meta data of serializer
    class Meta:
        """meta data"""

        model = MFGUserEV
        fields = (
            "email",
            "first_name",
            "last_name",
            "password",
            "username",
            "post_code",
            "country",
            "key",
        )
        extra_kwargs = {"password": {"write_only": True}}

    # create method to insert data in database.
    def create(self, validated_data):
        """create user method"""
        user = User.objects.create(**validated_data)
        return user


class UserGetDetailsSerializer(serializers.ModelSerializer):
    """get user details"""

    profile_picture = serializers.SerializerMethodField("get_image")
    first_name = serializers.SerializerMethodField("get_first_name")
    last_name = serializers.SerializerMethodField("get_last_name")
    user_post_code = serializers.SerializerMethodField("get_post_code")
    user_country = serializers.SerializerMethodField("get_country")
    user_name = serializers.SerializerMethodField("get_user_name")

    email = serializers.SerializerMethodField("get_email")
    token = serializers.SerializerMethodField("get_token")
    driivz_account_number = serializers.SerializerMethodField(
        "get_driivz_account_number"
    )
    user_have_ev = serializers.SerializerMethodField("get_user_have_ev")
    user_evs = serializers.SerializerMethodField("get_user_evs")
    loyalty_enabled = serializers.SerializerMethodField("get_loyalty_enabled")
    two_factor_auth_done = serializers.SerializerMethodField(
        "get_two_factor_auth_done"
    )
    phone_number = serializers.SerializerMethodField(
        "get_phone_number"
    )

    @classmethod
    def get_loyalty_enabled(cls, _):
        """get loyalty enable status"""
        return return_loyalty_enabled_status()

    @classmethod
    def get_user_have_ev(cls, user):
        """get user have ev or not status"""
        return  UserEVs.objects.filter(
            user_id=user
        ).first() is not None

    @classmethod
    def get_driivz_account_number(cls, user):
        """get user have ev or not status"""
        profile = Profile.objects.filter(user=user)
        if profile.first():
            return profile.first().get_driivz_account_number()
        return ""

    @classmethod
    def get_user_evs(cls, user):
        """get user evs"""
        return return_user_ev_list(user)

    @classmethod
    def get_image(cls, user):
        """get user profile picture"""
        profile = Profile.objects.filter(user=user)
        if profile.first():
            return profile.first().get_profile_picture()
        return "abc.com"

    @classmethod
    def get_email(cls, user):
        """get user email"""
        decrypter = Fernet(user.key)
        return decrypter.decrypt(user.encrypted_email).decode()

    def get_token(self, _):
        """get user token"""
        return str(self.context["token"])

    @classmethod
    def get_user_name(cls, user):
        """get user name"""
        return user.username

    @classmethod
    def get_first_name(cls, user):
        """get first name"""
        decrypter = Fernet(user.key)
        return decrypter.decrypt(user.first_name).decode()

    @classmethod
    def get_last_name(cls, user):
        """get last name"""
        decrypter = Fernet(user.key)
        return decrypter.decrypt(user.last_name).decode()

    @classmethod
    def get_post_code(cls, user):
        """get post code"""
        decrypter = Fernet(user.key)
        return decrypter.decrypt(user.post_code).decode() if user.post_code else ""

    @classmethod
    def get_country(cls, user):
        """get contry"""
        decrypter = Fernet(user.key)
        return decrypter.decrypt(user.country).decode() if user.country else ""

    @classmethod
    def get_phone_number(cls, user):
        """get contry"""
        decrypter = Fernet(user.key)
        return (
            decrypter.decrypt(user.phone_number).decode()
            if user.phone_number else ""
        )

    @classmethod
    def get_two_factor_auth_done(cls, user):
        """get two factor auth status"""
        return bool(
            user.user_profile.two_factor_done and
            user.user_profile.two_factor_done == YES
        )

    class Meta:
        """meta data"""

        model = MFGUserEV
        fields = (
            "email",
            "first_name",
            "last_name",
            "user_name",
            "user_post_code",
            "token",
            "user_country",
            "profile_picture",
            "user_have_ev",
            "user_evs",
            "loyalty_enabled",
            "driivz_account_number",
            "two_factor_auth_done",
            "phone_number"
        )
