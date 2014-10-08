from django.template import Library, Node, Variable, VariableDoesNotExist, TemplateSyntaxError
 
register = Library()

@register.simple_tag
def colour_table_row(status):
    if status == 'Error':
        return 'danger'
    if status == 'Processing':
        return 'warning'
    if status == 'Queued':
        return 'info'
    return status
