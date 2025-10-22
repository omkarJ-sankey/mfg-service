"""template tag"""
from django import template
from sharedServices.common import custom_round_function
register = template.Library()

@register.filter(name="wallet_amount_formatter", is_safe=False)
def wallet_amount_formatter(val, precision=2):
    try:
        if val:
            return str(custom_round_function(float(val), 2))
        return val
    except ValueError:
        raise template.TemplateSyntaxError(
            f"Invalid wallet balance"
        )
