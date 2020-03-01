from django.conf import settings
from django.db import models
from django.contrib.sessions.models import Session
from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import Group, PermissionsMixin

from django.utils import timezone

from datetime import datetime, date, timedelta
import json


USER_ROLES = (
    'Admin',
    'User',
)

# base class for Aries Agents
class AriesAgent(models.Model):
    agent_name = models.CharField(max_length=200, unique=True)
    api_key = models.CharField(max_length=40, unique=True)
    callback_key = models.CharField(max_length=40, unique=True)
    agent_config = models.TextField(max_length=4000, blank=True, null=True)
    agent_admin_port = models.IntegerField(null=True)
    agent_http_port = models.IntegerField(null=True)
    public_endpoint = models.CharField(max_length=200, blank=True, null=True)
    admin_endpoint = models.CharField(max_length=200, blank=True, null=True)
    managed_agent = models.BooleanField(default=False)
    mobile_agent = models.BooleanField(default=False)

    def __str__(self):
        return self.agent_name

# special class for managing Aries users and agents
class AriesUserManager(BaseUserManager):

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("The given email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)

        user.set_password(password)
        user.save()

        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)

        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get('is_superuser') is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)

# special class for Aries users (owns an agent)
class AriesUser(AbstractBaseUser, PermissionsMixin):
    """
    Simple custom User class with email-based login.
    """
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=80, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    is_staff = models.BooleanField(
        default=False,
        help_text="Designates whether the user can log into the admin site."
    )
    is_active = models.BooleanField(
        default=True,
        help_text=(
            "Designates whether this user should be treated as active. "
            "Unselect this instead of deleting accounts."
        )
    )
    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)
    agent = models.ForeignKey(AriesAgent, to_field="agent_name", related_name='agent_user', blank = True, null=True, on_delete=models.CASCADE)

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'email'

    objects = AriesUserManager()

    @property
    def roles(self):
        # -> Iterable
        # Produce a list of the given user's roles.

        return filter(self.has_role, USER_ROLES)

    def get_full_name(self):
        return "%s %s" % (self.first_name, self.last_name)

    def add_role(self, role):
        # String ->
        # Adds user to role group

        self.groups.add(Group.objects.get(name=role))

    def has_role(self, role):
        # String -> Boolean
        # Produce true if user is in the given role group.

        return self.groups.filter(name=role).exists()


# Roles to which an organization can belong
class AriesOrgRole(models.Model):
    name = models.CharField(max_length=40, unique=True)

    def __str__(self):
        return self.name

# Base class for organizations that use the Aries platform
class AriesOrganization(models.Model):
    org_name = models.CharField(max_length=60, unique=True)
    agent = models.ForeignKey(AriesAgent, to_field="agent_name", related_name='agent_org', blank = True, null=True, on_delete=models.CASCADE)
    role = models.ForeignKey(AriesOrgRole, blank = True, null=True, on_delete=models.CASCADE)
    ico_url = models.CharField(max_length=120, blank = True, null=True)
    managed_agent = models.BooleanField(default=True)

    def __str__(self):
        return self.org_name

# Association class for user/organization relationship
class AriesOrgRelationship(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='ariesrelationship_set', on_delete=models.CASCADE)
    org = models.ForeignKey(AriesOrganization, related_name='ariesrelationship_set', on_delete=models.CASCADE)

    def __str__(self):
        return self.user.email + ':' + self.org.org_name

# track user session and attached agent for background agents
class AriesSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session = models.ForeignKey(Session, on_delete=models.CASCADE)
    agent_name = models.CharField(max_length=60, blank=True, null=True)


# reference to a schema on the ledger
class IndySchema(models.Model):
    ledger_schema_id = models.CharField(max_length=80, unique=True)
    schema_name = models.CharField(max_length=80)
    schema_version = models.CharField(max_length=80)
    schema = models.TextField(max_length=4000)
    schema_template = models.TextField(max_length=4000)
    schema_data = models.TextField(max_length=4000)
    # orgs which contain these role(s) will automatically get cred defs created for this schema
    roles = models.ManyToManyField(AriesOrgRole)

    def __str__(self):
        return self.schema_name


# reference to a credential definition on the ledger
class IndyCredentialDefinition(models.Model):
    ledger_creddef_id = models.CharField(max_length=80, unique=True)
    ledger_schema = models.ForeignKey(IndySchema, on_delete=models.CASCADE)
    agent = models.ForeignKey(AriesAgent, to_field="agent_name", related_name='indycreddef_set', on_delete=models.CASCADE)
    creddef_name = models.CharField(max_length=80)
    creddef_handle = models.CharField(max_length=80)
    creddef_template = models.TextField(max_length=4000)
    creddef_data = models.TextField(max_length=4000)

    def __str__(self):
        return self.ledger_schema.schema_name + ":" + self.wallet.wallet_name + ":" + self.creddef_name


# Description of a proof request
class IndyProofRequest(models.Model):
    proof_req_name = models.CharField(max_length=400, unique=True)
    proof_req_description = models.TextField(max_length=4000)
    proof_req_attrs = models.TextField(max_length=4000)
    proof_req_predicates = models.TextField(max_length=4000, blank=True)

    def __str__(self):
        return self.proof_req_name


# base class for (unresponded) invitations
class AgentInvitation(models.Model):
    agent = models.ForeignKey(AriesAgent, to_field="agent_name", on_delete=models.CASCADE)
    partner_name = models.CharField(max_length=200)
    invitation = models.TextField(max_length=4000, blank=True)
    invitation_url = models.TextField(max_length=4000, blank=True)
    connecion_guid = models.CharField(max_length=80, blank=True)

# base class for Agent connections
class AgentConnection(models.Model):
    guid = models.CharField(max_length=80, primary_key=True)
    agent = models.ForeignKey(AriesAgent, to_field="agent_name", on_delete=models.CASCADE)
    partner_name = models.CharField(max_length=200)
    invitation = models.TextField(max_length=4000, blank=True)
    invitation_url = models.TextField(max_length=4000, blank=True)
    status = models.CharField(max_length=80, blank=True)

    def __str__(self):
        return self.agent.agent_name + ":" + self.partner_name + ", " +  self.guid


# base class for Agent conversations - issue/receive credential and request/provide proof
class AgentConversation(models.Model):
    guid = models.CharField(max_length=80, primary_key=True)
    connection = models.ForeignKey(AgentConnection, on_delete=models.CASCADE)
    conversation_type = models.CharField(max_length=30)

    def __str__(self):
        return self.connection.agent.agent_name + ":" + self.connection.partner_name + ":" + self.conversation_type + ", " +  self.guid
