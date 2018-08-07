"""
handles colouring table rows
"""
from django.template import Library

# pylint:disable=invalid-name
register = Library()


@register.simple_tag
def colour_table_row(status):
    """
    Switch statment for defining table colouring
    """
    if status == 'Error':
        return 'danger'
    if status == 'Processing':
        return 'warning'
    if status == 'Queued':
        return 'info'
    if status == 'Completed' or status == 'Skipped':
        return 'success'
    return status
