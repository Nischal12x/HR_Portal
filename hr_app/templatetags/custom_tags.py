from django import template
import calendar
register = template.Library()
import datetime
from django.utils import timezone

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

# Keep your existing get_badge_class filter
@register.filter(name='get_badge_class')
def get_badge_class(status):
    # ... your existing logic here ...
    return {
        'Pending': 'bg-warning',
        'In Progress': 'bg-info',
        'Completed': 'bg-success',
        'Claimed Completed': 'bg-primary',
    }.get(status, 'bg-secondary')


# Add the new filter for progress calculation
@register.filter(name='calculate_progress')
def calculate_progress(task):
    if not isinstance(task.start_date, datetime.date) or not isinstance(task.end_date, datetime.date):
        return 0 # Or handle as an error/default

    today = timezone.now().date()
    
    if today < task.start_date:
        return -1  # Indicates "not started"
        
    if today > task.end_date or task.status == 'Completed':
        return 100

    total_duration = (task.end_date - task.start_date).days
    elapsed_duration = (today - task.start_date).days

    if total_duration == 0:
        return 100  # Task is for a single day and it's today

    progress = (elapsed_duration / total_duration) * 100
    return min(int(progress), 100) # Return as an integer, cap at 100