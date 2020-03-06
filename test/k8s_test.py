import io
import json
import sys
import unittest
from unittest.mock import (
    call,
    patch,
)
from uuid import (
    uuid4,
)

sys.path.append('src')
from k8s import (
    K8sApi,
    K8sPod,
)


class K8sApiTest(unittest.TestCase):

    @patch('k8s.open', create=True)
    @patch('k8s.ssl.SSLContext', autospec=True, spec_set=True)
    @patch('k8s.http.client.HTTPSConnection', autospec=True, spec_set=True)
    def test_get_request_success(
            self,
            mock_https_connection_cls,
            mock_ssl_context_cls,
            mock_open):
        # Setup
        mock_response_dict = {str(uuid4()): str(uuid4())}
        mock_response_json = io.StringIO(json.dumps(mock_response_dict))
        mock_conn = mock_https_connection_cls.return_value
        mock_conn.getresponse.return_value = mock_response_json

        # Exercise
        k8s_api = K8sApi()
        response = k8s_api.get('/some/path')

        # Assert
        assert response == mock_response_dict


class K8sPodTest(unittest.TestCase):

    @patch('k8s.os', autospec=True, spec_set=True)
    @patch('k8s.K8sApi', autospec=True, spec_set=True)
    def test_pod_is_ready(
            self,
            mock_k8s_api_cls,
            mock_os):
        # Setup
        app_name = f'{uuid4()}'
        mock_model_name = f'{uuid4()}'
        mock_unit_name = f'{uuid4()}'
        mock_os.environ = {
            'JUJU_MODEL_NAME': mock_model_name,
            'JUJU_UNIT_NAME': mock_unit_name,
        }
        mock_k8s_api = mock_k8s_api_cls.return_value
        mock_k8s_api.get.return_value = {
            'kind': 'PodList',
            'items': [{
                'metadata': {
                    'annotations': {
                        'juju.io/unit': mock_unit_name
                    }
                },
                'status': {
                    'phase': 'Running',
                    'conditions': [{
                        'type': 'ContainersReady',
                        'status': 'True'
                    }]
                }
            }],
        }

        # Exercise
        pod = K8sPod(app_name)
        pod.fetch()

        # Assert
        assert mock_k8s_api.get.call_count == 1
        assert mock_k8s_api.get.call_args == call(
            '/api/v1/namespaces/{}/pods?labelSelector=juju-app={}'
            .format(mock_model_name, app_name)
        )
        assert pod.is_running
        assert pod.is_ready

    @patch('k8s.os', autospec=True, spec_set=True)
    @patch('k8s.K8sApi', autospec=True, spec_set=True)
    def test_pod_undefined(
            self,
            mock_k8s_api_cls,
            mock_os):
        # Setup
        app_name = f'{uuid4()}'
        mock_model_name = f'{uuid4()}'
        mock_unit_name = f'{uuid4()}'
        mock_os.environ = {
            'JUJU_MODEL_NAME': mock_model_name,
            'JUJU_UNIT_NAME': mock_unit_name,
        }
        mock_k8s_api = mock_k8s_api_cls.return_value
        mock_k8s_api.get.return_value = {
            'kind': 'Undefined'
        }

        # Exercise
        pod = K8sPod(app_name)
        pod.fetch()

        # Assert
        assert mock_k8s_api.get.call_count == 1
        assert mock_k8s_api.get.call_args == call(
            '/api/v1/namespaces/{}/pods?labelSelector=juju-app={}'
            .format(mock_model_name, app_name)
        )
        assert not pod.is_running
        assert not pod.is_ready

    @patch('k8s.os', autospec=True, spec_set=True)
    @patch('k8s.K8sApi', autospec=True, spec_set=True)
    def test_pod_not_running(
            self,
            mock_k8s_api_cls,
            mock_os):
        # Setup
        app_name = f'{uuid4()}'
        mock_model_name = f'{uuid4()}'
        mock_unit_name = f'{uuid4()}'
        mock_os.environ = {
            'JUJU_MODEL_NAME': mock_model_name,
            'JUJU_UNIT_NAME': mock_unit_name,
        }
        mock_k8s_api = mock_k8s_api_cls.return_value
        mock_k8s_api.get.return_value = {
            'kind': 'PodList',
            'items': [{
                'metadata': {
                    'annotations': {
                        'juju.io/unit': mock_unit_name
                    }
                },
                'status': {
                    'phase': 'Pending',
                    'conditions': [{
                        'type': 'ContainersReady',
                        'status': 'False'
                    }]
                }
            }],
        }

        # Exercise
        pod = K8sPod(app_name)
        pod.fetch()

        # Assert
        assert mock_k8s_api.get.call_count == 1
        assert mock_k8s_api.get.call_args == call(
            '/api/v1/namespaces/{}/pods?labelSelector=juju-app={}'
            .format(mock_model_name, app_name)
        )
        assert not pod.is_running
        assert not pod.is_ready
