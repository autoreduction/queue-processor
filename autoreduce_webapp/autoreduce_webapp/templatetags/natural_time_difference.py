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
        start = get_var(self.start, context)
        end = get_var(self.end, context)
        delta = end - start
        days = delta.days
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, remainder = divmod(remainder, 60)
        seconds = remainder
        human_delta = ''
        if days > 0:
            if len(human_delta) > 0:
                human_delta += ', '
            human_delta += '%i days' % days
        if hours > 0:
            if len(human_delta) > 0:
                human_delta += ', '
            human_delta += '%i hours' % hours
        if minutes > 0:
            if len(human_delta) > 0:
                human_delta += ', '
            human_delta += '%i minutes' % minutes
        if seconds > 0:
            if len(human_delta) > 0:
                human_delta += ', '
            human_delta += '%i seconds' % seconds
        return human_delta


def natural_time_difference(parser, token):
    args = token.split_contents()[1:]
    if len(args) != 2:
        raise TemplateSyntaxError, '%r tag requires two datetimes.' % token.contents.split()[0]
    return NaturalTimeDifferenceNode(*args)

register.tag('natural_time_difference', natural_time_difference)