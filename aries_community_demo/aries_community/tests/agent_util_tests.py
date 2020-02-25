from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase, LiveServerTestCase
from django.urls import reverse
from django.views.generic.edit import UpdateView

from django.conf import settings

from time import sleep

from ..models import *
from ..utils import *
from ..wallet_utils import *
from ..registration_utils import *
from ..agent_utils import *


# Use LiveServerTestCase to force the Agent Callback API to run, so we can get callbacks from
# the test agents during the test scenarios
class AgentInteractionTests(LiveServerTestCase):
    # override port for the LiveServer (default is 8081)
    port = 8000

    ##############################################################
    # agent process control tests
    ##############################################################
    def test_provision_and_start_agent_1(self):
        config1 = aries_provision_config(
                "test_agent_1", 
                "test_api_key_1",
                "test_conn_key_1",
                "secret_password",
                10000,
                10010,
                "localhost:10000",
                "localhost:10010",
                start_agent=True
            )
        proc1_info = start_aca_py("test_agent_1", config1, "http://localhost:10010", "test_api_key_1")

        config2 = aries_provision_config(
                "test_agent_2", 
                "test_api_key_2",
                "test_conn_key_2",
                "secret_password",
                10020,
                10030,
                "localhost:10020",
                "localhost:10030",
                start_agent=True
            )
        proc2_info = start_aca_py("test_agent_2", config2, "http://localhost:10030", "test_api_key_2")

        stop_aca_py(proc1_info["name"])
        stop_aca_py(proc2_info["name"])

        print("Done!!!")

    def test_provision_and_start_agent_2(self):
        config1 = aries_provision_config(
                "test_agent_3", 
                "test_api_key_3",
                "test_conn_key_3",
                "secret_password",
                10040,
                10050,
                "localhost:10040",
                "localhost:10050",
                start_agent=True
            )
        proc1_info = start_aca_py("test_agent_1", config1, "http://localhost:10050", "test_api_key_3")

        config2 = aries_provision_config(
                "test_agent_4", 
                "test_api_key_4",
                "test_conn_key_4",
                "secret_password",
                10060,
                10070,
                "localhost:10060",
                "localhost:10070",
                start_agent=True
            )
        proc2_info = start_aca_py("test_agent_2", config2, "http://localhost:10070", "test_api_key_4")

        stop_all_aca_py()

        print("Done!!!")


    def test_provision_and_start_agent_3(self):
        agent1 = initialize_and_provision_agent(
                "test_agent_5", 
                "secret_password",
                did_seed="test_agent_5_did_000000000000000",
                start_agent_proc=True
            )

        agent2 = initialize_and_provision_agent(
                "test_agent_6", 
                "secret_password",
                did_seed="test_agent_6_did_000000000000000",
                start_agent_proc=True
            )

        stop_agent(agent1)
        stop_agent(agent2)

        print("Done!!!")


    ##############################################################
    # user and org provisioning tests
    ##############################################################
    def create_user_and_org(self):
        # create, register and provision a user and org
        # create, register and provision a user
        email = random_alpha_string(10) + "@agent_utils.com"
        user = get_user_model().objects.create(
            email=email,
            first_name='Test',
            last_name='Registration',
        )
        user.save()
        raw_password = random_alpha_string(8)
        user_provision(user, raw_password)

        # now org
        org_name = 'Agent Utils ' + random_alpha_string(10)
        org = org_signup(user, raw_password, org_name)

        return (user, org, raw_password)

    def establish_agent_connection(self, org, user, init_org_agent=False, init_user_agent=False):
        # send connection request (org -> user)
        org_connection_1 = request_connection_invitation(org, user.email, initialize_agent=init_org_agent)
        sleep(1)

        # accept connection request (user -> org)
        user_connection_1 = receive_connection_invitation(user.agent, org.org_name, org_connection_1.invitation, initialize_agent=init_user_agent)
        sleep(1)

        # update connection status (org)
        org_connection_state = check_connection_status(org.agent, org_connection_1.guid, initialize_agent=init_org_agent)
        user_connection_state = check_connection_status(user.agent, user_connection_1.guid, initialize_agent=init_user_agent)

        return (org_connection_state, user_connection_state)

    def delete_user_and_org_agents(self, user, org, raw_password):
        # cleanup after ourselves
        # TODO
        #org_wallet_name = org.wallet.wallet_name
        #res = delete_wallet(org_wallet_name, raw_password)
        #self.assertEqual(res, 0)
        #user_wallet_name = user.wallet.wallet_name
        #res = delete_wallet(user_wallet_name, raw_password)
        #self.assertEqual(res, 0)
        pass

    def schema_and_cred_def_for_org(self, org):
        # create a "dummy" schema/cred-def that is unique to this org (matches the Alice/Faber demo schema)
        agent = org.agent
        agent_name = org.agent.agent_name

        schema_name = 'schema_' + agent_name
        schema_version = random_schema_version()
        schema_attrs = [
            'name', 'date', 'degree', 'age',
            ]
        (schema_json, creddef_template) = create_schema_json(schema_name, schema_version, schema_attrs)
        schema = create_schema(agent, schema_name, schema_version, schema_attrs, creddef_template)
        cred_def = create_creddef(agent, schema, 'creddef_' + agent_name, creddef_template)

         # Proof of Age
        proof_request = create_proof_request('Proof of Age Test', 'Proof of Age Test',
            [{'name':'name', 'restrictions':[{'issuer_did': '$ISSUER_DID'}]},
             {'name':'comments'}],
            [{'name': 'age','p_type': '>=','p_value': '$VALUE', 'restrictions':[{'issuer_did': '$ISSUER_DID'}]}]
            )

        return (schema, cred_def, proof_request)


    def issue_credential_from_org_to_user(self, org, user, org_connection, user_connection, cred_def, schema_attrs, cred_name, cred_tag):
        # issue a credential based on the default schema/credential definition
        org_conversation_1 = send_credential_offer(org.wallet, org_connection,  
                                            cred_tag, schema_attrs, cred_def, 
                                            cred_name)
        sleep(2)

        i = 0
        while True:
            handled_count = handle_inbound_messages(user.wallet, user_connection)
            i = i + 1
            if handled_count > 0 or i > 3:
                break
            sleep(2)
        user_conversations = AgentConversation.objects.filter(connection__wallet=user.wallet, conversation_type="CredentialOffer", status='Pending').all()
        user_conversation_1 = user_conversations[0]

        # send credential request (user -> org)
        user_conversation_2 = send_credential_request(user.wallet, user_connection, user_conversation_1)
        sleep(2)

        # send credential (org -> user)
        i = 0
        message = org_conversation_1
        while True:
            message = poll_message_conversation(org.wallet, org_connection, message, initialize_vcx=True)
            i = i + 1
            if message.conversation_type == 'IssueCredential' or i > 3:
                break
            sleep(2)
        org_conversation_2 = message
        sleep(2)

        # accept credential and update status (user)
        i = 0
        message = user_conversation_2
        while True:
            message = poll_message_conversation(user.wallet, user_connection, message, initialize_vcx=True)
            i = i + 1
            if message.status == 'Accepted' or i > 3:
                break
            sleep(2)
        user_conversation_3 = message
        sleep(2)

        # update credential offer status (org)
        i = 0
        message = org_conversation_2
        while True:
            message = poll_message_conversation(org.wallet, org_connection, message, initialize_vcx=True)
            i = i + 1
            if message.status == 'Accepted' or i > 3:
                break
            sleep(2)
        org_conversation_3 = message


    def test_register_org_with_schema_and_cred_def(self):
        # try creating a schema and credential definition under the organization
        (user, org, raw_password) = self.create_user_and_org()

        try:
            # startup the agent for that org
            start_agent(org.agent)

            (schema, cred_def, proof_request) = self.schema_and_cred_def_for_org(org)

            # fetch some stuff and validate some other stuff
            fetch_org = AriesOrganization.objects.filter(org_name=org.org_name).all()[0]
            self.assertEqual(len(fetch_org.agent.indycreddef_set.all()), 1)
            fetch_creddef = fetch_org.agent.indycreddef_set.all()[0]
            self.assertEqual(fetch_creddef.creddef_name, cred_def.creddef_name)

        finally:
            # shut down the agent for that org
            stop_agent(org.agent)

        # clean up after ourself
        self.delete_user_and_org_agents(user, org, raw_password)


    def test_agent_connection(self):
        # establish a connection between two agents
        (user, org, raw_password) = self.create_user_and_org()

        try:
            # startup the agent for that org
            start_agent(org.agent)
            start_agent(user.agent)

            (schema, cred_def, proof_request) = self.schema_and_cred_def_for_org(org)

            (org_connection_state, user_connection_state) = self.establish_agent_connection(org, user)

            self.assertEqual(org_connection_state, 'active')
            self.assertEqual(user_connection_state, 'active')
        finally:
            # shut down the agent for that org
            stop_agent(user.agent)
            stop_agent(org.agent)

        # clean up after ourself
        self.delete_user_and_org_agents(user, org, raw_password)

