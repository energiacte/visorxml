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

import base64
import logging
import os
import os.path
from datetime import date, datetime
from io import BytesIO, StringIO
from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView, View
from extra_views import FormSetView
from PIL import Image
from django.template import RequestContext
from .forms import XMLFileForm
from .reports import XMLReport
from .pdf_utils import render_to_pdf, get_xml_string_from_pdf
import string
import random
from django.shortcuts import render_to_response, get_object_or_404
from django.forms import formset_factory


logger = logging.getLogger(__name__)


def load_report(session):
    """ Load current report from filesystem if it exists
    else: return None
    """
    file_name = session['report_xml_name']
    file_path = os.path.join(settings.MEDIA_ROOT, file_name)
    try:
        with open(file_path, 'rb') as xmlfile:
            report = XMLReport([(file_name, xmlfile.read())])
            return report
    except FileNotFoundError:
        session.pop("report_xml_name")
        return None



def random_name(size=20, ext=".xml"):
    """ return random string of letters and digits with an extension.
    size -> length of the string
    ext -> extension
    """
    return "".join([random.choice(string.ascii_letters + string.digits) for n in range(size)]) + ext


def home(request):
    if request.session.get('report_xml_name', False):
        validated = True
    else:
        validated = False
    return render_to_response("home.html", {"validated":validated}, RequestContext(request))


class GetXMLView(View):
    """CBV that serve the current centificate info as XML
    """
    def get(self, request, *args, **kwargs):
        session = self.request.session
        file_name = session['report_xml_name']
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)
        output_file_name = 'certificado-%s.xml' % datetime.now().strftime('%Y%m%d%H%M')

        with open(file_path, 'rb') as xmlfile:
            response = HttpResponse(xmlfile.read(), content_type='application/xml')
            response['Content-Disposition'] = 'attachment;filename=%s' % output_file_name
            return response



def get_xml_strings(new_file):
    """Extracts the file name and the XML string from XML file or PDF file
    returns the tuple into a list
    """
    xml_strings = []

    xml_string = ""
    if os.path.splitext(new_file.name)[1] == ".pdf":
        xml_string = get_xml_string_from_pdf(new_file)

    elif os.path.splitext(new_file.name)[1] == ".xml":
        xml_string = new_file.read()

    xml_strings.append((new_file.name, xml_string))

    return xml_strings


def measures_xml_upload(request):
    """ processes a XML with improvement features ("MedidasdeMejora/Medida/"). Inserts it in the current XML file.
    """
    xml = request.FILES["measures-xml"]
    xml_str = xml.read()
    base_xml = request.session['report_xml_name']
    with open(os.path.join(settings.MEDIA_ROOT, base_xml), "rb") as base_file:
        base_str = base_file.read()
    xml_strings = [(base_xml, base_str), (xml.name, xml_str)]
    report = XMLReport(xml_strings)
    if len(report.errors.get('validation_errors', None)) == 0:
        report_file = report.save_to_file()
        if request.session.get('report_xml_name', False):
            os.remove(os.path.join(settings.MEDIA_ROOT, request.session['report_xml_name']))
        request.session['report_xml_name'] = report_file
        validated = True
    else:
        validated = False
    validation_data = report.errors

    return render_to_response("energy-performance-certificate.html", locals(), RequestContext(request))



def validate(request):
    """ processes a XML of Energy Certificate. If it's valid, it's saved in the FS and the old is removed.
    """
    validated = False
    validation_data = {}
    try:
        xml_file = request.FILES.get("certificate-file", None)
        if xml_file is not None:
            xml_strings = get_xml_strings(xml_file)
            report = XMLReport(xml_strings)
            report_file = report.save_to_file()
            if request.session.get('report_xml_name', False):
                os.remove(os.path.join(settings.MEDIA_ROOT, request.session['report_xml_name']))
            request.session['report_xml_name'] = report_file
            if len(report.errors.get('validation_errors', None)) == 0:
                validated = True
            validation_data = report.errors
    except:
        error = (None, 'El archivo "<strong>%s</strong>" no está bien formado' % xml_file.name)
        validation_data['validation_errors'] = [error,]
        if request.session.get('report_xml_name', False):
            os.remove(os.path.join(settings.MEDIA_ROOT, request.session['report_xml_name']))
            request.session.pop("report_xml_name")

    return render_to_response("energy-performance-certificate.html", locals(), RequestContext(request))


def view_certificate(request):
    """ View the current energy certificate in a web page
    """
    try:
        if request.session.get('report_xml_name', False):
            report = load_report(request.session)
            validation_data = report.errors
            validated = True
        else:
            validated = False
    except:
        validated = False

    return render_to_response("energy-performance-certificate.html", locals(), RequestContext(request))


def view_suplementary_report(request):
    """ View the current energy suplementary certificate in a web page
    """
    if request.session.get('report_xml_name', False):
        report = load_report(request.session)
        espacios = zip(report.data.CondicionesFuncionamientoyOcupacion,
                       report.data.InstalacionesIluminacion.Espacios)
        validated = True
        return render_to_response("supplementary-report.html", locals(), RequestContext(request))

    else:
        return HttpResponseRedirect(reverse_lazy("certificate"))



def download_pdf(request):
    """ View the current energy certificate as PDF
    """
    if not request.session.get('report_xml_name', False):
        return HttpResponseRedirect(reverse_lazy("certificate"))

    session = request.session
    filename = 'certificado-%s.pdf' % datetime.now().strftime('%Y%m%d%H%M')
    report = load_report(session)
    validated = True
    pdf = True
    html = render_to_string('energy-performance-certificate.html', locals())

    env = os.environ.copy()
    env.update({
        'generation_date': report.data.DatosDelCertificador.Fecha,
        'reference': report.data.IdentificacionEdificio.ReferenciaCatastral
    })
    xml_name = session['report_xml_name']
    xml_path = os.path.join(settings.MEDIA_ROOT, xml_name)
    return render_to_pdf(html, filename, xml_path, env)



def download_pdf_suplementary(request):
    """ View the current energy suplementary certificate as pdf
    """
    if not request.session.get('report_xml_name', False):
        return HttpResponseRedirect(reverse_lazy("certificate"))

    session = request.session
    filename = 'certificado-suplementario-%s.pdf' % datetime.now().strftime('%Y%m%d%H%M')
    report = load_report(session)
    espacios = zip(report.data.CondicionesFuncionamientoyOcupacion,
                       report.data.InstalacionesIluminacion.Espacios)

    html = render_to_string('supplementary-report.html', locals())

    env = {
        'generation_date': report.data.DatosDelCertificador.Fecha,
        'reference': report.data.IdentificacionEdificio.ReferenciaCatastral
    }
    return render_to_pdf(html, filename, None, env)



def delete_element(request):
    """ Delete measure with index = request.POST["measure"]
    """
    if request.method == "POST":
        try:
            report = load_report(request.session)
            report.delete_element(request.POST["type"],  int(request.POST["index"])-1)
            return HttpResponse("")
        except:
            raise Http404()
    raise Http404()


def new_visit(request):
    """ Add a new "Visita" node to the XML
    """
    report = load_report(request.session)
    report.new_visit()
    return HttpResponseRedirect(reverse_lazy("certificate")+"#anexo-iv")



class UpdateXMLView(View):
    """CBV for update current energy certificate.
    POST: receives name and value from the attr to update
    """
    def post(self, request, *args, **kwargs):
        element = request.POST['name']
        value = request.POST['value']

        report = load_report(self.request.session)
        report.update_element(element, value)

        return HttpResponse()

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(UpdateXMLView, self).dispatch(*args, **kwargs)



class UploadImageView(View):
    """CBV for upload images to the energy certificate.
    POST: receives image and section. Downsize the image (Max_Height(260), Max_Width(260)) and save it
    into the current XML with base64 encoding.
    """
    def post(self, request, *args, **kwargs):
        uploaded_image = request.FILES['image']
        section = request.POST['section']
        #Read and resize the image
        image = Image.open(BytesIO(uploaded_image.read()))
        maxsize = (460, 460)
        image.thumbnail(maxsize, Image.ANTIALIAS)

        #Convert the image to a base64 string
        image_buffer = BytesIO()
        image.save(image_buffer, format="PNG")
        image_string = base64.b64encode(image_buffer.getvalue())

        report = load_report(self.request.session)
        report.update_image(section, image_string)

        return HttpResponse()

    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super(UploadImageView, self).dispatch(*args, **kwargs)
