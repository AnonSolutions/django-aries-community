import asyncio
import aiohttp
import json
import os
from pathlib import Path
from tempfile import gettempdir
import random
import uuid
import threading
import subprocess
import time
import requests

from django.conf import settings

from rest_framework.response import Response

from .models import *
from .utils import *
from .indy_utils import *


DEFAULT_INTERNAL_HOST = "127.0.0.1"
DEFAULT_EXTERNAL_HOST = "localhost"

DUMMY_SEED = "00000000000000000000000000000000"


######################################################################
# utilities to provision Aries agents
######################################################################
def aries_provision_config(
        agent_name: str, 
        api_key: str,
        callback_key: str,
        wallet_key: str,
        http_port: int,
        admin_port: int,
        public_endpoint: str,
        admin_endpoint: str,
        did_seed: str=None, 
        genesis_data: str = None,
        params: dict = {},
        webhook_url: str = None,
        start_agent: bool = False
    ):
    """
    Build a configuration object for an Aries agent
    """

    internal_host = DEFAULT_INTERNAL_HOST
    external_host = DEFAULT_EXTERNAL_HOST

    rand_name = str(random.randint(100_000, 999_999))

    # TODO pull from settings file ARIES_CONFIG
    storage_type = "indy"
    wallet_type = "indy"
    wallet_name = agent_name.lower().replace(" ", "") + rand_name
    postgres = True
    postgres_config = settings.ARIES_CONFIG['storage_config']
    postgres_creds = settings.ARIES_CONFIG['storage_credentials']
    genesis_url = environ.get('GENESIS_URL', settings.ARIES_CONFIG['genesis_url'])
    webhook_host = settings.ARIES_CONFIG['webhook_host']
    webhook_port = settings.ARIES_CONFIG['webhook_port']
    webhook_url = "http://" + webhook_host + ":" + webhook_port + "/agent_cb/" + callback_key

    # endpoint exposed by ngrok
    #endpoint = "https://9f3a6083.ngrok.io"

    provisionConfig = []

    if start_agent:
        provisionConfig.extend([
            ("--endpoint", public_endpoint),
            ("--label", agent_name),
            "--auto-ping-connection",
            "--auto-accept-invites", 
            "--auto-accept-requests", 
            "--auto-respond-messages",
            ("--inbound-transport", "http", "0.0.0.0", str(http_port)),
            ("--outbound-transport", "http"),
            ("--admin", "0.0.0.0", str(admin_port)),
            ("--admin-api-key", api_key),
            #"--admin-insecure-mode",
        ])
    provisionConfig.extend([
        ("--wallet-type", wallet_type),
        ("--wallet-name", wallet_name),
        ("--wallet-key", wallet_key),
    ])
    if genesis_data:
        provisionConfig.append(("--genesis-transactions", genesis_data))
    else:
        provisionConfig.append(("--genesis-url",  genesis_url))
    if did_seed:
        provisionConfig.append(("--seed", did_seed))
    if storage_type:
        provisionConfig.append(("--storage-type", storage_type))
    if postgres:
        provisionConfig.extend(
            [
                ("--wallet-storage-type", "postgres_storage"),
                ("--wallet-storage-config", json.dumps(postgres_config)),
                ("--wallet-storage-creds", json.dumps(postgres_creds)),
            ]
        )
    provisionConfig.append(("--webhook-url", webhook_url))

    return provisionConfig


def get_unused_ports(count: int) -> []:
    ret = []
    for i in range(count):
        port = random.randrange(16000, 32000)
        ret.append(port)
    return ret


def initialize_and_provision_agent(
        agent_name: str, raw_password, did_seed=None, org_role='', start_agent_proc=False,
        mobile_agent=False, managed_agent=None, admin_port=None, admin_endpoint=None,
        http_port=None, http_endpoint=None, api_key=None, webhook_key=None
    ) -> AriesAgent:
    """
    Initialize and provision a new Aries Agent.
    """

    agent = AriesAgent(agent_name=agent_name)
    agent.api_key = api_key if api_key else random_an_string(40)
    agent.callback_key = webhook_key if webhook_key else random_an_string(20)
    agent.mobile_agent = mobile_agent
    agent.managed_agent = managed_agent

    if mobile_agent or (not managed_agent):
        start_agent_proc = False

    if not mobile_agent:
        ports = get_unused_ports(2)
        agent.agent_admin_port = admin_port if admin_port else ports[0]
        agent.agent_http_port = http_port if http_port else ports[1]
        managed_agent_host = settings.ARIES_CONFIG['managed_agent_host']
        public_endpoint = http_endpoint if http_endpoint else "http://" + managed_agent_host + ":" + str(agent.agent_http_port)
        admin_endpoint = admin_endpoint if admin_endpoint else "http://" + managed_agent_host + ":" + str(agent.agent_admin_port)

        startConfig = aries_provision_config(
                                agent.agent_name,
                                agent.api_key, 
                                agent.callback_key,
                                raw_password, 
                                agent.agent_http_port,
                                agent.agent_admin_port,
                                public_endpoint,
                                admin_endpoint,
                                did_seed=did_seed,
                                start_agent=True
                            )
        startConfig_json = json.dumps(startConfig)
        agent.agent_config = startConfig_json
        agent.public_endpoint = public_endpoint
        agent.admin_endpoint = admin_endpoint

    if did_seed:
        nym_info = create_and_register_did(agent.agent_name, did_seed)

    if start_agent_proc:
        try:
            start_agent(agent, config=startConfig)
        except:
            raise

    return agent


def start_agent(agent, cmd: str='start', config=None):
    """
    Start up an instance of an Aries Agent.
    """
    if agent.mobile_agent or (not agent.managed_agent):
        return

    if not config:
        config = json.loads(agent.agent_config)

    start_aca_py(agent.agent_name, config, agent.admin_endpoint, agent.api_key)


def stop_agent(agent):
    """
    Shut down a running Aries Agent.
    """
    if agent.mobile_agent or (not agent.managed_agent):
        return

    stop_aca_py(agent.agent_name)



######################################################################
# low-level utilities to manage aca-py processes
######################################################################

DEFAULT_BIN_PATH = "../venv/bin"
DEFAULT_PYTHON_PATH = ".."
START_TIMEOUT = 30.0
s_print_lock = threading.Lock()
running_procs = {}

def s_print(*a, **b):
    """Thread safe print function"""
    with s_print_lock:
        print(*a, **b)

def output_reader(proc_name, proc):
    while True:
        line = proc.stdout.readline()
        if line and 0 < len(line):
            s_print("Stdout {0}: {1}".format(proc_name, line), end="")
        else:
            break

def stderr_reader(proc_name, proc):
    while True:
        line = proc.stderr.readline()
        if line and 0 < len(line):
            s_print("Stderr {0}: {1}".format(proc_name, line), end="")
        else:
            break

def detect_process(admin_url, api_key, start_timeout=START_TIMEOUT):
    text = None

    def fetch_swagger(url: str, api_key: str, timeout: float):
        ADMIN_REQUEST_HEADERS = {}
        # set admin header per agent
        if api_key is not None:
           ADMIN_REQUEST_HEADERS = {"x-api-key": api_key}

        text = None
        wait_time = START_TIMEOUT
        while wait_time > 0:
            try:
                resp = requests.get(url, headers=ADMIN_REQUEST_HEADERS)
                resp.raise_for_status()
                text = resp.text
                return text
            except Exception:
                pass
            time.sleep(0.5)
            wait_time = wait_time - 0.5
        return text

    status_url = admin_url + "/status"
    status_text = fetch_swagger(status_url, api_key, start_timeout)
    print("Agent running with admin url", admin_url)

    if not status_text:
        raise Exception(
            "Timed out waiting for agent process to start. "
            + f"Admin URL: {status_url}"
        )
    ok = False
    try:
        status = json.loads(status_text)
        ok = isinstance(status, dict) and "version" in status
    except json.JSONDecodeError:
        pass
    if not ok:
        raise Exception(
            f"Unexpected response from agent process. Admin URL: {status_url}"
        )

def start_aca_py(agent_name, agent_args, admin_endpoint, api_key, bin_path=None, python_path=None, wait=True):
    """
    Start an aca-py process and record the process handle by agent name
    """
    cmd_path = "aca-py"
    if bin_path is None:
        bin_path = DEFAULT_BIN_PATH
    if bin_path:
        cmd_path = os.path.join(bin_path, cmd_path)
    cmd_args = list(flatten((["python3", cmd_path, "start"], agent_args)))

    my_env = os.environ.copy()
    python_path = DEFAULT_PYTHON_PATH if python_path is None else python_path
    if python_path:
        my_env["PYTHONPATH"] = python_path

    print("Starting aca-py with:", cmd_args)
    proc = subprocess.Popen(
        cmd_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=my_env,
        encoding="utf-8",
    )
    time.sleep(0.5)
    t1 = threading.Thread(target=output_reader, args=(agent_name, proc,))
    t1.start()
    t2 = threading.Thread(target=stderr_reader, args=(agent_name, proc,))
    t2.start()

    print("Started, waiting for status check ...")
    if wait:
        time.sleep(1.0)
        detect_process(admin_endpoint, api_key)

    proc_info = {"name": agent_name, "proc": proc, "threads": [t1, t2,]}
    running_procs[agent_name] = proc_info
    print("Done")

    return proc_info


def stop_aca_py(proc_name):
    """
    Stop an aca-py process by agent name (if running)
    """
    print("Terminating aca-py process ...")
    proc = None
    threads = []
    proc_info = running_procs.get(proc_name)
    if proc_info:
        proc = proc_info["proc"]
        threads = proc_info["threads"]

    try:
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=1.0)
                print(f"Exited with return code {proc.returncode}")
            except subprocess.TimeoutExpired:
                msg = "Process did not terminate in time"
                print(msg)
                raise Exception(msg)
        print("Joining threads ...")
        for tn in threads:
            tn.join()
    finally:
        try:
            running_procs.pop(proc_name)
        except:
            pass


def stop_all_aca_py():
    """
    Shut down all aca-py processes
    """
    while 0 < len(running_procs):
        proc_name = next(iter(running_procs))
        stop_aca_py(proc_name)


######################################################################
# utilities to create schemas and credential defitions
######################################################################
MAX_RETRIES = 3

def agent_post_with_retry(url, payload, headers=None):
    retries = 0
    while True:
        try:
            # test code to test exception handling
            #if retries < MAX_RETRIES:
            #    raise Exception("Fake exception!!!")
            response = requests.post(
                url,
                payload,
                headers=headers,
            )
            response.raise_for_status()
            return response
        except Exception as e:
            print("Error posting", url, e)
            retries = retries + 1
            if retries > MAX_RETRIES:
                raise e
            time.sleep(5)

def create_schema_json(schema_name, schema_version, schema_attrs):
    """
    Create an Indy Schema object based on a list of attributes.
    Returns the schema as well as a template for creating credentials.
    """

    schema = {
        'name': schema_name,
        'version': schema_version,
        'attributes': schema_attrs
    }
    creddef_template = {}
    for attr in schema_attrs:
        creddef_template[attr] = ''

    return (json.dumps(schema), json.dumps(creddef_template))


def create_schema(agent, schema_name, schema_version, schema_attrs, schema_template):
    """
    Create an Indy Schema and also store in our local database.
    Note that the agent must be running.
    """

    ADMIN_REQUEST_HEADERS = {}
    # set admin header per agent
    if agent.api_key is not None:
       ADMIN_REQUEST_HEADERS = {"x-api-key": agent.api_key}

    try:
        schema_request = {
            "schema_name": schema_name,
            "schema_version": schema_version,
            "attributes": schema_attrs,
        }
        response = agent_post_with_retry(
            agent.admin_endpoint + "/schemas",
            json.dumps(schema_request),
            headers=ADMIN_REQUEST_HEADERS,
        )
        response.raise_for_status()
        schema_id = response.json()

        indy_schema = IndySchema(
                            ledger_schema_id = schema_id["schema_id"],
                            schema_name = schema_name,
                            schema_version = schema_version,
                            schema = schema_attrs,
                            schema_template = schema_template
                            )
        indy_schema.save()
    except:
        raise

    return indy_schema


def create_creddef(agent, indy_schema, creddef_name, creddef_template, initialize_vcx=True):
    """
    Create an Indy Credential Definition (VCX) and also store in our local database
    Note that the agent must be running.
    """

    ADMIN_REQUEST_HEADERS = {}
    # set admin header per agent
    if agent.api_key is not None:
       ADMIN_REQUEST_HEADERS = {"x-api-key": agent.api_key}

    try:
        cred_def_request = {"schema_id": indy_schema.ledger_schema_id}
        print(cred_def_request)
        response = agent_post_with_retry(
            agent.admin_endpoint + "/credential-definitions",
            json.dumps(cred_def_request),
            headers=ADMIN_REQUEST_HEADERS,
        )
        response.raise_for_status()
        cred_def_id = response.json()

        indy_creddef = IndyCredentialDefinition(
                            ledger_creddef_id = cred_def_id,
                            ledger_schema = indy_schema,
                            agent = agent,
                            creddef_name = creddef_name,
                            creddef_template = creddef_template
                            )
        indy_creddef.save()
    except:
        raise

    return indy_creddef


def create_proof_request(name, description, attrs, predicates):
    """
    Create a proof request template (local database only).
    """

    proof_req_attrs = json.dumps(attrs)
    proof_req_predicates = json.dumps(predicates)
    proof_request = IndyProofRequest(
                            proof_req_name = name,
                            proof_req_description = description,
                            proof_req_attrs = proof_req_attrs,
                            proof_req_predicates = proof_req_predicates
                            )
    proof_request.save()

    return proof_request


######################################################################
# utilities to create and confirm agent-to-agent connections
######################################################################
def start_agent_if_necessary(agent, initialize_agent) -> (AriesAgent, bool):
    # start agent if necessary
    if initialize_agent:
        try:
            detect_process(agent.admin_endpoint, agent.api_key, start_timeout=1.0)
            # didn't start it (assume it's already running)
            return (agent, False)
        except:
            # not running, try to start
            start_agent(agent)
            return (agent, True)
    else:
        # didn't start it (assume it's already running)
        return (agent, False)


def request_connection_invitation(org, requestee_name, initialize_agent=False):
    """
    Request an Aries Connection Invitation from <partner org>.
    Creates a connection record for the requestor only 
    (receiver connection record is created when receiving the invitation).
    """

    # start the agent if requested (and necessary)
    (partner_agent, agent_started) = start_agent_if_necessary(org.agent, initialize_agent)

    # create connection and generate invitation
    try:
        ADMIN_REQUEST_HEADERS = {}
        # set admin header per agent
        if partner_agent.api_key is not None:
           ADMIN_REQUEST_HEADERS = {"x-api-key": partner_agent.api_key}

        response = requests.post(
                partner_agent.admin_endpoint + "/connections/create-invitation",
                headers=ADMIN_REQUEST_HEADERS,
        )
        response.raise_for_status()
        my_invitation = response.json()
        print(my_invitation)
        my_status = check_connection_status(partner_agent, my_invitation["connection_id"])
        print(my_status)

        connection = AgentConnection(
            guid = my_invitation["connection_id"],
            agent = partner_agent,
            partner_name = requestee_name,
            invitation = json.dumps(my_invitation["invitation"]),
            invitation_url = my_invitation["invitation_url"],
            status = my_status
        )
        connection.save()
    except:
        raise
    finally:
        if agent_started:
            stop_agent(partner_agent)

    return connection


def receive_connection_invitation(agent, partner_name, invitation, initialize_agent=False):
    """
    Receive an Aries Connection Invitation.
    Creates a receiver connection record.
    """

    # start the agent if requested (and necessary)
    (agent, agent_started) = start_agent_if_necessary(agent, initialize_agent)

    # create connection and generate invitation
    try:
        ADMIN_REQUEST_HEADERS = {}
        # set admin header per agent
        if agent.api_key is not None:
           ADMIN_REQUEST_HEADERS = {"x-api-key": agent.api_key}

        response = requests.post(
            agent.admin_endpoint
            + "/connections/receive-invitation?alias="
            + partner_name,
            invitation,
            headers=ADMIN_REQUEST_HEADERS
        )
        response.raise_for_status()
        my_connection = response.json()
        print(my_connection)

        connections = AgentConnection.objects.filter(agent=agent, guid=my_connection["connection_id"]).all()
        if 0 < len(connections):
            connection = connections[0]
        else:
            connection = AgentConnection(
                guid = my_connection["connection_id"],
                agent = agent,
                partner_name = partner_name,
                invitation = invitation,
                status = my_connection["state"]
            )
        connection.save()
    except:
        raise
    finally:
        if agent_started:
            stop_agent(agent)

    return connection


def get_agent_connection(agent, connection_id, initialize_agent=False):
    """
    Fetches the Connection object from the agent.
    """

    # start the agent if requested (and necessary)
    (agent, agent_started) = start_agent_if_necessary(agent, initialize_agent)

    connection = None

    # create connection and check status
    try:
        ADMIN_REQUEST_HEADERS = {}
        # set admin header per agent
        if agent.api_key is not None:
           ADMIN_REQUEST_HEADERS = {"x-api-key": agent.api_key}

        response = requests.get(
            agent.admin_endpoint
            + "/connections/"
            + connection_id,
            headers=ADMIN_REQUEST_HEADERS
        )
        response.raise_for_status()
        connection = response.json()
    except:
        raise
    finally:
        if agent_started:
            stop_agent(agent)

    return connection


def check_connection_status(agent, connection_id, initialize_agent=False):
    """
    Check status of the Connection.
    Called when an invitation has been sent and confirmation has not yet been received.
    """

    # create connection and check status
    try:
        connection = get_agent_connection(agent, connection_id, initialize_agent)

        connections = AgentConnection.objects.filter(agent=agent, guid=connection_id).all()
        if 0 < len(connections):
            my_connection = connections[0]
            my_connection.status = connection["state"]
            my_connection.save()
        else:
            my_connection = None
    except:
        raise

    return connection["state"]


def handle_agent_connections_callback(agent, topic, payload):
    """
    Handle connections processing callbacks from the agent
    """
    # TODO handle callbacks during connections protocol handshake
    # - for now only update connection status
    print(">>> callback:", agent.agent_name, topic)
    try:
        connection_id = payload["connection_id"]
        connection = AgentConnection.objects.filter(guid=connection_id, agent=agent).get()
        connection.status = payload["state"]
        connection.save()
        return Response("{}")
    except Exception as e:
        print(e)
        return Response("{}")


def handle_agent_connections_activity_callback(agent, topic, payload):
    """
    Handle connections activity callbacks from the agent
    """
    # TODO determine use cases where this is called
    print(">>> callback:", agent.agent_name, topic, payload)
    return Response("{}")


######################################################################
# utilities to offer, request, send and receive credentials
######################################################################

def send_credential_offer(agent, connection, credential_tag, schema_attrs, cred_def, credential_name, initialize_agent=False):
    """
    Send a Credential Offer.
    """

    # start the agent if requested (and necessary)
    (agent, agent_started) = start_agent_if_necessary(agent, initialize_agent)

    try:
        my_connection = run_coroutine_with_args(Connection.deserialize, json.loads(connection.connection_data))
        my_cred_def = run_coroutine_with_args(CredentialDef.deserialize, json.loads(cred_def.creddef_data))
        cred_def_handle = my_cred_def.handle

        # create a credential (the last '0' is the 'price')
        credential = run_coroutine_with_args(IssuerCredential.create, credential_tag, schema_attrs, int(cred_def_handle), credential_name, '0')

        run_coroutine_with_args(credential.send_offer, my_connection)

        # serialize/deserialize credential - waiting for Alice to rspond with Credential Request
        credential_data = run_coroutine(credential.serialize)

        conversation = AgentConversation(
            connection = connection,
            conversation_type = 'CredentialOffer',
            message_id = 'N/A',
            status = 'Sent',
            conversation_data = json.dumps(credential_data))
        conversation.save()
    except:
        raise
    finally:
        if initialize_vcx:
            try:
                shutdown(False)
            except:
                raise

    return conversation
    

def send_credential_request(wallet, connection, conversation, initialize_vcx=True):
    """
    Respond to a Credential Offer by sending a Credentia Request.
    """

    if initialize_vcx:
        try:
            config_json = wallet.wallet_config
            run_coroutine_with_args(vcx_init_with_config, config_json)
        except:
            raise

    # create connection and generate invitation
    try:
        my_connection = run_coroutine_with_args(Connection.deserialize, json.loads(connection.connection_data))
        #my_offer = run_coroutine_with_args()
    
        offer_json = [json.loads(conversation.conversation_data),]
        credential = run_coroutine_with_args(Credential.create, 'credential', offer_json)

        run_coroutine_with_args(credential.send_request, my_connection, 0)

        # serialize/deserialize credential - wait for Faber to send credential
        credential_data = run_coroutine(credential.serialize)

        conversation.status = 'Sent'
        conversation.conversation_data = json.dumps(credential_data)
        conversation.conversation_type = 'CredentialRequest'
        conversation.save()
    except:
        raise
    finally:
        if initialize_vcx:
            try:
                shutdown(False)
            except:
                raise

    return conversation


def handle_agent_credentials_callback(agent, topic, payload):
    """
    Handle credential processing callbacks from the agent
    """
    # TODO handle callbacks during credential exchange protocol handshake
    # - update credential status
    print(">>> callback:", agent.agent_name, topic, payload)
    return Response("{}")


