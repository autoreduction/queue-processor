from django.template import Library, Node, Variable, VariableDoesNotExist, TemplateSyntaxError
 
register = Library()

@register.simple_tag
def colour_table_row(status):
    if status is 'Error':
        return 'danger'
    if status is 'Processing':
        return 'warning'
    if status is 'Queued':
        return 'info'
    return status
