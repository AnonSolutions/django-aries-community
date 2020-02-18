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


