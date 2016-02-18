#!/usr/bin/env python
#encoding:utf8
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

import tempfile
import subprocess
import os

from django.conf import settings
from django.http import HttpResponse
from PyPDF2 import PdfFileWriter as PdfWriter
from PyPDF2 import PdfFileReader as PdfReader

def render_to_pdf(html, filename, xml_filename, env={}):
    debug = settings.DEBUG
    debug = False
    if debug:
        return HttpResponse(html)

    fd_html, filename_html = tempfile.mkstemp()
    fd_pdf, filename_pdf = tempfile.mkstemp(suffix=".pdf")
    fd_pdf2, filename_pdf2 = tempfile.mkstemp(suffix=".pdf")
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
        reader = PdfReader(pdf, strict=False)
        writer = PdfWriter()
        writer.appendPagesFromReader(reader)
        with open(xml_filename, "rb") as xml:
            writer.addAttachment("certificado.xml",xml.read())
            with open(filename_pdf2, "wb") as out:
                writer.write(out)
                out.close()
            pdf.close()

    with open(filename_pdf2, 'rb') as pdf:
        response = HttpResponse(pdf.read(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment;filename=%s' % filename

        pdf.close()
        os.remove(filename_pdf)
        os.remove(filename_pdf2)
        return response
