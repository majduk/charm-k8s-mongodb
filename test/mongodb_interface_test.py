import sys
import unittest
from uuid import uuid4
from unittest.mock import (
    patch,
    create_autospec,
    MagicMock,
)
sys.path.append('lib')
sys.path.append('src')
from ops.framework import (
    EventBase,
)
from mongodb_interface_provides import (
    MongoDbInterfaceDataFormatter,
    MongoDbInterfaceClient,
    MongoDbServer
)


class MongoDbInterfaceTest(unittest.TestCase):

    @patch('ops.framework.BoundStoredState')
    def test_mongo_server_on_joined(self, mock_store_class):
        # Setup
        mock_app = f'{uuid4()}'
        mock_store = mock_store_class.return_value
        mock_store.apps.return_value = []
        mock_charm = MagicMock()
        mock_relations = {f'{uuid4()}': f'{uuid4()}'}
        mock_charm.framework.model._relations = mock_relations
        mock_event = create_autospec(EventBase)
        mock_event.relation = {f'{uuid4()}': f'{uuid4()}'}
        mock_event.app = MagicMock()
        mock_event.app.name.return_value = mock_app
        # Exercise
        server = MongoDbServer(mock_charm, 'mongo')
        server.on_joined(mock_event)
        # Validate
        assert server.state.apps.append.call_count == 1

    @patch('ops.framework.BoundStoredState')
    def test_mongo_server_on_departed(self, mock_store_class):
        # Setup
        mock_app = f'{uuid4()}'
        mock_store = mock_store_class.return_value
        mock_store.apps.return_value = []
        mock_charm = MagicMock()
        mock_relations = {f'{uuid4()}': f'{uuid4()}'}
        mock_charm.framework.model._relations = mock_relations
        mock_event = create_autospec(EventBase)
        mock_event.relation = {f'{uuid4()}': f'{uuid4()}'}
        mock_event.app = MagicMock()
        mock_event.app.name.return_value = mock_app
        # Exercise
        server = MongoDbServer(mock_charm, 'mongo')
        server.on_departed(mock_event)
        # Validate
        assert server.state.apps == []

    def test_mongo_client(self):
        # Setup
        mock_name = uuid4()
        mock_id = uuid4()
        mock_relation = MagicMock()
        mock_relation.name = mock_name
        mock_relation.id = mock_id
        # Exercise
        client = MongoDbInterfaceClient(mock_relation, None)
        # Validate
        assert client.name == mock_name
        assert client.id == mock_id
        assert isinstance(client.formatter, MongoDbInterfaceDataFormatter)

    def test_mongo_data_formatter(self):
        # Setup
        mock_data = uuid4()
        # Exercise
        formatter = MongoDbInterfaceDataFormatter()
        config = formatter.format(mock_data)
        # Validate
        assert config == {'connection_string': mock_data}
