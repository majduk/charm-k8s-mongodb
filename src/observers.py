#!/usr/bin/env python3

from abc import abstractmethod
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
                logger.info('Missing or invalid image resource: {}'
                            .format(resource))
                return

        if not self._framework.unit_is_leader:
            self._framework.unit_status_set(WaitingStatus('Not the leader'))
            logger.info('Delegating pod configuration to the leader')
            return

        spec = self._builder.build_spec()
        self._framework.unit_status_set(
            MaintenanceStatus('Configuring container'))
        self._framework.pod_spec_set(spec)
        if self._pod.is_ready:
            self._framework.unit_status_set(ActiveStatus('ready'))
            logger.info('Pod is ready')
            return
        self._framework.unit_status_set(MaintenanceStatus('Pod is not ready'))
        logger.info('Pod is not ready')


class RelationObserver(BaseObserver):

    def handle(self, event):
        data = self._builder.build_relation_data(event.client.formatter)
        logger.info('Serve {} with {}'.format(event.client, data))
        self._framework.relation_data_set(event.relation, data)


class StatusObserver(BaseObserver):

    def handle(self, event):
        if self._pod.is_ready:
            logger.info('Pod is ready')
            self._framework.unit_status_set(ActiveStatus())
            return
        self._framework.unit_status_set(BlockedStatus('Pod is not ready'))
        logger.info('Pod is not ready')
