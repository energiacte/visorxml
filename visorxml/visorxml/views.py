import hashlib
import logging
import os.path

from django.conf import settings
from django.core.urlresolvers import reverse_lazy
from django.http import HttpResponseRedirect
from django.views.generic import TemplateView, FormView

from .forms import XMLFileForm
from .reports import XMLReport, analize


logger = logging.getLogger(__name__)


class HomeView(TemplateView):
    template_name = "home.html"


class ValidatorView(FormView):
    template_name = "validator.html"
    form_class = XMLFileForm
    success_url = reverse_lazy('validator')

    def form_valid(self, form):
        session = self.request.session
        uploaded_file = self.request.FILES['base']
        xmldata = uploaded_file.read()
        session['base_name'] = uploaded_file.name
        hashkey = hashlib.md5(xmldata).hexdigest()
        if session.get('base_hashkey') != hashkey:  # or not os.path.exists(datafiles.path(session['base_storedname'])):
            session['base_hashkey'] = hashkey

            file_path = os.path.join(settings.MEDIA_ROOT, hashkey)
            with open(file_path, 'wb') as f:
                f.write(xmldata)
                session['base_stored_name'] = file_path
        report = XMLReport(xmldata)

        validation_data = {
            'base_validation_errors': report.validate(),
            'base_info': analize(report)
        }

        has_errors = 'ERROR' if validation_data['base_validation_errors'] else 'OK'
        logger.info('%s, %s, %s\n' % (session['base_name'],
                                      hashkey,
                                      has_errors))

        context_data = self.get_context_data(form=form)
        context_data['validation_data'] = validation_data
        return self.render_to_response(context_data)


class ViewerView(TemplateView):
    template_name = "viewer.html"

    def get(self, request, *args, **kwargs):
        session = request.session
        if session.get('base_stored_name', False):
            return super(ViewerView, self).get(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse_lazy('validator'))

    def get_context_data(self, **kwargs):
        context = super(ViewerView, self).get_context_data(**kwargs)
        context['modo'] = 'data'

        session = self.request.session
        file_path = os.path.join(settings.MEDIA_ROOT, session['base_hashkey'])
        with open(file_path, 'rb') as xmlfile:
            context['report'] = XMLReport(xmlfile.read())

        return context


class GetPDFView(TemplateView):
    pass
