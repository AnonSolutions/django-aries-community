import asyncio
import aiohttp
import json
from os import environ
import random

import nacl.bindings
import nacl.exceptions
import nacl.utils

#from typing import Callable, Optional, Sequence, Tuple
from typing import Tuple

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


def create_keypair(seed: bytes = None) -> Tuple[bytes, bytes]:
    """
    Create a public and private signing keypair from a seed value.

    Args:
        seed: Seed for keypair

    Returns:
        A tuple of (public key, secret key)

    """
    if not seed:
        seed = random_seed()
    pk, sk = nacl.bindings.crypto_sign_seed_keypair(seed)
    return pk, sk


def validate_seed(seed: (str, bytes)) -> bytes:
    """
    Convert a seed parameter to standard format and check length.

    Args:
        seed: The seed to validate

    Returns:
        The validated and encoded seed

    """
    if not seed:
        return None
    if isinstance(seed, str):
        if "=" in seed:
            seed = b64_to_bytes(seed)
        else:
            seed = seed.encode("ascii")
    if not isinstance(seed, bytes):
        raise Exception("Seed value is not a string or bytes")
    if len(seed) != 32:
        raise Exception("Seed value must be 32 bytes in length")
    return seed


def seed_to_did(seed: str) -> (str, str):
    """
    Derive a DID from a seed value.

    Args:
        seed: The seed to derive

    Returns:
        The DID derived from the seed

    """
    seed = validate_seed(seed)
    verkey, _ = create_keypair(seed)
    did = bytes_to_b58(verkey[:16])
    return (did, verkey)


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
            print("Registered", nym_info)
    except Exception as e:
        raise Exception(str(e)) from None
    if not nym_info or not "did" in nym_info or not nym_info["did"]:
        raise Exception(
            "DID registration failed: {}".format(nym_info)
        )
    return nym_info


def create_and_register_did(alias, did_seed, org_role=None):
    """
    Register DID on ledger (except Trustee which is assumed already there)
    """

    if org_role and org_role == 'Trustee':
        # don't register Trustee role
        return None

    if not settings.ARIES_CONFIG['register_dids']:
        return None

    ledger_url = environ.get('LEDGER_URL', settings.ARIES_CONFIG['ledger_url'])
    nym_info = run_coroutine_with_args(register_did_on_ledger, ledger_url, alias, did_seed)

    return nym_info
