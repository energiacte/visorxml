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

import tempfile
import subprocess
import os
import random
import string
from django.conf import settings
from django.http import HttpResponse
from PyPDF2 import PdfFileWriter as PdfWriter
from PyPDF2 import PdfFileReader as PdfReader

def render_to_pdf(html, filename, xml_filename, env={}):
    "Render html file to pdf using the given filename and environment. Embed xml data if available"
    debug = settings.DEBUG
    debug = False
    if debug:
        return HttpResponse(html)

    fd_html, filename_html = tempfile.mkstemp()
    fd_pdf, filename_pdf = tempfile.mkstemp(suffix=".pdf")
    _, filename_pdf2 = tempfile.mkstemp(suffix=".pdf")
    os.close(fd_pdf)
    try:
        with open(fd_html, 'wb') as f:
            f.write(html.encode('utf8'))
        path = os.path.join(os.path.dirname(__file__), '..', 'webkit', 'webkit2pdf')

        try:
            if not debug:
                env['DISPLAY'] = ':1'
                # Fake empty SSL Confif file to be able to run phantomjs in Buster
                env['OPENSSL_CONF'] = os.path.abspath(
                    os.path.join(os.path.dirname(__file__), '..', 'webkit', 'openssl.cnf'))
        except KeyError:
            pass

        env.update(dict(os.environ)) # keep OS env vars, such as PATH

        cmd = [path,
               "-f", filename_html,
               "-o", filename_pdf,
               "--mediaroot", settings.MEDIA_ROOT,
               "--staticroot", settings.STATIC_ROOT,
               "--scriptname", settings.FORCE_SCRIPT_NAME or '']
        proc = subprocess.Popen(cmd, env=env)

        while True:
            proc.poll()
            if proc.returncode is not None:
                break

    except Exception as error:
        print(error)
    finally:
        os.remove(filename_html)


    if xml_filename:
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

    else:
        with open(filename_pdf, 'rb') as pdf:
            response = HttpResponse(pdf.read(), content_type='application/pdf')
            response['Content-Disposition'] = 'attachment;filename=%s' % filename

            pdf.close()

            os.remove(filename_pdf)
            os.remove(filename_pdf2)
            return response



def get_xml_string_from_pdf(file):
    "Detach xml data embedded in pdf file"
    pdf_name = random_name(ext=".pdf")
    xml_name = random_name()

    with open(pdf_name, "wb") as pdf:
        pdf.write(file.read())

    cmd = "pdfdetach %s -save 1 -o %s" % (pdf_name, xml_name)
    os.system(cmd)

    with open(xml_name, "rb") as xml:
        xml_string = xml.read()

    os.remove(pdf_name)
    os.remove(xml_name)

    return xml_string



def random_name(size=20, ext=".xml"):
    "Create random name with ascci letters and string with given size + extension"
    return "".join([random.choice(string.ascii_letters + string.digits) for n in range(size)]) + ext
