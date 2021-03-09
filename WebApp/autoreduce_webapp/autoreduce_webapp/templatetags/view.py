# ############################################################################### #
# Autoreduction Repository : https://github.com/ISISScientificComputing/autoreduce
#
# Copyright &copy; 2019 ISIS Rutherford Appleton Laboratory UKRI
# SPDX - License - Identifier: GPL-3.0-or-later
# ############################################################################### #
"""
Taken from: https://djangosnippets.org/snippets/1568/
"""
from django.conf import settings
from django.template import Library, Node, TemplateSyntaxError, Variable
from django.urls import get_callable, URLResolver

# pylint:disable=invalid-name
register = Library()


class ViewNode(Node):
    """
    Handles the ViewNode
    """
    def __init__(self, url_or_view, args, kwargs):
        self.url_or_view = url_or_view
        self.args = args
        self.kwargs = kwargs

    def render(self, context):
        """
        Render the view node
        """
        if 'request' not in context:
            return ""
        request = context['request']

        url_or_view = Variable(self.url_or_view).resolve(context)
        try:
            urlconf = getattr(request, "urlconf", settings.ROOT_URLCONF)
            resolver = URLResolver(r'^/', urlconf)
            view, args, kwargs = resolver.resolve(url_or_view)
        # pylint: disable=bare-except
        except:
            view = get_callable(url_or_view)
            args = [Variable(arg).resolve(context) for arg in self.args]
            kwargs = {}
            for key, value in self.kwargs.items():
                kwargs[key] = Variable(value).resolve(context)

        try:
            if callable(view):
                render_fnc = view(context['request'], *args, **kwargs).content.\
                    decode('unicode_escape')
                return render_fnc
            raise "%r is not callable" % view
        # pylint: disable=bare-except
        except:
            if settings.DEBUG_PROPAGATE_EXCEPTIONS:
                raise
        return ""


def do_view(_, token):
    """
    Inserts the output of a view, using fully qualified view name (and then some
    args), a or local Django URL.

     {% view view_or_url arg[ arg2] k=v [k2=v2...] %}

    This might be helpful if you are trying to do 'on-server' AJAX of page
    panels. Most browsers can call back to the server to get panels of content
    asynchonously, whilst others (such as mobiles that don't support AJAX very
    well) can have a template that embeds the output of the URL synchronously
    into the main page. Yay! Go the mobile web!

    Follow standard templatetag instructions for installing.

    IMPORTANT: the calling template must receive a context variable called
    'request' containing the original HttpRequest. This means you should be OK
    with permissions and other session state.

    ALSO NOTE: that middleware is not invoked on this 'inner' view.

    Example usage...

    Using a view name (or something that evaluates to a view name):
     {% view "mymodule.views.inner" "value" %}
     {% view "mymodule.views.inner" keyword="value" %}
     {% view "mymodule.views.inner" arg_expr %}
     {% view "mymodule.views.inner" keyword=arg_expr %}
     {% view view_expr "value" %}
     {% view view_expr keyword="value" %}
     {% view view_expr arg_expr %}
     {% view view_expr keyword=arg_expr %}

    Using a URL (or something that evaluates to a URL):
     {% view "/inner" %}
     {% view url_expr %}


    (Note that every argument will be evaluated against context except for the
    names of any keyword arguments. If you're warped enough to need evaluated
    keyword names, then you're probably smart enough to add this yourself!)

    """

    args = []
    kwargs = {}
    tokens = token.split_contents()
    if len(tokens) < 2:
        raise TemplateSyntaxError("%r tag requires one or more arguments" % token.contents.split()[0])
    _ = tokens.pop(0)
    url_or_view = tokens.pop(0)
    # pylint: disable=redefined-argument-from-local
    for token in tokens:
        equals = token.find("=")
        if equals == -1:
            args.append(token)
        else:
            kwargs[str(token[:equals])] = token[equals + 1:]
    return ViewNode(url_or_view, args, kwargs)


register.tag('view', do_view)
