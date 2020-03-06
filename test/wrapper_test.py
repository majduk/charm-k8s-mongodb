from pathlib import Path
import sys
import shutil
import unittest
from uuid import uuid4
import json
import tempfile
from unittest.mock import (
    call,
    patch,
    create_autospec,
    MagicMock,
)
sys.path.append('lib')
sys.path.append('src')
from ops.framework import (
    Framework
)
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

from wrapper import FrameworkWrapper


class FrameworkWrapperTest(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.mock_framework = self.create_framework()
        self.addCleanup(shutil.rmtree, self.tmpdir)

    def create_framework(self):
        model = create_autospec(Model)
        model.unit = create_autospec(Unit)
        model.unit.is_leader = MagicMock(return_value=False)
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

    def test_config(self):
        # Setup
        mock_data = {'key': f'{uuid4()}'}
        self.mock_framework.model.config = MagicMock(return_value=mock_data)
        # Exercise
        wrapper = FrameworkWrapper(self.mock_framework, None)
        config = wrapper.config()
        # Assert
        assert config == mock_data

    def test_state(self):
        # Setup
        mock_state = {'key': f'{uuid4()}'}
        # Exercise
        wrapper = FrameworkWrapper(self.mock_framework, mock_state)
        config = wrapper.state
        # Assert
        assert config == mock_state

    def test_resources(self):
        # Setup
        mock_data = {'key': f'{uuid4()}'}
        self.mock_framework.model.resources = MagicMock(return_value=mock_data)
        # Exercise
        wrapper = FrameworkWrapper(self.mock_framework, None)
        config = wrapper.resources()
        # Assert
        assert config == mock_data

    def test_app_name(self):
        # Exercise
        wrapper = FrameworkWrapper(self.mock_framework, None)
        config = wrapper.app_name
        # Assert
        assert config == "test-app"

    def test_pod_spec_set(self):
        # Setup
        mock_data = {'key': f'{uuid4()}'}
        # Exercise
        wrapper = FrameworkWrapper(self.mock_framework, None)
        wrapper.pod_spec_set(mock_data)
        # Assert
        assert self.mock_framework.model.pod.set_spec.call_count == 1
        assert self.mock_framework.model.pod.set_spec.call_args ==\
            call(mock_data)

    def test_status_set(self):
        # Setup
        mock_data = {'key': f'{uuid4()}'}
        # Exercise
        wrapper = FrameworkWrapper(self.mock_framework, None)
        wrapper.unit_status_set(mock_data)
        # Assert
        assert self.mock_framework.model.unit.status == mock_data

    @patch('subprocess.check_output')
    def test_goal_state_units(self, mock_subproc):
        # Setup
        mock_data = {"units": {
            "mongodb-k8s/0": {"status": "active",
                              "since": "2020-03-05 10:53:51Z"},
            "mongodb-k8s/1": {"status": "active",
                              "since": "2020-03-05 10:55:30Z"},
            "mongodb-k8s/2": {"status": "active",
                              "since": "2020-03-05 10:55:23Z"}},
                     "relations": {}}
        mock_output = MagicMock()
        mock_output.decode.return_value = json.dumps(mock_data)
        mock_subproc.return_value = mock_output
        # Exercise
        wrapper = FrameworkWrapper(self.mock_framework, None)
        config = wrapper.goal_state_units
        # Assert
        assert config == mock_data['units']

    def test_unit_is_leader(self):
        # Exercise
        wrapper = FrameworkWrapper(self.mock_framework, None)
        config = wrapper.unit_is_leader
        # Assert
        assert config is False
