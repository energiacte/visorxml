import hashlib
import logging
import os.path
from datetime import date

from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.template.loader import render_to_string
from django.views.generic import TemplateView

from extra_views import FormSetView

from .forms import XMLFileForm
from .reports import XMLReport
from .pdf_utils import render_to_pdf


logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = "home.html"


class ValidatorView(FormSetView):
    template_name = "validator.html"
    form_class = XMLFileForm
    extra = 2
    success_url = reverse_lazy('validator')

    def formset_valid(self, formset):
        session = self.request.session

        xml_files = []
        for form_index, form in enumerate(formset.forms):
            uploaded_file = form.cleaned_data.get('file', None)
            if uploaded_file:
                xml_files.append(uploaded_file)

        xml_strings = self.save_session_info(xml_files)
        report = XMLReport(xml_strings)
        report_file = report.save_to_file(settings.MEDIA_ROOT)
        session['report_xml_name'] = report_file

        context_data = self.get_context_data(formset=formset)
        context_data['validation_data'] = report.errors

        return self.render_to_response(context_data)

    def save_session_info(self, xml_files):
        """
        Get a list of uploaded XML files and save some data in the user session.
        Returns a list of tuples, [(file_name, xml_file_content), ...]
        """
        session = self.request.session

        xml_strings = []
        for file_index, xml_file in enumerate(xml_files):
            session['file_%s_name' % file_index] = xml_file.name

            xml_string = xml_file.read()
            xml_strings.append((xml_file.name, xml_string))
            hashkey = hashlib.md5(xml_string).hexdigest()
            file_path = os.path.join(settings.MEDIA_ROOT, hashkey)
            if session.get('file_%s_hashkey' % file_index) != hashkey or not os.path.exists(file_path):
                session['file_%s_hashkey' % file_index] = hashkey

                with open(file_path, 'wb') as f:
                    f.write(xml_string)
                    session['file_%s_stored_name' % file_index] = file_path

        return xml_strings


class EnergyPerformanceCertificateView(TemplateView):
    template_name = "energy-performance-certificate.html"

    def get(self, request, *args, **kwargs):
        session = request.session
        if session.get('report_xml_name', False):
            return super(EnergyPerformanceCertificateView, self).get(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy('validator'))

    def get_context_data(self, **kwargs):
        context = super(EnergyPerformanceCertificateView, self).get_context_data(**kwargs)
        session = self.request.session
        file_name = session['report_xml_name']
        file_path = os.path.join(settings.MEDIA_ROOT, file_name)
        with open(file_path, 'rb') as xmlfile:
            report = XMLReport([(file_name, xmlfile.read())])

        espacios = zip(report.data.CondicionesFuncionamientoyOcupacion,
                       report.data.InstalacionesIluminacion.Espacios)

        context['report'] = report
        context['espacios'] = espacios

        return context


class EnergyPerformanceCertificatePDFView(EnergyPerformanceCertificateView):
    def render_to_response(self, context, **response_kwargs):
        session = self.request.session
        filename = '%s-%s' %(date.today().strftime('%Y%m%d'), session['file_0_name'])

        html = render_to_string(self.template_name, context)

        env = {
            'generation_date': context['report'].data.DatosDelCertificador.Fecha,
            'reference': context['report'].data.IdentificacionEdificio.ReferenciaCatastral
        }
        return render_to_pdf(html, '%s.pdf' % filename, env)


class SupplementaryReportView(EnergyPerformanceCertificateView):
    template_name = "supplementary-report.html"


class SupplementaryReportPDFView(EnergyPerformanceCertificatePDFView):
    template_name = "supplementary-report.html"
