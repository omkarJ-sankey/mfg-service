"""configurations forms"""
from django import forms
from django.forms import ModelForm

# pylint:disable=import-error
from sharedServices.model_files.config_models import (
    ConnectorConfiguration,
    MapMarkerConfigurations,
    ServiceConfiguration,
    BaseConfigurations,
)
from sharedServices.constants import CONNECTOR_CLASS, FORM_CONTAINER


class ConnectorRegistrationForm(ModelForm):
    """connector registration form"""

    class Meta:
        """meta data"""

        model = ConnectorConfiguration
        fields = ["connector_plug_type", "image_path"]
        widgets = {
            "connector_plug_type": forms.TextInput(
                attrs={"class": CONNECTOR_CLASS}
            ),
            "image_path": forms.TextInput(attrs={"class": CONNECTOR_CLASS}),
        }
        labels = {
            "connector_plug_type": ("Connector Type"),
            "image_path": ("Image"),
        }


class ServiceRegistrationForm(ModelForm):
    """service registartion form"""

    class Meta:
        """meta data"""

        model = ServiceConfiguration
        fields = ["service_name", "image_path"]
        widgets = {
            "service_name": forms.TextInput(attrs={"class": CONNECTOR_CLASS}),
            "image_path": forms.TextInput(attrs={"class": CONNECTOR_CLASS}),
        }
        labels = {
            "service_name": ("Name"),
            "image_path": ("Image"),
        }


class ShopRegistrationForm(ModelForm):
    """shop registration form"""

    class Meta:
        """meta data"""

        model = ServiceConfiguration
        fields = ["service_name", "service_type", "image_path"]
        widgets = {
            "service_name": forms.TextInput(attrs={"class": CONNECTOR_CLASS}),
            "service_type": forms.TextInput(attrs={"class": CONNECTOR_CLASS}),
            "image_path": forms.TextInput(attrs={"class": CONNECTOR_CLASS}),
        }
        labels = {
            "service_name": ("Name"),
            "service_type": ("Type"),
            "image_path": ("Image"),
        }


class AddMapMarkerInfoForm(ModelForm):
    """add marker form"""

    class Meta:
        """meta data"""

        model = MapMarkerConfigurations
        fields = ["map_marker_key", "map_marker_image"]
        widgets = {
            "map_marker_key": forms.TextInput(
                attrs={
                    "class": FORM_CONTAINER,
                    "placeholder": "Enter map marker key name",
                }
            ),
        }
        labels = {
            "map_marker_key": ("Marker key/name"),
            "map_marker_image": ("Marker image"),
        }


class AddBaseConfigurationsForm(ModelForm):
    """add marker form"""

    class Meta:
        """meta data"""

        model = BaseConfigurations
        fields = [
            "base_configuration_key",
            "base_configuration_value",
            "base_configuration_image",
        ]
        widgets = {
            "base_configuration_key": forms.TextInput(
                attrs={
                    "class": FORM_CONTAINER,
                    "placeholder": "Enter base configuration key name",
                }
            ),
            "base_configuration_value": forms.TextInput(
                attrs={
                    "class": FORM_CONTAINER,
                    "placeholder": "Enter base configuration value",
                }
            ),
        }
        labels = {
            "base_configuration_key": ("Configuration key"),
            "base_configuration_value": ("Configuration value"),
            "base_configuration_image": ("Configuration image"),
        }
