from django import forms
from django.core.validators import RegexValidator

from .conutry_codes import COUNTRY_CODES


class DisplayBlockUserForm(forms.Form):
    action = forms.ChoiceField(
        label="Action",
        widget=forms.Select({
            "class": "form-select mb-3",
            "onchange": "togglePhoneOrEmailField(this.value)"
        }),
        choices=tuple(
            [
                ("", "Select"),
                ("1", "Remove user phone verification"),
                ("2", "Block user account from the app"),
                ("3", "Block user phone number")
            ]
        )
    )
    email = forms.EmailField(
        label="Email",
        required=False,
        max_length=300,
        min_length=2,
        widget=forms.EmailInput({
            "class": "form-control",
            "placeholder": "Johndoe@gmail.com",
            "id": "email"
        })
    )
    country_code = forms.ChoiceField(
        label="Country Code",
        required=False,
        widget=forms.Select({
            "class": "form-select mb-3",
            'id': 'country_code'    
        }),
        choices=tuple(
            [
                ("", "Select country code"),
            ]+ [
                (
                    country["countryCode"],
                    f"({country['countryCode']}) {country['country']}"
                )
                for country in COUNTRY_CODES
            ]
        )
    )
    phone = forms.CharField(
        label="Phone",
        required=False,
        widget=forms.TextInput({
            "type": "tel",
            "class": "form-control",
            "placeholder": "6677887799",
            "pattern" : r"[1-9]\d{8,14}$",
            "id": "phone"
        }),
        validators=[
            RegexValidator(
                r"^(d{1,3})?,?\s?\d{8,14}",
                message="Please provide valid phone number"
            )
        ]
    )

