#!/usr/bin/env python
# encoding: utf8

# This is where you define the models of your application.
# This may be split into several modules in the same way as views.py

from flask.ext.wtf import Form
from flask.ext.uploads import UploadSet
from flask.ext.wtf.file import FileField, FileAllowed, FileRequired
from wtforms.fields import SubmitField
from wtforms.validators import Required

datafiles = UploadSet('datafiles', ('xml'.split()))

class XMLFileForm(Form):
    file = FileField(u'Archivo XML',
                     validators=[FileRequired(),
                                 FileAllowed(datafiles, u'¡Use archivos de informe con extensión .xml!')],
                     description=u'Archivo con un informe en formato XML.')
    submit = SubmitField(u'Validar')

