from django.template import Library, Node, Variable, \
    VariableDoesNotExist, TemplateSyntaxError
from django.contrib.auth.models import User
from django.utils.safestring import mark_safe

register = Library()
 
def get_var(v, context):
    try:
        return v.resolve(context)
    except VariableDoesNotExist:
        return v.var
 
class UserNameNode(Node):
 
    def __init__(self, usernumber):
        self.usernumber = Variable(usernumber)
 
    def render(self, context):
        usernumber = unicode(get_var(self.usernumber, context))
        person = User.objects.get(username=usernumber)
        return mark_safe('<a href="mailto:' + person.email + '">'+ person.first_name + " " + person.last_name + '</a>')
 
@register.tag
def get_user_name(parser, token):
    args = token.split_contents()[1:]
    if len(args) != 1:
        raise TemplateSyntaxError, '%r tag requires a single string.' % token.contents.split()[0]
    return UserNameNode(*args)