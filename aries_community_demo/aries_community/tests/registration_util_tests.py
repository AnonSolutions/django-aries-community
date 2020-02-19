from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.views.generic.edit import UpdateView

from ..models import *
from ..registration_utils import *
from ..wallet_utils import *


class RegistrationTests(TestCase):

    def test_user_registration(self):
        # create, register and provision a user
        email = 'test1@registration.com'
        user = get_user_model().objects.create(
            email=email,
            first_name='Test',
            last_name='Registration',
        )
        user.save()
        raw_password = 'pass1234'
        user_provision(user, raw_password)

        # fetch and start agent
        fetch_user = get_user_model().objects.filter(email=email).all()[0]
        user_agent_name = get_user_wallet_name(email)
        self.assertEqual(fetch_user.agent.agent_name, user_agent_name)


    def test_org_registration(self):
        # create, register and provision a user and org
        # create, register and provision a user
        email = 'test2@registration.com'
        user_agent_name = get_user_wallet_name(email)
        user = get_user_model().objects.create(
            email=email,
            first_name='Test',
            last_name='Registration',
        )
        user.save()
        raw_password = 'pass1234'
        user_provision(user, raw_password)

        # now org
        org_name = 'My Unittest Org Inc'
        org = org_signup(user, raw_password, org_name)

        # fetch everything ...
        fetch_user = get_user_model().objects.filter(email=email).all()[0]
        fetch_org = AriesOrganization.objects.filter(org_name=org_name).all()[0]
        org_agent_name = get_org_wallet_name(org_name)
        self.assertEqual(fetch_org.agent.agent_name, org_agent_name)

        # verify relationship
        self.assertEqual(len(fetch_user.ariesrelationship_set.all()), 1)
        user_org = fetch_user.ariesrelationship_set.all()[0].org
        self.assertEqual(user_org.org_name, org_name)

        self.assertEqual(len(fetch_org.ariesrelationship_set.all()), 1)
        org_user = fetch_org.ariesrelationship_set.all()[0].user
        self.assertEqual(org_user.email, email)

