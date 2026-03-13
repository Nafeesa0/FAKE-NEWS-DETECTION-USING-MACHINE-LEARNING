from django import template

register = template.Library()


@register.filter
def as_percent(value):
    """Convert a 0–1 float to a 0–100 float for display as a percentage."""
    try:
        return float(value) * 100
    except (TypeError, ValueError):
        return 0
