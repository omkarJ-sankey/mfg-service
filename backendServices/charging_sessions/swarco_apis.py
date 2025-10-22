"""SWARCO api call functions"""
# Date - 31/01/2022

# File details-
#   Author          - Manish Pawar
#   Description     - This file contains API calls for SWARCO.
#   Name            - SWARCO APIs
#   Modified by     - Manish Pawar
#   Modified date   - 31/01/2022


# These are all the imports that we are exporting from
# different module's from project or library.
import threading
from datetime import datetime
import json
from simplejson import JSONDecodeError
from decouple import config

from rest_framework import status
from django.utils import timezone

# pylint:disable=import-error
from sharedServices.model_files.app_user_models import Profile
from sharedServices.model_files.charging_session_models import ChargingSession

from sharedServices.constants import (
    SESSION_CLOSED,
    REQUEST_API_TIMEOUT,
    GET_REQUEST,
    POST_REQUEST,
)

from sharedServices.common import (
    array_to_string_converter,
)
from sharedServices.sentry_tracers import traced_request
from .app_level_constants import (
    SWARCO,
    CHECK_SESSION_CONNECTION_TIME_IN_SECONDS,
)


def check_swarco_session_status(*arg):
    """this function called after 90 seconds to check whtehr is conncted to
    device or not"""
    list_of_arg = list(arg)
    session = ChargingSession.objects.filter(id=list_of_arg[0])
    user = Profile.objects.filter(user=list_of_arg[1])
    print("swarco charger connection checking session call")
    print("session id", list_of_arg[2])
    headers = {
        "api-auth": config("DJANGO_APP_SWARCO_API_AUTH"),
        "emp-session-id": list_of_arg[2],
        "Authorization": f"Bearer {user.first().swarco_token}",
    }
    response = traced_request(
        GET_REQUEST,
        f"{config('DJANGO_APP_SWARCO_BASE_URL')}/api/v1/session-status",
        headers=headers,
        timeout=REQUEST_API_TIMEOUT,
    )
    print(f"Session API Status -> {response.status_code}")
    print(f"Session API response ->{json.loads(response.content)}")
    if (
        user.first()
        and session.first().session_status == "start"
        and response.status_code == 200
    ):
        content = json.loads(response.content)
        if content["status"]:
            print("SWARCO running state check -> session is running")
            session.update(
                session_status="running",
                charging_data=array_to_string_converter([content]),
            )
        else:
            print("SWARCO running state check ->session rejected")
            session.update(
                session_status="rejected",
                charging_data=array_to_string_converter([content]),
                feedback="Session is expired because user did not \
                                connected to the charger.",
            )


def swarco_user_authentication_using_refresh_token(access_token, user):
    """this function authenticates MFG EV app user with SWARCO using
    refresh token"""
    print("SWARCO auth API call using refresh token")
    auth_response = traced_request(
        POST_REQUEST,
        f"{config('DJANGO_APP_SWARCO_BASE_URL')}/oauth/token",
        data={
            "boundary": "WebAppBoundary",
            "grant_type": "refresh_token",
            "client_id": config("DJANGO_APP_SWARCO_CLIENT_ID"),
            "client_secret": config("DJANGO_APP_SWARCO_CLIENT_SECRET"),
            "refresh_token": access_token.first().swarco_refresh_token,
        },
        timeout=REQUEST_API_TIMEOUT,
    )
    print(
        f"User id-{user.id}, message -> auth response with \
            swarco refresh token received"
    )
    print(
        f"User id-{user.id}, message -> start session API \
            auth status {auth_response.status_code}"
    )
    return auth_response


def swarco_generate_tokens_for_new_user(user):
    """this function is used to crete tokens for new MFG EV
    app user for SWARCO"""
    print(
        "SWARCO auth API called for new token creation using \
            email and password"
    )
    auth_response = traced_request(
        POST_REQUEST,
        f"{config('DJANGO_APP_SWARCO_BASE_URL')}/oauth/token",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        data={
            "boundary": "WebAppBoundary",
            "grant_type": "external",
            "client_id": config("DJANGO_APP_SWARCO_CLIENT_ID"),
            "client_secret": config("DJANGO_APP_SWARCO_CLIENT_SECRET"),
            "username": user.user_email,
            "password": user.password,
        },
        timeout=REQUEST_API_TIMEOUT,
    )
    print(
        f"User id-{user.id}, message -> auth response for \
            new user verification by swarco received"
    )
    print(
        f"User id-{user.id}, message -> session API new \
            user auth status {auth_response.status_code} "
    )

    return auth_response


def swarco_start_session_api_call(*arg):
    """this function is used to call SWARCO start session API"""
    (
        auth_response,
        user,
        request_data,
        station,
        chargepoint,
        connector,
        payment_id,
    ) = arg
    content = json.loads(auth_response.content)
    access_token = Profile.objects.filter(user=user)
    access_token.update(
        swarco_token=content["access_token"],
        swarco_refresh_token=content["refresh_token"],
    )

    # Swarco start session API called
    response = traced_request(
        POST_REQUEST,
        f"{config('DJANGO_APP_SWARCO_BASE_URL')}/api/v1/startstop",
        headers={
            "api-auth": config("DJANGO_APP_SWARCO_API_AUTH"),
            "Authorization": f"Bearer {content['access_token']}",
            "Content-Type": "application/json",
        },
        data=json.dumps(request_data),
        timeout=REQUEST_API_TIMEOUT,
    )
    print(
        f"User id-{user.id} , message-> start session \
            API status code {response.status_code}"
    )
    if response.status_code == 200:
        response_data = json.loads(response.content)
        if response_data["status"]:
            charging_session = None
            print(
                f"User id-{user.id} , message -> session started successfully"
            )
            if response_data["status_code"] == "Started":
                charging_session = ChargingSession.objects.create(
                    start_time=timezone.localtime(
                        datetime.fromtimestamp(
                            response_data["started_timestamp"]
                        )
                    ),
                    station_id=station,
                    chargepoint_id=chargepoint,
                    connector_id=connector,
                    user_id=user,
                    payment_id=payment_id,
                    back_office=chargepoint.back_office,
                    session_status="start",
                    emp_session_id=response_data["emp_session_id"],
                )
                start_time = threading.Timer(
                    CHECK_SESSION_CONNECTION_TIME_IN_SECONDS,
                    check_swarco_session_status,
                    [
                        charging_session.id,
                        user,
                        response_data["emp_session_id"],
                    ],
                )
                start_time.start()
            if charging_session:
                response_data = json.loads(response.content)
                response_data["access_token"] = content["access_token"]
                response_data["refresh_token"] = content["refresh_token"]
                response_data["back_office"] = SWARCO
                return {
                    "status_code": response.status_code,
                    "status": True,
                    "message": response_data["message"],
                    "data": response_data,
                }
            return {
                "status_code": status.HTTP_501_NOT_IMPLEMENTED,
                "status": False,
                "message": "something went wrong, \
                    please try to connect again.",
            }
        # session start API failed
        print(f"User id-{user.id} , message -> session start API failed")
        print(f"User id-{user.id} , session api response-> {response_data} ")
        return {
            "status_code": status.HTTP_200_OK,
            "status": False,
            "message": response_data["message"],
            "data": response_data,
        }

    if response.status_code == 401:
        print(
            f"User id-{user.id} , message -> authentication failed by swarco"
        )
        return {
            "status_code": response.status_code,
            "status": False,
            "message": "Failed to authenticate user.",
        }
    return {
        "status_code": response.status_code,
        "status": False,
        "message": "Start session request failed.",
    }


def swarco_stop_session_api_call(*arg):
    """this function is used to call SWARCO stop session API"""
    auth_response, user, request_data = arg

    content = json.loads(auth_response.content)

    access_token = Profile.objects.filter(user=user)
    access_token.update(
        swarco_token=content["access_token"],
        swarco_refresh_token=content["refresh_token"],
    )

    response = traced_request(
        POST_REQUEST,
        f"{config('DJANGO_APP_SWARCO_BASE_URL')}/api/v1/startstop",
        headers={
            "api-auth": config("DJANGO_APP_SWARCO_API_AUTH"),
            "Authorization": f"Bearer {content['access_token']}",
            "Content-Type": "application/json",
        },
        data=json.dumps(request_data),
        timeout=REQUEST_API_TIMEOUT,
    )

    if response.status_code == 200:
        response_data = json.loads(response.content)
        if response_data["status"]:
            print(
                f"User id-{user.id} , message -> Session stopped \
                    successfully (Auth by refresh token)"
            )
            charging_session = ChargingSession.objects.filter(
                user_id=user, emp_session_id=request_data["emp_session_id"]
            )
            if charging_session.first():
                charging_session.update(
                    session_status="closed",
                    end_time=timezone.localtime(timezone.now()),
                )
            response_data["emp_session_id"] = request_data["emp_session_id"]
            response_data["access_token"] = content["access_token"]
            response_data["refresh_token"] = content["refresh_token"]
            response_data["back_office"] = SWARCO
            return {
                "status_code": status.HTTP_200_OK,
                "status": True,
                "message": response_data["message"],
                "data": response_data,
            }
        # failed to stop session
        print(
            f"User id-{user.id} ,Failed to stop session\
                (Auth by refresh token)"
        )
        return {
            "status_code": status.HTTP_200_OK,
            "status": False,
            "message": response_data["message"],
            "data": response_data,
        }

    if response.status_code == 401:
        print("SWARCO stop session failed 401")
        try:
            return {
                "status_code": response.status_code,
                "status": False,
                "message": json.loads(response.content)["message"],
            }
        except JSONDecodeError:
            return {
                "status_code": response.status_code,
                "status": False,
                "message": "Failed to authenticate user.",
            }

    print("SWARCO stop session failed", response.content)
    return {
        "status_code": response.status_code,
        "status": False,
        "message": json.loads(response.content)["message"],
    }


def swarco_check_session_status_api_call(auth_response, user, session):
    """this function is used to check session status API"""
    content = json.loads(auth_response.content)

    access_token = Profile.objects.filter(user=user)
    access_token.update(
        swarco_token=content["access_token"],
        swarco_refresh_token=content["refresh_token"],
    )
    headers = {
        "api-auth": config("DJANGO_APP_SWARCO_API_AUTH"),
        "emp-session-id": session.emp_session_id,
        "Authorization": f"Bearer {content['access_token']}",
    }
    response = traced_request(
        GET_REQUEST,
        f"{config('DJANGO_APP_SWARCO_BASE_URL')}/api/v1/session-status",
        headers=headers,
        timeout=REQUEST_API_TIMEOUT,
    )
    print(
        f"Session API Status (from MFG save feedback API)\
             -> {response.status_code}"
    )
    print("Session API response (from MFG save feedback API)")
    return response


def swarco_start_session_function(args):
    """this function initializes the user sessions for SWARCO"""
    print("successfully called SWARO")
    (
        start_session_request,
        station,
        chargepoint,
        connector,
        access_token,
        payment_id,
        _,
    ) = args

    if access_token.first().swarco_token:
        # Authenticate user for SWARCO using refresh token
        auth_response = swarco_user_authentication_using_refresh_token(
            access_token, start_session_request.user
        )
        if auth_response.status_code == 200:
            # Successfully authenticated user
            response = swarco_start_session_api_call(
                auth_response,
                start_session_request.user,
                start_session_request.data,
                station,
                chargepoint,
                connector,
                payment_id,
            )
            return response
        print(
            f"User id-{start_session_request.user.id},\
                Refresh token authentication \
                failed by swarco,and new token generation process called \
                    using username and password"
        )
    # Following code is executing because user logged in for first time
    # either with MFG app or SWARCO
    print("SWRCO auth API called for new user")
    auth_response_by_swarco = swarco_generate_tokens_for_new_user(
        start_session_request.user
    )
    if auth_response_by_swarco.status_code == 200:
        # Successfully created tokens for new user
        response = swarco_start_session_api_call(
            auth_response_by_swarco,
            start_session_request.user,
            start_session_request.data,
            station,
            chargepoint,
            connector,
            payment_id,
        )
        return response
    return {
        "status_code": auth_response_by_swarco.status,
        "status": False,
        "message": "Failed to authenticate user for charging service",
    }


def swarco_stop_session_function(args):
    """this function stops SWARCO session"""
    (stop_session_request, access_token, _) = args

    if access_token.first():
        # Authenticate user for SWARCO using refresh token
        auth_response = swarco_user_authentication_using_refresh_token(
            access_token, stop_session_request.user
        )
        if auth_response.status_code == 200:
            response = swarco_stop_session_api_call(
                auth_response,
                stop_session_request.user,
                stop_session_request.data,
            )
            return response
        print(
            f"User id-{stop_session_request.user.id},\
            Refresh token \
                authentication failed by \
                    swarco for stop charging API,\
                        and new token generation process called \
                            using username and password"
        )
        auth_response_by_swarco = swarco_generate_tokens_for_new_user(
            stop_session_request.user
        )
        if auth_response_by_swarco.status_code == 200:
            # Successfully created tokens for new user
            response = swarco_stop_session_api_call(
                auth_response_by_swarco,
                stop_session_request.user,
                stop_session_request.data,
            )
            return response
        return {
            "status_code": auth_response.status,
            "status": False,
            "message": "Failed to authenticate user for \
                charging service",
        }
    # failed to load tokens of user
    return {
        "status_code": status.HTTP_501_NOT_IMPLEMENTED,
        "status": False,
        "message": "Something went wrong.",
    }


def swarco_force_stop_session_function(args):
    """this function forcely stops SWARCO session"""
    force_stop_session = args[0]
    access_token = Profile.objects.filter(user=force_stop_session.user)
    # Authenticate user for SWARCO using refresh token
    auth_response = swarco_user_authentication_using_refresh_token(
        access_token, force_stop_session.user
    )
    response_data = {}
    if auth_response.status_code == 200:
        # successfully authenticated user using refresh token
        content = json.loads(auth_response.content)
        access_token.update(
            swarco_token=content["access_token"],
            swarco_refresh_token=content["refresh_token"],
        )

        response_data["status_code"] = "Stopped"
        response_data["emp_session_id"] = force_stop_session.data[
            "emp_session_id"
        ]
        response_data["access_token"] = content["access_token"]
        response_data["refresh_token"] = content["refresh_token"]
        return {
            "status_code": status.HTTP_200_OK,
            "status": True,
            "message": SESSION_CLOSED,
            "data": response_data,
        }
    # failed to authenticate user using refresh token so generating new
    # tokens for user
    auth_response_by_swarco = swarco_generate_tokens_for_new_user(
        force_stop_session.user
    )
    if auth_response_by_swarco.status_code == 200:
        print(
            f"User id-{force_stop_session.user.id},\
            Successfully authenticated user using \
            username and password for stop API by SWARCO."
        )
        content = json.loads(auth_response_by_swarco.data)
        access_token.update(
            swarco_token=content["access_token"],
            swarco_refresh_token=content["refresh_token"],
        )

        response_data["status_code"] = "Stopped"
        response_data["emp_session_id"] = force_stop_session.data[
            "emp_session_id"
        ]
        response_data["access_token"] = content["access_token"]
        response_data["refresh_token"] = content["refresh_token"]
        return {
            "status_code": status.HTTP_200_OK,
            "status": True,
            "message": SESSION_CLOSED,
            "data": response_data,
        }

    # Also failed to create new tokens for user so sending old tokens
    # from db
    response_data["status_code"] = "Stopped"
    response_data["emp_session_id"] = force_stop_session.data["emp_session_id"]
    response_data["access_token"] = access_token.first().swarco_token
    response_data["refresh_token"] = access_token.first().swarco_refresh_token
    return {
        "status_code": status.HTTP_200_OK,
        "status": True,
        "message": SESSION_CLOSED,
        "data": response_data,
    }
