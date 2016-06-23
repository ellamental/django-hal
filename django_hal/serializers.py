"""
HAL serializers for Django REST Framework.

"""

from __future__ import print_function

from collections import OrderedDict

from django.utils.http import urlencode
from rest_framework import serializers
from rest_framework.utils.serializer_helpers import ReturnDict

from .utils import reverse, move_request_from_kwargs_to_context

# DEPRECATED: Import fields to make them available as:
#             ``from django_hal.serializers import LinksField, QueryField``
#
from .fields import LinksField, QueryField


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

        resource_name = self._get_meta('resource_name', 'items')

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


