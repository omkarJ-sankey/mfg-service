from rest_framework import serializers
import re
from sharedServices.common import (
    generate_token_func,
    email_validator,
    otp_validator,
    password_validator,
    set_token_cache,
)

class AdminLoginRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(required=False)

    def validate_email(self, value):
        if not email_validator(value):
            raise serializers.ValidationError("Please provide email with right format")
        return value

    def validate_password(self, value):
        if not password_validator(value):
            raise serializers.ValidationError(
                "Password length should be more than 8, \
                        and must contain one uppercase letter, one lowercase \
                            and one special character."
            )
        return value
    
class AdminOTPVerificationRequestSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(required=True)
    otp = serializers.CharField(required=True, max_length=4)

    def validate_otp(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("OTP must be numeric")
        return value
