from django.apps import apps as django_apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

import asyncio
import random
import string


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
