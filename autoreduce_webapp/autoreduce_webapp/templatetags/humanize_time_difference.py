from django.template import Library, Node, Variable, VariableDoesNotExist, TemplateSyntaxError

register = Library()
 
def get_var(v, context):
    try:
        return v.resolve(context)
    except VariableDoesNotExist:
        return v.var

class NaturalTimeDifferenceNode(Node):

    def __init__(self, start, end):
        self.start = Variable(start)
        self.end = Variable(end)
 
    def render(self, context):
        start = unicode(get_var(self.start, context))
        end = unicode(get_var(self.end, context))
        delta = end - start
        human_delta = ''
        if delta.days > 0:
            if len(human_delta) > 0:
                human_delta += ', '
            human_delta += '%i days' % delta.days
        if delta.hours > 0:
            if len(human_delta) > 0:
                human_delta += ', '
            human_delta += '%i hours' % delta.hours
        if delta.minutes > 0:
            if len(human_delta) > 0:
                human_delta += ', '
            human_delta += '%i minutes' % delta.minutes
        if delta.seconds > 0:
            if len(human_delta) > 0:
                human_delta += ', '
            human_delta += '%i seconds' % delta.seconds
        return human_delta


@register.tag
def natural_time_difference(parser, token):
    args = token.split_contents()[1:]
    if len(args) != 2:
        raise TemplateSyntaxError, '%r tag requires two datetimes.' % token.contents.split()[0]
    return NaturalTimeDifferenceNode(*args)
