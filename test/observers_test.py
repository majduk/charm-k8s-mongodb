import sys
import unittest
from uuid import uuid4
from unittest.mock import (
    call,
    patch,
    create_autospec
)
sys.path.append('lib')
sys.path.append('src')
from ops.framework import (
    EventBase
)
from ops.model import (
    ActiveStatus,
    BlockedStatus,
    WaitingStatus,
    MaintenanceStatus
)

from observers import (
    StatusObserver,
    RelationObserver,
    ConfigChangeObserver
)
from ops.charm import RelationJoinedEvent


class StatusObserverTest(unittest.TestCase):

    def create_image_resource_obj(self, mock_image_resource, fetch):
        mock_image_resource_obj = mock_image_resource.return_value
        mock_image_resource_obj.fetch.return_value = fetch
        mock_image_resource_obj.image_path = f'{uuid4()}/{uuid4()}'
        mock_image_resource_obj.username = f'{uuid4()}'
        mock_image_resource_obj.password = f'{uuid4()}'
        return mock_image_resource_obj

    @patch('k8s.K8sPod', autospec=True, spec_set=True)
    @patch('builders.MongoBuilder', autospec=True, spec_set=True)
    @patch('wrapper.FrameworkWrapper', autospec=True, spec_set=True)
    @patch('charm.OCIImageResource', autospec=True, spec_set=True)
    def test_handle_pod_ready(self, mock_image_resource_clazz,
                              mock_framework_clazz,
                              mock_builder_clazz, mock_pod_clazz):
        # Setup
        mock_event = create_autospec(EventBase, spec_set=True)
        mock_framework = mock_framework_clazz.return_value
        mock_builder = mock_builder_clazz.return_value
        mock_pod = mock_pod_clazz.return_value
        mock_pod.is_ready = True

        mock_image_resource_obj =\
            self.create_image_resource_obj(mock_image_resource_clazz, True)
        images = {
            'mongodb-image': mock_image_resource_obj
        }

        # Exercise
        observer = StatusObserver(
            mock_framework,
            images,
            mock_pod,
            mock_builder
        )
        observer.handle(mock_event)
        # Verify
        assert mock_framework.unit_status_set.call_count == 1
        assert isinstance(mock_framework.unit_status_set.call_args[0][0],
                          ActiveStatus)

    @patch('k8s.K8sPod', autospec=True, spec_set=True)
    @patch('builders.MongoBuilder', autospec=True, spec_set=True)
    @patch('wrapper.FrameworkWrapper', autospec=True, spec_set=True)
    @patch('charm.OCIImageResource', autospec=True, spec_set=True)
    def test_handle_pod_not_ready(self, mock_image_resource_clazz,
                                  mock_framework_clazz,
                                  mock_builder_clazz, mock_pod_clazz):
        # Setup
        mock_event = create_autospec(EventBase, spec_set=True)
        mock_framework = mock_framework_clazz.return_value
        mock_builder = mock_builder_clazz.return_value
        mock_pod = mock_pod_clazz.return_value
        mock_pod.is_ready = False

        mock_image_resource_obj =\
            self.create_image_resource_obj(mock_image_resource_clazz, True)
        images = {
            'mongodb-image': mock_image_resource_obj
        }

        # Exercise
        observer = StatusObserver(
            mock_framework,
            images,
            mock_pod,
            mock_builder
        )
        observer.handle(mock_event)
        # Verify
        assert mock_framework.unit_status_set.call_count == 1
        assert isinstance(mock_framework.unit_status_set.call_args[0][0],
                          BlockedStatus)


class RelationObserverTest(unittest.TestCase):

    def create_image_resource_obj(self, mock_image_resource, fetch):
        mock_image_resource_obj = mock_image_resource.return_value
        mock_image_resource_obj.fetch.return_value = fetch
        mock_image_resource_obj.image_path = f'{uuid4()}/{uuid4()}'
        mock_image_resource_obj.username = f'{uuid4()}'
        mock_image_resource_obj.password = f'{uuid4()}'
        return mock_image_resource_obj

    @patch('k8s.K8sPod', autospec=True, spec_set=True)
    @patch('builders.MongoBuilder', autospec=True, spec_set=True)
    @patch('wrapper.FrameworkWrapper', autospec=True, spec_set=True)
    @patch('charm.OCIImageResource', autospec=True, spec_set=True)
    def test_handle_relation_joined(self, mock_image_resource_clazz,
                                    mock_framework_clazz,
                                    mock_builder_clazz, mock_pod_clazz):
        # Setup
        mock_event = create_autospec(RelationJoinedEvent)
        mock_framework = mock_framework_clazz.return_value
        mock_builder = mock_builder_clazz.return_value
        mock_pod = mock_pod_clazz.return_value
        mock_pod.is_ready = True

        relation = uuid4()
        mock_event.relation = relation
        rel_data = {str(uuid4()): str(uuid4())}
        mock_builder.build_relation_data.return_value = rel_data

        mock_image_resource_obj =\
            self.create_image_resource_obj(mock_image_resource_clazz, True)
        images = {
            'mongodb-image': mock_image_resource_obj
        }

        # Exercise
        observer = RelationObserver(
            mock_framework,
            images,
            mock_pod,
            mock_builder
        )
        observer.handle(mock_event)
        # Verify
        assert mock_framework.relation_data_set.call_count == 1
        assert mock_framework.relation_data_set.call_args == call(relation,
                                                                  rel_data)


class ConfigChangeObserverTest(unittest.TestCase):

    def create_image_resource_obj(self, mock_image_resource, fetch):
        mock_image_resource_obj = mock_image_resource.return_value
        mock_image_resource_obj.fetch.return_value = fetch
        mock_image_resource_obj.image_path = f'{uuid4()}/{uuid4()}'
        mock_image_resource_obj.username = f'{uuid4()}'
        mock_image_resource_obj.password = f'{uuid4()}'
        return mock_image_resource_obj

    @patch('k8s.K8sPod', autospec=True, spec_set=True)
    @patch('builders.MongoBuilder', autospec=True, spec_set=True)
    @patch('wrapper.FrameworkWrapper', autospec=True, spec_set=True)
    @patch('charm.OCIImageResource', autospec=True, spec_set=True)
    def test_handle_spec_set_pod_ready(self, mock_image_resource_clazz,
                                       mock_framework_clazz,
                                       mock_builder_clazz, mock_pod_clazz):
        # Setup
        mock_event = create_autospec(EventBase)
        mock_framework = mock_framework_clazz.return_value
        mock_builder = mock_builder_clazz.return_value
        mock_pod = mock_pod_clazz.return_value
        mock_pod.is_ready = True

        mock_image_resource_obj =\
            self.create_image_resource_obj(mock_image_resource_clazz, True)
        images = {
            'mongodb-image': mock_image_resource_obj
        }

        spec = {str(uuid4()): str(uuid4())}
        mock_builder.build_spec.return_value = spec

        # Exercise
        observer = ConfigChangeObserver(
            mock_framework,
            images,
            mock_pod,
            mock_builder
        )
        observer.handle(mock_event)
        # Verify
        assert mock_framework.unit_status_set.call_count == 2
        assert isinstance(
            mock_framework.unit_status_set.call_args[0][0], ActiveStatus)
        assert mock_framework.pod_spec_set.call_count == 1
        assert mock_framework.pod_spec_set.call_args == call(spec)

    @patch('k8s.K8sPod', autospec=True, spec_set=True)
    @patch('builders.MongoBuilder', autospec=True, spec_set=True)
    @patch('wrapper.FrameworkWrapper', autospec=True, spec_set=True)
    @patch('charm.OCIImageResource', autospec=True, spec_set=True)
    def test_handle_spec_set_pod_not_ready(self, mock_image_resource_clazz,
                                           mock_framework_clazz,
                                           mock_builder_clazz, mock_pod_clazz):
        # Setup
        mock_event = create_autospec(EventBase)
        mock_framework = mock_framework_clazz.return_value
        mock_builder = mock_builder_clazz.return_value
        mock_pod = mock_pod_clazz.return_value
        mock_pod.is_ready = False

        mock_image_resource_obj =\
            self.create_image_resource_obj(mock_image_resource_clazz, True)
        images = {
            'mongodb-image': mock_image_resource_obj
        }

        spec = {str(uuid4()): str(uuid4())}
        mock_builder.build_spec.return_value = spec

        # Exercise
        observer = ConfigChangeObserver(
            mock_framework,
            images,
            mock_pod,
            mock_builder
        )
        observer.handle(mock_event)
        # Verify
        assert mock_framework.unit_status_set.call_count == 2
        assert isinstance(
            mock_framework.unit_status_set.call_args[0][0], MaintenanceStatus)
        assert mock_framework.pod_spec_set.call_count == 1
        assert mock_framework.pod_spec_set.call_args == call(spec)

    @patch('k8s.K8sPod', autospec=True, spec_set=True)
    @patch('builders.MongoBuilder', autospec=True, spec_set=True)
    @patch('wrapper.FrameworkWrapper', autospec=True, spec_set=True)
    @patch('charm.OCIImageResource', autospec=True, spec_set=True)
    def test_handle_spec_set_not_leader(self, mock_image_resource_clazz,
                                        mock_framework_clazz,
                                        mock_builder_clazz, mock_pod_clazz):
        # Setup
        mock_event = create_autospec(EventBase)
        mock_framework = mock_framework_clazz.return_value
        mock_framework.unit_is_leader = False
        mock_builder = mock_builder_clazz.return_value
        mock_pod = mock_pod_clazz.return_value
        mock_pod.is_ready = False

        mock_image_resource_obj =\
            self.create_image_resource_obj(mock_image_resource_clazz, True)
        images = {
            'mongodb-image': mock_image_resource_obj
        }

        spec = {str(uuid4()): str(uuid4())}
        mock_builder.build_spec.return_value = spec

        # Exercise
        observer = ConfigChangeObserver(
            mock_framework,
            images,
            mock_pod,
            mock_builder
        )
        observer.handle(mock_event)
        # Verify
        assert mock_framework.unit_status_set.call_count == 1
        assert isinstance(mock_framework.unit_status_set.call_args[0][0],
                          WaitingStatus)
        assert mock_framework.pod_spec_set.call_count == 0

    @patch('k8s.K8sPod', autospec=True, spec_set=True)
    @patch('builders.MongoBuilder', autospec=True, spec_set=True)
    @patch('wrapper.FrameworkWrapper', autospec=True, spec_set=True)
    @patch('charm.OCIImageResource', autospec=True, spec_set=True)
    def test_handle_spec_not_fetch(self, mock_image_resource_clazz,
                                   mock_framework_clazz,
                                   mock_builder_clazz, mock_pod_clazz):
        # Setup
        mock_event = create_autospec(EventBase)
        mock_framework = mock_framework_clazz.return_value
        mock_builder = mock_builder_clazz.return_value
        mock_pod = mock_pod_clazz.return_value
        mock_pod.is_ready.return_value = False

        mock_image_resource_obj =\
            self.create_image_resource_obj(mock_image_resource_clazz, False)
        images = {
            'mongodb-image': mock_image_resource_obj
        }

        spec = {str(uuid4()): str(uuid4())}
        mock_builder.build_spec.return_value = spec

        # Exercise
        observer = ConfigChangeObserver(
            mock_framework,
            images,
            mock_pod,
            mock_builder
        )
        observer.handle(mock_event)
        # Verify
        assert mock_framework.unit_status_set.call_count == 1
        assert isinstance(
            mock_framework.unit_status_set.call_args[0][0], BlockedStatus)
        assert mock_framework.pod_spec_set.call_count == 0
