from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import (
    create_autospec,
    patch,
    call,
    Mock
)
from uuid import uuid4

sys.path.append('lib')
from ops.charm import (
    CharmMeta,
)
from ops.framework import (
    EventBase,
    Framework,
)

from ops.model import (
    Model,
    Unit,
    Pod,
    ConfigData,
    Application,
    ActiveStatus,
    BlockedStatus,
    WaitingStatus,
)

sys.path.append('src')
from charm import (
    MongoDbCharm
)


class CharmTest(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.mock_framework = self.create_framework()
        self.addCleanup(shutil.rmtree, self.tmpdir)

    def create_framework(self):
        model = create_autospec(Model)
        model.unit = create_autospec(Unit)
        model.unit.is_leader = Mock(return_value=True)
        model.app = create_autospec(Application)
        model.pod = create_autospec(Pod)
        model.config = create_autospec(ConfigData)
        framework = Framework(self.tmpdir / "framework.data",
                              self.tmpdir, CharmMeta(), model)

        framework.model.app.name = "test-app"
        self.addCleanup(framework.close)

        return framework

    def create_image_resource_obj(self, mock_image_resource, fetch):
        mock_image_resource_obj = mock_image_resource.return_value
        mock_image_resource_obj.fetch.return_value = fetch
        mock_image_resource_obj.image_path = f'{uuid4()}/{uuid4()}'
        mock_image_resource_obj.username = f'{uuid4()}'
        mock_image_resource_obj.password = f'{uuid4()}'
        return mock_image_resource_obj

    @patch('charm.OCIImageResource')
    def test__on_event_leader_fetched(self, mock_image_resource_clazz):
        # setup test
        mock_image_resource_obj =\
            self.create_image_resource_obj(mock_image_resource_clazz, True)
        mock_event = create_autospec(EventBase)
        spec = {
            'containers': [{
                'name': self.mock_framework.model.app.name,
                'imageDetails': {
                    'imagePath': mock_image_resource_obj.registry_path,
                    'username': mock_image_resource_obj.username,
                    'password': mock_image_resource_obj.password,
                },
                'ports': [{
                    'containerPort':
                    self.mock_framework.model.config['advertised-port'],
                    'protocol': 'TCP',
                }],
            }],
        }
        # run code
        charm_obj = MongoDbCharm(self.mock_framework, None)
        charm_obj.on_start(mock_event)
        # check assertions
        assert isinstance(self.mock_framework.model.unit.status, ActiveStatus)
        assert mock_image_resource_obj.fetch.call_count == 1
        assert self.mock_framework.model.pod.set_spec.call_count == 1
        assert self.mock_framework.model.pod.set_spec.call_args == call(spec)

    @patch('charm.OCIImageResource')
    def test__on_event_leader_not_fetched(self, mock_image_resource_clazz):
        # setup test
        mock_image_resource_obj =\
            self.create_image_resource_obj(mock_image_resource_clazz, False)
        mock_event = create_autospec(EventBase)
        # run code
        charm_obj = MongoDbCharm(self.mock_framework, None)
        charm_obj.on_start(mock_event)
        # check assertions
        assert isinstance(self.mock_framework.model.unit.status, BlockedStatus)
        assert mock_image_resource_obj.fetch.call_count == 1
        assert self.mock_framework.model.pod.set_spec.call_count == 0

    @patch('charm.OCIImageResource')
    def test__on_event_not_leader(self, mock_image_resource_clazz):
        # setup test
        mock_image_resource_obj =\
            self.create_image_resource_obj(mock_image_resource_clazz, True)
        mock_event = create_autospec(EventBase)
        self.mock_framework.model.unit.is_leader = Mock(return_value=False)
        # run code
        charm_obj = MongoDbCharm(self.mock_framework, None)
        charm_obj.on_start(mock_event)
        # check assertions
        assert isinstance(self.mock_framework.model.unit.status, WaitingStatus)
        assert mock_image_resource_obj.fetch.call_count == 1
        assert self.mock_framework.model.pod.set_spec.call_count == 0
