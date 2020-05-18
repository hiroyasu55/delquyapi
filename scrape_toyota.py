import settings  # noqa: F401
import urllib.parse as parse
from datetime import date  # noqa: F401
import re
import os  # noqa: F401
from pprint import pprint  # noqa: F401
import json
import app.lib.log as log
import app.models.Detail as Detail

logger = log.getLogger(__name__)


# Main
if __name__ == '__main__':

    with open('data/toyota.json', 'r') as f:
        result = json.load(f)
    details = result['details']

    current_date = ''
    current_details = Detail.find_by_government('toyota')
    if len(current_details) > 0:
        current_date = current_details[-1]['release_date']

    details = list(filter(lambda d: d['release_date'] > current_date, details))
    for detail in details:
        pprint(detail)
        Detail.insert(detail)

    exit()
