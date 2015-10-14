import tempfile
import subprocess
import os

from django.conf import settings
from django.http import HttpResponse


def render_to_pdf(html, filename, env={}):
    debug = settings.DEBUG
    debug = False
    if debug:
        return HttpResponse(html)

    fd_html, filename_html = tempfile.mkstemp()
    fd_pdf, filename_pdf = tempfile.mkstemp(suffix=".pdf")
    os.close(fd_pdf)
    try:
        os.write(fd_html, html.encode('utf8'))
        os.close(fd_html)
        path = os.path.join(os.path.dirname(__file__), '..', 'webkit', 'webkit2pdf')

        try:
            if not debug:
                env['DISPLAY'] = ':1'
        except KeyError:
            pass

        proc = subprocess.Popen([path, "-f", filename_html, "-o", filename_pdf], env=env)

        while True:
            proc.poll()
            if proc.returncode is not None:
                break
    finally:
        os.remove(filename_html)

    with open(filename_pdf, 'rb') as pdf:
        response = HttpResponse(pdf.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment;filename=%s' % filename
        return response
