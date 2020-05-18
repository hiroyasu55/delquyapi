import app.models.Datastore as Datastore
import app.lib.log as log
from pprint import pprint  # noqa: F401


logger = log.getLogger(__name__)
KIND = 'Person'


def _define_id(no):
    id = 'P_' + str(no).zfill(8)
    return id


def define_id(person):
    if not person.get('no'):
        raise Exception('"no" not definied.')

    return _define_id(person['no'])


def insert(person):
    if type(person) == list:
        return list(map(lambda p: insert(p), person))
    id = define_id(person)
    entity = Datastore.insert(KIND, person, id=id)
    logger.debug('Insert person %s', id)
    return Datastore.entity_to_dict(entity)


def update(person):
    if type(person) == list:
        return list(map(lambda p: update(p), person))
    id = define_id(person)
    entity = Datastore.update(KIND, person, id=id)
    logger.debug('Update person %s', id)
    return Datastore.entity_to_dict(entity)


def upsert(person):
    if type(person) == list:
        return list(map(lambda p: upsert(p), person))
    id = define_id(person)
    entity = Datastore.upsert(KIND, person, id=id)
    logger.debug('Upsert person %s', id)
    return Datastore.entity_to_dict(entity)


def _find(filters=[], order=[], offset=0, limit=None):
    entities = Datastore.find(KIND, filters=filters, order=order, offset=offset, limit=limit)
    persons = list(map(lambda e: Datastore.entity_to_dict(e), entities))
    return persons


def find(filters=[], order=[], offset=0, limit=None):
    # persons = []
    # age_filters = list(filter(lambda f: f['key'] == 'age', filters))
    # if len(age_filters) > 0:
    #     age_filters[0].split(',')

    entities = Datastore.find(KIND, filters=filters, order=order, offset=offset, limit=limit)
    persons = list(map(lambda e: Datastore.entity_to_dict(e), entities))
    return persons


def find_by_id(id):
    entity = Datastore.find_by_id(KIND, id)
    return Datastore.entity_to_dict(entity)


def find_by_no(no):
    id = _define_id(no)
    entity = Datastore.find_by_id(KIND, id)
    return Datastore.entity_to_dict(entity)


def get_last_no():
    nos = Datastore.get_one_property(KIND, 'no', order=['-no'], limit=1)
    if len(nos) == 0:
        return 0

    return nos[0]['no']


def delete_by_no(person):
    if type(person) == list:
        return list(map(lambda p: delete_by_no(p), person))
    entity = Datastore.find_one(KIND, 'no', person['no'])

    return Datastore.delete(KIND, entity.key.id)


def delete(person):
    if type(person) == list:
        return list(map(lambda p: delete(p), person))

    elif type(person) == dict:
        id = define_id(person)
    else:
        id = person

    entity = Datastore.delete(KIND, id)
    logger.debug('delete %s', id)
    return Datastore.entity_to_dict(entity)


def count(filters=[]):
    return Datastore.count(KIND, filters)


def current_date():
    entities = Datastore.get_one_property(KIND, 'release_date', order=['-release_date'], limit=1)
    if len(entities) == 0:
        return ''
    return Datastore.entity_to_dict(entities[0]['release_date'])


def get_tree_parent(person):
    if not person.get('contacts'):
        return None
    contacts = sorted(person['contacts'], key=lambda c: c['person_no'])
    parent = find_by_no(contacts[0]['person_no'])
    if not parent:
        raise Exception('parent[{}] not exists.'.format(contacts[0]['person_no']))
    return parent


def get_tree_root(person):
    root = person
    while True:
        parent = get_tree_parent(root)
        if not parent:
            break
        root = parent
    return root


def _get_nodes(no, persons=None, level=0, current_no=None):
    nodes = []
    total = 0

    persons = list(filter(lambda p: p and p.get('contacts'), persons))

    if len(persons) == 0:
        return 0, []

    for i, p in enumerate(persons):
        if p['contacts'][0]['person_no'] != no:
            continue
        node = {
            'level': level,
        }
        node.update(p)
        if p['no'] == current_no:
            node['current'] = True
        nodes.append(node)
        persons[i] = None

    if len(nodes) == 0:
        return 0, []
    total = len(nodes)

    persons = list(filter(lambda p: p, persons))
    for node in nodes:
        _total, _nodes = _get_nodes(node['no'], persons=persons, level=level + 1, current_no=current_no)
        if _total > 0:
            total += _total
            node['nodes'] = _nodes

    return total, nodes


def _get_tree(person, persons=None, current_no=None):
    if not persons:
        persons = find()
        persons = list(filter(lambda p: p.get('contacts') or p['reason'] == 'recurrence', persons))

    root = get_tree_root(person)
    tree = {
        'root': root,
    }
    if root['no'] == person['no']:
        tree['current'] = True

    total, nodes = _get_nodes(root['no'], level=1, persons=persons, current_no=current_no)

    tree['total'] = total
    if total > 0:
        tree['nodes'] = nodes

    return tree


def get_tree(person=None):
    if person:
        return _get_tree(person, current_no=person['no'])

    trees = []
    persons = find()

    roots = list(filter(lambda p: not p.get('contacts') and p['reason'] != 'recurrence', persons))
    persons = list(filter(lambda p: p.get('contacts') or p['reason'] == 'recurrence', persons))
    for root in roots:
        _persons = persons[:]
        total, nodes = _get_nodes(root['no'], level=1, persons=_persons)
        tree = {
            'root': root,
            'total': total
        }
        if total > 0:
            tree['nodes'] = nodes
        trees.append(tree)

    return trees
