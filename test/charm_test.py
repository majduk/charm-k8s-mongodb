from pathlib import Path
import sys
import shutil
import unittest
import tempfile
from unittest.mock import (
    patch,
    create_autospec,
    Mock,
    MagicMock
)

from uuid import uuid4

sys.path.append('lib')
sys.path.append('src')

from ops.model import (
    Model,
    Unit,
    Pod,
    ConfigData,
    Application,
)

from ops.charm import (
    CharmMeta,
)
from ops.framework import (
    EventBase,
    Framework,
)

from charm import (
    MongoDbCharm
)

from wrapper import FrameworkWrapper


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
        raw_meta = {
            'provides': {'mongo': {"interface": "mongodb"}}
        }
        framework = Framework(self.tmpdir / "framework.data.{}"
                              .format(str(uuid4)),
                              self.tmpdir, CharmMeta(raw=raw_meta), model)

        framework.model.app.name = "test-app"
        self.addCleanup(framework.close)

        return framework

    @patch('charm.StatusObserver', spec_set=True, autospec=True)
    @patch.object(FrameworkWrapper, 'goal_state_units',
                  MagicMock(return_value={}))
    @patch.object(FrameworkWrapper, 'config', MagicMock(return_value={}))
    def test_on_relation(self, mock_observer_clazz):
        # setup test
        mock_event = create_autospec(EventBase)
        mock_observer = mock_observer_clazz.return_value

        # run code
        charm_obj = MongoDbCharm(self.mock_framework, None)
        charm_obj.on_update_status_delegator(mock_event)

        # check assertions
        assert mock_observer.handle.call_count == 1
