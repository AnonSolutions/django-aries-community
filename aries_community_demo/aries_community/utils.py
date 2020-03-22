from django.apps import apps as django_apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

import asyncio
import random
import string

import base58
import base64


######################################################################
# Indy model override utilities
######################################################################

def get_aries_settings_model(model_type):
    """
    Return the Aries override model that is active in this project.
    model_type is 'ARIES_ORGANIZATION_MODEL' or 'ARIES_ORG_RELATION_MODEL'
    """

    try:
        return django_apps.get_model(getattr(settings, model_type), require_ready=False)
    except ValueError:
        raise ImproperlyConfigured("%s must be of the form 'app_label.model_name'" % model_type)
    except LookupError:
        raise ImproperlyConfigured(
            "%s refers to model '%s' that has not been installed" % (model_type, getattr(settings, model_type))
        )

def get_ariesmodel(model_type):
    """
    Return the Aries override model that is active in this project.
    model_type is 'ARIES_ORGANIZATION_MODEL' or 'ARIES_ORG_RELATION_MODEL'
    """
    
    try:
        return django_apps.get_model(model_type, require_ready=False)
    except ValueError:
        raise ImproperlyConfigured("%s must be of the form 'app_label.model_name'" % model_type)
    except LookupError:
        raise ImproperlyConfigured(
            "refers to model '%s' that has not been installed" % model_type
        )


######################################################################
# a few random utilities
######################################################################

def random_int(low, high):
    return random.randint(low, high)

def random_alpha_string(length, contains_spaces=False):
    if contains_spaces:
        chars = string.ascii_uppercase + ' '
    else:
        chars = string.ascii_uppercase
    return ''.join(random.SystemRandom().choice(chars) for _ in range(length))

def random_numeric_string(length):
    chars = string.digits
    return ''.join(random.SystemRandom().choice(chars) for _ in range(length))

def random_an_string(length, contains_spaces=False):
    if contains_spaces:
        chars = string.ascii_uppercase + string.digits + ' '
    else:
        chars = string.ascii_uppercase + string.digits
    return ''.join(random.SystemRandom().choice(chars) for _ in range(length))

def random_schema_version():
    version = format("%d.%d.%d" % (random.randint(1, 101), random.randint(1, 101), random.randint(1, 101)))
    return version


######################################################################
# coroutine utilities
######################################################################

def run_coroutine(coroutine):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine())
    finally:
        loop.close()

def run_coroutine_with_args(coroutine, *args):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine(*args))
    finally:
        loop.close()

def run_coroutine_with_kwargs(coroutine, *args, **kwargs):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coroutine(*args, **kwargs))
    finally:
        loop.close()


######################################################################
# other misc
######################################################################

def flatten(args):
    for arg in args:
        if isinstance(arg, (list, tuple)):
            yield from flatten(arg)
        else:
            yield arg


######################################################################
# other misc
######################################################################

def pad(val: str) -> str:
    """Pad base64 values if need be: JWT calls to omit trailing padding."""
    padlen = 4 - len(val) % 4
    return val if padlen > 2 else (val + "=" * padlen)


def unpad(val: str) -> str:
    """Remove padding from base64 values if need be."""
    return val.rstrip("=")


def b64_to_bytes(val: str, urlsafe=False) -> bytes:
    """Convert a base 64 string to bytes."""
    if urlsafe:
        return base64.urlsafe_b64decode(pad(val))
    return base64.b64decode(pad(val))


def b64_to_str(val: str, urlsafe=False, encoding=None) -> str:
    """Convert a base 64 string to string on input encoding (default utf-8)."""
    return b64_to_bytes(val, urlsafe).decode(encoding or "utf-8")


def bytes_to_b64(val: bytes, urlsafe=False, pad=True) -> str:
    """Convert a byte string to base 64."""
    b64 = (
        base64.urlsafe_b64encode(val).decode("ascii")
        if urlsafe
        else base64.b64encode(val).decode("ascii")
    )
    return b64 if pad else unpad(b64)


def str_to_b64(val: str, urlsafe=False, encoding=None, pad=True) -> str:
    """Convert a string to base64 string on input encoding (default utf-8)."""
    return bytes_to_b64(val.encode(encoding or "utf-8"), urlsafe, pad)


def set_urlsafe_b64(val: str, urlsafe: bool = True) -> str:
    """Set URL safety in base64 encoding."""
    if urlsafe:
        return val.replace("+", "-").replace("/", "_")
    return val.replace("-", "+").replace("_", "/")


def b58_to_bytes(val: str) -> bytes:
    """Convert a base 58 string to bytes."""
    return base58.b58decode(val)


def bytes_to_b58(val: bytes) -> str:
    """Convert a byte string to base 58."""
    return base58.b58encode(val).decode("ascii")
