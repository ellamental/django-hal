"""
HAL serializers for Django REST Framework.

"""

from __future__ import print_function

from collections import OrderedDict

from django.core.urlresolvers import reverse as dj_reverse, NoReverseMatch
from django.utils.http import urlencode
from rest_framework import serializers
from rest_framework.reverse import reverse as rf_reverse
from rest_framework.utils.serializer_helpers import ReturnDict


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


class LinksField(serializers.DictField):
    """HAL-style _links field.

    Parameters
    ----------
    *args : tuple
        A tuple representing the relation name, and arguments to
        reverse the url.  Example: `(name, urlpattern, {'pk', 'pk'})`.

        name : str
            The string used to identify the url in the final output.
        urlpattern : str
            A named urlpattern.
        kwargs : dict
          The kwargs to pass (with the urlpattern) to `reverse`.

          This is a dict where the key is the url kwarg, and the value is the
          attribute to lookup on the instance.  So, `{'user', 'pk'}` would
          translate to `{'user': getattr(instance, 'pk')}`.

    Example
    -------

        MySerializer(serializers.Serializer):
            _links = LinksField(
                ('self', 'namespace:view-name', {'pk': 'pk'})
            )

        # Outputs:
        #
        #     {
        #       '_links': {
        #         'self': 'https://.../my-resource/34'
        #       }
        #     }

      A shorthand syntax is available to reduce the repetitiveness of
      `{'pk': 'pk'}`, when both the kwarg and the instance attribute name
      are the same.

          ('ref', 'urlpattern', 'pk')

      is equivalent to

          ('ref', 'urlpattern', {'pk': 'pk'})

      In a full example that looks like:

          MySerializer(serializers.Serializer):
              _links = LinksField(
                  ('self', 'namespace:view-name', 'pk')
              )

          # Outputs:
          #
          #     {
          #         '_links': {
          #             'self': { 'href': 'https://.../my-resource/34' }
          #         }
          #     }

    """

    def __init__(self, *links):
        super(LinksField, self).__init__(read_only=True)
        self.links = links

    def to_representation(self, instance):
        """Return an ordered dictionary of HAL-style links."""
        request = self.context.get('request')
        ret = OrderedDict()
        for link in self.links:
            name = link[0]
            ret[name] = self.to_link(request, instance, *link[1:])
        return ret

    def get_attribute(self, instance, *args, **kwargs):
        """Return the whole instance, instead of looking up an attribute value.

        Implementation note: We do this because `Serializer.to_representation`
        builds the list of serializer fields with something like:

            for field in serializer_fields:
              field.to_representation(field.get_attribute(instance))

        Since we need the instance in `to_representation` so we can query arbitrary
        attributes on it to build urls, we simply have to return the instance here.
        """
        return instance

    def to_link(self, request, instance, urlpattern, kwargs=None,
                query_kwargs=None):
        """Return an absolute url for the given urlpattern."""
        if query_kwargs:
            query_kwargs = {k: getattr(instance, v) for k, v in query_kwargs.items()}
        if not kwargs:
            url = reverse(urlpattern, request=request)
            if not query_kwargs:
                return {'href': url}
            return {'href': '%s?%s' % (url, urlencode(query_kwargs))}

        if isinstance(kwargs, basestring):
            # `(ref, urlpattern, string)` where `string` is equivalent to
            # `{string: string}`
            url = reverse(urlpattern,
                          kwargs={kwargs: getattr(instance, kwargs)},
                          request=request)
            if not query_kwargs:
                return {'href': url}
            return {'href': '%s?%s' % (url, urlencode(query_kwargs))}

        reverse_kwargs = {}
        if kwargs:
            for k, v in kwargs.items():
                reverse_kwargs[k] = getattr(instance, v)
        try:
            url = reverse(urlpattern, kwargs=reverse_kwargs, request=request)
            if not query_kwargs:
                return {'href': url}
            return {'href': '%s?%s' % (url, urlencode(query_kwargs))}
        except NoReverseMatch:
            return None


# Serializers
# ===========

class BaseSerializerDataMixin(object):
    """Mixin to include ``rest_framework.serializers.BaseSerializer.data``.

    The only reason this exists is to provide access to the BaseSerializer's
    implementation of ``.data``, when you've super-classed a super-class of
    ``BaseSerializer`` that overrides ``.data`` with an incompatible
    implementation.

    This is implemented as a mixin to make it simple to keep this up-to-date
    with ``rest_framework.serializers.BaseSerializer`` and avoid coupling this
    to any specific implementation.

    Motivation:

    Due to the way super works, you can't call ``.data`` on the superclass's
    superclass, without also calling it on the superclass.  This is a problem
    for ``HALListSerializer`` because it's super class,
    ``rest_framework.serializers.ListSerializer``, implements ``.data`` as
    ``return ReturnList(super(ListSerializer, self).data)``.  This essentially
    converts the HAL-format dict we return in ``to_representation`` to a list
    of the dict's keys (``['_links', '_embedded']``).

    """
    def base_serializer_data(self):
        if hasattr(self, 'initial_data') and not hasattr(self, '_validated_data'):
            msg = (
                'When a serializer is passed a `data` keyword argument you '
                'must call `.is_valid()` before attempting to access the '
                'serialized `.data` representation.\n'
                'You should either call `.is_valid()` first, '
                'or access `.initial_data` instead.'
            )
            raise AssertionError(msg)

        if not hasattr(self, '_data'):
            if self.instance is not None and not getattr(self, '_errors', None):  # noqa
                self._data = self.to_representation(self.instance)
            elif hasattr(self, '_validated_data') and not getattr(self, '_errors', None):  # noqa
                self._data = self.to_representation(self.validated_data)
            else:
                self._data = self.get_initial()

        return self._data


def move_request_from_kwargs_to_context(kwargs):
    """Relocate ``kwargs['request']`` to ``kwargs['context']['request']``."""
    request = kwargs.pop('request', None)
    if request:
        if 'context' not in kwargs:
            kwargs['context'] = {'request': request}
        elif not kwargs['context'].get('request'):
            kwargs['context']['request'] = request


class HALListSerializer(BaseSerializerDataMixin, serializers.ListSerializer):
    def _get_meta(self, key, default=None):
        meta = getattr(self.child, 'Meta', None)
        if meta is None:
            return None
        return getattr(meta, key, default)

    def to_representation(self, data):
        results = super(HALListSerializer, self).to_representation(data)

        list_reverse = self._get_meta('list_reverse')
        assert list_reverse, "HALSerializer Meta class must define list_reverse."  # noqa

        # Handle reverse-relationships where the API route/url is defined by an
        # attribute on the parent.  Example, `/api/users/32/emails/`, the
        # list-view url is defined by the `pk` on the `User` model, so we need
        # to access `data.instance.pk` to reverse the url, essentially
        # preforming something like: `reverse('api:user-email-list',
        # pk=data.instance.pk)`.
        #
        kwargs = {}
        if isinstance(list_reverse, tuple):
            list_reverse, kwargs = list_reverse

            if not isinstance(kwargs, dict):
                # kwargs is a string where the key == the instance attribute
                # name.
                #
                kwargs = {kwargs: kwargs}

            # DEBUG: Verify that we have been passed a RelatedManager.
            #
            if hasattr(data, 'instance'):
                kwargs = {k: getattr(data.instance, v)
                          for k, v in kwargs.items()}
            else:
                # If the QuerySet is not a RelatedManager, there is no
                # `instance` to get attributes from.
                #
                raise Exception((
                    "Keyword arguments can only be used with "
                    "RelatedManagers.  Good: User.email_set "
                    "Bad: Emails.objects.filter(user=user)  "
                    "[[TODO(nick): This exception message is confusing...]]"))

        resource_name = self._get_meta('resource_name', 'items') # or 'items'

        request = self.context.get('request')
        self_url = reverse(list_reverse, request=self.context.get('request'),
                           kwargs=kwargs)
        if request.GET:
            query_args = {k: v for k, v in request.GET.items()}
            self_url = u'%s?%s' % (self_url, urlencode(query_args))

        ret = OrderedDict(
            _links={
                'self': {
                    'href': self_url,
                },
            },
            _embedded={
                resource_name: results,
            },
        )
        return ret

    @property
    def data(self):
        data = self.base_serializer_data()
        return ReturnDict(data, serializer=self)


class HALSerializer(BaseSerializerDataMixin, serializers.Serializer):
    """Serializer that returns data in HAL-format.

    For the ListSerializer to work correctly, you must define ``resource_name``
    and ``list_reverse`` on your subclass's ``Meta`` class.

    """
    def __init__(self, *args, **kwargs):
        move_request_from_kwargs_to_context(kwargs)
        super(HALSerializer, self).__init__(*args, **kwargs)

    @classmethod
    def many_init(cls, *args, **kwargs):
        kwargs['child'] = cls()
        move_request_from_kwargs_to_context(kwargs)
        return HALListSerializer(*args, **kwargs)


class HALModelSerializer(BaseSerializerDataMixin, serializers.ModelSerializer):
    """ModelSerializer that returns data in HAL-format.

    For the ListSerializer to work correctly, you must define ``resource_name``
    and ``list_reverse`` on your subclass's ``Meta`` class.

    """
    def __init__(self, *args, **kwargs):
        move_request_from_kwargs_to_context(kwargs)
        super(HALModelSerializer, self).__init__(*args, **kwargs)

    @classmethod
    def many_init(cls, *args, **kwargs):
        kwargs['child'] = cls()
        move_request_from_kwargs_to_context(kwargs)
        return HALListSerializer(*args, **kwargs)


class HyperlinkedModelSerializer(serializers.HyperlinkedModelSerializer):
    """`HyperlinkedModelSerializer` that supports url namespacing.

    DEPRECATED: In favor of HAL-style _links with `LinksField`.

    NOTE: This assumes that the namespace for self and related fields is equal
    to the app_name for that particular model.

    """
    # TODO(nick): Allow the view_name for the self field to be overridden by a
    #   class attribute.
    # TODO(nick): Allow the namespace for the self field to be overridden by a
    #   class attribute.
    # TODO(nick): If both view_name and namespace are provided, view_name
    #   should take presidence.
    # TODO(nick): Allow this to be used without a namespace.  Maybe a class
    #   attribute like `use_namespace = True` or implied if any other namespace
    #   related class attribute is set?
    # TODO(nick): Add some more detail to this docstring and some examples of
    #   how this differs from the original implementation.

    def build_relational_field(self, field_name, relation_info):
        cls, kwargs = super(
            HyperlinkedModelSerializer, self).build_relational_field(
                field_name, relation_info)
        namespace = relation_info.related_model._meta.app_label
        view_name = ':'.join((namespace, kwargs['view_name']))
        kwargs['view_name'] = view_name
        return cls, kwargs

    def build_url_field(self, field_name, model_class):
      cls, kwargs = super(HyperlinkedModelSerializer, self).build_url_field(
          field_name, model_class)
      namespace = model_class._meta.app_label
      view_name = ':'.join((namespace, kwargs['view_name']))
      kwargs['view_name'] = view_name
      return cls, kwargs


class QueryField(serializers.HyperlinkedIdentityField):
    """Return the query url that lists related objects in a reverse relation.

    Example
    -------

    .. code:: python

        class Book:
            title = CharField()
            author = ForeignKey(Author)

        class Author:
            name = CharField()

        url('books/query/author/<pk>', ..., name='book-query-by-author')

        class AuthorSerializer:
            name = CharField()
            books = QueryField('book-query-by-author')

        >>> nick = Author(name='Nick').save()
        >>> book1 = Book(title='Part 1', author=nick)
        >>> book2 = Book(title='Part 2', author=nick)
        >>> AuthorSerializer(nick)
        {
            'name': 'Nick',
            'books': '../books/query/author/1',
        }

    Raises
    ------
    django.*.NoReverseMatch
        if the `view_name` and `lookup_field` attributes are not configured to
        correctly match the URL conf.

    """
    lookup_field = 'pk'

    def __init__(self, view_name, url_kwarg=None, query_kwarg=None, **kwargs):
        assert url_kwarg is not None or query_kwarg is not None, 'The `url_kwarg` argument is required.'  # noqa

        kwargs['lookup_field'] = kwargs.get('lookup_field', self.lookup_field)
        self.url_kwarg = url_kwarg
        self.query_kwarg = query_kwarg

        super(QueryField, self).__init__(view_name, **kwargs)

    def get_url(self, obj, view_name, request, response_format):
        lookup_value = getattr(obj, self.lookup_field)

        if self.url_kwarg:
            kwargs = {self.url_kwarg: lookup_value}
            return reverse(view_name,
                           kwargs=kwargs,
                           request=request,
                           format=response_format)

        url = reverse(view_name,
                      request=request,
                      format=response_format)
        query_kwargs = {self.query_kwarg: lookup_value}
        return u'%s?%s' % (url, urlencode(query_kwargs))
