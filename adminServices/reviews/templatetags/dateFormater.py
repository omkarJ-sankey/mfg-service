from django import template
from datetime import datetime as dt

register = template.Library()

# This is custom function for format date in template
@register.filter(name="date_formater", is_safe=False)
def date_formater(val, precision=2):
    try:
        date_ = val
    except ValueError:
        raise template.TemplateSyntaxError(
            f"Value must be an date. {val} is not an date"
        )
    if date_:
        return str(date_.day) + "/" + str(date_.month) + "/" + str(date_.year)
    else:
        return "-"
