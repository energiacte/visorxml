from django.shortcuts import render
import os
from django.http import HttpResponseRedirect, HttpResponse, Http404
from django.views.generic import TemplateView, View
from .reports import XMLReport, BASE_XML_MINI, random_name
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from datetime import datetime,date
from .pdf_utils import render_to_pdf
from django.template.loader import render_to_string


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

def new_report(session):
    name = random_name()
    report = XMLReport([(name, BASE_XML_MINI),])
    report.save_to_file(name)
    session['new_xml_name'] = name
    return report



def generate_report(request):
    """ View the current energy certificate in a web page
    """
    if request.session.get('new_xml_name', False):
    	report = load_report(request.session)
    	validation_data = report.errors
    	
    else:
    	report = new_report(request.session)

    download = True

    return render(request, "generadorxml/generate_xml.html", locals())

from generadorxml.templatetags.generadorxml import escalasvg



@method_decorator(csrf_exempt)
def update_xml_mini(request):
    element = request.POST['name']
    value = request.POST['value']

    report = load_report(request.session)
    report.update_element(element, value)

    if value in "A B C D E F G".split(" "): #IF value is a letter -> return new SVG
        return HttpResponse(escalasvg(value))
 
    return HttpResponse()



def download_xml(request):
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
        'generation_date': str(date.today()),
        'reference': report.data.IdentificacionEdificio.ReferenciaCatastral
    })
    xml_name = session['new_xml_name']
    xml_path = os.path.join(settings.MEDIA_ROOT, xml_name)
    return render_to_pdf(html, filename, xml_path, env)