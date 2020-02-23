from django.http import HttpResponseBadRequest, HttpResponseRedirect, HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, get_user_model, login
from django.urls import reverse
from django.conf import settings

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response

import uuid

from .forms import *
from .models import *
from .wallet_utils import *
from .registration_utils import *
from .agent_utils import *


USER_ROLE = getattr(settings, "DEFAULT_USER_ROLE", 'User')
ORG_ROLE = getattr(settings, "DEFAULT_ORG_ROLE", 'Admin')

###############################################################
# UI views to support user and organization registration
###############################################################

# Sign up as a site user, and create a wallet
def user_signup_view(
    request,
    template=''
    ):
    """
    Create a user account with a managed wallet.
    """

    if request.method == 'POST':
        form = UserSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)

            if Group.objects.filter(name=USER_ROLE).exists():
                user.groups.add(Group.objects.get(name=USER_ROLE))
            user.save()

            # create an Indy wallet - derive wallet name from email, and re-use raw password
            user = user_provision(user, raw_password)

            # TODO need to auto-login with Atria custom user
            #login(request, user)

            return redirect('login')
    else:
        form = UserSignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


# Sign up as an org user, and create a wallet
def org_signup_view(
    request,
    template=''
    ):
    """
    Signup an Organization with a managed wallet.
    Creates a user account and links to the Organization.
    """

    if request.method == 'POST':
        form = OrganizationSignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('email')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            user.managed_wallet = False

            if Group.objects.filter(name='Admin').exists():
                user.groups.add(Group.objects.get(name='Admin'))
            user.save()

            # create and provision org, including org wallet
            org_name = form.cleaned_data.get('org_name')
            org_role_name = form.cleaned_data.get('org_role_name')
            org_ico_url = form.cleaned_data.get('ico_url')
            org_role, created = AriesOrgRole.objects.get_or_create(name=org_role_name)
            org = org_signup(user, raw_password, org_name, org_role=org_role, org_ico_url=org_ico_url)

            # TODO need to auto-login with Atria custom user
            #login(request, user)

            return redirect('login')
    else:
        form = OrganizationSignUpForm()
    return render(request, 'registration/signup.html', {'form': form})


###############################################################
# Agent callback web service
###############################################################
TOPIC_CONNECTIONS = "connections"
TOPIC_CONNECTIONS_ACTIVITY = "connections_actvity"
TOPIC_CREDENTIALS = "credentials"
TOPIC_PRESENTATIONS = "presentations"
TOPIC_GET_ACTIVE_MENU = "get-active-menu"
TOPIC_PERFORM_MENU_ACTION = "perform-menu-action"
TOPIC_ISSUER_REGISTRATION = "issuer_registration"
TOPIC_PROBLEM_REPORT = "problem-report"

@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def agent_cb_view(
    request,
    topic,
    format=None
    ):
    """
    Handle callbacks from the Aries agents
    """
    payload = request.data
    print(">>> callback:", topic, payload)

    return Response("{}")


###############################################################
# UI views to support wallet and agent UI functions
###############################################################
def profile_view(
    request,
    template=''
    ):
    """
    Example of user-defined view for Profile tab.
    """
    return render(request, 'aries/profile.html')

def data_view(
    request,
    template=''
    ):
    """
    Example of user-defined view for Data tab.
    """
    return render(request, 'aries/data.html')

def wallet_view(
    request,
    template=''
    ):
    """
    Example of user-defined view for Wallet tab.
    """
    return render(request, 'aries/wallet.html')

import importlib

def plugin_view(request, view_name):
    """
    Find and invoke user-defined view.
    These are configured in settings file.
    """

    view_function = getattr(settings, view_name)
    print(view_function)

    mod_name, func_name = view_function.rsplit('.',1)
    mod = importlib.import_module(mod_name)
    func = getattr(mod, func_name)

    return func(request)

