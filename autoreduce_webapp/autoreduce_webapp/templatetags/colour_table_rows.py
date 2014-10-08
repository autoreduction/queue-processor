from django.template import Library, Node, Variable, VariableDoesNotExist, TemplateSyntaxError
 
register = Library()

@register.simple_tag
def colour_table_row(status):
    if status is 'error':
        return 'danger'
    if status is 'processing':
        return 'warning'
    if status is 'queued':
        return 'info'
    return ''
