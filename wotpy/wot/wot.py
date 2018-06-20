#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Class that serves as the WoT entrypoint.
"""

import json

import six
import tornado.gen
# noinspection PyCompatibility
from tornado.httpclient import AsyncHTTPClient, HTTPRequest

from wotpy.td.description import ThingDescription
from wotpy.td.thing import Thing
from wotpy.wot.consumed.thing import ConsumedThing
from wotpy.wot.dictionaries.wot import ThingTemplateDict
from wotpy.wot.exposed.thing import ExposedThing

DEFAULT_FETCH_TIMEOUT_SECS = 20.0


class WoT(object):
    """The WoT object is the API entry point and it is exposed by an
    implementation of the WoT Runtime. The WoT object does not expose
    properties, only methods for discovering, consuming and exposing a Thing."""

    def __init__(self, servient):
        self._servient = servient

    def discover(self, thing_filter):
        """Starts the discovery process that will provide ConsumedThing
        objects that match the optional argument ThingFilter."""

        raise NotImplementedError()

    @classmethod
    @tornado.gen.coroutine
    def fetch(cls, url, timeout_secs=None):
        """Accepts an url argument and returns a Future
        that resolves with a Thing Description string."""

        timeout_secs = timeout_secs or DEFAULT_FETCH_TIMEOUT_SECS

        http_client = AsyncHTTPClient()
        http_request = HTTPRequest(url, request_timeout=timeout_secs)

        http_response = yield http_client.fetch(http_request)

        td_doc = json.loads(http_response.body)
        td = ThingDescription(td_doc)

        raise tornado.gen.Return(td.to_str())

    def consume(self, td_str):
        """Accepts a thing description string argument and returns a
        ConsumedThing object instantiated based on that description."""

        td = ThingDescription(td_str)

        return ConsumedThing(servient=self._servient, td=td)

    def produce(self, model):
        """Accepts a model argument of type ThingModel and returns an ExposedThing
        object, locally created based on the provided initialization parameters."""

        assert isinstance(model, six.string_types) or isinstance(model, ThingTemplateDict)

        if isinstance(model, six.string_types):
            json_td = ThingDescription(doc=model)
            thing = json_td.build_thing()
            exposed_thing = ExposedThing(servient=self._servient, thing=thing)
        else:
            thing = Thing(id=model.id)
            exposed_thing = ExposedThing(servient=self._servient, thing=thing)

        self._servient.add_exposed_thing(exposed_thing)

        return exposed_thing

    @tornado.gen.coroutine
    def produce_from_url(self, url, timeout_secs=None):
        """Return a Future that resolves to an ExposedThing created
        from the thing description retrieved from the given URL."""

        td_str = yield self.fetch(url, timeout_secs=timeout_secs)
        exposed_thing = self.produce(td_str)

        raise tornado.gen.Return(exposed_thing)

    @tornado.gen.coroutine
    def consume_from_url(self, url, timeout_secs=None):
        """Return a Future that resolves to a ConsumedThing created
        from the thing description retrieved from the given URL."""

        td_str = yield self.fetch(url, timeout_secs=timeout_secs)
        consumed_thing = self.consume(td_str)

        raise tornado.gen.Return(consumed_thing)
