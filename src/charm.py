#!/usr/bin/env python3

import sys
sys.path.append('lib')

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main

from resources import OCIImageResource
from wrapper import FrameworkWrapper
from k8s import K8sPod
from observers import (
    ConfigChangeObserver,
    StatusObserver,
    RelationObserver,
)
from builders import MongoBuilder
import logging

logger = logging.getLogger()


class MongoDbCharm(CharmBase):
    _state = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self._framework_wrapper = FrameworkWrapper(self.framework, self._state)
        self._resources = {
            'mongodb-image': OCIImageResource('mongodb-image')
        }

        self._mongo_builder = MongoBuilder(
            self._framework_wrapper.app_name,
            self._framework_wrapper.config,
            self._resources,
            self._framework_wrapper.goal_state_units
        )

        if self._framework_wrapper.config['enable-sidecar']:
            self._resources['mongodb-sidecar-image'] = OCIImageResource(
                'mongodb-sidecar-image')

        self._pod = K8sPod(self._framework_wrapper.app_name)

        delegators = [
            (self.on.start, self.on_config_changed_delegator),
            (self.on.upgrade_charm, self.on_config_changed_delegator),
            (self.on.config_changed, self.on_config_changed_delegator),
            (self.on.update_status, self.on_update_status_delegator),
            (self.on.mongo_relation_joined,
             self.on_relation_changed_delegator),
            (self.on.mongo_relation_changed,
             self.on_relation_changed_delegator),
            (self.on.mongo_relation_departed,
             self.on_relation_changed_delegator),
            (self.on.mongo_relation_broken,
             self.on_relation_changed_delegator),
        ]
        for delegator in delegators:
            self.framework.observe(delegator[0], delegator[1])

    def on_config_changed_delegator(self, event):
        logger.info('on_config_changed_delegator({})'.format(event))
        return ConfigChangeObserver(
            self._framework_wrapper,
            self._resources,
            self._pod,
            self._mongo_builder).handle(event)

    def on_relation_changed_delegator(self, event):
        logger.info('on_relation_changed_delegator({})'.format(event))
        return RelationObserver(
            self._framework_wrapper,
            self._resources,
            self._pod,
            self._mongo_builder).handle(event)

    def on_update_status_delegator(self, event):
        logger.info('on_update_status_delegator({})'.format(event))
        return StatusObserver(
            self._framework_wrapper,
            self._resources,
            self._pod,
            self._mongo_builder).handle(event)


if __name__ == "__main__":
    main(MongoDbCharm)
