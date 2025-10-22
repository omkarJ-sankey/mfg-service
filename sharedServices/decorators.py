"""decorators"""
import jwt
from passlib.hash import django_pbkdf2_sha256 as handler

from django.utils import timezone
from django.shortcuts import redirect
from django.urls import resolve

from .model_files.admin_user_models import (
    AdminAuthorization,
    AdminUser,
    LoginRecords,
)
from .common import (
    generate_token_func,
    DJANGO_APP_REFRESH_TOKEN_SECRET,
    set_token_cache,
)
from .constants import YES


def decorator(cls):
    """decorator"""
    mod = __import__(cls.__module__)
    mod.root = cls


def unauthenticated_user(view_func):
    """unauthenticted user checker decorator"""

    def wrapper_func(request, *args, **kwargs):
        """warpper fun"""
        if (
            request.COOKIES.get("token", "default") != "default"
            and request.COOKIES.get("remember_me", "default") == YES
            and request.COOKIES.get("token_verification_string", "default")
            != "default"
        ):
            token = request.COOKIES["token"]
            hashed_token = request.COOKIES["token_verification_string"]
            if handler.verify(token, hashed_token):
                return redirect("dashboard")
        return view_func(request, *args, **kwargs)

    return wrapper_func


def check_token_availablity(token, request, view_func, *args, **kwargs):
    """check token"""
    token_exists = None
    try:
        token_exists_checker = AdminAuthorization.objects.filter(token=token)
        if token_exists_checker.first():
            token_exists = token_exists_checker.first()
        else:
            raise AttributeError("Token verification failed")
    except (TimeoutError, AttributeError):
        if (
            request.COOKIES.get("remember_me", "default") == YES
            and request.COOKIES.get("token_verification_string", "default")
            != "default"
        ):
            hashed_token = request.COOKIES["token_verification_string"]
            if handler.verify(token, hashed_token):
                if (
                    handler.verify(token, hashed_token)
                    and request.COOKIES.get("refresh_token", "default")
                    != "default"
                    and request.COOKIES.get("token_auth", "default")
                    != "default"
                ):
                    auth_payload = jwt.decode(
                        request.COOKIES["refresh_token"],
                        DJANGO_APP_REFRESH_TOKEN_SECRET,
                        algorithms=["HS256"],
                    )
                    hashed_authorization_id = request.COOKIES["token_auth"]
                    if handler.verify(
                        f"{auth_payload['authorization_id']}",
                        hashed_authorization_id,
                    ):
                        token_exists_checker = (
                            AdminAuthorization.objects.filter(
                                id=auth_payload["authorization_id"]
                            )
                        )
                        if token_exists_checker.first():
                            token_exists = token_exists_checker.first()
                        else:
                            return view_func(request, *args, **kwargs)
    return token_exists


def authenticated_user(view_func):
    """authenticated user checker decorator"""

    def wrapper_func(request, *args, **kwargs):
        """warpper fun"""
        current_url = resolve(request.path_info).url_name
        if request.COOKIES.get("token", "default") != "default":
            token = request.COOKIES["token"]

            token_exists = check_token_availablity(
                token, request, view_func, *args, **kwargs
            )

            if token_exists:
                user_status = LoginRecords.objects.get(
                    user_id=token_exists.user_id
                )
                if user_status == "Inactive":
                    return redirect("AdminLogin")
                payload = {}
                try:
                    payload = jwt.decode(
                        token, token_exists.token_secret, algorithms=["HS256"]
                    )
                except jwt.InvalidTokenError:
                    payload = jwt.decode(
                        token_exists.refresh_token,
                        DJANGO_APP_REFRESH_TOKEN_SECRET,
                        algorithms=["HS256"],
                    )
                user = AdminUser.objects.get(id=payload["user_id"])
                if (
                    timezone.localtime(timezone.now())
                    > token_exists.token_expire_time
                ):
                    admin_authorization = AdminAuthorization.objects.filter(
                        user_id_id=int(payload["user_id"])
                    )
                    if admin_authorization.first() is None:
                        response = redirect("AdminLogin")
                        response.delete_cookie("token")
                        return response
                    token_data = generate_token_func(
                        payload["user_id"], admin_authorization.first().id
                    )
                    admin_authorization.update(
                        token=str(token_data[0]),
                        token_secret=token_data[1],
                        refresh_token=token_data[3],
                        token_expire_time=token_data[2],
                    )
                    response = redirect(current_url)
                    response = set_token_cache(
                        token_data, request, response, admin_authorization
                    )
                    return response
                request.user = user
                return view_func(request, *args, **kwargs)
        response = redirect("AdminLogin")
        response.delete_cookie("token")
        return response

    return wrapper_func


def allowed_users(section=""):
    """allowed users decorator"""

    def decorator_func(view_func):
        def wrapper_func(request, *args, **kwargs):
            if request.user.role_id.access_content.filter(
                name=section
            ).first():
                return view_func(request, *args, **kwargs)
            return redirect("dashboard")

        return wrapper_func

    return decorator_func
