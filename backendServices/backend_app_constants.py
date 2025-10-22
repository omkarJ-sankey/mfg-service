"""backend responses"""
from rest_framework.response import Response
from rest_framework import status

TRIP_NOT_FOUND = Response(
    {
        "status_code": status.HTTP_404_NOT_FOUND,
        "status": False,
        "message": "Trip with provided id not found!!",
    }
)
TRIP_ID_NOT_PROVIDED = Response(
    {
        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
        "status": False,
        "message": "Trip id not provided!!",
    }
)
INVALID_TRIP_ID = Response(
    {
        "status_code": status.HTTP_406_NOT_ACCEPTABLE,
        "status": False,
        "message": "Provided trip id is not valid!!",
    }
)
UNAUTHORIZED = Response(
    {
        "status_code": status.HTTP_401_UNAUTHORIZED,
        "status": False,
        "message": "Not authorized.",
    }
)

MULTIPLE_LOGIN = Response(
    {
        "status_code": status.HTTP_409_CONFLICT,
        "status": False,
        "message": "You have logged in from another device!",
    }
)

DATA_NOT_FOUND = Response(
    {
        "status_code": status.HTTP_200_OK,
        "status": True,
        "message": "Data Not found",
    }
)
DATA_INVALID = Response(
    {
        "status_code": status.HTTP_403_FORBIDDEN,
        "status": False,
        "message": "Invalid data",
    }
)
SERVER_ERROR = Response(
    {
        "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "status": False,
        "message": "Something went wrong",
    }
)

# constant for getting currency symbols dynamically
CURRENCY_SYMBOLS = {"Euro": "(€)", "GBP": "(£)"}
