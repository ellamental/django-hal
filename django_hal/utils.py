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


def link(rel=None, name=None, profile=None, pattern=None):
    """A slightly nicer interface for creating a link dict.

    Parameters
    ----------
    rel : str
        The ``rel`` property of the link.  This should document the "relation"
        between the resources (not the resource itself).
    name : str
        The ``name`` property of the link.  The ``name`` should be used as a
        secondary means of identification (useful primarily when there are
        multiple links for a single ``rel``).
    profile : str
        The ``profile`` property of the link.  This should identify and
        document the "resource type" this relation refers to.  This parameter
        should be a currie and/or url pattern.
    pattern : Union[str, dict]
        A url pattern to pass to ``reverse`` (generates the ``href`` property).
        If the pattern requires kwargs or the resulting url should have a query
        string appended, you may pass a dict.  See ``pattern`` for more
        information.

    Returns
    -------
    dict
        A dict containing all the parameters.

    """
    # Support a shorthand for keyword arguments.  Where the keyword and the
    # attribute are the same, you may use a string instead of a dict with the
    # same key/value (e.g., 'pk' instead of {'pk': 'pk'}.
    #
    return {
        'rel': rel,
        'name': name,
        'profile': profile,
        'pattern': pattern,
    }


def pattern(pattern, kwargs=None, query=None):
    """A slightly nicer interface for creating a url pattern dict.

    Parameters
    ----------
    pattern : str
        The url pattern.
    kwargs : dict
        A dict of {'kwarg': 'attribute'}, where `kwarg` is the keyword argument
        used in the urlconf, and `attribute` is the instance attribute to get
        the value from.
    query : dict
        A dict of {'kwarg': 'attribute'}, where `kwarg` is the keyword argument
        to be used in query string, and `attribute` is the instance attribute
        to get the value from.

    Returns
    -------
    dict
        A dict containing all the parameters.

    """
    # Support a shorthand for keyword arguments.  Where the keyword and the
    # attribute are the same, you may use a string instead of a dict with the
    # same key/value (e.g., 'pk' instead of {'pk': 'pk'}.
    #
    if isinstance(kwargs, basestring):
        kwargs = {kwargs: kwargs}

    return {
        'pattern': pattern,
        'kwargs': kwargs,
        'query': query,
    }
