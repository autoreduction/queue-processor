"""
Node for handling replacing
"""
from django.template import Library, Node, Variable, TemplateSyntaxError

from WebApp.autoreduce_webapp.autoreduce_webapp.templatetags.common_helpers import get_var


register = Library()


class ReplaceNode(Node):
    """
    Node for replacing text
    """
    def __init__(self, s, old, new):
        self.s = Variable(s)
        self.old = Variable(old)
        self.new = Variable(new)

    def render(self, context):
        """
        Render the replace text Node
        """
        s = unicode(get_var(self.s, context))
        old = unicode(get_var(self.old, context))
        new = unicode(get_var(self.new, context))
        return s.replace(old, new)


@register.tag
def replace(_, token):
    """
    Return the ReplaceNode
    """
    args = token.split_contents()[1:]
    if len(args) != 3:
        raise TemplateSyntaxError('%r tag requires a string, an old value, and a new value.'
                                  % token.contents.split()[0])
    return ReplaceNode(*args)
