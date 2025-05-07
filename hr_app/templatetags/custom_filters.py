
from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def slice_first(value, count):
    if value is None:
        return []
    return value[:count]


@register.filter
def length_gt(value, count):
    if value is None:
        return False
    return len(value) > count

