from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

import yaml
import os

from aries_community.utils import *
from aries_community.models import *
from aries_community.agent_utils import *
from aries_community.registration_utils import *


USER_ROLE = getattr(settings, "DEFAULT_USER_ROLE", 'User')
ORG_ROLE = getattr(settings, "DEFAULT_ORG_ROLE", 'Admin')

def get_attr_value(key):
    if isinstance(key, dict):
        object_type = None
        object_attrs = {}
        for attr_attr in key:
            if attr_attr == 'class':
                object_type = key['class']
            else:
                object_attrs[attr_attr] = key[attr_attr]
        return get_aries_model(object_type).objects.filter(**object_attrs).get()
    else:
        return key

class Command(BaseCommand):
    help = 'Loads Organizations and optionally creates Credential Definitions'

    def add_arguments(self, parser):
        parser.add_argument('config_file', nargs='+')

    def handle(self, *args, **options):
        schemas = None
        org = None

        # verify that config file exists and we can load yaml
        self.stdout.write("config_file = %s" % str(options['config_file']))
        with open(str(options['config_file'][0]), 'r') as stream:
            try:
                orgs = yaml.load(stream)
            except yaml.YAMLError as exc:
                self.stdout.write(exc)
                raise

            # validate data in yaml file
            for name in orgs:
                org = orgs[name]
                # TODO validation

        # now create orgs (and potentially create cred defs)
        if orgs:
            for name in orgs:
                org = orgs[name]
                first_name = org['first_name']
                last_name = org['last_name']
                email = org['email']
                password = org['password']
                role_name = org['role']
                ico_url = org['ico_url'] if 'ico_url' in org else None
                managed_agent = org['managed_agent'] if 'managed_agent' in org else True
                admin_port = org['admin_port'] if 'admin_port' in org else None
                admin_endpoint = org['admin_endpoint'] if 'admin_endpoint' in org else None
                http_port = org['http_port'] if 'http_port' in org else None
                http_endpoint = org['http_endpoint'] if 'http_endpoint' in org else None
                api_key = org['api_key'] if 'api_key' in org else None
                webhook_key = org['webhook_key'] if 'webhook_key' in org else None

                if "$random" in name:
                    name = name.replace("$random", random_alpha_string(12))
                if "$random" in email:
                    email = email.replace("$random", random_alpha_string(12))

                user_attrs = {}
                if 'user' in org:
                    for attr in org['user']:
                        user_attrs[attr] = get_attr_value(org['user'][attr])
                user = get_user_model().objects.create_user(first_name=first_name, last_name=last_name, email=email, password=password, **user_attrs)
                user.groups.add(Group.objects.get(name=ORG_ROLE))
                user.save()

                org_attrs = {}
                if 'org' in org:
                    for attr in org['org']:
                        org_attrs[attr] = get_attr_value(org['org'][attr])
                relation_attrs = {}
                if 'relation' in org:
                    for attr in org['relation']:
                        relation_attrs[attr] = get_attr_value(org['relation'][attr])
                org_role, created = AriesOrgRole.objects.get_or_create(name=role_name)
                org = org_signup(
                    user, password, name, 
                    org_attrs=org_attrs, org_relation_attrs=relation_attrs, org_role=org_role, org_ico_url=ico_url,
                    managed_agent=managed_agent, admin_port=admin_port, admin_endpoint=admin_endpoint,
                    http_port=http_port, http_endpoint=http_endpoint, api_key=api_key, webhook_key=webhook_key
                )

