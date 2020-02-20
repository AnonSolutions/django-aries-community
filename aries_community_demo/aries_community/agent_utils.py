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
    genesis_url = settings.ARIES_CONFIG['genesis_url']

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
            "--admin-insecure-mode",
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
    if start_agent and webhook_url:
        provisionConfig.append(("--webhook-url", webhook_url))

    return provisionConfig


def get_unused_ports(count: int) -> []:
    ret = []
    for i in range(count):
        port = random.randrange(16000, 32000)
        ret.append(port)
    return ret


def initialize_and_provision_agent(
        agent_name: str, raw_password, did_seed=None, org_role='', start_agent_proc=False
    ) -> AriesAgent:
    """
    Initialize and provision a new Aries Agent.
    """

    agent = AriesAgent(agent_name=agent_name)

    ports = get_unused_ports(2)
    agent.agent_admin_port = ports[0]
    agent.agent_http_port = ports[1]
    public_endpoint = "http://localhost:" + str(agent.agent_http_port)
    admin_endpoint = "http://localhost:" + str(agent.agent_admin_port)

    startConfig = aries_provision_config(
                            agent.agent_name, 
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
    if not config:
        config = json.loads(agent.agent_config)

    start_aca_py(agent.agent_name, config, agent.admin_endpoint)


def stop_agent(agent):
    """
    Shut down a running Aries Agent.
    """
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

def detect_process(admin_url):
    text = None

    def fetch_swagger(url: str, timeout: float):
        text = None
        wait_time = START_TIMEOUT
        while wait_time > 0:
            try:
                resp = requests.get(url)
                print(resp, resp.status_code)
                resp.raise_for_status()
                text = resp.text
                return text
            except Exception:
                pass
            time.sleep(0.5)
            wait_time = wait_time - 0.5
        return text

    status_url = admin_url + "/status"
    status_text = fetch_swagger(status_url, START_TIMEOUT)
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

def start_aca_py(agent_name, agent_args, admin_endpoint, bin_path=None, python_path=None, wait=True):
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
        detect_process(admin_endpoint)

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
        running_procs.pop(proc_name)


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
    # TODO set admin header per agent
    #if AGENT_ADMIN_API_KEY is not None:
    #   ADMIN_REQUEST_HEADERS = {"x-api-key": AGENT_ADMIN_API_KEY}

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
    # TODO set admin header per agent
    #if AGENT_ADMIN_API_KEY is not None:
    #   ADMIN_REQUEST_HEADERS = {"x-api-key": AGENT_ADMIN_API_KEY}

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

