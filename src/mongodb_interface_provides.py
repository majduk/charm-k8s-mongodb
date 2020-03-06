from ops.framework import (
    EventsBase,
    EventSource,
    Object,
    StoredState
)
from ops.charm import RelationEvent


class NewClientEvent(RelationEvent):

    def restore(self, snapshot):
        super().restore(snapshot)
        self.client = MongoDbInterfaceClient(self.relation, self.unit)


class MongoDbServerEvents(EventsBase):
    new_client = EventSource(NewClientEvent)


class MongoDbServer(Object):
    on = MongoDbServerEvents()
    state = StoredState()

    def __init__(self, charm, relation_name):
        super().__init__(charm, relation_name)
        self.relation_name = relation_name
        self.framework.observe(charm.on.start, self.init_state)
        self.framework.observe(charm.on[relation_name].relation_joined,
                               self.on_joined)
        self.framework.observe(charm.on[relation_name].relation_departed,
                               self.on_departed)

    def init_state(self, event):
        self.state.apps = []

    @property
    def _relations(self):
        return self.model.relations[self.relation_name]

    def on_joined(self, event):
        if event.app not in self.state.apps:
            self.state.apps.append(event.app.name)
            self.on.new_client.emit(MongoDbInterfaceClient(event.relation,
                                                           self.model.unit))

    def on_departed(self, event):
        self.state.apps = [app.name for app in self._relations]

    def clients(self):
        return [
            MongoDbInterfaceClient(
                relation,
                self.model.unit) for relation in self._relations]


class MongoDbInterfaceClient:

    def __init__(self, relation, local_unit):
        self._relation = relation
        self._local_unit = local_unit

    @property
    def name(self):
        return self._relation.name

    @property
    def id(self):
        return self._relation.id

    @property
    def formatter(self):
        return MongoDbInterfaceDataFormatter()


class MongoDbInterfaceDataFormatter:

    def format(self, mongo_uri):
        return {'connection_string': mongo_uri}
