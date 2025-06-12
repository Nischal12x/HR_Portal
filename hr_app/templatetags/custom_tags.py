from django import template
import calendar
register = template.Library()

@register.simple_tag
def increment(value):
    return value + 1


@register.filter
def get_status_color(status):
    colors = {
        'Completed': '#198754',  # Bootstrap green
        'Pending': '#ffc107',    # Bootstrap yellow
        'Claimed Completed': '#0dcaf0'  # Bootstrap info
    }
    return colors.get(status, '#6c757d')  # default gray

@register.filter
def get_status_text_color(status):
    dark_text_statuses = ['Pending', 'Claimed Completed']
    return '#000' if status in dark_text_statuses else '#fff'

@register.filter
def pluck(queryset, attr):
    """Extracts a list of attribute values from a queryset or list."""
    return [getattr(item, attr, None) for item in queryset]

@register.filter
def contains(value, item):
    """Returns True if item is in value."""
    return item in value

@register.filter
def get_badge_class(status):
    status_map = {
        'Completed': 'bg-success text-white',
        'Pending': 'bg-warning text-dark',
        'Claimed Completed': 'bg-info text-dark'
    }
    return status_map.get(status, 'bg-secondary text-white')

@register.filter
def currency_format(value):
    try:
        return f"Rs.{float(value):,.2f}"
    except (ValueError, TypeError):
        return "Rs.0.00"
@register.filter
def month_name(month_number):
    return calendar.month_name[int(month_number)]