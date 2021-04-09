# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Renders the time difference between to given times
"""
from django.template import Library, Node, Variable, TemplateSyntaxError
from django.template.defaultfilters import pluralize

from .common_helpers import get_var

# pylint:disable=invalid-name
register = Library()


class NaturalTimeDifferenceNode(Node):
    """
    Class for computing and rendering time differences
    """
    def __init__(self, start, end):
        self.start = Variable(start)
        self.end = Variable(end)

    def render(self, context):
        """
        Render the response
        """
        start = get_var(self.start, context)
        end = get_var(self.end, context)
        delta = end - start
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, remainder = divmod(remainder, 60)
        seconds = remainder
        human_delta = ''
        if days > 0:
            if human_delta:
                human_delta += ', '
            human_delta += '%i day%s' % (days, pluralize(days))
        if hours > 0:
            if human_delta:
                human_delta += ', '
            human_delta += '%i hour%s' % (hours, pluralize(hours))
        if minutes > 0:
            if human_delta:
                human_delta += ', '
            human_delta += '%i minute%s' % (minutes, pluralize(minutes))
        if seconds > 0:
            if human_delta:
                human_delta += ', '
            human_delta += '%i second%s' % (seconds, pluralize(seconds))
        return human_delta


def natural_time_difference(_, token):
    """
    Return NaturalTimeDifference Node
    """
    args = token.split_contents()[1:]
    if len(args) != 2:
        raise TemplateSyntaxError('%r tag requires two datetimes.' % token.contents.split()[0])
    return NaturalTimeDifferenceNode(*args)


register.tag('natural_time_difference', natural_time_difference)
