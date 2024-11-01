from django import template

register = template.Library()

@register.filter
def wrap_text(value, length=50):
    """Wrap text after a specified number of characters."""
    return '<br>'.join([value[i:i + length] for i in range(0, len(value), length)])


@register.filter(name='range')
def range_filter(value):
    return range(value)