from google.cloud import datastore
from datetime import datetime
import app.lib.log as log


logger = log.getLogger(__name__)
client = datastore.Client()


def now_string():
    return datetime.now().strftime(r'%Y-%m-%d %H:%M:%S')


def entity_to_dict(data):
    if data is None:
        return data

    if data.__class__.__name__ == 'Entity':
        data = dict(data)

    if type(data) is dict:
        for key in data:
            data[key] = entity_to_dict(data[key])
    elif type(data) is list:
        data = list(map(lambda d: entity_to_dict(d), data))

    return data


def insert(kind, object, id=None):
    if id:
        entity_key = client.key(kind, id)
        if client.get(entity_key):
            raise Exception('Entity already exists. kind={},id={}'.format(kind, id))
    else:
        entity_key = client.key(kind)

    entity = datastore.Entity(entity_key)
    entity.update(object)
    entity.update({'created': now_string(), 'updated': now_string()})
    client.put(entity)
    entity['id'] = entity.key.id or id
    logger.debug('insert: kind={},id={}'.format(kind, id))

    return entity


def _update(entity, object=None):
    if object:
        entity.update(object)
    entity.update({'updated': now_string()})
    client.put(entity)
    return entity


def update(kind, object, id):
    if not id:
        raise Exception('update: id not defined.')

    entity = find_by_id(kind, id)
    if not entity:
        raise Exception('Entity not found. kind={},id={}'.format(kind, id))

    entity = _update(entity, object=object)
    logger.debug('update: kind=%s id=%s', kind, id)

    return entity


def upsert(kind, object, id=None):
    entity = None
    if id:
        entity = find_by_id(kind, id)
        if entity:
            entity = _update(entity, object=object)
            client.put(entity)
            logger.debug('upsert(update): kind=%s id=%s', kind, id)
        else:
            entity = insert(kind, object, id=id)
            logger.debug('upsert(insert): kind=%s id=%s', kind, id)

    else:
        entity = insert(kind, object)
        logger.debug('upsert(insert): kind=%s', kind)

    return entity


def find(kind, filters=[], order=[], offset=0, limit=None):
    query = client.query(kind=kind)
    for f in filters:
        symbol = f.get('symbol') or '='
        query.add_filter(f['key'], symbol, f['value'])

    query.order = order
    param = {
        'offset': offset,
        'limit': limit
    }

    entities = list(query.fetch(**param))
    return entities


def find_by_id(kind, id):
    entity = None

    if not id:
        raise Exception('find_by_id: id not defined.')

    entitiy_key = client.key(kind, id)
    entity = client.get(entitiy_key)
    return entity


def find_one(kind, key=None, value=None):
    entity = None

    if not key:
        raise Exception('find_one: key not defined.')
    if not value:
        raise Exception('find_one: value not defined.')

    query = client.query(kind=kind)
    query.add_filter(key, '=', value)
    entities = list(query.fetch())
    if len(entities) == 0:
        return None
    entity = entities[0]

    return entity


def delete(kind, id, ignore_none=False):
    if not id:
        raise Exception('delete: id not defined.')

    key = client.key(kind, id)
    if not key:
        if not ignore_none:
            raise Exception('Entity not exists. kind={},id={}'.format(kind, id))
        else:
            log.debug('delete: Ignore no entity. kind={},id={}'.format(kind, id))
            return None

    result = client.delete(key)
    logger.debug('delete: kind=%s id=%s', kind, id)
    return result


def delete_one(kind, key=None, value=None):
    if not key:
        raise Exception('delete_one: key not defined.')
    if not value:
        raise Exception('delete_one: value not defined.')

    entity = find_one(kind, key=key, value=value)
    if not entity:
        logger.warning('delete_one: entity not found.')
        return None

    client.delete(client.key(kind, entity.key.id))
    return entity


def count(kind, filters=[]):
    query = client.query(kind=kind)
    query.keys_only()
    for f in filters:
        symbol = f.get('symbol') or '='
        query.add_filter(f['key'], symbol, f['value'])

    entities = list(query.fetch())
    return len(entities)


def get_one_property(kind, property, filters=[], order=None, offset=0, limit=None):
    query = client.query(kind=kind)
    query.projection = [property]
    query.distinct_on = [property]

    for f in filters:
        symbol = f.get('symbol') or '='
        query.add_filter(f['key'], symbol, f['value'])

    query.order = order or [property]
    param = {
        'offset': offset,
        'limit': limit
    }

    entities = list(query.fetch(**param))

    return list(entities)
