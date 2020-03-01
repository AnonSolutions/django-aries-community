import os
import datetime
import platform

from .settings import *


ARIES_CONFIG['storage_config'] = {'url': 'wallet-db:5432'}
ARIES_CONFIG['ledger_url']      = 'http://test.bcovrin.vonx.io'
ARIES_CONFIG['genesis_url'] = 'http://test.bcovrin.vonx.io/genesis'
ARIES_CONFIG['managed_agent_host'] = 'aries-django'
ARIES_CONFIG['webhook_host'] = 'aries-django'
ARIES_CONFIG['webhook_port'] = '8000'
