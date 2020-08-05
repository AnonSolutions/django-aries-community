from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils.translation import ugettext_lazy as trans

import json

from .models import *


###############################################################
# Forms to support user and organization registration
###############################################################
class BaseSignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=100, label=trans('First Name'), required=False,
                                 help_text='Optional.')
    last_name = forms.CharField(max_length=200, label=trans('Last Name'), required=False,
                                 help_text='Optional.')
    date_birth = forms.CharField(max_length=50, label=trans('Date of birth'), required=False,
                                 help_text='Optional.') 
    email = forms.EmailField(max_length=254, label=trans('Email Address'), required=True,
                                 help_text=trans('Required. Provide a valid email address.'))
    photo = forms.ImageField(label=trans('Photo'), required=False, help_text='Optional.')


class UserSignUpForm(BaseSignUpForm):
    mobile_agent = forms.BooleanField(required=False, initial=False, label=trans('Mobile Agent'))

    class Meta:
        model = get_user_model()
        fields = ('first_name', 'last_name', 'date_birth', 'email', 'photo', 'password1', 'password2', 'mobile_agent')


class OrganizationSignUpForm(BaseSignUpForm):
    org_name = forms.CharField(max_length=60, label=trans('Company Name'), required=True,
                                 help_text='Required.')
    org_role_name = forms.CharField(max_length=40, label=trans('Company Role'), required=True,
                                 help_text='Required.')
    ico_url = forms.CharField(max_length=120, label=trans("URL for company logo"), required=False)

    managed_agent = forms.BooleanField(required=False, initial=True, label=trans('Managed Agent'))
    admin_port = forms.IntegerField(label='Agent Admin Port', required=False)
    admin_endpoint = forms.CharField(max_length=200, label=trans('Agent Admin Endpoint'), required=False)
    http_port = forms.IntegerField(label='Agent Http Port', required=False)
    http_endpoint = forms.CharField(max_length=200, label=trans('Agent Http Endpoint'), required=False)
    api_key = forms.CharField(max_length=40, label=trans('Agent Admin API Key'), required=False)
    webhook_key = forms.CharField(max_length=20, label=trans('Agent Webhook Callback Key'), required=False)

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

class SendConnectionInvitationFormList(AgentNameForm):
    partner_name = forms.ModelChoiceField(queryset=AriesOrganization.objects.all())
    def __init__(self, *args, **kwargs):
        super(SendConnectionInvitationFormList, self).__init__(*args, **kwargs)
        self.fields['agent_name'].widget.attrs['readonly'] = True
        self.fields['agent_name'].widget.attrs['hidden'] = True
        
        
class SendConnectionInvitationForm(AgentNameForm):
    partner_name = forms.CharField(label=trans('Partner Name'), max_length=60)

    def __init__(self, *args, **kwargs):
        super(SendConnectionInvitationForm, self).__init__(*args, **kwargs)
        self.fields['agent_name'].widget.attrs['readonly'] = True
        self.fields['agent_name'].widget.attrs['hidden'] = True


class SendConnectionResponseForm(SendConnectionInvitationForm):
    invitation_id = forms.IntegerField(widget=forms.HiddenInput())
    invitation_details = forms.CharField(label=trans('Invitation'), max_length=4000, widget=forms.Textarea)
    invitation_url = forms.CharField(label=trans('Invitation URL'), max_length=4000, widget=forms.Textarea)

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


######################################################################
# forms to offer, request, send and receive credentials
######################################################################
class SendConversationResponseForm(AgentNameForm):
    conversation_id = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(SendConversationResponseForm, self).__init__(*args, **kwargs)
        self.fields['agent_name'].widget.attrs['readonly'] = True
        self.fields['agent_name'].widget.attrs['hidden'] = True
        self.fields['conversation_id'].widget.attrs['readonly'] = True


class PollConversationStatusForm(VisibleAgentNameForm):
    conversation_id = forms.CharField(label="Id")

    def __init__(self, *args, **kwargs):
        super(PollConversationStatusForm, self).__init__(*args, **kwargs)
        self.fields['agent_name'].widget.attrs['readonly'] = True
        self.fields['conversation_id'].widget.attrs['readonly'] = True


class SelectCredentialOfferForm(AgentNameForm):
    connection_id = forms.CharField(widget=forms.HiddenInput())
    partner_name = forms.CharField(label=trans('Partner Name'), max_length=60)
    cred_def = forms.ModelChoiceField(label='Cred Def', queryset=IndyCredentialDefinition.objects.all())

    def __init__(self, *args, **kwargs):
        super(SelectCredentialOfferForm, self).__init__(*args, **kwargs)
        self.fields['agent_name'].widget.attrs['readonly'] = True
        self.fields['agent_name'].widget.attrs['hidden'] = True
        self.fields['connection_id'].widget.attrs['readonly'] = True
        self.fields['partner_name'].widget.attrs['readonly'] = True

        # build a list of Credential Definitions available to the current wallet
        initial = kwargs.get('initial')
        if initial:
            agent_name = initial.get('agent_name')
            self.fields['cred_def'].queryset = IndyCredentialDefinition.objects.filter(agent__agent_name=agent_name).all()


class SendCredentialOfferForm(AgentNameForm):
    connection_id = forms.CharField(widget=forms.HiddenInput())
    partner_name = forms.CharField(label=trans('Partner Name'), max_length=60)
    cred_def = forms.CharField(max_length=80, widget=forms.HiddenInput())
    credential_name = forms.CharField(label=trans('Credential Name'), max_length=80)
    schema_attrs = forms.CharField(label=trans('Credential Attributes'), max_length=4000, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(SendCredentialOfferForm, self).__init__(*args, **kwargs)
        self.fields['agent_name'].widget.attrs['readonly'] = True
        self.fields['agent_name'].widget.attrs['hidden'] = True
        self.fields['connection_id'].widget.attrs['readonly'] = True
        self.fields['partner_name'].widget.attrs['readonly'] = True
        self.fields['cred_def'].widget.attrs['readonly'] = True

        # build a list of attributes for the given schema
        initial = kwargs.get('initial')
        if initial:
            schema_attrs = initial.get('schema_attrs', '{}')
            schema_attrs = json.loads(schema_attrs)
            self.fields['schema_attrs'].widget.attrs['hidden'] = True
            for attr in schema_attrs:
                field_name = 'schema_attr_' + attr
                self.fields[field_name] = forms.CharField(label=attr, max_length=200)


class SendCredentialResponseForm(SendConversationResponseForm):
    # a bunch of fields that are read-only to present to the user
    from_partner_name = forms.CharField(label=trans('Partner Name'), max_length=60)
    claim_name = forms.CharField(label=trans('Credential Name'), max_length=500)
    libindy_offer_schema_id = forms.CharField(max_length=120, widget=forms.HiddenInput())
    credential_attrs = forms.CharField(label=trans('Credential Attrs'), max_length=4000, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(SendCredentialResponseForm, self).__init__(*args, **kwargs)
        self.fields['from_partner_name'].widget.attrs['readonly'] = True
        self.fields['claim_name'].widget.attrs['readonly'] = True
        self.fields['libindy_offer_schema_id'].widget.attrs['readonly'] = True
        self.fields['credential_attrs'].widget.attrs['readonly'] = True

        # build a list of attributes for the current schema
        initial = kwargs.get('initial')
        if initial:
            credential_attrs = initial.get('credential_attrs', {})
            self.fields['credential_attrs'].widget.attrs['hidden'] = True
            for attr in credential_attrs:
                field_name = 'credential_attr_' + attr
                self.fields[field_name] = forms.CharField(label=attr, initial=credential_attrs[attr])
                self.fields[field_name].widget.attrs['readonly'] = True


######################################################################
# forms to request, send and receive proofs
######################################################################
class SelectProofRequestForm(AgentNameForm):
    connection_id = forms.CharField(widget=forms.HiddenInput())
    partner_name = forms.CharField(label=trans('Partner Name'), max_length=60)
    proof_request = forms.ModelChoiceField(label=trans('Proof Request Type'), queryset=IndyProofRequest.objects.all())

    def __init__(self, *args, **kwargs):
        super(SelectProofRequestForm, self).__init__(*args, **kwargs)
        self.fields['agent_name'].widget.attrs['readonly'] = True
        self.fields['agent_name'].widget.attrs['hidden'] = True
        self.fields['connection_id'].widget.attrs['readonly'] = True
        self.fields['partner_name'].widget.attrs['readonly'] = True


class SendProofRequestForm(AgentNameForm):
    connection_id = forms.CharField(widget=forms.HiddenInput())
    partner_name = forms.CharField(label=trans('Partner Name'), max_length=60)
    proof_name = forms.CharField(label=trans('Proof Name'), max_length=500)
    proof_attrs = forms.CharField(label=trans('Proof Attributes'), max_length=4000, widget=forms.Textarea)
    proof_predicates = forms.CharField(label=trans('Proof Predicates'), max_length=4000, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(SendProofRequestForm, self).__init__(*args, **kwargs)
        self.fields['agent_name'].widget.attrs['readonly'] = True
        self.fields['agent_name'].widget.attrs['hidden'] = True



        self.fields['connection_id'].widget.attrs['readonly'] = True
        self.fields['partner_name'].widget.attrs['readonly'] = True


class SendProofReqResponseForm(SendConversationResponseForm):
    # a bunch of fields that are read-only to present to the user
    from_partner_name = forms.CharField(label=trans('Partner Name'), max_length=60)
    proof_req_name = forms.CharField(label=trans('Proof Request Name'), max_length=500)

    def __init__(self, *args, **kwargs):
        super(SendProofReqResponseForm, self).__init__(*args, **kwargs)
        self.fields['from_partner_name'].widget.attrs['readonly'] = True
        self.fields['proof_req_name'].widget.attrs['readonly'] = True

class RemoveConnectionForm(AgentNameForm):
    partner_name = forms.CharField(label=trans('Partner Name'), max_length=60)
    connection_id = forms.CharField(label=trans('connection_id'), max_length=60)
    def __init__(self, *args, **kwargs):
        super(RemoveConnectionForm, self).__init__(*args, **kwargs)
        self.fields['partner_name'].widget.attrs['readonly'] = True
        self.fields['agent_name'].widget.attrs['readonly'] = True
        self.fields['agent_name'].widget.attrs['hidden'] = True

class SendConnectionInvitationFormList(AgentNameForm):
    def __init__(self, *args, **kwargs):
        super(SendConnectionInvitationFormList, self).__init__(*args, **kwargs)
        self.fields['agent_name'].widget.attrs['readonly'] = True
        self.fields['agent_name'].widget.attrs['hidden'] = True
#Create list of organizations that have not yet been connected to the person
        initial = kwargs.get('initial')
        agent = initial.get('agent_name', {})
        exclude_filter = AgentConnection.objects.filter(agent=agent).values_list('partner_name', flat=True)
        list = AriesOrganization.objects.values_list('org_name', flat=True)
        if initial:
            field_name = 'partner_name'
            self.fields[field_name] = forms.ModelChoiceField(queryset=AriesOrganization.objects.exclude(org_name__in=exclude_filter))
       
class SelectProofReqClaimsForm(SendProofReqResponseForm):
    proof_request = forms.CharField(label=trans('Requested Proof'), widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super(SelectProofReqClaimsForm, self).__init__(*args, **kwargs)

        # list requested attributes and the available claims, for the user to select
        initial = kwargs.get('initial')
        if initial:
            available_claims = initial.get('selected_claims', '{}')
            proof_request = initial.get('proof_request', '{}')

            for attr in proof_request['presentation_request']['requested_attributes']:
                field_name = 'proof_req_attr_' + attr
                choices = []
                claim_no = 0

                for claim in available_claims:
                    if attr in claim['presentation_referents']:
                        choices.append(('ref::'+claim['cred_info']['referent'], json.dumps(claim['cred_info']['attrs'])))
                        claim_no = claim_no + 1
                if 0 < len(choices):
                    self.fields[field_name] = forms.MultipleChoiceField(label=attr, choices=tuple(choices), widget=forms.RadioSelect(attrs={"checked":""}))
                else:
                    self.fields[field_name] = forms.CharField(label=trans('No claims available for')+ ' ' +attr+', enter value:', max_length=80)



class UserUpdateForm(AgentNameForm):
    first_name = forms.CharField(max_length=80, label=trans('First Name'), required=False,
                                 help_text='Optional.')
    last_name = forms.CharField(max_length=150, label=trans('Last Name'), required=False,
                                 help_text='Optional.')
    email = forms.CharField(max_length=80, label=trans('Email'), required=False,
                                 help_text='Optional.')
    date_birth = forms.CharField(max_length=150, label=trans('Date of birth'), required=False,
                                 help_text='Optional.')
    ori_photo = forms.CharField(label=trans('Original photo'), required=False, help_text='Optional.')
    new_photo = forms.ImageField(label=trans('New photo'), required=False, help_text='Optional.')
    password1 = forms.CharField(max_length=150, label=trans('New password'), required=False,
                                 help_text='Optional.', widget=forms.PasswordInput)


    def __init__(self, *args, **kwargs):
        super(UserUpdateForm, self).__init__(*args, **kwargs)
        self.fields['email'].widget.attrs['readonly'] = True
        self.fields['agent_name'].widget.attrs['readonly'] = True
        self.fields['agent_name'].widget.attrs['hidden'] = True

        initial = kwargs.get('initial')

        if initial:
            agent = initial.get('agent_name', {})
            filters = AriesUser.objects.filter(agent=agent).values()
            self.fields['first_name'].initial = filters[0]['first_name']
            self.fields['last_name'].initial = filters[0]['last_name']
            self.fields['email'].initial = filters[0]['email']
            self.fields['date_birth'].initial = filters[0]['date_birth']
            self.fields['ori_photo'].initial = filters[0]['photo']
            self.fields['password1'].initial = filters[0]['password']

class RemoveCredentialForm(AgentNameForm):
    referent = forms.CharField(label=trans('Referent'), max_length=200)
    def __init__(self, *args, **kwargs):
        super(RemoveCredentialForm, self).__init__(*args, **kwargs)
        self.fields['referent'].widget.attrs['readonly'] = True
        self.fields['agent_name'].widget.attrs['readonly'] = True
        self.fields['agent_name'].widget.attrs['hidden'] = True

class RevokeCredentialForm(AgentNameForm):
    referent = forms.CharField(label=trans('Referent'), max_length=200)
    def __init__(self, *args, **kwargs):
        super(RevokeCredentialForm, self).__init__(*args, **kwargs)
        self.fields['referent'].widget.attrs['readonly'] = True
        self.fields['agent_name'].widget.attrs['readonly'] = True
        self.fields['agent_name'].widget.attrs['hidden'] = True

class CredentialProposalForm(AgentNameForm):
    connection_id = forms.CharField(label=trans('connection_id'), max_length=100)
    partner_name = forms.CharField(label=trans('Partner Name'), max_length=100)
    credential_name = forms.CharField(label=trans('Credential Name'), max_length=100)
    agent_name = forms.CharField(label=trans('Agent Name'), max_length=100)

    def __init__(self, *args, **kwargs):
        super(CredentialProposalForm, self).__init__(*args, **kwargs)
        self.fields['agent_name'].widget.attrs['readonly'] = True
#       self.fields['agent_name'].widget.attrs['hidden'] = True
        self.fields['connection_id'].widget.attrs['readonly'] = True
        self.fields['partner_name'].widget.attrs['readonly'] = True
        initial = kwargs.get('initial')

        if initial:
            agent = initial.get('partner_name', {})
            self.fields['credential_name'] = forms.ModelChoiceField(queryset=IndyCredentialDefinition.objects.filter(agent__agent_name='o_'+agent))
            
class CredentialProposalForm(AgentNameForm):
    connection_id = forms.CharField(widget=forms.HiddenInput())
    partner_name = forms.CharField(label=trans('Partner Name'), max_length=100)
    credential_name = forms.CharField(label=trans('Credential Name'), max_length=100)
    agent_name = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        super(CredentialProposalForm, self).__init__(*args, **kwargs)
        self.fields['agent_name'].widget.attrs['readonly'] = True
#       self.fields['agent_name'].widget.attrs['hidden'] = True
        self.fields['connection_id'].widget.attrs['readonly'] = True
        self.fields['partner_name'].widget.attrs['readonly'] = True
        initial = kwargs.get('initial')

        if initial:
            agent = initial.get('partner_name', {})
            self.fields['credential_name'] = forms.ModelChoiceField(queryset=IndyCredentialDefinition.objects.filter(agent__agent_name='o_'+agent))

class SendCredentialProposalForm(AgentNameForm):
    connection_id = forms.CharField(widget=forms.HiddenInput())
    partner_name = forms.CharField(label=trans('Partner Name'), max_length=60)
    cred_def = forms.CharField(max_length=80, widget=forms.HiddenInput())
    credential_name = forms.CharField(widget=forms.HiddenInput())
    schema_attrs = forms.CharField(label=trans('Credential Attributes'), max_length=500, widget=forms.Textarea)

    def __init__(self, *args, **kwargs):
        super(SendCredentialProposalForm, self).__init__(*args, **kwargs)
        self.fields['agent_name'].widget.attrs['readonly'] = True
        self.fields['agent_name'].widget.attrs['hidden'] = True
        self.fields['connection_id'].widget.attrs['readonly'] = True
        self.fields['partner_name'].widget.attrs['readonly'] = True
        self.fields['cred_def'].widget.attrs['readonly'] = True

        # build a list of attributes for the given schema
        initial = kwargs.get('initial')
        if initial:
            schema_attrs = initial.get('schema_attrs', '{}')
            schema_attrs = json.loads(schema_attrs)
            self.fields['schema_attrs'].widget.attrs['hidden'] = True
            for attr in schema_attrs:
                field_name = 'schema_attr_' + attr
                self.fields[field_name] = forms.CharField(label=attr, max_length=500)


class SendCredentialResponseFormProposal(SendConversationResponseForm):
    # a bunch of fields that are read-only to present to the user
    agent_name = forms.CharField(widget=forms.HiddenInput())
    libindy_offer_schema_id = forms.CharField(widget=forms.HiddenInput())
    conversation_id = forms.CharField(label=trans('conversation_id'), max_length=500)
    from_partner_name = forms.CharField(widget=forms.HiddenInput())
    claim_name = forms.CharField(widget=forms.HiddenInput())
    credential_attrs = forms.CharField(label=trans('Credential Attributs'), max_length=500)

    def __init__(self, *args, **kwargs):
        super(SendCredentialResponseFormProposal, self).__init__(*args, **kwargs)
        self.fields['agent_name'].widget.attrs['readonly'] = True
        self.fields['agent_name'].widget.attrs['hidden'] = True
        self.fields['libindy_offer_schema_id'].widget.attrs['readonly'] = True
        self.fields['libindy_offer_schema_id'].widget.attrs['hidden'] = True
        self.fields['conversation_id'].widget.attrs['readonly'] = True
        self.fields['claim_name'].widget.attrs['readonly'] = True
        self.fields['claim_name'].widget.attrs['hidden'] = True
        self.fields['from_partner_name'].widget.attrs['hidden'] = True
        self.fields['from_partner_name'].widget.attrs['hidden'] = True
#       self.fields['credential_attrs'].widget.attrs['readonly'] = False


        # build a list of attributes for the current schema
        initial = kwargs.get('initial')
        if initial:
            credential_attrs = initial.get('credential_attrs', {})
            self.fields['credential_attrs'].widget.attrs['hidden'] = True
            for attr in credential_attrs:
                field_name = 'credential_attr_' + attr
                self.fields[field_name] = forms.CharField(label=attr, initial=credential_attrs[attr])
                self.fields[field_name].widget.attrs['readonly'] = True

class CredentialDeleteForm(forms.Form):
    # a bunch of fields that are read-only to present to the user
    agent_name = forms.CharField(widget=forms.HiddenInput())
    conversation_id = forms.CharField(label=trans('conversation_id'), max_length=500)
    credential_attrs= forms.CharField(label=trans('credential_attrs'), max_length=500)

    def __init__(self, *args, **kwargs):
        super(CredentialDeleteForm, self).__init__(*args, **kwargs)
        self.fields['agent_name'].widget.attrs['readonly'] = True
        self.fields['agent_name'].widget.attrs['hidden'] = True
        self.fields['conversation_id'].widget.attrs['readonly'] = True

        # build a list of attributes for the current schema
        initial = kwargs.get('initial')
        if initial:
            credential_attrs = initial.get('credential_attrs', {})
            self.fields['credential_attrs'].widget.attrs['hidden'] = True
            for attr in credential_attrs:
                field_name = 'credential_attr_' + attr
                self.fields[field_name] = forms.CharField(label=attr, initial=credential_attrs[attr])
                self.fields[field_name].widget.attrs['readonly'] = True


class SendCredentialRevokeForm(SendConversationResponseForm):
    # a bunch of fields that are read-only to present to the user
    agent_name = forms.CharField(widget=forms.HiddenInput())
    cred_rev_id = forms.CharField(label=trans('Cred_rev_id'), max_length=10)
    rev_reg_id = forms.CharField(widget=forms.HiddenInput())
    conversation_id = forms.CharField(label=trans('conversation_id'), max_length=120)

    def __init__(self, *args, **kwargs):
        super(SendCredentialRevokeForm, self).__init__(*args, **kwargs)
        self.fields['agent_name'].widget.attrs['readonly'] = True
        self.fields['cred_rev_id'].widget.attrs['readonly'] = True
        self.fields['conversation_id'].widget.attrs['readonly'] = True
        self.fields['rev_reg_id'].widget.attrs['hidden'] = True

