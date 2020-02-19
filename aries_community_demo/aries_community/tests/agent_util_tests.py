from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.views.generic.edit import UpdateView

from django.conf import settings

from time import sleep

from ..models import *
from ..utils import *
from ..wallet_utils import *
from ..registration_utils import *
from ..agent_utils import *


class AgentInteractionTests(TestCase):

    def test_provision_and_start_agent_1(self):
        config1 = aries_provision_config(
                "test_agent_1", 
                "secret_password",
                10000,
                10010,
                "localhost:10010",
                start_agent=True
            )
        proc1_info = start_aca_py("test_agent_1", config1, "http://localhost:10010")

        config2 = aries_provision_config(
                "test_agent_2", 
                "secret_password",
                10020,
                10030,
                "localhost:10030",
                start_agent=True
            )
        proc2_info = start_aca_py("test_agent_2", config2, "http://localhost:10030")

        stop_aca_py(proc1_info["name"])
        stop_aca_py(proc2_info["name"])

        print("Done!!!")

    def test_provision_and_start_agent_2(self):
        config1 = aries_provision_config(
                "test_agent_3", 
                "secret_password",
                10040,
                10050,
                "localhost:10050",
                start_agent=True
            )
        proc1_info = start_aca_py("test_agent_1", config1, "http://localhost:10050")

        config2 = aries_provision_config(
                "test_agent_4", 
                "secret_password",
                10060,
                10070,
                "localhost:10070",
                start_agent=True
            )
        proc2_info = start_aca_py("test_agent_2", config2, "http://localhost:10070")

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

