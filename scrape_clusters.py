import settings  # noqa: F401
from datetime import date  # noqa: F401
import os  # noqa: F401
from pprint import pprint  # noqa: F401
import config
import json
import app.lib.log as log
import app.lib.util as util
import app.models.Cluster as Cluster


logger = log.getLogger('scrape_clusters')


# Main
if __name__ == '__main__':

    with open('data/clusters.json', 'r') as f:
        result = json.load(f)
    clusters = result['clusters']

    for cluster in clusters:
        pprint(cluster)
        Cluster.upsert(cluster)
