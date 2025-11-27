from django import template

register = template.Library()

@register.filter
def split(value, separator=','):
    return [item.strip() for item in value.split(separator)]
