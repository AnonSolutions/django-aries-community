from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.db.models import Q

import json

from .models import *


###############################################################
# Forms to support user and organization registration
###############################################################
class UserSignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=80, label='First Name', required=False,
                                 help_text='Optional.')
    last_name = forms.CharField(max_length=150, label='Last Name', required=False,
                                 help_text='Optional.')
    email = forms.EmailField(max_length=254, label='Email Address', required=True,
                                 help_text='Required. Provide a valid email address.')

    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2')


class OrganizationSignUpForm(UserSignUpForm):
    org_name = forms.CharField(max_length=60, label='Company Name', required=True,
                                 help_text='Required.')
    org_role_name = forms.CharField(max_length=40, label='Company Role', required=True,
                                 help_text='Required.')
    ico_url = forms.CharField(max_length=120, label="URL for company logo", required=False)


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
    connection_id = forms.IntegerField(widget=forms.HiddenInput())
    invitation_details = forms.CharField(label='Invitation', max_length=4000, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(SendConnectionResponseForm, self).__init__(*args, **kwargs)
        self.fields['connection_id'].widget.attrs['readonly'] = True


class PollConnectionStatusForm(VisibleAgentNameForm):
    connection_id = forms.IntegerField(label="Id")

    def __init__(self, *args, **kwargs):
        super(PollConnectionStatusForm, self).__init__(*args, **kwargs)
        self.fields['agent_name'].widget.attrs['readonly'] = True
        self.fields['connection_id'].widget.attrs['readonly'] = True

