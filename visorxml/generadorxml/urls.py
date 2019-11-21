from django.conf.urls import include, url
from django.views.decorators.csrf import csrf_exempt
from generadorxml.views import (
  update_xml_mini, download_xml, download_pdf, validate, clean_report, generate_report)

urlpatterns = [
  url(r'^update-xml-mini$', update_xml_mini, name='update-xml-mini'),
  url(r'^download-xml-mini$', download_xml, name='download-xml-mini'),
  url(r'^download-pdf-mini$', download_pdf, name='download-pdf-mini'),
  url(r'^validate$', validate, name='validate-mini-xml'),
  url(r'^clean$', clean_report, name='clean-report'),
  url(r'', generate_report, name="generate-report"),
]