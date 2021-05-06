import app.models.Datastore as Datastore
import app.lib.log as log


logger = log.getLogger(__name__)
KIND = 'Detail'


def _define_id(government, no):
    id = government + '_' + str(no).zfill(8)
    return id


def define_id(detail):
    if not detail.get('government'):
        raise Exception('"government" not definied.')
    elif not detail.get('no'):
        raise Exception('"no" not definied.')

    return _define_id(detail['government'], detail['no'])


def insert(detail):
    if type(detail) == list:
        return list(map(lambda d: insert(d), detail))
    id = define_id(detail)
    entity = Datastore.insert(KIND, detail, id=id)
    logger.debug('Insert detail %s', id)
    return Datastore.entity_to_dict(entity)


def update(detail):
    if type(detail) == list:
        return list(map(lambda d: update(d), detail))
    id = define_id(detail)
    entity = Datastore.update(KIND, detail, id=id)
    logger.debug('Update detail %s', id)
    return Datastore.entity_to_dict(entity)


def upsert(detail):
    if type(detail) == list:
        return list(map(lambda d: upsert(d), detail))
    id = define_id(detail)
    entity = Datastore.upsert(KIND, detail, id=id)
    logger.debug('Upsert detail %s', id)
    return Datastore.entity_to_dict(entity)


def find(filters=[], order=[], offset=0, limit=None):
    entities = Datastore.find(KIND, filters=filters, order=order, offset=offset, limit=limit)
    details = list(map(lambda e: Datastore.entity_to_dict(e), entities))
    return details


def find_by_id(id):
    entity = Datastore.find_by_id(KIND, id)
    return Datastore.entity_to_dict(entity)


def find_by_government(government, filters=[], order=[], offset=0, limit=None):
    _filters = [{
        'key': 'government',
        'value': government
    }]
    _filters.extend(filters)
    return find(filters=_filters, order=order, offset=offset, limit=limit)


def find_by_government_no(government, no):
    id = _define_id(government, no)
    entity = Datastore.find_by_id(KIND, id)
    return Datastore.entity_to_dict(entity)


def delete(detail):
    if type(detail) == list:
        return list(map(lambda d: delete(d), detail))

    elif type(detail) == dict:
        id = define_id(detail)
    else:
        id = detail

    entity = Datastore.delete(KIND, id)
    logger.debug('delete %s', id)
    return Datastore.entity_to_dict(entity)


def count(filters=[]):
    return Datastore.count(KIND, filters=filters)
