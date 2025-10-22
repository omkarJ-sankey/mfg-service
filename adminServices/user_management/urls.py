"""usermanagement urls"""
# File details-
#   Author      - Shubham Dhumal
#   Description - This file is declatre urlpatterns of usermangement
#   Name        - User Management urls
#   Modified by - Shubham Dhumal

from django.urls import path
from .views import (
    user_management,
    add_new_user,
    activate_user,
    deactivate_user,
    update_user,
    change_profile_picture,
    check_email_exist,
    check_username_exist,
)

# This are urls for user mangement
# 1. 'usermanagement/' it's render page
# 2. 'newuser/' it's end point for createing user
# 3. 'inactivate/, avtivate/' this endpoint change status of perticular user
# 4. 'updateuser/' this endpoind update user information
urlpatterns = [
    path("", user_management, name="usermanagement"),
    path("newuser/", add_new_user, name="newuser"),
    path("inactivate/", deactivate_user, name="inactivate"),
    path("activate/", activate_user, name="activate_user"),
    path("updateuser/", update_user, name="updateuser"),
    path(
        "update-user-picture/",
        change_profile_picture,
        name="change_profile_picture",
    ),
    path("validate-email/", check_email_exist, name="validate-email"),
    path("validate-user/", check_username_exist, name="validate-username"),
]
