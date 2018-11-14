from __future__ import unicode_literals

from collections import OrderedDict

from django import template
from django.contrib.sites.models import Site
from django.http import QueryDict
from django.utils.safestring import mark_safe
from django.utils.encoding import force_text
from django.template import Library, Node, Variable
from django.template.defaultfilters import stringfilter
from six.moves.urllib.parse import urlencode

register = template.Library()

from amp_tools.settings import settings


@register.simple_tag
def amp_canonical_link(request):
    getvars = OrderedDict(request.GET.copy().items())
    rel = "amphtml"
    if settings.AMP_TOOLS_GET_PARAMETER in getvars:
        del getvars[settings.AMP_TOOLS_GET_PARAMETER]
        rel = "canonical"
    else:
        getvars[settings.AMP_TOOLS_GET_PARAMETER] = settings.AMP_TOOLS_GET_VALUE
        getvars.move_to_end(settings.AMP_TOOLS_GET_PARAMETER, last=False)

    if len(getvars.keys()) > 0:
        getvars = urlencode(getvars)
    else:
        getvars = ''

    href = '%s?%s' % (request.path, getvars) if getvars else request.path

    href = "%s://%s%s" % (request.scheme, Site.objects.get_current().domain, href)

    return mark_safe('<link rel="%s" href="%s" />' % (rel, href))


class AddGetParameter(Node):
    def __init__(self, values, url=None):
        self.url = url
        self.values = values

    def render(self, context):
        if self.url:
            params = QueryDict(self.values)
        else:
            req = Variable('request').resolve(context)
            self.url = req.path
            params = req.GET.copy()

            for key, value in self.values.items():
                resolved = value.resolve(context)
                if resolved:
                    params[key] = value.resolve(context)

        return "{}?{}".format(self.url, params.urlencode())


@register.tag
def amp_link(parser, token):
    try:
        # split_contents() knows not to split quoted strings.
        tag_name, url = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires a single argument" % token.contents.split()[0]
        )
    if not (url[0] == url[-1] and url[0] in ('"', "'")):
        raise template.TemplateSyntaxError(
            "%r tag's argument should be in quotes" % tag_name
        )
    params = "{}={}".format(
        settings.AMP_TOOLS_GET_PARAMETER,
        settings.AMP_TOOLS_GET_VALUE
    )
    return AddGetParameter(params, url[1:-1])


@register.filter
def amp_urlparam(value):
    return "%s?%s=%s" % (value, settings.AMP_TOOLS_GET_PARAMETER, settings.AMP_TOOLS_GET_VALUE)


@register.filter(name='amp_img')
@stringfilter
def amp_img(html_code):
    """Convert <img> to <amp-img>"""
    return html_code.replace("<img", "<amp-img")
