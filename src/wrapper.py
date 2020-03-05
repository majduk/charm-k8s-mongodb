#!/usr/bin/env python3
import json
import subprocess
import logging

logger = logging.getLogger()


class FrameworkWrapper:

    def __init__(self, framework, state):
        self._framework = framework
        self._state = state

    @property
    def config(self):
        return self._framework.model.config

    @property
    def state(self):
        return self._state

    @property
    def resources(self):
        return self._framework.model.resources

    @property
    def app_name(self):
        return self._framework.model.app.name

    def pod_spec_set(self, spec):
        logger.info('pod_spec_set {}'.format(str(spec)))
        self._framework.model.pod.set_spec(spec)

    @property
    def unit_is_leader(self):
        return self._framework.model.unit.is_leader()

    def unit_status_set(self, state):
        logger.info('unit_status_set {}'.format(str(state)))
        self._framework.model.unit.status = state

    def relation_data_set(self, relation, data):
        logger.info('relation_data_set {}'.format(str(data)))
        relation.data[self._framework.model.unit].update(data)

    @property
    def goal_state_units(self):
        cmd = ['goal-state', '--format=json']
        goal_state = json.loads(subprocess.check_output(cmd).decode('UTF-8'))
        return goal_state['units']
