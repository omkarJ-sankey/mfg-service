"""date formater for templates"""
from django import template

register = template.Library()


@register.filter(name="offers_date_formater", is_safe=True)
# pylint:disable=unused-argument
def offers_date_formater(val, precision=2):
    """this function formats dates for templates"""
    try:
        if val:
            date = val.strftime("%d/%m/%Y %H:%M").split()
        else:
            return ""
    except ValueError:
        # pylint:disable=raise-missing-from
        raise template.TemplateSyntaxError(
            f"Value must be an integer. {val} is not an string"
        )
    return date[0] + " at " + date[1]
