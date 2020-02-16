import asyncio
import aiohttp
import json
from os import environ
import random

from django.conf import settings

from .models import *
from .utils import *


def calc_did_seed(agent_name, org_role=''):
    """
    calculate a did seed based on the agent name
    """

    if org_role == 'Trustee':
        return settings.ARIES_CONFIG['default_enterprise_seed']
    else:
        return (settings.ARIES_CONFIG['default_institution_seed'] + agent_name)[-32:]


async def register_did_on_ledger(ledger_url, alias, seed):
    """
    Register DID on ledger via VON Network ledger browser
    """

    try:
        async with aiohttp.ClientSession() as client:
            response = await client.post(
                "{}/register".format(ledger_url),
                json={"alias": alias, "seed": seed, "role": "TRUST_ANCHOR"},
            )
            nym_info = await response.json()
    except Exception as e:
        raise Exception(str(e)) from None
    if not nym_info or not nym_info["did"]:
        raise Exception(
            "DID registration failed: {}".format(nym_info)
        )
    return nym_info


def create_and_register_did(wallet_name, org_role):
    """
    Register DID on ledger (except Trustee which is assumed already there)
    """

    if org_role == 'Trustee':
        # don't register Trustee role
        return

    if not settings.ARIES_CONFIG['register_dids']:
        return

    enterprise_seed = calc_did_seed(wallet_name, org_role)
    ledger_url = settings.ARIES_CONFIG['ledger_url']
    nym_info = run_coroutine_with_args(register_did_on_ledger, ledger_url, wallet_name, enterprise_seed)

    return nym_info
