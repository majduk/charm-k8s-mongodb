from pathlib import Path
import random
import shutil
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import (
    call,
    create_autospec,
    patch
)
from uuid import uuid4

sys.path.append('lib')
from ops.charm import (
    CharmMeta,
)
from ops.framework import (
    EventBase,
    Framework
)
from ops.model import (
    ActiveStatus,
    MaintenanceStatus,
)

sys.path.append('src')
from charm import (
    MongoDbCharm
)


class CharmTest(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        # Ensure that we clean up the tmp directory even when the test
        # fails or errors out for whatever reason.
        self.addCleanup(shutil.rmtree, self.tmpdir)

    def create_framework(self):
        framework = Framework(self.tmpdir / "framework.data",
                              self.tmpdir, CharmMeta(), None)
        # Ensure that the Framework object is closed and cleaned up even
        # when the test fails or errors out.
        self.addCleanup(framework.close)

        return framework

    def test_func_fast(self):
        pass
