from hashlib import sha256
from app.models.Store import Store


store = Store()
KIND = 'User'
h = sha256()

SCHEMA = {
    'id': 'str',
    'name': 'str',
    'password': 'str'
}


class User(object):
    _users = []

    def __init__(self, id=None, name=None, password=None):
        if not name:
            raise Exception('Name not defined.')
        if not password:
            raise Exception('Password not defined.')
        if id:
            self.id = name

        self.name = name
        self.password = User.hash_password(password)

    def __str__(self):
        return 'User(id={},name={},password={})'.format(self.id, self.name, self.password)

    def check_password(self, password):
        return (User.hash_password(password) == self.password)

    def add(self):
        obj = {
            'name': self.name,
            'password': self.password
        }
        entity = store.add(KIND, obj)
        return (entity is not None)

    @classmethod
    def get(self, id):
        entity = store.get(KIND, id)
        if not entity:
            return None

        user = User(id=entity['id'], name=entity['name'], password=entity['password'])
        return user

    @classmethod
    def hash_password(cls, password):
        h.update(password.encode('utf-8'))
        return h.hexdigest()

    @classmethod
    def find(cls, id):
        _users = [
            User(1, 'user1', 'abcxyz'),
            User(2, 'user2', 'abcxyz'),
        ]
        table = {u.id: u for u in _users}
        return table.get(id, None)

    @classmethod
    def get_by_name(cls, name):
        _users = [
            User(1, 'user1', 'abcxyz'),
            User(2, 'user2', 'abcxyz'),
        ]
        table = {u.name: u for u in _users}
        return table.get(name, None)
