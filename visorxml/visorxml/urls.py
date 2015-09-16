from django.conf.urls import include, url
from django.contrib import admin

from .views import (HomeView,
                    ValidatorView)

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^validator$', ValidatorView.as_view(), name='validator')
]
