#!/usr/bin/env python3
import json
import http.client
import os
import ssl


class K8sApi:

    def get(self, path):
        return self.request('GET', path)

    def delete(self, path):
        return self.request('DELETE', path)

    def request(self, method, path):
        with open("/var/run/secrets/kubernetes.io/serviceaccount/token") \
                as token_file:
            kube_token = token_file.read()

        ssl_context = ssl.SSLContext()
        ssl_context.load_verify_locations(
            '/var/run/secrets/kubernetes.io/serviceaccount/ca.crt')

        headers = {
            'Authorization': f'Bearer {kube_token}'
        }

        conn = http.client.HTTPSConnection('kubernetes.default.svc',
                                           context=ssl_context)
        conn.request(method=method, url=path, headers=headers)

        return json.loads(conn.getresponse().read())


class K8sPod:

    def __init__(self, app_name):
        self._app_name = app_name
        self._status = None

    def fetch(self):
        namespace = os.environ["JUJU_MODEL_NAME"]

        path = f'/api/v1/namespaces/{namespace}/pods?' \
               f'labelSelector=juju-app={self._app_name}'

        api_server = K8sApi()
        response = api_server.get(path)

        if response.get('kind', '') == 'PodList' and response['items']:
            unit = os.environ['JUJU_UNIT_NAME']
            status = next(
                (i for i in response['items']
                 if i['metadata']['annotations'].get('juju.io/unit') == unit),
                None
            )
        else:
            status = None

        self._status = status

    def map_unit_to_pvc(self):
        if self.is_running:
            return self._status['spec']['volumes'][0]['persistentVolumeClaim']['claimName']
        return None

    @property
    def is_ready(self):
        if not self._status:
            self.fetch()
        if not self._status:
            return False
        return next(
            (
                condition['status'] == "True" for condition
                in self._status['status']['conditions']
                if condition['type'] == 'ContainersReady'
            ),
            False
        )

    @property
    def is_running(self):
        if not self._status:
            self.fetch()
        if not self._status:
            return False
        return self._status['status']['phase'] == 'Running'


class K8sPvc:

    def __init__(self, app_name):
        self._app_name = app_name
        self._status = None

    def fetch(self):
        namespace = os.environ["JUJU_MODEL_NAME"]

        pods = K8sPod(self._app_name)

        path = f'/api/v1/namespaces/{namespace}/persistentvolumeclaims?' \
               f'labelSelector=juju-app={self._app_name}'

        api_server = K8sApi()
        response = api_server.get(path)

        if response.get('kind', '') == 'PersistentVolumeClaimList' \
                and response['items']:
            status = next(
                (i for i in response['items']
                 if i['metadata']['name'] == pods.map_unit_to_pvc()),
                None
            )
        else:
            status = None

        self._status = status

    def delete(self):
        namespace = os.environ["JUJU_MODEL_NAME"]

        if self.is_running:
            pvc_name = self._status['metadata']['name']
            path = f'/api/v1/namespaces/{namespace}/' \
                   f'persistentvolumeclaims/{pvc_name}'

            api_server = K8sApi()
            api_server.delete(path)

    @property
    def is_running(self):
        # pending bound lost
        if not self._status:
            self.fetch()
        if not self._status:
            return False
        return self._status['status']['phase'] == 'Bound'
