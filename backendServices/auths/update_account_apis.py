"""update user account APIs"""
# Date - 26/06/2021


# File details-
#   Author          - Manish Pawar
#   Description     - This file is mainly focused on APIs
#                       related to user account updation APIs.
#   Name            - Account updation API
#   Modified by     - Shivkumar Kumbhar
#   Modified date   - 31/03/2023


# These are all the imports that we are exporting from different
# module's from project or library.
import base64
from cryptography.fernet import Fernet

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from django.shortcuts import get_object_or_404
from django.core.files.base import ContentFile

# pylint:disable=import-error
from sharedServices.model_files.app_user_models import (
    MFGUserEV,
    Profile,
)
from sharedServices.common import (
    handle_concurrent_user_login,
    randon_string_generator,
)
from sharedServices.constants import COMMON_ERRORS, API_ERROR_OBJECT

from .serializers import UserGetDetailsSerializer


class UpdateUserData(APIView):
    """This API will allow user to change his data"""

    @classmethod
    def post(cls, update_request):
        """post request to user data"""
        try:
            # If bearer token is passed to API then we can get the current
            # user with request.user
            first_name = update_request.data.get("first_name", False)
            last_name = update_request.data.get("last_name", False)
            postal_code = update_request.data.get("postal_code", False)
            country = update_request.data.get("country", False)
            profile_picture = update_request.data.get("profile_picture", False)
            image_format = update_request.data.get("image_format", False)
            remove_image = update_request.data.get("remove_image", False)
            image_to_upload = None
            # Based on user status of authentication we will perform queries
            # the request.auth returns null if user is not authenticated
            update_account_user = update_request
            if not update_account_user.auth:
                return Response(
                    {
                        "status_code": status.HTTP_401_UNAUTHORIZED,
                        "status": False,
                        "message": "Not authorized user to update data",
                    }
                )

            if not handle_concurrent_user_login(
                update_account_user.user.id, update_account_user.auth
            ):
                return Response(
                    {
                        "status_code": status.HTTP_409_CONFLICT,
                        "status": False,
                        "message": "You have logged in from another device!",
                    }
                )

            if not (
                ("v4" in update_account_user.build_absolute_uri() and (first_name or last_name))
                or (
                    "v4" not in update_account_user.build_absolute_uri()
                    and (first_name or last_name or postal_code or country)
                )
            ):
                return Response(
                    {
                        "status_code": status.HTTP_304_NOT_MODIFIED,
                        "status": False,
                        "message": "Updated data not provided!!.",
                    }
                )

            user_object = get_object_or_404(
                MFGUserEV, id=update_request.user.id
            )
            profile_object = None
            profile_object = get_object_or_404(
                Profile, user_id=update_request.user.id
            )
            encrypter = Fernet(update_request.user.key)
            user_object.first_name = (
                encrypter.encrypt(first_name.encode())
                if first_name
                else user_object.first_name
            )
            user_object.last_name = (
                encrypter.encrypt(last_name.encode())
                if last_name
                else user_object.last_name
            )
            if "v4" not in update_account_user.build_absolute_uri():
                user_object.post_code = (
                    encrypter.encrypt((postal_code.strip()).encode())
                    if postal_code
                    else user_object.post_code
                )
                user_object.country = (
                    encrypter.encrypt(country.encode())
                    if country
                    else user_object.country
                )

            if remove_image:
                profile_picture_for_deletetion = Profile.objects.get(
                    user=update_request.user
                )
                profile_picture_for_deletetion.profile_picture.delete()
                profile_picture_for_deletetion.profile_picture = None
                profile_picture_for_deletetion.save()
            elif profile_picture:
                if profile_object:
                    profile_picture_for_updation = Profile.objects.get(
                        user=update_request.user
                    )
                    profile_picture_for_updation.profile_picture.delete()
                # Base64 conversion to file
                random_string = randon_string_generator()
                if profile_object:
                    image_to_upload = ContentFile(
                        base64.b64decode(profile_picture),
                        name=f"profile_pic_{random_string}."
                        + image_format.split("/")[-1],
                    )
                    profile_object.profile_picture = image_to_upload
            user_object.save()
            if profile_object:
                if profile_picture:
                    profile_object.save()
            else:
                if image_to_upload:
                    Profile.objects.create(
                        user=update_request.user,
                        profile_picture=image_to_upload,
                    )

            return Response(
                {
                    "status_code": status.HTTP_200_OK,
                    "status": True,
                    "message": "Updated successfully!!.",
                    "data": UserGetDetailsSerializer(
                        MFGUserEV.objects.get(id=update_request.user.id),
                        context={"token": update_request.auth},
                    ).data,
                }
            )
        except COMMON_ERRORS as exception:
            print(
                f"Update User Data API failed due to exception -> {exception}"
            )
            return API_ERROR_OBJECT
