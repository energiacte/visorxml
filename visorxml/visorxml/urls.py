#!/usr/bin/env python
#encoding:utf-8
#
# Copyright (c) 2015 Ministerio de Fomento
#                    Instituto de Ciencias de la Construcción Eduardo Torroja (IETcc-CSIC)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

from django.conf.urls import include, url
from django.contrib import admin

from .views import (GetXMLView,
                    UpdateXMLView,
                    UploadImageView)

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', 'visorxml.views.home', name='home'),
    url(r'^validator/?$', 'visorxml.views.validate', name='validator'),
    url(r'^visits/new/?$', 'visorxml.views.new_visit', name='new_visit'),
    url(r'^singularsolutions/add/?$', 'visorxml.views.add_singular_solutions', name='add_singular_solutions'),
    url(r'^element/delete/?$', 'visorxml.views.delete_element', name='delete_element'),
    url(r'^measures-xml/?$', 'visorxml.views.measures_xml_upload', name='measures_xml_upload'),
    url(r'^xml$', GetXMLView.as_view(), name='get-xml'),
    url(r'^certificate$', 'visorxml.views.view_certificate', name='certificate'),
    url(r'^certificate-pdf$', 'visorxml.views.download_pdf', name='certificate-pdf'),
    url(r'^supplementary-report$', 'visorxml.views.view_suplementary_report', name='supplementary-report'),
    url(r'^supplementary-report-pdf$', 'visorxml.views.download_pdf_suplementary', name='supplementary-report-pdf'),
    url(r'^update-xml$', UpdateXMLView.as_view(), name='update-xml'),
    url(r'^upload-image$', UploadImageView.as_view(), name='upload-image'),
]

