from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.db.models import Q

import json

from .models import *


###############################################################
# Forms to support user and organization registration
###############################################################
class BaseSignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=80, label='First Name', required=False,
                                 help_text='Optional.')
    last_name = forms.CharField(max_length=150, label='Last Name', required=False,
                                 help_text='Optional.')
    email = forms.EmailField(max_length=254, label='Email Address', required=True,
                                 help_text='Required. Provide a valid email address.')


class UserSignUpForm(BaseSignUpForm):
    mobile_agent = forms.BooleanField(required=False, initial=False, label='Mobile Agent')

    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2', 'mobile_agent')


class OrganizationSignUpForm(BaseSignUpForm):
    org_name = forms.CharField(max_length=60, label='Company Name', required=True,
                                 help_text='Required.')
    org_role_name = forms.CharField(max_length=40, label='Company Role', required=True,
                                 help_text='Required.')
    ico_url = forms.CharField(max_length=120, label="URL for company logo", required=False)

    managed_agent = forms.BooleanField(required=False, initial=True, label='Managed Agent')
    admin_port = forms.IntegerField(label='Agent Admin Port', required=False)
    admin_endpoint = forms.CharField(max_length=200, label='Agent Admin Endpoint', required=False)
    http_port = forms.IntegerField(label='Agent Http Port', required=False)
    http_endpoint = forms.CharField(max_length=200, label='Agent Http Endpoint', required=False)
    api_key = forms.CharField(max_length=40, label='Agent Admin API Key', required=False)
    webhook_key = forms.CharField(max_length=20, label='Agent Webhook Callback Key', required=False)

    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2', 
            'org_name', 'org_role_name', 'ico_url',
            'managed_agent', 'admin_port', 'admin_endpoint', 'http_port', 'http_endpoint', 
            'api_key', 'webhook_key')


######################################################################
# forms to create and confirm agent-to-agent connections
######################################################################
class AgentNameForm(forms.Form):
    agent_name = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(AgentNameForm, self).__init__(*args, **kwargs)
        self.fields['agent_name'].widget.attrs['readonly'] = True

class VisibleAgentNameForm(forms.Form):
    agent_name = forms.CharField(max_length=60)

    def __init__(self, *args, **kwargs):
        super(VisibleAgentNameForm, self).__init__(*args, **kwargs)
        self.fields['agent_name'].widget.attrs['readonly'] = True


class SendConnectionInvitationForm(AgentNameForm):
    partner_name = forms.CharField(label='Partner Name', max_length=60)

    def __init__(self, *args, **kwargs):
        super(SendConnectionInvitationForm, self).__init__(*args, **kwargs)
        self.fields['agent_name'].widget.attrs['readonly'] = True
        self.fields['agent_name'].widget.attrs['hidden'] = True


class SendConnectionResponseForm(SendConnectionInvitationForm):
    invitation_id = forms.IntegerField(widget=forms.HiddenInput())
    invitation_details = forms.CharField(label='Invitation', max_length=4000, widget=forms.Textarea)
    invitation_url = forms.CharField(label='Invitation URL', max_length=4000, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(SendConnectionResponseForm, self).__init__(*args, **kwargs)
        self.fields['invitation_id'].widget.attrs['readonly'] = True
        self.fields['invitation_details'].widget.attrs['readonly'] = True
        self.fields['invitation_url'].widget.attrs['readonly'] = True


class PollConnectionStatusForm(VisibleAgentNameForm):
    connection_id = forms.CharField(label="Id")

    def __init__(self, *args, **kwargs):
        super(PollConnectionStatusForm, self).__init__(*args, **kwargs)
        self.fields['agent_name'].widget.attrs['readonly'] = True
        self.fields['connection_id'].widget.attrs['readonly'] = True

