#!/usr/bin/env python
# encoding: utf8

"""Definición de entidades para el análisis de informes de resultados en XML"""

import os
from visorxml.informes import InformeXML

TESTFILE = os.path.join(os.path.dirname(__file__), './static/validador/InformeTerciario_ejemplo.xml')
with open(TESTFILE) as xmlfile:
    informe = InformeXML(xmlfile.read())
    print informe.astext
    print informe.potenciamediailum
    print informe.emisionesdatos
