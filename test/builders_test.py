from pathlib import Path
import sys
import unittest
from unittest.mock import (
    patch
)
sys.path.append('lib')
sys.path.append('src')

from uuid import uuid4
from builders import MongoBuilder
from resources import OCIImageResource

class MongoBuilderTest(unittest.TestCase):

    def create_image_resource_obj(self, mock_image_resource, fetch):
        mock_image_resource_obj = mock_image_resource.return_value
        mock_image_resource_obj.fetch.return_value = fetch
        mock_image_resource_obj.image_path = f'{uuid4()}/{uuid4()}'
        mock_image_resource_obj.username = f'{uuid4()}'
        mock_image_resource_obj.password = f'{uuid4()}'
        return mock_image_resource_obj

    @patch('charm.OCIImageResource', autospec=True, spec_set=True)
    def test_spec(self, mock_image_resource_clazz):
        # Setup
        mock_image_resource_obj =\
            self.create_image_resource_obj(mock_image_resource_clazz, True)
        app_name = 'app-name'
        config = {
            'enable-sidecar': False,
            'service-name': 'service-name',
            'advertised-port': 1234,
            'replica-set': 'replica-set',
            'advertised-hostname': 'advertised-hostname',
            'namespace': 'namespace',
            'cluster-domain': 'cluster-domain'
        }
        goal_state_units = None
        images = {
            'mongodb-image': mock_image_resource_obj
        }
        # Exercise
        builder = MongoBuilder(
            app_name,
            config,
            images,
            goal_state_units
        )
        spec = builder.build_spec()
        # Verify
        assert spec == {'containers':[
            {
                'name': app_name,
                'imageDetails': {
                    'imagePath': mock_image_resource_obj.image_path,
                    'username': mock_image_resource_obj.username,
                    'password': mock_image_resource_obj.password,
                },
                'command': [
                    'mongod',
                    '--bind_ip',
                    '0.0.0.0',
                ],
                'ports': [{
                    'containerPort':
                    config['advertised-port'],
                    'protocol': 'TCP',
                }],
                'config': {
                    'ALLOW_ANONYMOUS_LOGIN': 'yes'
                },
                'readinessProbe': {
                  'tcpSocket':{
                    'port': config['advertised-port'],
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
                      'mongo --port ' + str(config['advertised-port']) + 
                      ' --eval "rs.status()" | grep -vq "REMOVED"',
                      ]},
                      'initialDelaySeconds': 45,
                      'timeoutSeconds': 5,
                  }
                }
            ]}

    @patch('charm.OCIImageResource', autospec=True, spec_set=True)
    def test_spec_sidecar(self,mock_image_resource_clazz):
        # Setup
        mock_image_resource_obj =\
            self.create_image_resource_obj(mock_image_resource_clazz, True)
        mock_image_resource_obj2 =\
            self.create_image_resource_obj(mock_image_resource_clazz, True)            
        app_name = 'app-name'
        config = {
            'enable-sidecar': True,
            'service-name': 'service-name',
            'advertised-port': 1234,
            'replica-set': 'replica-set',
            'advertised-hostname': 'advertised-hostname',
            'namespace': 'namespace',
            'cluster-domain': 'cluster-domain'
        }
        pod_labels = "juju-app={}".format(config['advertised-hostname'])
        goal_state_units = None
        images = {
            'mongodb-image': mock_image_resource_obj,
            'mongodb-sidecar-image': mock_image_resource_obj2,
        }
        # Exercise
        builder = MongoBuilder(
            app_name,
            config,
            images,
            goal_state_units
        )
        spec = builder.build_spec()
        # Verify
        assert spec == {'containers':[
            {
                'name': app_name,
                'imageDetails': {
                    'imagePath': mock_image_resource_obj.image_path,
                    'username': mock_image_resource_obj.username,
                    'password': mock_image_resource_obj.password,
                },
                'command': [
                    'mongod',
                    '--bind_ip',
                    '0.0.0.0',
                ],
                'ports': [{
                    'containerPort':
                    config['advertised-port'],
                    'protocol': 'TCP',
                }],
                'config': {
                    'ALLOW_ANONYMOUS_LOGIN': 'yes'
                },
                'readinessProbe': {
                  'tcpSocket':{
                    'port': config['advertised-port'],
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
                      'mongo --port ' + str(config['advertised-port']) + 
                      ' --eval "rs.status()" | grep -vq "REMOVED"',
                      ]},
                      'initialDelaySeconds': 45,
                      'timeoutSeconds': 5,
                  }
                },
                {
                'name': 'mongodb-sidecar-k8s',
                'imageDetails': {
                    'imagePath': mock_image_resource_obj2.image_path,
                    'username': mock_image_resource_obj2.username,
                    'password': mock_image_resource_obj2.password,
                },
                'config': {
                     'KUBERNETES_MONGO_SERVICE_NAME': config['service-name'],
                     'KUBE_NAMESPACE': config['namespace'],
                     'MONGO_SIDECAR_POD_LABELS': pod_labels,
                     'KUBERNETES_CLUSTER_DOMAIN': config['cluster-domain'],
                },               
               }                
            ]}                    

    def test_relation_data(self):
        app_name = 'app-name'
        config = {
            'enable-sidecar': True,
            'service-name': 'service-name',
            'advertised-port': 1234,
            'replica-set': 'replica-set',
            'advertised-hostname': 'advertised-hostname',
            'namespace': 'namespace',
            'cluster-domain': 'cluster-domain'
        }

        goal_state = {"units":{
            "mongodb-k8s/0":{"status":"active","since":"2020-03-05 10:53:51Z"},
            "mongodb-k8s/1":{"status":"active","since":"2020-03-05 10:55:30Z"},
            "mongodb-k8s/2":{"status":"active","since":"2020-03-05 10:55:23Z"}},
            "relations":{}}
        images = {}
        # Exercise
        builder = MongoBuilder(
            app_name,
            config,
            images,
            goal_state['units']
        )
        spec = builder.build_relation_data()
        # Verify
        assert spec == {'connection_string': 'mongodb://'
                        'mongodb-k8s-0.service-name:1234,'
                        'mongodb-k8s-1.service-name:1234,'
                        'mongodb-k8s-2.service-name:1234'
                        '/?replicaSet=replica-set'}                          