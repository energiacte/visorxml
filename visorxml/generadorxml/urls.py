from django.conf.urls import include, url
from django.views.decorators.csrf import csrf_exempt 

urlpatterns = [
  url(r'^update-xml-mini$', "generadorxml.views.update_xml_mini", name='update-xml-mini'),
  url(r'^download-xml-mini$', "generadorxml.views.download_xml", name='download-xml-mini'),
  url(r'^download-pdf-mini$', "generadorxml.views.download_pdf", name='download-pdf-mini'),
  url(r'^validate$', "generadorxml.views.validate", name='validate-mini-xml'),
  url(r'', "generadorxml.views.generate_report", name="generate-report"),

]