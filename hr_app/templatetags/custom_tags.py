from django import template

register = template.Library()

@register.simple_tag
def increment(value):
    return value + 1