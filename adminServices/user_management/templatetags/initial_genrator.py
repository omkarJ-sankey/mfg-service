"""name initials generator"""
from django import template

register = template.Library()


@register.filter(name="initial_genrator", is_safe=False)
# pylint:disable=unused-argument
def initial_genrator(val, precision=2):
    """this functions returns name initials"""
    try:
        initials = ""
        name = val.split()
        if len(name) > 1:
            initials = name[0][0] + name[-1][0]
        else:
            initials = "UU"
    except ValueError:
        # pylint:disable=raise-missing-from
        raise template.TemplateSyntaxError(
            f"Value must be an integer. {val} is not an string"
        )
    return initials.upper()
