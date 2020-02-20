import os
import datetime
import platform

from .settings import *


ARIES_CONFIG['storage_config'] = {'url': 'wallet-db:5432'}
ARIES_CONFIG['ledger_url']      = 'http://webserver:8000'
ARIES_CONFIG['genesis_url'] = 'http://webserver:8000/genesis'

