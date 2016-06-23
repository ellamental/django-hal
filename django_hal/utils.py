"""
General utilities for django_hal

"""

from django.core.urlresolvers import reverse as dj_reverse, NoReverseMatch
from rest_framework.reverse import reverse as rf_reverse

# TODO(nick): It may be a better idea to use the django sites framework to get
#     the base url to a resource, rather than the request.  This would decouple
#     the serializers from the views, and provide a nicer, but still uniform,
#     interface for working with the api when not in browser.  The current
#     solution will simply build a *different* url than would be built if the
#     request was present.
#
#     My guess is that the reason DRF uses the request is to handle versioning,
#     especially where developers use the url to implement that
#     (e.g., `/api/v1`).  Since that's not a practice I want to support
#     out-of-the-box, we can probably use the sites framework with no penalty.
#     We could make that an opt-in, where developers can make the explicit
#     trade-off of giving up these features to put versioning in the url (and
#     and possibly request headers).
#
def reverse(*args, **kwargs):
    """Allows use of the hyperlinked fields, without passing a request.

    This is very useful for situations where you don't have a request to pass,
    for instance, when using the shell or during testing.

    """
    request = kwargs.pop('request')
    if request:
        return rf_reverse(*args, request=request, **kwargs)
    else:
        return dj_reverse(*args, **kwargs)


def move_request_from_kwargs_to_context(kwargs):
    """Relocate ``kwargs['request']`` to ``kwargs['context']['request']``."""
    request = kwargs.pop('request', None)
    if request:
        if 'context' not in kwargs:
            kwargs['context'] = {'request': request}
        elif not kwargs['context'].get('request'):
            kwargs['context']['request'] = request
