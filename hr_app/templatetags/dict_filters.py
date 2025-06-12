from django import template

register = template.Library()

@register.filter
def dictget(d, key):
    if isinstance(d, dict):
        return d.get(key, "")
    return ""
