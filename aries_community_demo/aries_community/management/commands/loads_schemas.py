from django.core.management.base import BaseCommand
from django.utils import timezone
import yaml
import os

from aries_community.models import *
from aries_community.agent_utils import *


class Command(BaseCommand):
    help = 'Loads Schemas and optionally creates Credential Definitions'

    def add_arguments(self, parser):
        parser.add_argument('config_file', nargs='+')
        parser.add_argument('org_id', nargs='+', type=int)

        # Named (optional) arguments
        parser.add_argument(
            '--cred_defs',
            action='store_true',
            dest='cred_defs',
            help='Create Credential Definitions for the selected organization, for all Schemas',
        )

    def handle(self, *args, **options):
        schemas = None
        org = None

        # verify that config file exists and we can load yaml
        self.stdout.write("config_file = %s" % str(options['config_file']))
        with open(str(options['config_file'][0]), 'r') as stream:
            try:
                schemas = yaml.load(stream)
            except yaml.YAMLError as exc:
                self.stdout.write(exc)
                raise

            # validate data in yaml file
            for name in schemas:
                spec = schemas[name]
                # TODO validation

        # verify org exists
        self.stdout.write("issue schemas for org_id = %s" % str(options['org_id'][0]))
        orgs = AriesOrganization.objects.filter(id=options['org_id'][0]).all()
        if 0 == len(orgs):
            self.stdout.write("no organization found for org_id = %s" % str(options['org_id']))
            raise Exception("no organization found for org_id = %s" % str(options['org_id']))

        org = orgs[0]

        try:
            # startup the agent for that org
            start_agent(org.agent)

            # now create schemas (and potentially create cred defs)
            if schemas and org:
                for name in schemas:
                    spec = schemas[name]

                    if spec['type'] == 'schema':
                        if spec['version'] == '$generate':
                            version = random_schema_version()
                        else:
                            version = spec['version']
                        attributes = spec['attributes']
                        # TODO save roles (to auto-create cred defs for the schema(s))
                        (schema_json, creddef_template) = create_schema_json(name, version, attributes)
                        schema = create_schema(org.agent, name, version, attributes, creddef_template)
                        self.stdout.write("Created schema for %s" % name)

                        # add role(s) to this schema
                        if 'issuing_roles' in spec:
                            for role_name in spec['issuing_roles']:
                                role, created = AriesOrgRole.objects.get_or_create(name=role_name)
                                schema.roles.add(role)
                            schema.save()

                        # add cred def?
                        if options['cred_defs']:
                            creddef = create_creddef(org.agent, schema, schema.schema_name + '-' + org.wallet.wallet_name, schema.schema_template)
                            self.stdout.write("Created cred def for schema %s" % name)
                    elif spec['type'] == 'proof_request':
                        description = spec['description']
                        if 'revealed_attributes' in spec:
                            revealed_attributes = spec['revealed_attributes']
                        else:
                            revealed_attributes = []
                        if 'predicates' in spec:
                            predicates = spec['predicates']
                        else:
                            predicates = []
                        create_proof_request(name, description, revealed_attributes, predicates)
                        self.stdout.write("Created proof request for %s" % name)

        finally:
            # shut down the agent for that org
            stop_agent(org.agent)
