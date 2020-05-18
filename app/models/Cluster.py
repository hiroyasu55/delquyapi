import app.models.Datastore as Datastore
import app.lib.log as log


logger = log.getLogger(__name__)
KIND = 'Cluster'


def _define_id(no):
    id = 'C_' + str(no).zfill(8)
    return id


def define_id(cluster):
    if not cluster.get('no'):
        raise Exception('"no" not definied.')

    return _define_id(cluster['no'])


def insert(cluster):
    if type(cluster) == list:
        return list(map(lambda c: insert(c), cluster))
    id = define_id(cluster)
    entity = Datastore.insert(KIND, cluster, id=id)
    logger.debug('Insert cluster %s', id)
    return Datastore.entity_to_dict(entity)


def update(cluster):
    if type(cluster) == list:
        return list(map(lambda c: update(c), cluster))
    id = define_id(cluster)
    entity = Datastore.update(KIND, cluster, id=id)
    logger.debug('Update cluster %s', id)
    return Datastore.entity_to_dict(entity)


def upsert(cluster):
    if type(cluster) == list:
        return list(map(lambda c: upsert(c), cluster))
    id = define_id(cluster)
    entity = Datastore.upsert(KIND, cluster, id=id)
    logger.debug('Upsert cluster %s', id)
    return Datastore.entity_to_dict(entity)


def find(filters=[], order=[], offset=0, limit=None):
    entities = Datastore.find(KIND, filters=filters, order=order, offset=offset, limit=limit)
    clusters = list(map(lambda e: Datastore.entity_to_dict(e), entities))
    return clusters


def find_by_id(id):
    entity = Datastore.find_by_id(KIND, id)
    return Datastore.entity_to_dict(entity)


def find_by_no(no):
    id = _define_id(no)
    entity = Datastore.find_by_id(KIND, id)
    return Datastore.entity_to_dict(entity)


def delete(cluster):
    if type(cluster) == list:
        return list(map(lambda c: delete(c), cluster))

    elif type(cluster) == dict:
        id = define_id(cluster)
    else:
        id = cluster

    entity = Datastore.delete(KIND, id)
    logger.debug('delete %s', id)
    return Datastore.entity_to_dict(entity)


def count(filters=[]):
    return Datastore.count(KIND, filters)
