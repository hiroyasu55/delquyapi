import settings  # noqa: F401
from app import app
import config
import app.lib.log as log

logger = log.getLogger(__name__)


# Main
if __name__ == '__main__':
    param = {
        'debug': config.DEBUG
    }
    if config.FLASK_PORT:
        param['port'] = config.FLASK_PORT
    app.run(**param)
