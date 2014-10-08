from django.template import Library, Node, Variable, VariableDoesNotExist, TemplateSyntaxError
 
register = Library()

class ColourNode(Node):
 
    def __init__(self, status):
        self.status = Variable(status)
 
    def render(self, context):
        if get_var(self.status, context) is 'error':
            return 'danger'
        if get_var(self.status, context) is 'processing':
            return 'warning'
        if get_var(self.status, context) is 'queued':
            return 'info'
        return ''

@register.tag
def colour_table_row(parser, token):
    args = token.split_contents()[1:]
    if len(args) != 1:
        raise TemplateSyntaxError, '%r tag requires a single string' % token.contents.split()[0]
    status = args[0]
    return ColourNode(status)
