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
import json
import subprocess


class MongoDbCharm(CharmBase):
    state = StoredState()

    def __init__(self, *args):
        super().__init__(*args)
        self.framework.observe(self.on.start, self.on_start)
        for event in (self.on.start,
                      self.on.upgrade_charm,
                      self.on.config_changed):
            self.framework.observe(event, self.on_start)
            self.framework.observe(self.on.update_status, self.on_update_status)
            self.framework.observe(self.on.mongo_relation_joined, self.on_mongo_relation_joined)
        self.mongodb_image = OCIImageResource('mongodb-image')
        self.sidecar_image = OCIImageResource('mongodb-sidecar-image')

    def _make_container_spec(self):
        return {
                'name': self.framework.model.app.name,
                'imageDetails': {
                    'imagePath': self.mongodb_image.image_path,
                    'username': self.mongodb_image.username,
                    'password': self.mongodb_image.password,
                },
                'command': [
                    'mongod',
                    '--bind_ip',
                    '0.0.0.0',
                ],
                'ports': [{
                    'containerPort':
                    self.framework.model.config['advertised-port'],
                    'protocol': 'TCP',
                }],
                'config': {
                    'ALLOW_ANONYMOUS_LOGIN': 'yes'
                },
                'readinessProbe': {
                  'tcpSocket':{
                    'port': self.framework.model.config['advertised-port'],
                    },
                  'timeoutSeconds': 5,
                  'periodSeconds': 5,
                  'initialDelaySeconds': 10,
                },
                'livenessProbe': {
                  'exec': {
                      'command':[
                      '/bin/sh',
                      '-c',
                      'mongo --port ' + str(self.framework.model.config['advertised-port']) + ' --eval "rs.status()" | grep -vq "REMOVED"',
                      ]},
                      'initialDelaySeconds': 45,
                      'timeoutSeconds': 5,
                  }
                }

    def _make_sidecar_spec(self):
        pod_labels = "juju-app={}".format(self.framework.model.config['advertised-hostname'])
        return {
                'name': 'mongodb-sidecar-k8s',
                'imageDetails': {
                    'imagePath': self.sidecar_image.image_path,
                    'username': self.sidecar_image.username,
                    'password': self.sidecar_image.password,
                },
                'config': {
                     'KUBERNETES_MONGO_SERVICE_NAME': self.framework.model.config['service-name'],
                     'KUBE_NAMESPACE': self.framework.model.config['namespace'],
                     'MONGO_SIDECAR_POD_LABELS': pod_labels,
                     'KUBERNETES_CLUSTER_DOMAIN': self.framework.model.config['cluster-domain'],
                },               
               }


    def make_pod_spec(self, sidecar = False):
        """Make pod specification for Kubernetes

        Returns:
            pod_spec: Pod specification for Kubernetes
        """
        spec = {
            'containers': [ self._make_container_spec() ] 
            }
        if sidecar:
            spec['containers'].append( self._make_sidecar_spec() )
        return spec

    def on_start(self, event):
        unit = self.framework.model.unit
        has_sidecar = self.framework.model.config['enable-sidecar']
        resources = self.framework.model.resources
        if not self.mongodb_image.fetch(resources):
            unit.status = BlockedStatus('Missing or invalid image resource')
            return
        if has_sidecar and not self.sidecar_image.fetch(resources):
            unit.status = BlockedStatus('Missing or invalid image resource')
            return
        if not self.framework.model.unit.is_leader():
            unit.status = WaitingStatus('Not leader')
            return
        spec = self.make_pod_spec( sidecar = has_sidecar)
        unit.status = MaintenanceStatus('Configuring container')
        self.framework.model.pod.set_spec(spec)
        self.state.is_started = True
        unit.status = ActiveStatus()

    def on_update_status(self, event):
        unit = self.framework.model.unit
        unit.status = ActiveStatus()

    def goal_state(self):
        """Juju goal state values"""
        cmd = ['goal-state', '--format=json']
        return json.loads(subprocess.check_output(cmd).decode('UTF-8'))

    def on_mongo_relation_joined(self, event):
        mongo_uri = "mongodb://"
        for i, unit in enumerate(self.goal_state()['units']):
            pod_base_name = unit.split('/')[0]
            service_name = self.framework.model.config['service-name']
            pod_name = "{}-{}".format(pod_base_name, i)
            if i:
                mongo_uri += ","
            mongo_uri += "{}.{}:{}".format(pod_name, service_name,
                                           self.framework.model.config['advertised-port'])
        if self.framework.model.config['enable-sidecar']:
            mongo_uri += "/?replicaSet={}".format(self.framework.model.config['replica-set'])
        print("MongoDB URI: " + mongo_uri)
        relation = event.relation
        relation.data[self.framework.model.unit]['connection_string']=mongo_uri

if __name__ == "__main__":
    main(MongoDbCharm)
