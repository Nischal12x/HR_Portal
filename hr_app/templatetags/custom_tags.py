from django import template

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
def get_badge_class(status):
    status_map = {
        'Completed': 'bg-success text-white',
        'Pending': 'bg-warning text-dark',
        'Claimed Completed': 'bg-info text-dark'
    }
    return status_map.get(status, 'bg-secondary text-white')
