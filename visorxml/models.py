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
    base = FileField(u'Archivo XML',
                     validators=[FileRequired(),
                                 FileAllowed(datafiles, u'¡Use archivos de informe con extensión .xml!')],
                     description=u'Informe de evaluación de la eficiencia energética en formato XML. Archivo base')
    mej1 = FileField(u'Archivo XML con medidas de mejora nº1',
                       validators=[FileAllowed(datafiles, u'¡Use archivos de informe con extensión .xml!')],
                       description=u'Medidas de mejora desde archivo XML.')
    mej2 = FileField(u'Archivo XML con medidas de mejora nº2',
                       validators=[FileAllowed(datafiles, u'¡Use archivos de informe con extensión .xml!')],
                       description=u'Medidas de mejora desde archivo XML.')
    mej3 = FileField(u'Archivo XML con medidas de mejora nº3',
                       validators=[FileAllowed(datafiles, u'¡Use archivos de informe con extensión .xml!')],
                       description=u'Medidas de mejora desde archivo XML.')
    submit = SubmitField(u'Validar')

