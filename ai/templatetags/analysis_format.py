import re
from decimal import Decimal

from django import template
from django.utils.formats import number_format

register = template.Library()

# The tools write money with 2 decimals, percentages with 1 and counts with
# none, so only money has this shape.
MONEY_PATTERN = re.compile(r'-?[0-9]+\.[0-9]{2}')


@register.filter
def evidence_value(value):
    """Show a money evidence as R$ 1.234,56, and anything else unchanged."""
    if not MONEY_PATTERN.fullmatch(str(value)):
        return value
    amount = number_format(Decimal(value), 2, force_grouping=True)
    return f'R$ {amount}'
