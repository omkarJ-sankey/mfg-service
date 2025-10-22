from rest_framework import serializers
from sharedServices.model_files.notifications_module_models import PushNotifications
from sharedServices.model_files.app_user_models import (
    MFGUserEV,
)
from cryptography.fernet import Fernet


class addPushNotificationSerializer(serializers.ModelSerializer):

    class Meta:
        model = PushNotifications
        fields = '__all__'
        

class getAllUsers(serializers.ModelSerializer):

    user_post_code = serializers.SerializerMethodField("get_post_code")
    user_country = serializers.SerializerMethodField("get_country")

    @classmethod
    def get_post_code(cls, user):
        """get post code"""
        decrypter = Fernet(user.key)
        return decrypter.decrypt(user.post_code).decode()
    
    @classmethod
    def get_country(cls, user):
        """get contry"""
        decrypter = Fernet(user.key)
        return decrypter.decrypt(user.country).decode()

    class Meta:
        model = MFGUserEV
        fields = ['id','user_post_code','last_login','email','password','first_name','last_name','username','user_country','key','customer_id','timestamp']
    
    
    