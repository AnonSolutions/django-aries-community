from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.views.generic.edit import UpdateView

from ..models import *


User = get_user_model()
TEST_USER_EMAIL = 'test@example.com'
TEST_USER_FIRST_NAME = 'Test'
TEST_USER_LAST_NAME = 'User'


class AriesAgentTests(TestCase):
    """
    Tests for Aries agent model class
    """

    def test_agent_create(self):
        # create an agent
        my_agent = AriesAgent.objects.create(
            agent_name='test_agent',
            agent_config='{"some":"test", "string":"."}',
        )
        my_agent.save()

        fetch_agent = AriesAgent.objects.filter(agent_name='test_agent').all()
        self.assertEqual(len(fetch_agent), 1)
        self.assertEqual(fetch_agent[0].agent_name, 'test_agent')


class AriesUserTests(TestCase):
    """
    Tests for Aries custom User class.
    """

    def setUp(self):
        # Creates a single-user test database.
        self.user = User.objects.create(
            email=TEST_USER_EMAIL,
            first_name=TEST_USER_FIRST_NAME,
            last_name=TEST_USER_LAST_NAME,
        )

    def test_user_exists(self):
        # Tests user in setUp() does exists
        my_user = User.objects.filter(email=TEST_USER_EMAIL).all()[0]
        self.assertEqual(my_user.first_name, TEST_USER_FIRST_NAME)

    def test_user_with_agent(self):
        # test we can create a user with an agent
        my_agent = AriesAgent.objects.create(
            agent_name='test_agent',
            agent_config='{"some":"test", "string":"."}',
        )
        my_agent.save()
        my_user = User.objects.filter(email=TEST_USER_EMAIL).all()[0]
        my_user.agent = my_agent
        my_user.save()

        fetch_user = User.objects.filter(email=TEST_USER_EMAIL).all()[0]
        self.assertEqual(my_user.agent.agent_name, my_agent.agent_name)


class AriesOrganizationTests(TestCase):
    """
    Tests for Aries organization class 
    """

    def test_organization_create(self):
        # tests creating an organization with an agent 
        my_agent = AriesAgent.objects.create(
            agent_name='test_agent',
            agent_config='{"some":"test", "string":"."}',
        )
        my_agent.save()
        my_org = AriesOrganization.objects.create(
            org_name='My Org',
            agent=my_agent,
        )
        my_org.save()

        fetch_org = AriesOrganization.objects.filter(org_name='My Org').all()
        self.assertEqual(len(fetch_org), 1)
        self.assertEqual(fetch_org[0].agent.agent_name, 'test_agent')


class AriesOrgRelationshipTests(TestCase):
    """
    Tests for Aries organization/user relationship class 
    """

    def test_relationship_create(self):
        # tests creating a relationship between a user and organization
        user_agent = AriesAgent.objects.create(
            agent_name='user_agent',
            api_key='my_test_000',
            callback_key='my_callback_000',
            agent_config='{"some":"test", "string":"."}',
        )
        user_agent.save()
        my_user = User.objects.create(
            email='user@org.com',
            first_name='org',
            last_name='user',
            agent=user_agent,
        )
        org_agent = AriesAgent.objects.create(
            agent_name='org_agent',
            api_key='my_test_001',
            callback_key='my_callback_111',
            agent_config='{"some":"test", "string":"."}',
        )
        org_agent.save()
        my_org = AriesOrganization.objects.create(
            org_name='My Org',
            agent=org_agent,
        )
        my_org.save()
        my_relationship = AriesOrgRelationship.objects.create(
            org=my_org,
            user=my_user,
        )

        fetch_user = User.objects.filter(email='user@org.com').all()[0]
        self.assertEqual(len(fetch_user.ariesrelationship_set.all()), 1)
        user_org = fetch_user.ariesrelationship_set.all()[0].org
        self.assertEqual(user_org.org_name, 'My Org')

        fetch_org = AriesOrganization.objects.filter(org_name='My Org').all()[0]
        self.assertEqual(len(fetch_org.ariesrelationship_set.all()), 1)
        org_user = fetch_org.ariesrelationship_set.all()[0].user
        self.assertEqual(org_user.email, 'user@org.com')


class IndySchemaTests(TestCase):
    """
    Tests for IndySchema class
    """
    def test_schema_create(self):
        schema = IndySchema.objects.create(
            ledger_schema_id='123',
            schema_name='My Schema',
            schema_version='1.1.1',
            schema='this is the schema data',
            schema_template='template for adding credentials',
            schema_data='data written to the ledger',
        )
        schema.save()

        fetch_schema = IndySchema.objects.filter(ledger_schema_id='123').all()
        self.assertEqual(len(fetch_schema), 1)
        self.assertEqual(fetch_schema[0].schema_name, 'My Schema')


class IndyCredentialDefinitionTests(TestCase):
    """
    Tests for IndyCredentialDefinition class
    """
    def test_credentialdefinition_create(self):
        agent = AriesAgent.objects.create(
            agent_name='test_agent',
            agent_config='{"some":"test", "string":"."}',
        )
        agent.save()
        schema = IndySchema.objects.create(
            ledger_schema_id='123',
            schema_name='My Schema',
            schema_version='1.1.1',
            schema='this is the schema data',
            schema_template='template for adding credentials',
            schema_data='data written to the ledger',
        )
        schema.save()
        cred_def = IndyCredentialDefinition.objects.create(
            ledger_creddef_id='456',
            ledger_schema=schema,
            agent=agent,
            creddef_name='my cred def',
            creddef_handle='4',
            creddef_template='a template for adding credentials',
            creddef_data='data written to the ledger',
        )
        cred_def.save()

        fetch_cred_def = IndyCredentialDefinition.objects.filter(ledger_creddef_id='456').all()
        self.assertEqual(len(fetch_cred_def), 1)
        self.assertEqual(fetch_cred_def[0].ledger_schema.schema_name, 'My Schema')
        self.assertEqual(fetch_cred_def[0].creddef_name, 'my cred def')


class IndyProofRequestTests(TestCase):
    """
    Tests for IndyProofRequest class
    """
    def test_proofrequest_create(self):
        proof_request = IndyProofRequest.objects.create(
            proof_req_name='test name',
            proof_req_description='a description',
            proof_req_attrs='revealed attributes',
            proof_req_predicates='zkp attributes',
        )
        proof_request.save()

        fetch_proof_request = IndyProofRequest.objects.filter(proof_req_name='test name').all()
        self.assertEqual(len(fetch_proof_request), 1)
        self.assertEqual(fetch_proof_request[0].proof_req_name, 'test name')


class AgentConnectionTests(TestCase):
    """
    Tests for Aries AgentConnection class
    """
    def test_connection_create(self):
        agent = AriesAgent.objects.create(
            agent_name='test_agent',
            api_key='my_test_002',
            callback_key='my_callback_222',
            agent_config='{"some":"test", "string":"."}',
        )
        agent.save()
        connection = AgentConnection.objects.create(
            guid='111',
            agent=agent,
            partner_name='partner',
            invitation='invitation to connect',
        )
        connection.save()

        fetch_connection = AgentConnection.objects.filter(agent=agent, partner_name='partner').all()
        self.assertEqual(len(fetch_connection), 1)
        self.assertEqual(fetch_connection[0].partner_name, 'partner')


class AgentConversationTests(TestCase):
    """
    Tests for AgentConversation class
    """
    def test_conversation_create(self):
        agent = AriesAgent.objects.create(
            agent_name='test_agent',
            api_key='my_test_003',
            callback_key='my_callback_333',
            agent_config='{"some":"test", "string":"."}',
        )
        agent.save()
        connection = AgentConnection.objects.create(
            guid='111',
            agent=agent,
            partner_name='partner',
            invitation='invitation to connect',
        )
        connection.save()
        conversation = AgentConversation.objects.create(
            guid='123',
            connection=connection,
            conversation_type='proof or credential',
        )
        conversation.save()

        fetch_conversation = AgentConversation.objects.filter(connection__agent=agent, connection=connection, guid='123').all()
        self.assertEqual(len(fetch_conversation), 1)

