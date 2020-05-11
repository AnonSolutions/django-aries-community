from django.contrib import admin

from .models import *


# Register your models here.
admin.site.register(AriesUser)
admin.site.register(AriesOrgRole)
admin.site.register(AriesOrganization)
admin.site.register(AriesOrgRelationship)
admin.site.register(AriesAgent)
admin.site.register(IndySchema)
admin.site.register(IndyCredentialDefinition)
admin.site.register(IndyProofRequest)
admin.site.register(AgentInvitation)
admin.site.register(AgentConnection)
admin.site.register(AgentConversation)
