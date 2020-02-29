# pylint: disable=invalid-name
"""
Copyright (c) All rights reserved, Volker Kettenbach 2017 - 2020. Germany.
"""

#  """ Copyright (c) All rights reserved, Volker Kettenbach 2017 - 2020. Germany. """

import logging
from gunicorn import glogging


# https://github.com/benoitc/gunicorn/blob/master/examples/example_config.py
# commandline: --workers=5 --timeout 120 -b :80 --access-logfile - --error-logfile -

class CustomGunicornLogger(glogging.Logger):
    """ Custom Logger for hunicorn"""
    def setup(self, cfg):
        super().setup(cfg)

        # Add filters to Gunicorn logger
        logger = logging.getLogger("gunicorn.access")
        logger.addFilter(HealthCheckFilter())


class HealthCheckFilter(logging.Filter): # pylint: disable=too-few-public-methods
    """ Healthcheck filter for cusom logger """
    def filter(self, record):
        return 'GET /healthcheck' not in record.getMessage()


daemon = False
workers = 5
bind = "0.0.0.0:80"
timeout = 30
loglevel = 'info'
errorlog = '-'
accesslog = '-'
logger_class = CustomGunicornLogger
