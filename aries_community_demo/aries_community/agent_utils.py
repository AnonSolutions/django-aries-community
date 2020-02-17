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
from time import sleep
import requests

from django.conf import settings

from .models import *
from .utils import *


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
        endpoint: str,
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
    postgres_config = {'url': 'localhost:5432'}
    postgres_creds = {'account': 'postgres', 'password': 'mysecretpassword', 'admin_account': 'postgres', 'admin_password': 'mysecretpassword'}

    # endpoint exposed by ngrok
    #endpoint = "https://9f3a6083.ngrok.io"

    provisionConfig = []

    if start_agent:
        provisionConfig.extend([
            ("--endpoint", endpoint),
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
    for i in range[count]:
        port = random.randrange(16000, 32000)
        ret.append(port)
    return ret


def initialize_and_provision_agent(
        agent: AriesAgent, raw_password, did_seed=None, org_role=''
    ) -> AriesAgent:
    """
    Initialize and provision a new Aries Agent.
    """

    ports = get_unused_ports(2)
    agent.agent_admin_port = ports[0]
    agent.agent_http_port = ports[1]

    provisionConfig = aries_provision_config(
                            agent.agent_name, 
                            raw_password, 
                            agent.agent_http_port,
                            agent.agent_admin_port,
                            did_seed=did_seed,
                            start_agent=False
                        )
    startConfig = aries_provision_config(
                            agent.agent_name, 
                            raw_password, 
                            agent.agent_http_port,
                            agent.agent_admin_port,
                            did_seed=did_seed,
                            start_agent=True
                        )
    startConfig_json = json.dumps(startConfig)
    agent.agent_config = startConfig_json

    print(" >>> Provision an agent and wallet, get back configuration details")
    try:
        config = provision_agent(agent, provisionConfig)
    except:
        raise

    return agent


def provision_agent(agent, provisionConfig):
    """
    Provision an instance of an Aries Agent.
    """
    start_agent(agent, cmd='provision', config=provisionConfig)
    pass


def start_agent(agent, cmd: str='start', config=None):
    """
    Start up an instance of an Aries Agent.
    """
    if not config:
        config = agent.agent_config
    pass


def stop_agent(agent):
    """
    Shut down a running Aries Agent.
    """
    pass


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
            sleep(0.5)
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

def start_aca_py(agent_name, agent_args, endpoint, bin_path=None, python_path=None, wait=True):
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
    sleep(0.5)
    t1 = threading.Thread(target=output_reader, args=(agent_name, proc,))
    t1.start()
    t2 = threading.Thread(target=stderr_reader, args=(agent_name, proc,))
    t2.start()

    print("Started, waiting for status check ...")
    if wait:
        sleep(1.0)
        detect_process(endpoint)

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
    while 0 < len(running_procs):
        proc_name = next(iter(running_procs))
        stop_aca_py(proc_name)
