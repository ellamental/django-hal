"""
HAL serializers for Django REST Framework.

"""

from __future__ import print_function

from collections import OrderedDict

from django.core import urlresolvers
from django.utils.http import urlencode
from rest_framework import serializers
from rest_framework.utils.serializer_helpers import ReturnDict

from .utils import reverse, move_request_from_kwargs_to_context

# DEPRECATED: Import fields to make them available as:
#             ``from django_hal.serializers import LinksField, QueryField``
#
from .fields import LinksField, QueryField


def _to_link(self, request, instance, urlpattern, kwargs=None,
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
    except urlresolvers.NoReverseMatch:
        return None


def _link_to_dict(request, instance, link):
    assert link['pattern'] or link['href'], "Link must have an href or pattern."

    try:
        if link['pattern']:
            pattern = link['pattern'].get('pattern')
            kwargs = link['pattern'].get('kwargs')
            query = link['pattern'].get('query')

            if kwargs:
                kwargs = {k: getattr(instance, v) for k, v in kwargs.items()}
                url = reverse(pattern, kwargs=kwargs, request=request)
            else:
                url = reverse(pattern, request=request)

            if query:
                query = {k: getattr(instance, v) for k, v in query.items()}
                url = u'%s?%s' % (url, urlencode(query))

    except urlresolvers.NoReverseMatch:
        url = None
        return None  # ?

    ret = {
        'href': url,
    }
    if link.get('name'):
        ret['name'] = link['name']
    if link.get('profile'):
        ret['profile'] = link['profile']

    return ret


def _process_links(links_dict, request, instance, links):
    ret = links_dict
    for link in links:
        link_dict = _link_to_dict(request, instance, link)

        # If there is an existing entry for ``rel``, ``rel`` becomes
        # an array of link objects.
        #
        # .. seealso:: https://tools.ietf.org/html/draft-kelly-json-hal-08#section-4.1.1
        #
        current = ret.get(link['rel'])
        if not current:
            ret[link['rel']] = link_dict
        else:
            if isinstance(current, dict):
                ret[link['rel']] = [current]
            ret[link['rel']].append(link_dict)
    return ret



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

        # resource_name = self._get_meta('resource_name', 'items') # DEPRECATED
        # rel = self._get_meta('rel', 'item')  # DEPRECATED
        profile = self._get_meta('profile', 'item')

        request = self.context.get('request')
        self_url = reverse(list_reverse, request=self.context.get('request'),
                           kwargs=kwargs)
        if request.GET:
            query_args = {k: v for k, v in request.GET.items()}
            self_url = u'%s?%s' % (self_url, urlencode(query_args))

        self_link = {
            'href': self_url,
        }
        profile = self._get_meta('profile')
        if profile:
            self_link['profile'] = profile

        ret = OrderedDict(
            _links={
                'self': self_link,
            },
            _embedded={
                profile: results,
            },
        )
        return ret

    @property
    def data(self):
        data = self.base_serializer_data()
        return ReturnDict(data, serializer=self)


class HALSerializer(BaseSerializerDataMixin, serializers.Serializer):
    """Serializer that returns data in HAL-format.

    For the ListSerializer to work correctly, you must define ``rel``
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

    def _get_self_link(self, instance):
        request = self.context.get('request')
        pattern = getattr(self.Meta, 'detail_reverse')

        if isinstance(pattern, basestring):
            pattern = (pattern, {'pk': 'pk'})
        elif isinstance(pattern[1], basestring):
            pattern = (pattern[0], {pattern[1]: pattern[1]})
        return {'href': reverse(pattern[0],
                                kwargs={k:getattr(instance, v)
                                        for k, v in pattern[1].items()},
                                request=request)}

    def to_representation(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        ret = OrderedDict()
        fields = self._readable_fields

        request = self.context.get('request')

        meta_links = getattr(self.Meta, '_links', None)
        if meta_links:
            self_link = self._get_self_link(instance)
            links_dict = OrderedDict((
                ('self', self_link),
            ))
            _links = _process_links(links_dict, request, instance, meta_links)
            ret['_links'] = _links

        for field in fields:
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue

            if attribute is None:
                # We skip `to_representation` for `None` values so that
                # fields do not have to explicitly deal with that case.
                ret[field.field_name] = None
            else:
                ret[field.field_name] = field.to_representation(attribute)

        return ret


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


