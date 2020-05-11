import asyncio
import aiohttp
import json
from os import environ
import random

from django.conf import settings

from .models import *
from .utils import *


######################################################################
# basic wallet management utilities
######################################################################
def get_user_wallet_name(username):
    """
    Determine wallet name based on a user name (email).
    """

    wallet_name = username.replace("@", "_")
    wallet_name = wallet_name.replace(".", "_")
    return 'i_{}'.format(wallet_name).lower()


def get_org_wallet_name(orgname):
    """
    Determine wallet name based on an organization name.
    """

    wallet_name = orgname.replace("@", "_")
    wallet_name = wallet_name.replace(".", "_")
    wallet_name = wallet_name.replace(" ", "_")
    return 'o_{}'.format(wallet_name).lower()


def wallet_config(wallet_name):
    """
    Build a wallet configuration dictionary (postgres specific).
    """

    storage_config = settings.INDY_CONFIG['storage_config']
    wallet_config = settings.INDY_CONFIG['wallet_config']
    wallet_config['id'] = wallet_name
    wallet_config['storage_config'] = storage_config
    wallet_config_json = json.dumps(wallet_config)
    return wallet_config_json


def wallet_credentials(raw_password):
    """
    Build wallet credentials dictionary (postgres specific).
    """

    storage_credentials = settings.INDY_CONFIG['storage_credentials']
    wallet_credentials = settings.INDY_CONFIG['wallet_credentials']
    wallet_credentials['key'] = raw_password
    wallet_credentials['storage_credentials'] = storage_credentials
    wallet_credentials_json = json.dumps(wallet_credentials)
    return wallet_credentials_json

