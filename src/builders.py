#!/usr/bin/env python3


class MongoBuilder:

    def __init__(self, app_name, config, images, units):
        self._app_name = app_name
        self._config = config
        self._images = images
        self._units = units

    def build_spec(self):
        return self.__make_pod_spec__(self._config['enable-sidecar'])

    def build_relation_data(self):
        return {'connection_string': self.__make_mongodb_uri__()}

    def __make_mongodb_uri__(self):
        mongo_uri = "mongodb://"
        for i, unit in enumerate(self._units):
            pod_base_name = unit.split('/')[0]
            service_name = self._config['service-name']
            pod_name = "{}-{}".format(pod_base_name, i)
            if i:
                mongo_uri += ","
            mongo_uri += "{}.{}:{}".format(pod_name, service_name,
                                           self._config['advertised-port'])
        if self._config['enable-sidecar']:
            mongo_uri += "/?replicaSet={}".format(self._config['replica-set'])
        return mongo_uri

    def __make_container_spec__(self):
        return {
            'name': self._app_name,
            'imageDetails': {
                'imagePath': self._images['mongodb-image'].image_path,
                'username': self._images['mongodb-image'].username,
                'password': self._images['mongodb-image'].password,
            },
            'command': [
                'mongod',
                '--bind_ip',
                '0.0.0.0',
            ],
            'ports': [{
                'containerPort':
                    self._config['advertised-port'],
                    'protocol': 'TCP',
            }],
            'config': {
                'ALLOW_ANONYMOUS_LOGIN': 'yes'
            },
            'readinessProbe': {
                'tcpSocket': {
                    'port': self._config['advertised-port'],
                },
                'timeoutSeconds': 5,
                'periodSeconds': 5,
                'initialDelaySeconds': 10,
            },
            'livenessProbe': {
                'exec': {
                    'command': [
                        '/bin/sh',
                        '-c',
                        'mongo --port ' +
                        str(self._config['advertised-port']) +
                        ' --eval "rs.status()" | grep -vq "REMOVED"',
                    ]},
                'initialDelaySeconds': 45,
                'timeoutSeconds': 5,
            }
        }

    def __make_sidecar_spec__(self):
        pod_labels = "juju-app={}".format(self._config['advertised-hostname'])
        return {
            'name': 'mongodb-sidecar-k8s',
            'imageDetails': {
                    'imagePath':
                    self._images['mongodb-sidecar-image'].image_path,
                    'username':
                    self._images['mongodb-sidecar-image'].username,
                    'password':
                    self._images['mongodb-sidecar-image'].password,
            },
            'config': {
                'KUBERNETES_MONGO_SERVICE_NAME': self._config['service-name'],
                'KUBE_NAMESPACE': self._config['namespace'],
                'MONGO_SIDECAR_POD_LABELS': pod_labels,
                'KUBERNETES_CLUSTER_DOMAIN': self._config['cluster-domain'],
            },
        }

    def __make_pod_spec__(self, sidecar=False):
        """Make pod specification for Kubernetes

        Returns:
            pod_spec: Pod specification for Kubernetes
        """
        spec = {
            'containers': [self.__make_container_spec__()]
        }
        if sidecar:
            spec['containers'].append(self.__make_sidecar_spec__())
        return spec
