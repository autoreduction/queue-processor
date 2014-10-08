from django.template import Library, Node, Variable, VariableDoesNotExist, TemplateSyntaxError
 
register = Library()

@register.simple_tag
def colour_table_row(parser, token):
    args = token.split_contents()[1:]
    if len(args) != 1:
        raise TemplateSyntaxError, '%r tag requires a single string' % token.contents.split()[0]
    status = args[0]
    if status is 'error':
        return 'danger'
    if status is 'processing':
        return 'warning'
    if status is 'queued':
        return 'info'
    return ''
