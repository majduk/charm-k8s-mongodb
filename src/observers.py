#!/usr/bin/env python3

from abc import abstractmethod
import re
import sys
sys.path.append('lib')
from ops.model import (
    ActiveStatus,
    BlockedStatus,
    WaitingStatus,
    MaintenanceStatus,
)
import logging

logger = logging.getLogger()


class BaseObserver:

    def __init__(self, framework, resources, pod, builder):
        self._framework = framework
        self._resources = resources
        self._pod = pod
        self._builder = builder

    @abstractmethod
    def handle(self, event):
        pass


class ConfigChangeObserver(BaseObserver):

    def handle(self, event):
        for resource in self._resources.keys():
            if not self._resources[resource].fetch(self._framework.resources):
                self._framework.unit_status_set(
                    BlockedStatus('Missing or invalid image resource: {}'
                                  .format(resource)))
                return
        if not self._framework.unit_is_leader:
            self._framework.unit_status_set(WaitingStatus('Not the leader'))
            return

        spec = self._builder.build_spec()
        self._framework.unit_status_set(
            MaintenanceStatus('Configuring container'))
        self._framework.pod_spec_set(spec)
        if self._pod.is_ready:
            self._framework.unit_status_set(ActiveStatus('ready'))
            return
        self._framework.unit_status_set(MaintenanceStatus('Pod is not ready'))


class RelationObserver(BaseObserver):

    def handle(self, event):
        handler_name = "handle_" + \
            re.sub(r'(?<!^)(?=[A-Z])', '_',
                       event.__class__.__name__).lower()
        try:
            handler = self.__getattribute__(handler_name)
        except AttributeError:
            print("Handler {} undefined, ignoring".format(handler_name))
            return
        handler(event)

    def handle_relation_joined_event(self, event):
        data = self._builder.build_relation_data()
        self._framework.relation_data_set(event.relation, data)


class StatusObserver(BaseObserver):

    def handle(self, event):
        if self._pod.is_ready:
            self._framework.unit_status_set(ActiveStatus())
            return
        self._framework.unit_status_set(BlockedStatus('Pod is not ready'))
