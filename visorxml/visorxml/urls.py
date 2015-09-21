from django.conf.urls import include, url
from django.contrib import admin

from .views import (HomeView,
                    ValidatorView,
                    ViewerView,
                    GetPDFView)

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^validator$', ValidatorView.as_view(), name='validator'),
    url(r'^viewer$', ViewerView.as_view(), name='viewer'),
    url(r'^pdf$', GetPDFView.as_view(), name='get_pdf')
]
