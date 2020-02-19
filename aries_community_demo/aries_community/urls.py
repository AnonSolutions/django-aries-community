from django.urls import path, include
from django.conf.urls import url
from django.contrib.auth import views as auth_views
from django.conf import settings

from .views import *


urlpatterns = [
    path('accounts/', include('django.contrib.auth.urls')),
    path('signup/', user_signup_view, name='signup'),
    path('org_signup/', org_signup_view, name='org_signup'),
    path('profile/', plugin_view, name='aries_profile', kwargs={'view_name': 'ARIES_PROFILE_VIEW'}),
    path('', auth_views.LoginView.as_view(), name='login'),
]
