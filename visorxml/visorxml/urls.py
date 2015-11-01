from django.conf.urls import include, url
from django.contrib import admin

from .views import (HomeView,
                    ValidatorView,
                    EnergyPerformanceCertificateView,
                    EnergyPerformanceCertificatePDFView,
                    SupplementaryReportView,
                    SupplementaryReportPDFView)

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^validator$', ValidatorView.as_view(), name='validator'),
    url(r'^certificate$', EnergyPerformanceCertificateView.as_view(), name='certificate'),
    url(r'^certificate-pdf$', EnergyPerformanceCertificatePDFView.as_view(), name='certificate-pdf'),
    url(r'^supplementary-report$', SupplementaryReportView.as_view(), name='supplementary-report'),
    url(r'^supplementary-report-pdf$', SupplementaryReportPDFView.as_view(), name='supplementary-report-pdf'),
]
