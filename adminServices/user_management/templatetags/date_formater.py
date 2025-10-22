"""date formater for templates"""
from django import template
from django.utils import timezone

register = template.Library()


@register.filter(name="date_formater", is_safe=True)
# pylint:disable=unused-argument
def date_formater(val, precision=2):
    """this function formats dates for templates"""
    try:
        if val:
            date = timezone.localtime(val).strftime("%d/%m/%Y %H:%M").split()
        else:
            return ""
    except ValueError:
        # pylint:disable=raise-missing-from
        raise template.TemplateSyntaxError(
            f"Value must be an integer. {val} is not an string"
        )
    return date[0] + " at " + date[1]

@register.filter(name="wallet_amount", is_safe=False)
def wallet_amount(val, precision=2):
    try:
        if val:
            return str(float(val)/100)
        return "Not available"
    except ValueError:
        raise template.TemplateSyntaxError(
            f"Value must be an date. {val} is not an date"
        )
