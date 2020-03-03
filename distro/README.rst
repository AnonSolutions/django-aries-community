===============
Aries Community
===============

Aries Community is a simple Django framework for building
Hyperledger Indy/Aries Agent enabled web applications.
Detailed documentation is in the "docs" directory.

Please see https://github.com/AnonSolutions/django-aries-community for detailed docmentation


Quick start
-----------

You can find a basic Aries Community application here https://github.com/AnonSolutions/aries-community-demo

To add aries_community to your own django application:

1. Copy the requirements.txt file into your application directory and install requirements

2. Add "aries_community" to your INSTALLED_APPS setting like this:

.. code-block:: python

        INSTALLED_APPS = [
            ...
            'aries_community',
        ]

3. Add the following Indy configuration settings (this is for a local install):

.. code-block:: python

        import platform

        def file_ext():
            if platform.system() == 'Linux':
                return '.so'
            elif platform.system() == 'Darwin':
                return '.dylib'
            elif platform.system() == 'Windows':
                return '.dll'
            else:
                return '.so'

        ARIES_CONFIG = {
            'storage_config': {'url': 'localhost:5432'},
            'storage_credentials': {'account': 'postgres', 'password': 'mysecretpassword', 'admin_account': 'postgres', 'admin_password': 'mysecretpassword'},
            'register_dids': True,
            'ledger_url': 'http://localhost:9000',
            'genesis_url': 'http://localhost:9000/genesis',
            'default_enterprise_seed': 'aries_community_enterprise_00000',
            'default_institution_seed': 'aries_community_institution_0000',
            'managed_agent_host': 'localhost',
            'webhook_host': 'localhost',
            'webhook_port': '8000',
        }

4. Ensure your local templates are loaded first:

.. code-block:: python

        TEMPLATES = [
            {
                ...
                'DIRS': [
                    os.path.join(BASE_DIR, '<your app>/templates'),
                ],
                ...
            },
        ]

5. Override User, Organization and Relationship models, if you have your own subclass of these models:

.. code-block:: python

        AUTH_USER_MODEL = 'aries_community.IndyUser'
        ARIES_ORGANIZATION_MODEL = 'aries_community.IndyOrganization'
        ARIES_ORG_RELATION_MODEL = 'aries_community.IndyOrgRelationship'

6. Include the indy URLconf in your project urls.py like this:

.. code-block:: python

        path('aries/', include('aries_community.urls')),

7. Ensure you have all pre-requisites running, as per django-aries-community docs

8. Run `python manage.py migrate` to create the indy models.

10. Run `python manage.py runserver` and connect to http://localhost:8000/

You can customize the UI and add event handling for Aries Connection and Messaging events.  See the demos in
https://github.com/AnonSolutions/aries-community-demo for examples of how to do this.

View detailed documentation in the Docs directory (https://github.com/AnonSolutions/django-aries-community)

