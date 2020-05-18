import urllib.request
import urllib.parse
from urllib.error import URLError
import socket
import time
from bs4 import BeautifulSoup
import app.lib.log as log
import config


logger = log.getLogger(__name__)


def html_to_text(html, br_delimiter='\n'):
    DUMMY_STRING = r'[aynvScmp034ms5]'

    for br in html.select('br'):
        if br.string:
            br.replace_with(DUMMY_STRING + br.string)
        else:
            br.replace_with(DUMMY_STRING)

    text = html.text.strip().replace('\n', '').replace(DUMMY_STRING, br_delimiter)
    return text


def create_soup(url):
    retry_count = 4
    timeout_sec = 3

    soup = None
    for i in range(0, retry_count):
        try:
            req = urllib.request.Request(
                url=url,
                headers={
                    'User-Agent': config.USER_AGENT
                }
            )
            with urllib.request.urlopen(req, timeout=timeout_sec) as res:
                soup = BeautifulSoup(res, 'html.parser')
                break

        except socket.timeout:
            logger.info('timeout, retry url:%s', url)

        except URLError as e:
            if isinstance(e.reason, socket.timeout):
                logger.info('Timeout, retry:%s', url)
                time.sleep(0.5)
            else:
                raise e

        except Exception as e:
            raise e

    if not soup:
        raise Exception('Request timeout url:{}.'.format(url))

    time.sleep(0.5)

    return soup
