"""View rendering of reports
"""
import os
from datetime import datetime

from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy

from visorxml.pdf_utils import render_to_pdf
from .reports import XMLReport, BASE_XML_MINI, random_name


def load_report(session):
    """ Load current report from filesystem if it exists
    else: return None
    """
    file_name = session['new_xml_name']
    file_path = os.path.join(settings.MEDIA_ROOT, file_name)
    try:
        with open(file_path, 'rb') as xmlfile:
            report = XMLReport([(file_name, xmlfile.read())])
            return report
    except FileNotFoundError:
        session.pop("new_xml_name")
        return None

def clean_report(request):
    "Remove report data from session and file backup"
    if "new_xml_name" in request.session:
        file_name = request.session['new_xml_name']
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)
        try:
            os.remove(file_path)
        except FileNotFoundError: # nothing to do
            pass
        request.session.pop("new_xml_name")

    return HttpResponseRedirect(reverse("generate-report"))

def new_report(session):
    """ Create new mini-xml
    """
    name = random_name()
    report = XMLReport([(name, BASE_XML_MINI),])
    report.save_to_file(name)
    session['new_xml_name'] = name
    return report


def validate(request):
    "validate report"
    report = load_report(request.session)
    if len(report.errors["validation_errors"]) == 0:
        return HttpResponse("Yes")
    else:
        return HttpResponse("No")

def generate_report(request):
    """ View for the mini xml form. If not exists, new mini-xml is created
    """
    if request.session.get('new_xml_name', False):
    	report = load_report(request.session)
    	
    else:
    	report = new_report(request.session)

    return render(request, "generadorxml/generate_xml.html", locals())


@method_decorator(csrf_exempt)
def update_xml_mini(request):
    """ View for update elements of the XML.
        If value is a uppercase letter (Calificacion) returns new svg for replace it
    """
    element = request.POST['name']
    value = request.POST['value']
    report = load_report(request.session)
    report.update_element(element, value)
    return HttpResponse()


def download_xml(request):
        """ Download mini-XML
        """
        session = request.session
        file_name = session['new_xml_name']
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)
        output_file_name = 'certificado-%s.xml' % datetime.now().strftime('%Y%m%d%H%M')

        with open(file_path, 'rb') as xmlfile:
            response = HttpResponse(xmlfile.read(), content_type='application/xml')
            response['Content-Disposition'] = 'attachment;filename=%s' % output_file_name
            return response


def download_pdf(request):
    """ Download the current energy certificate as PDF
    """
    if not request.session.get('new_xml_name', False):
        return HttpResponseRedirect(reverse_lazy("generate-report"))

    session = request.session
    filename = 'certificado-%s.pdf' % datetime.now().strftime('%Y%m%d%H%M')
    report = load_report(session)
    pdf = True
    html = render_to_string('generadorxml/generate_xml.html', locals())

    env = os.environ.copy()
    env.update({
        'generation_date': report.data.DatosDelCertificador.Fecha,
        'reference': report.data.IdentificacionEdificio.ReferenciaCatastral
    })
    xml_name = session['new_xml_name']
    xml_path = os.path.join(settings.MEDIA_ROOT, xml_name)
    return render_to_pdf(html, filename, xml_path, env)