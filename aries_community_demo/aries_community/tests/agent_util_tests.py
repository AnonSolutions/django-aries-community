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

    def api_key_ADMIN_REQUEST_HEADERS(self, api_key):
        ADMIN_REQUEST_HEADERS = {}
        # set admin header per agent
        if api_key is not None:
           ADMIN_REQUEST_HEADERS = {"x-api-key": api_key}
        return ADMIN_REQUEST_HEADERS


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
        proc1_info = start_aca_py("test_agent_1", config1, "http://localhost:10010", self.api_key_ADMIN_REQUEST_HEADERS("test_api_key_1"))

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
        proc2_info = start_aca_py("test_agent_2", config2, "http://localhost:10030", self.api_key_ADMIN_REQUEST_HEADERS("test_api_key_2"))

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
        proc1_info = start_aca_py("test_agent_1", config1, "http://localhost:10050", self.api_key_ADMIN_REQUEST_HEADERS("test_api_key_3"))

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
        proc2_info = start_aca_py("test_agent_2", config2, "http://localhost:10070", self.api_key_ADMIN_REQUEST_HEADERS("test_api_key_4"))

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

        return (org_connection_1, org_connection_state, user_connection_1, user_connection_state)

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


    def issue_credential_from_org_to_user(self, org, user, org_connection, user_connection, cred_def_id, schema_attrs):
        # issue a credential based on the default schema/credential definition
        org_conversation_1 = send_credential_offer(org.agent, org_connection, schema_attrs, cred_def_id, initialize_agent=True)
        sleep(2)

        i = 0
        while True:
            # we should receive a conversation to handle
            user_in_cred_exches = AgentConversation.objects.filter(connection__agent=user.agent, 
                conversation_type=CRED_EXCH_CONVERSATION, status="offer_received").all()
            count = len(user_in_cred_exches)
            i = i + 1
            if count > 0 or i > 3:
                break
            sleep(2)
        user_conversation_1 = user_in_cred_exches[0]

        # send credential request (user -> org)
        user_conversation_2 = send_credential_request(user.agent, user_conversation_1, initialize_agent=True)
        sleep(2)

        # send credential (org -> user)
        i = 0
        while True:
            status = check_conversation_status(org.agent, org_conversation_1.guid, CRED_EXCH_CONVERSATION, initialize_agent=True)
            i = i + 1
            if status == 'credential_acked' or i > 3:
                break
            sleep(2)

        # accept credential and update status (user)
        i = 0
        while True:
            status = check_conversation_status(user.agent, user_conversation_2.guid, CRED_EXCH_CONVERSATION, initialize_agent=True)
            i = i + 1
            if status == 'credential_acked' or i > 3:
                break
            sleep(2)


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

            (org_connection, org_connection_state, user_connection, user_connection_state) = self.establish_agent_connection(org, user)

            self.assertEqual(org_connection_state, 'active')
            self.assertEqual(user_connection_state, 'active')
        finally:
            # shut down the agent for that org
            stop_agent(user.agent)
            stop_agent(org.agent)

        # clean up after ourself
        self.delete_user_and_org_agents(user, org, raw_password)


    def test_agent_credential_exchange_raw(self):
        # exchange credentials between two agents
        (user, org, raw_password) = self.create_user_and_org()

        try:
            # startup the agent for that org
            start_agent(org.agent)
            start_agent(user.agent)

            (schema, cred_def, proof_request) = self.schema_and_cred_def_for_org(org)

            # establish a connection
            (org_connection, org_connection_state, user_connection, user_connection_state) = self.establish_agent_connection(org, user)

            # check that user has no offers or credentials
            user_conversations = AgentConversation.objects.filter(connection=user_connection, conversation_type=CRED_EXCH_CONVERSATION, status='offer_received').all()
            self.assertEqual(len(user_conversations), 0)
            user_credentials = fetch_credentials(user.agent)
            self.assertEqual(len(user_credentials), 0)

            # issue credential offer (org -> user)
            schema_attrs = json.loads(cred_def.creddef_template)
            # data normally provided by the org data pipeline
            schema_attrs['name'] = 'Joe Smith'
            schema_attrs['date'] = '2018-01-01'
            schema_attrs['degree'] = 'B.A.Sc. Honours'
            schema_attrs['age'] = '25'
            attr_values = [
                {"name": "name", "value": "Joe Smith"},
                {"name": "date", "value": "2018-01-01"},
                {"name": "degree", "value": "B.A.Sc. Honours"},
                {"name": "age", "value": "25"},
            ]
            org_conversation_1 = send_credential_offer(org.agent, org_connection, attr_values, cred_def.ledger_creddef_id)
            sleep(2)

            i = 0
            while True:
                # once the user receives the cred offer, request the credential
                user_conversations = AgentConversation.objects.filter(connection=user_connection, conversation_type=CRED_EXCH_CONVERSATION, status='offer_received').all()
                i = i + 1
                if len(user_conversations) > 0 or i > 3:
                    break
                sleep(2)
            self.assertEqual(len(user_conversations), 1)
            user_conversation_1 = user_conversations[0]

            # send credential request (user -> org)
            user_conversation_2 = send_credential_request(user.agent, user_conversation_1)
            sleep(2)

            # wait for credential (org -> user)
            i = 0
            while True:
                user_conversations = AgentConversation.objects.filter(connection=user_connection, conversation_type=CRED_EXCH_CONVERSATION, status='credential_acked').all()
                i = i + 1
                if len(user_conversations) > 0 or i > 3:
                    break
                sleep(2)
            self.assertEqual(len(user_conversations), 1)
            sleep(2)

            # get updated credential status (org)
            i = 0
            while True:
                org_conversations = AgentConversation.objects.filter(connection=org_connection, conversation_type=CRED_EXCH_CONVERSATION, status='credential_acked').all()
                i = i + 1
                if len(org_conversations) > 0 or i > 3:
                    break
                sleep(2)
            self.assertEqual(len(org_conversations), 1)

            # verify credential is in user wallet
            user_credentials = fetch_credentials(user.agent)
            self.assertEqual(len(user_credentials), 1)

        finally:
            # shut down the agent for that org
            stop_agent(user.agent)
            stop_agent(org.agent)

        # clean up after ourself
        self.delete_user_and_org_agents(user, org, raw_password)


    def test_agent_credential_exchange(self):
        # request and deliver a proof between two agents
        (user, org, raw_password) = self.create_user_and_org()

        try:
            # startup the agent for that org
            start_agent(org.agent)
            start_agent(user.agent)

            (schema, cred_def, proof_request) = self.schema_and_cred_def_for_org(org)

            # establish a connection
            (org_connection, org_connection_state, user_connection, user_connection_state) = self.establish_agent_connection(org, user)

            # make up a credential
            schema_attrs = json.loads(cred_def.creddef_template)
            schema_attrs['name'] = 'Joe Smith'
            schema_attrs['date'] = '2018-01-01'
            schema_attrs['degree'] = 'B.A.Sc. Honours'
            schema_attrs['age'] = '25'
            cred_name = 'Cred4Proof Credential Name'
            attr_values = [
                {"name": "name", "value": "Joe Smith"},
                {"name": "date", "value": "2018-01-01"},
                {"name": "degree", "value": "B.A.Sc. Honours"},
                {"name": "age", "value": "25"},
            ]

            # issue credential (org -> user)
            self.issue_credential_from_org_to_user(org, user, org_connection, user_connection, cred_def.ledger_creddef_id, attr_values)

            # verify credential is in user wallet
            user_credentials = fetch_credentials(user.agent)
            self.assertEqual(len(user_credentials), 1)

        finally:
            # shut down the agent for that org
            stop_agent(user.agent)
            stop_agent(org.agent)

        # clean up after ourself
        self.delete_user_and_org_agents(user, org, raw_password)


    def test_agent_proof_exchange(self):
        # request and deliver a proof between two agents
        (user, org, raw_password) = self.create_user_and_org()

        try:
            # startup the agent for that org
            start_agent(org.agent)
            start_agent(user.agent)

            (schema, cred_def, proof_request) = self.schema_and_cred_def_for_org(org)

            # establish a connection
            (org_connection, org_connection_state, user_connection, user_connection_state) = self.establish_agent_connection(org, user)

            # make up a credential
            schema_attrs = json.loads(cred_def.creddef_template)
            schema_attrs['name'] = 'Joe Smith'
            schema_attrs['date'] = '2018-01-01'
            schema_attrs['degree'] = 'B.A.Sc. Honours'
            schema_attrs['age'] = '25'
            cred_name = 'Cred4Proof Credential Name'
            attr_values = [
                {"name": "name", "value": "Joe Smith"},
                {"name": "date", "value": "2018-01-01"},
                {"name": "degree", "value": "B.A.Sc. Honours"},
                {"name": "age", "value": "25"},
            ]

            # issue credential (org -> user)
            self.issue_credential_from_org_to_user(org, user, org_connection, user_connection, cred_def.ledger_creddef_id, attr_values)

            # verify credential is in user wallet
            user_credentials = fetch_credentials(user.agent)
            self.assertEqual(len(user_credentials), 1)

            # construct the proof request to send to the user (to whom we have just issued a credential)
            proof_req_attrs = proof_request.proof_req_attrs
            proof_req_predicates = proof_request.proof_req_predicates

            issuer_did = get_public_did(org.agent)
            proof_req_attrs = proof_req_attrs.replace('$ISSUER_DID', issuer_did)
            proof_req_predicates = proof_req_predicates.replace('$ISSUER_DID', issuer_did)
            proof_req_predicates = proof_req_predicates.replace('"$VALUE"', '21')
            proof_req_attrs = json.loads(proof_req_attrs)
            proof_req_predicates = json.loads(proof_req_predicates)
            proof_name = "My Cool Proof"
            proof_uuid = "Some Uuid Value"

            requested_attrs = {}
            for requested_attr in proof_req_attrs:
                referent = requested_attr["name"] + "_referent"
                requested_attrs[referent] = requested_attr
            requested_predicates = {}
            for requested_predicate in proof_req_predicates:
                referent = requested_predicate["name"] + "_referent"
                requested_predicates[referent] = requested_predicate

            # issue proof request (org -> user)
            org_conversation_1 = send_proof_request(org.agent, org_connection, proof_name, requested_attrs, requested_predicates)
            sleep(2)

            # poll to receive proof request
            i = 0
            while True:
                # once the user receives the request, build the proof
                user_conversations = AgentConversation.objects.filter(connection=user_connection, conversation_type=PROOF_REQ_CONVERSATION, status='request_received').all()
                i = i + 1
                if len(user_conversations) > 0 or i > 3:
                    break
                sleep(2)
            self.assertEqual(len(user_conversations), 1)
            user_conversation_1 = user_conversations[0]

            # select credential(s) for proof (user)
            claims_data = get_claims_for_proof_request(user.agent, user_conversation_1)
            self.assertEqual(len(claims_data), 1)
            requested_proof = get_agent_conversation(user.agent, user_conversation_1.guid, PROOF_REQ_CONVERSATION)

            supplied_attrs = {}
            supplied_predicates = {}
            supplied_self_attested_attrs = {}
            # build array of credential id's (from wallet)
            for claim_data in claims_data:
                for referent in claim_data['presentation_referents']:
                    if referent in requested_proof["presentation_request"]["requested_attributes"] and referent not in supplied_attrs:
                        supplied_attrs[referent] = { "cred_id": claim_data["cred_info"]["referent"], "revealed": True }
                    if referent in requested_proof["presentation_request"]["requested_predicates"] and referent not in supplied_predicates:
                        supplied_predicates[referent] = { "cred_id": claim_data["cred_info"]["referent"] }
            for referent in requested_proof["presentation_request"]["requested_attributes"]:
                if referent not in supplied_attrs:
                    supplied_self_attested_attrs[referent] = "User supplied value"

            # construct proof and send (user -> org)
            user_conversation_2 = send_claims_for_proof_request(user.agent, user_conversation_1, supplied_attrs, supplied_predicates, supplied_self_attested_attrs)

            # accept and validate proof (org)
            i = 0
            while True:
                org_conversations = AgentConversation.objects.filter(connection=org_connection, conversation_type=PROOF_REQ_CONVERSATION, status='verified').all()
                i = i + 1
                if len(org_conversations) > 0 or i > 3:
                    break
                sleep(2)
            self.assertEqual(len(org_conversations), 1)
            org_conversation_2 = org_conversations[0]

            # TODO verify some stuff ...
        finally:
            # shut down the agent for that org
            stop_agent(user.agent)
            stop_agent(org.agent)

        # clean up after ourself
        self.delete_user_and_org_agents(user, org, raw_password)


    def test_agent_proof_exchange_2_creds(self):
        # request and deliver a proof between two agents
        (user, org, raw_password) = self.create_user_and_org()

        try:
            # startup the agent for that org
            start_agent(org.agent)
            start_agent(user.agent)

            (schema, cred_def, proof_request) = self.schema_and_cred_def_for_org(org)

            # establish a connection
            (org_connection, org_connection_state, user_connection, user_connection_state) = self.establish_agent_connection(org, user)

            # make up a credential
            schema_attrs = json.loads(cred_def.creddef_template)
            schema_attrs['name'] = 'Joe Smith'
            schema_attrs['date'] = '2018-01-01'
            schema_attrs['degree'] = 'B.A.Sc. Honours'
            schema_attrs['age'] = '25'
            cred_name = 'Cred4Proof Credential Name'
            attr_values = [
                {"name": "name", "value": "Joe Smith"},
                {"name": "date", "value": "2018-01-01"},
                {"name": "degree", "value": "B.A.Sc. Honours"},
                {"name": "age", "value": "25"},
            ]

            # issue credential (org -> user)
            self.issue_credential_from_org_to_user(org, user, org_connection, user_connection, cred_def.ledger_creddef_id, attr_values)

            # verify credential is in user wallet
            user_credentials = fetch_credentials(user.agent)
            self.assertEqual(len(user_credentials), 1)

            # make up a credential
            schema_attrs = json.loads(cred_def.creddef_template)
            schema_attrs['name'] = 'Joe Smith 2'
            schema_attrs['date'] = '2018-01-02'
            schema_attrs['degree'] = 'M.Sc. Honours'
            schema_attrs['age'] = '28'
            cred_name = 'Cred4Proof Credential Name 2'

            # issue credential (org -> user)
            self.issue_credential_from_org_to_user(org, user, org_connection, user_connection, cred_def.ledger_creddef_id, attr_values)

            # verify credential is in user wallet
            user_credentials = fetch_credentials(user.agent)
            self.assertEqual(len(user_credentials), 2)

            # construct the proof request to send to the user (to whom we have just issued a credential)
            proof_req_attrs = proof_request.proof_req_attrs
            proof_req_predicates = proof_request.proof_req_predicates

            issuer_did = get_public_did(org.agent)
            proof_req_attrs = proof_req_attrs.replace('$ISSUER_DID', issuer_did)
            proof_req_predicates = proof_req_predicates.replace('$ISSUER_DID', issuer_did)
            proof_req_predicates = proof_req_predicates.replace('"$VALUE"', '21')
            proof_req_attrs = json.loads(proof_req_attrs)
            proof_req_predicates = json.loads(proof_req_predicates)
            proof_name = "My Cool Proof"
            proof_uuid = "Some Uuid Value"

            requested_attrs = {}
            additional_filters = {}
            for requested_attr in proof_req_attrs:
                referent = requested_attr["name"] + "_referent"
                requested_attrs[referent] = requested_attr
                additional_filters[referent] = {'attr::degree::value':'M.Sc. Honours'}
            requested_predicates = {}
            for requested_predicate in proof_req_predicates:
                referent = requested_predicate["name"] + "_referent"
                requested_predicates[referent] = requested_predicate
                additional_filters[referent] = {'attr::degree::value':'M.Sc. Honours'}

            # issue proof request (org -> user)
            org_conversation_1 = send_proof_request(org.agent, org_connection, proof_name, requested_attrs, requested_predicates)
            sleep(2)

            # poll to receive proof request
            i = 0
            while True:
                # once the user receives the request, build the proof
                user_conversations = AgentConversation.objects.filter(connection=user_connection, conversation_type=PROOF_REQ_CONVERSATION, status='request_received').all()
                i = i + 1
                if len(user_conversations) > 0 or i > 3:
                    break
                sleep(2)
            self.assertEqual(len(user_conversations), 1)
            user_conversation_1 = user_conversations[0]

            # select credential(s) for proof (user)
            claims_data = get_claims_for_proof_request(user.agent, user_conversation_1)
            self.assertEqual(len(claims_data), 2)

            requested_proof = get_agent_conversation(user.agent, user_conversation_1.guid, PROOF_REQ_CONVERSATION)

            # try again with additional_filters
            # TODO the additional_filters is currently not working :-(
            claims_data = get_claims_for_proof_request(user.agent, user_conversation_1, additional_filters=additional_filters)
            print("claims_data with filter:", claims_data)
            self.assertEqual(len(claims_data), 1)

            supplied_attrs = {}
            supplied_predicates = {}
            supplied_self_attested_attrs = {}
            # build array of credential id's (from wallet)
            for claim_data in claims_data:
                for referent in claim_data['presentation_referents']:
                    if referent in requested_proof["presentation_request"]["requested_attributes"] and referent not in supplied_attrs:
                        supplied_attrs[referent] = { "cred_id": claim_data["cred_info"]["referent"], "revealed": True }
                    if referent in requested_proof["presentation_request"]["requested_predicates"] and referent not in supplied_predicates:
                        supplied_predicates[referent] = { "cred_id": claim_data["cred_info"]["referent"] }
            for referent in requested_proof["presentation_request"]["requested_attributes"]:
                if referent not in supplied_attrs:
                    supplied_self_attested_attrs[referent] = "User supplied value"

            # construct proof and send (user -> org)
            user_conversation_2 = send_claims_for_proof_request(user.agent, user_conversation_1, supplied_attrs, supplied_predicates, supplied_self_attested_attrs)

            # accept and validate proof (org)
            i = 0
            while True:
                org_conversations = AgentConversation.objects.filter(connection=org_connection, conversation_type=PROOF_REQ_CONVERSATION, status='verified').all()
                i = i + 1
                if len(org_conversations) > 0 or i > 3:
                    break
                sleep(2)
            self.assertEqual(len(org_conversations), 1)
            org_conversation_2 = org_conversations[0]

            # TODO verify some stuff ...
        finally:
            # shut down the agent for that org
            stop_agent(user.agent)
            stop_agent(org.agent)

        # clean up after ourself
        self.delete_user_and_org_agents(user, org, raw_password)


    def test_agent_proof_exchange_restrictions(self):
        # request and deliver a proof between two agents
        (user, org, raw_password) = self.create_user_and_org()

        try:
            # startup the agent for that org
            start_agent(org.agent)
            start_agent(user.agent)

            (schema, cred_def, proof_request) = self.schema_and_cred_def_for_org(org)

            # establish a connection
            (org_connection, org_connection_state, user_connection, user_connection_state) = self.establish_agent_connection(org, user)

            # make up a credential
            schema_attrs = json.loads(cred_def.creddef_template)
            schema_attrs['name'] = 'Joe Smith'
            schema_attrs['date'] = '2018-01-01'
            schema_attrs['degree'] = 'B.A.Sc. Honours'
            schema_attrs['age'] = '25'
            cred_name = 'Cred4Proof Credential Name'
            attr_values = [
                {"name": "name", "value": "Joe Smith"},
                {"name": "date", "value": "2018-01-01"},
                {"name": "degree", "value": "B.A.Sc. Honours"},
                {"name": "age", "value": "25"},
            ]

            # issue credential (org -> user)
            self.issue_credential_from_org_to_user(org, user, org_connection, user_connection, cred_def.ledger_creddef_id, attr_values)

            # verify credential is in user wallet
            user_credentials = fetch_credentials(user.agent)
            self.assertEqual(len(user_credentials), 1)

            # make up a credential
            schema_attrs = json.loads(cred_def.creddef_template)
            schema_attrs['name'] = 'Joe Smith 2'
            schema_attrs['date'] = '2018-01-02'
            schema_attrs['degree'] = 'M.Sc. Honours'
            schema_attrs['age'] = '28'
            cred_name = 'Cred4Proof Credential Name 2'

            # issue credential (org -> user)
            self.issue_credential_from_org_to_user(org, user, org_connection, user_connection, cred_def.ledger_creddef_id, attr_values)

            # verify credential is in user wallet
            user_credentials = fetch_credentials(user.agent)
            self.assertEqual(len(user_credentials), 2)

            # construct the proof request to send to the user (to whom we have just issued a credential)
            proof_req_attrs = proof_request.proof_req_attrs
            proof_req_predicates = proof_request.proof_req_predicates

            issuer_did = get_public_did(org.agent)
            proof_req_attrs = proof_req_attrs.replace('$ISSUER_DID', issuer_did)
            proof_req_predicates = proof_req_predicates.replace('$ISSUER_DID', issuer_did)
            proof_req_predicates = proof_req_predicates.replace('"$VALUE"', '21')
            proof_req_attrs = json.loads(proof_req_attrs)
            for proof_req_attr in proof_req_attrs:
                if 'restrictions' in proof_req_attr:
                    proof_req_attr['restrictions'].append({'attr::degree::value':'M.Sc. Honours'})
            proof_req_predicates = json.loads(proof_req_predicates)
            for proof_req_predicate in proof_req_predicates:
                if 'restrictions' in proof_req_predicate:
                    proof_req_predicate['restrictions'].append({'attr::degree::value':'M.Sc. Honours'})
            proof_name = "My Cool Proof"
            proof_uuid = "Some Uuid Value"

            requested_attrs = {}
            for requested_attr in proof_req_attrs:
                referent = requested_attr["name"] + "_referent"
                requested_attrs[referent] = requested_attr
            requested_predicates = {}
            for requested_predicate in proof_req_predicates:
                referent = requested_predicate["name"] + "_referent"
                requested_predicates[referent] = requested_predicate

            # issue proof request (org -> user)
            org_conversation_1 = send_proof_request(org.agent, org_connection, proof_name, requested_attrs, requested_predicates)
            sleep(2)

            # poll to receive proof request
            i = 0
            while True:
                # once the user receives the request, build the proof
                user_conversations = AgentConversation.objects.filter(connection=user_connection, conversation_type=PROOF_REQ_CONVERSATION, status='request_received').all()
                i = i + 1
                if len(user_conversations) > 0 or i > 3:
                    break
                sleep(2)
            self.assertEqual(len(user_conversations), 1)
            user_conversation_1 = user_conversations[0]

            # select credential(s) for proof (user)
            claims_data = get_claims_for_proof_request(user.agent, user_conversation_1)
            print("claims_data:", claims_data)
            self.assertEqual(len(claims_data), 1)
            requested_proof = get_agent_conversation(user.agent, user_conversation_1.guid, PROOF_REQ_CONVERSATION)

            supplied_attrs = {}
            supplied_predicates = {}
            supplied_self_attested_attrs = {}
            # build array of credential id's (from wallet)
            for claim_data in claims_data:
                for referent in claim_data['presentation_referents']:
                    if referent in requested_proof["presentation_request"]["requested_attributes"] and referent not in supplied_attrs:
                        supplied_attrs[referent] = { "cred_id": claim_data["cred_info"]["referent"], "revealed": True }
                    if referent in requested_proof["presentation_request"]["requested_predicates"] and referent not in supplied_predicates:
                        supplied_predicates[referent] = { "cred_id": claim_data["cred_info"]["referent"] }
            for referent in requested_proof["presentation_request"]["requested_attributes"]:
                if referent not in supplied_attrs:
                    supplied_self_attested_attrs[referent] = "User supplied value"

            # construct proof and send (user -> org)
            user_conversation_2 = send_claims_for_proof_request(user.agent, user_conversation_1, supplied_attrs, supplied_predicates, supplied_self_attested_attrs)

            # accept and validate proof (org)
            i = 0
            while True:
                org_conversations = AgentConversation.objects.filter(connection=org_connection, conversation_type=PROOF_REQ_CONVERSATION, status='verified').all()
                i = i + 1
                if len(org_conversations) > 0 or i > 3:
                    break
                sleep(2)
            self.assertEqual(len(org_conversations), 1)
            org_conversation_2 = org_conversations[0]

            # TODO verify some stuff ...
        finally:
            # shut down the agent for that org
            stop_agent(user.agent)
            stop_agent(org.agent)

        # clean up after ourself
        self.delete_user_and_org_agents(user, org, raw_password)


