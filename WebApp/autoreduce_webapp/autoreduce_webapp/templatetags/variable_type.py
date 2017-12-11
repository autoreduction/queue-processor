from django.template import Library
 
register = Library()

@register.simple_tag
def variable_type(var_type):
    if var_type == 'boolean':
        return 'checkbox'
    if var_type == 'list_number' or var_type == 'list_text':
        return 'text'
    return var_type
