#!/usr/bin/env python3

import sys
sys.path.append('lib')

from ops.charm import CharmBase
from ops.framework import StoredState
from ops.main import main
from ops.model import (
    ActiveStatus,
    BlockedStatus,
    WaitingStatus,
    MaintenanceStatus,
)
from resources import OCIImageResource


class MongoDbCharm(CharmBase):
    state = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.start, self.on_start)
        for event in (self.on.start,
                      self.on.upgrade_charm,
                      self.on.config_changed):
            self.framework.observe(event, self.on_start)
        self.mongodb_image = OCIImageResource('mongodb-image')

    def make_pod_spec(self):
        """Make pod specification for Kubernetes

        Returns:
            pod_spec: Pod specification for Kubernetes
        """
        spec = {
            'containers': [{
                'name': self.framework.model.app.name,
                'imageDetails': {
                    'imagePath': self.mongodb_image.registry_path,
                    'username': self.mongodb_image.username,
                    'password': self.mongodb_image.password,
                },
                'ports': [{
                    'containerPort':
                    self.framework.model.config['advertised-port'],
                    'protocol': 'TCP',
                }],
            }],
        }
        return spec

    def on_start(self, event):
        unit = self.framework.model.unit
        if not self.mongodb_image.fetch():
            unit.status = BlockedStatus('Missing or invalid image resource')
            return
        if not self.framework.model.unit.is_leader():
            unit.status = WaitingStatus('Not leader')
            return
        spec = self.make_pod_spec()
        unit.status = MaintenanceStatus('Configuring container')
        self.framework.model.pod.set_spec(spec)
        self.state.is_started = True
        unit.status = ActiveStatus()


if __name__ == "__main__":
    main(MongoDbCharm)
