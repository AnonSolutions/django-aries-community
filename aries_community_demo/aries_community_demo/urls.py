from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('aries_community.urls')),
    path('api/', include('aries_api.urls')),
]
