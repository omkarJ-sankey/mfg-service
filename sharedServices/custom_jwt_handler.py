"""custom jwt handler"""
from rest_framework_simplejwt.tokens import RefreshToken


def   jwt_payload_handler(user):
    """this returns the access token for user"""
    refresh = RefreshToken.for_user(user)

    return str(refresh.access_token)


def jwt_payload_for_third_party_user(user):
    """this function returns access token and refresh
        token for third party user"""
    refresh = RefreshToken.for_user(user)
    return [str(refresh.access_token), str(refresh)]
