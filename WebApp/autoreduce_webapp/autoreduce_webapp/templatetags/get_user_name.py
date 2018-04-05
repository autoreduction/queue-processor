"""
Handles finding the user name
"""
import logging

from django.template import Library, Node, Variable, TemplateSyntaxError
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe
from django.core.exceptions import ObjectDoesNotExist

from WebApp.autoreduce_webapp.autoreduce_webapp.templatetags.common_helpers import get_var

logger = logging.getLogger(__name__)
register = Library()


class UserNameNode(Node):
    """
    class for theUser name node
    """
    def __init__(self, user_number):
        self.user_number = Variable(user_number)

    def render(self, context):
        """
        Render the user name node
        """
        user_number = unicode(get_var(self.user_number, context))
        try:
            person = User.objects.get(username=user_number)
        except ObjectDoesNotExist:
            return mark_safe('Autoreduction Service')
        return mark_safe('<a href="mailto:' + person.email + '">'
                         + person.first_name + " " + person.last_name + '</a>')


@register.tag
def get_user_name(_, token):
    """
    get the user name
    :return: UsernameNode
    """
    args = token.split_contents()[1:]
    if len(args) != 1:
        raise TemplateSyntaxError('%r tag requires a single string.'
                                  % token.contents.split()[0])
    return UserNameNode(*args)
