from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.auth import get_user_model
from django.conf import settings

import json

from .models import *
from .wallet_utils import *


USER_ROLE = getattr(settings, "DEFAULT_USER_ROLE", 'User')
ORG_ROLE = getattr(settings, "DEFAULT_ORG_ROLE", 'Admin')

def url_aries_profile(role):
    if role == ORG_ROLE:
        return 'aries/base_organization_profile.html'
    else:
        return 'aries/base_individual_profile.html'

def is_organization_login(user, path):
    org_url = getattr(settings, 'ORG_NAMESPACE', None)
    if org_url:
        if org_url in path:
            return True
        return False
    if user.has_role(ORG_ROLE):
        print("User has org role", ORG_ROLE)
        return True
    return False

def user_agent_logged_in_handler(request, user, agent_name):
    #print("Login wallet, {} {} {}".format(user.email, request.session.session_key, agent_name))
    #(session, session_created) = AriesSession.objects.get_or_create(user=user, session_id=request.session.session_key)
    #session.agent_name = agent_name
    #session.save()
    # TODO start aca-py agent for user
    pass

def user_agent_logged_out_handler(request, user):
    #print("Logout wallet, {} {}".format(user.email, request.session.session_key))
    #session = AriesSession.objects.get(user=user, session_id=request.session.session_key)
    #session.agent_name = None
    #session.save()
    # TODO shut down aca-py agent for user
    pass

def user_logged_in_handler(sender, user, request, **kwargs):
    if 'agent_name' in request.session:
        agent_name = request.session['agent_name']
    else:
        agent_name = None
    print("Login user {} {} {}".format(user.email, request.session.session_key, agent_name))
    #(session, session_created) = AriesSession.objects.get_or_create(user=user, session_id=request.session.session_key, agent_name=agent_name)
    #agent_background_task("Started by user login", user.id, request.session.session_key, repeat=AGENT_POLL_INTERVAL)


def user_logged_out_handler(sender, user, request, **kwargs):
    print("Logout user {} {}".format(user.email, request.session.session_key))
    #AriesSession.objects.get(user=user, session_id=request.session.session_key).delete()
    # TODO


def handle_agent_login_internal(request, user, agent_name, raw_password):
    # get user or org associated with this agent
    related_user = get_user_model().objects.filter(agent__agent_name=agent_name).all()
    related_org = AriesOrganization.objects.filter(agent__agent_name=agent_name).all()
    if len(related_user) == 0 and len(related_org) == 0:
        raise Exception('Error Agent with no owner {}'.format(agent_name))

    # now try to open the agent - will throw an exception if it fails
    # TODO
    #wallet_handle = open_wallet(agent_name, raw_password)
    #close_wallet(wallet_handle)

    if len(related_user) > 0:
        request.session['agent_type'] = 'user'
        request.session['agent_owner'] = related_user[0].email
    elif len(related_org) > 0:
        request.session['agent_type'] = 'org'
        request.session['agent_owner'] = related_org[0].org_name
    request.session['agent_name'] = agent_name
    request.session['agent_password'] = raw_password

    user_agent_logged_in_handler(request, user, agent_name)


def handle_agent_logout_internal(request):
    # clear agent-related session variables
    if 'agent_type' in request.session:
        del request.session['agent_type']
    if 'agent_name' in request.session:
        del request.session['agent_name']
    if 'raw_password' in request.session:
        del request.session['raw_password']
    if 'agent_owner' in request.session:
        del request.session['agent_owner']


def init_user_session(sender, user, request, **kwargs):
    target = request.POST.get('next', '/profile/')
    if is_organization_login(user, target):
        request.session['ACTIVE_ROLE'] = ORG_ROLE
        orgs = AriesOrgRelationship.objects.filter(user=user).all()
        if 0 < len(orgs):
            sel_org = orgs[0].org
            request.session['ACTIVE_ORG'] = str(sel_org.id)

            # login as org wallet
            # TODO
            #if sel_org.wallet is not None:
            #    sel_wallet = sel_org.wallet
            #    config = json.loads(sel_wallet.wallet_config)
            #    handle_wallet_login_internal(request, user, config['agent_name'], config['wallet_key'])
    else:
        if user.has_role(USER_ROLE):
            request.session['ACTIVE_ROLE'] = USER_ROLE
        else:
            # TODO for now just set a dummy default - logged in user with no role assigned
            request.session['ACTIVE_ROLE'] = USER_ROLE

        # try to login as user wallet
        # TODO
        #if user.wallet is not None:
        #    sel_wallet = user.wallet
        #    config = json.loads(sel_wallet.wallet_config)
        #    handle_wallet_login_internal(request, user, config['agent_name'], config['wallet_key'])

    role = request.session['ACTIVE_ROLE']
    request.session['ARIES_PROFILE'] = url_aries_profile(role)
    print("Profile =", request.session['ARIES_PROFILE'])

    # setup background "virtual agent"
    user_logged_in_handler(sender, user, request, **kwargs)


def clear_user_session(sender, user, request, **kwargs):
    # setup background "virtual agent"
    user_logged_out_handler(sender, user, request, **kwargs)

    if 'ACTIVE_ROLE' in request.session:
        del request.session['ACTIVE_ROLE']
    if 'ACTIVE_ORG' in request.session:
        del request.session['ACTIVE_ORG']
    request.session['ARIES_PROFILE'] = ''


user_logged_in.connect(init_user_session)

user_logged_out.connect(clear_user_session)


