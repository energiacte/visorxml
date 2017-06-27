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

"""Definición de entidades para el análisis de informes de resultados en XML"""
import os.path
import numbers
from collections import OrderedDict, defaultdict
from decimal import Decimal
import string
import random
from django.conf import settings
import lxml.etree
from lxml.html.clean import clean_html
import base64
import io
import PIL.Image
import datetime

XSDPATH = settings.XSDPATH_MINI
SERVICIOS = 'Global Calefaccion Refrigeracion ACS Iluminacion'.split()

class Bunch(OrderedDict):
    """Contenedor genérico"""
    def __init__(self, *args, **kwds):
        super(Bunch, self).__init__()

    def __str__(self):
        state = ['%s=%s' % (attribute, value)
                 for (attribute, value) in self.__dict__.items()
                 if not attribute.startswith('_OrderedDict')]
        return '\n'.join(state)

def random_name(size=20, ext=".xml"):
    return "".join([random.choice(string.ascii_letters + string.digits) for n in range(size)]) + ext

# Return true if node can be deleted
def delete_node(element, value):
    if value != "":
        return False

    base =  element.split(".")[0]
    if base in "DatosDelCertificador|IdentificacionEdificio|DatosGeneralesyGeometria".split("|"):
        return False

    return not "Global" in element


class XMLReport(object):
    def __init__(self, xml_strings):
        '''
        xml_strings es una lista de tuplas. Las tuplas son de la forma (nombre_fichero, contenido)
        '''
        self.xml_parser = lxml.etree.XMLParser(resolve_entities=False, remove_blank_text=True, ns_clean=True, remove_comments=True, recover=True, encoding='UTF-8')

        self.xmlschema = None
        self.errors = {
            'extra_files_errors': None,
            'validation_errors': [],
            'info': []
        }
        self._data = None
        self._xml_strings = xml_strings
        self.xmltree = self.get_xmltree()
        if self.xmltree is not None:
            self._parsetree()
            self.validate()

    def save_to_file(self, filename=None):
        xml_string = lxml.etree.tostring(self.xmltree, pretty_print=True, xml_declaration = True, encoding='UTF-8')
        if filename is None:
            filename = random_name()

        path = settings.MEDIA_ROOT

        with open(os.path.join(path, filename), 'wb') as output_file:
            output_file.write(xml_string)

        return filename

    def update_procedimiento(self):
        """Update field procedimiento"""
        procedimiento = self.xmltree.find('./IdentificacionEdificio/Procedimiento')
        try: # revisar procedimientos...
            if procedimiento is not None and '[Generador VisorXML 1.0]' not in procedimiento.text:
                procedimiento.text += ' + [Generador VisorXML 1.0]'
        except:
                procedimiento.text = '[Generador VisorXML 1.0]'

        fecha = self.xmltree.find('./DatosDelCertificador/Fecha')
        fecha.text  = datetime.date.today().strftime("%d/%m/%Y")

    def remove_node(self, node):
        node = self.xmltree.find(node)
        if node is not None:
            node.getparent().remove(node)


    def update_element(self, element, value):
        path = './%s' % '/'.join(element.split('.'))
        try:
            self.xmltree.find(path).text = value
            # Delete "Iluminacion" node in Tipo not terciario
            if element == "IdentificacionEdificio.TipoDeEdificio" and value in "ViviendaUnifamiliar|BloqueDeViviendaCompleto|ViviendaIndividualEnBloque".split("|"):
                self.remove_node('./Consumo/EnergiaPrimariaNoRenovable/Iluminacion')
                self.remove_node('./EmisionesCO2/Iluminacion')
                self.remove_node('./Calificacion/EmisionesCO2/Iluminacion')
                self.remove_node('./Calificacion/EnergiaPrimariaNoRenovable/Iluminacion')

            if delete_node(element, value):
                self.remove_node(path)

            self.update_procedimiento()
            base_xml_filename, base_xml_string = self._xml_strings[0]
            self.save_to_file(base_xml_filename)

        except AttributeError: # node doesnt exist
            parent = self.xmltree.find("/".join(path.split("/")[:-1]))
            node = lxml.etree.Element(path.split("/")[-1])
            node.text = value
            parent.append(node)
            self.update_procedimiento()
            self.save_to_file(self._xml_strings[0][0])


    def get_xmltree(self):
        # Get the base XML data
        base_xml_filename, base_xml_string = self._xml_strings[0]
        try:
            base_xml_tree = lxml.etree.XML(base_xml_string, parser=self.xml_parser)
            return base_xml_tree
        except lxml.etree.XMLSyntaxError:
            error = (None, 'El archivo "<strong>%s</strong>" no está bien formado' % base_xml_filename)
            self.errors['validation_errors'].append(error)
            return None

    def astext(self, tree, path):
        element = tree.find(path)
        if element is None or not element.text:
            return ''
        txt = element.text
        if txt and txt.startswith('data:text/html,'):
            txt = txt.lstrip('data:text/html,').strip()
            txt = clean_html(txt) if txt else ''
        return txt

    def asint(self, tree, path):
        """Value conversion with decimal separator repair"""
        infolist = self.errors['info']
        element = tree.find(path)
        if element is None or not element.text:
            return None
        etext = element.text
        # Corrección de separadores decimales / valores decimales
        for sepchar in ['.', ',']:
            if sepchar in etext:
                infolist.append(('AVISO', 'Corregido %s a entero en %s' % (etext, path), ''))
                etext = etext.split(sepchar)[0]
                element.text = etext
        try:
            val = int(etext)
        except ValueError:
            val = etext
            infolist.append(('ERROR', 'Valor entero %s incorrecto en %s' % (etext, path), ''))
        return val

    def asfloat(self, tree, path, prec=None):
        """Value conversion with decimal separator repair and precision control"""
        infolist = self.errors['info']
        element = tree.find(path)
        if element is None or not element.text:
            return None
        etext = element.text
        try:
            val = float(etext)
        except ValueError:
            # Corrección de comas
            etext1 = etext.replace(',', '.')
            try:
                val = float(etext1)
                element.text = etext1
                infolist.append(('AVISO', 'Corregida coma en valor decimal %s en %s' % (etext, path), ''))
            except ValueError:
                val = etext
                infolist.append(('ERROR', 'Valor decimal %s incorrecto en %s' % (etext, path), ''))
        # Corrección de dígitos decimales
        if (prec is not None) and isinstance(prec, int):
            if element.text[::-1].find('.') > prec:
                val = round(val, prec)
                element.text = "{1:.{0}f}".format(prec, val)
                infolist.append(('AVISO', 'Corregido %s a %i posiciones decimales en %s' % (etext, prec, path), ''))
        return val


    @property
    def version(self):
        """Version del esquema usado en el informe XML"""
        return self.xmltree.get('version')

    @property
    def data(self):
        """Objeto etree correspondiente al informe XML"""
        if self._data is None:
            self._data = self._parsetree()
        return self._data

    def _parsetree(self):
        data = Bunch()

        data.DatosDelCertificador = self.get_datos_certificador()
        data.IdentificacionEdificio = self.get_identificacion_edificio()
        data.DatosGeneralesyGeometria = self.get_datos_generales_y_geometria()
        data.Demanda = self.get_demanda()
        data.Consumo = self.get_consumo()
        data.EmisionesCO2 = self.get_emisiones_co2()
        data.Calificacion = self.get_calificacion()
 
        return data



    def get_datos_certificador(self):
        datos_certificador = Bunch()

        for attr in ['NombreyApellidos', 'NIF', 'RazonSocial', 'NIFEntidad', 'Domicilio',
                     'Municipio', 'CodigoPostal', 'Provincia', 'ComunidadAutonoma',
                     'Email', 'Telefono', 'Titulacion', 'Fecha']:
            setattr(datos_certificador, attr, self.astext(self.xmltree, './DatosDelCertificador/%s' % attr))

        return datos_certificador

    def get_identificacion_edificio(self):
        identificacion_edificio = Bunch()

        for attr in ['NombreDelEdificio', 'Direccion',
                     'Municipio', 'CodigoPostal', 'Provincia', 'ComunidadAutonoma',
                     'ZonaClimatica', 'AnoConstruccion', 'ReferenciaCatastral',
                     'TipoDeEdificio', 'NormativaVigente', 'Procedimiento',
                     'AlcanceInformacionXML']:
            setattr(identificacion_edificio, attr, self.astext(self.xmltree, './IdentificacionEdificio/%s' % attr))
        if 'ninguno' in identificacion_edificio.ReferenciaCatastral:
            identificacion_edificio.ReferenciaCatastral = '-'
        if 'Seleccione de la lista' in identificacion_edificio.NormativaVigente:
            identificacion_edificio.NormativaVigente = '-'

        return identificacion_edificio

    def get_datos_generales_y_geometria(self):
        datos_generales_y_geometria = Bunch()

        setattr(datos_generales_y_geometria, 'SuperficieHabitable',
                self.asfloat(self.xmltree, './DatosGeneralesyGeometria/SuperficieHabitable', prec=2))

        return datos_generales_y_geometria


    def get_demanda(self):
        demanda = Bunch()

        demanda.EdificioObjeto = Bunch()
        for attr in ['Global', 'Calefaccion', 'Refrigeracion', 'ACS']:
            setattr(demanda.EdificioObjeto, attr,
                    self.asfloat(self.xmltree, './Demanda/EdificioObjeto/%s' % attr, prec=2))

        demanda.EdificioDeReferencia = Bunch()
        for attr in ['Global', 'Calefaccion', 'Refrigeracion', 'ACS',
                     'Conjunta', 'Calefaccion08', 'Refrigeracion08',
                     'Conjunta08']:
            setattr(demanda.EdificioDeReferencia, attr,
                    self.asfloat(self.xmltree, './Demanda/EdificioDeReferencia/%s' % attr, prec=2))

        demanda.Exigencias = Bunch()
        for attr in ['LimiteCalefaccionVivienda', 'LimiteRefrigeracionVivienda',
                     'LimiteAhorroOtrosUsos']:
            setattr(demanda.Exigencias, attr,
                    self.asfloat(self.xmltree, './Demanda/Exigencias/%s' % attr, prec=2))

        return demanda

    def get_consumo(self):
        consumo = Bunch()
        consumo.EnergiaPrimariaNoRenovable = self.get_energia_primaria_no_renovable()

        return consumo


    def get_energia_primaria_no_renovable(self):
        energia_primaria_no_renovable = Bunch()

        for servicio in SERVICIOS:
            value = './Consumo/EnergiaPrimariaNoRenovable/%s' % servicio
            setattr(energia_primaria_no_renovable, servicio,
                    self.asfloat(self.xmltree, value, prec=2))

        return energia_primaria_no_renovable

    def get_emisiones_co2(self):
        emisiones_co2 = Bunch()

        for servicio in SERVICIOS + 'ConsumoElectrico ConsumoOtros TotalConsumoElectrico TotalConsumoOtros'.split():
            setattr(emisiones_co2, servicio,
                    self.asfloat(self.xmltree, './EmisionesCO2/%s' % servicio, prec=2))

        return emisiones_co2

    def get_calificacion(self):
        calificacion = Bunch()

        calificacion.Demanda = self.get_calificacion_demanda()
        calificacion.EnergiaPrimariaNoRenovable = self.get_calificacion_energia_primaria_no_renovable()
        calificacion.EmisionesCO2 = self.get_calificacion_emisiones_co2()

        return calificacion

    def get_calificacion_demanda(self):
        calificacion_demanda = Bunch()
        calificacion_demanda.Calefaccion = self.astext(self.xmltree, './Calificacion/Demanda/Calefaccion')
        calificacion_demanda.Refrigeracion = self.astext(self.xmltree, './Calificacion/Demanda/Refrigeracion')

        return calificacion_demanda

    def get_calificacion_energia_primaria_no_renovable(self):
        calificacion_energia_primaria_no_renovable = Bunch()


        calificacion_energia_primaria_no_renovable.Global = self.astext(self.xmltree,
                                                                './Calificacion/EnergiaPrimariaNoRenovable/Global')
        calificacion_energia_primaria_no_renovable.Calefaccion = self.astext(self.xmltree,
                                                                './Calificacion/EnergiaPrimariaNoRenovable/Calefaccion')
        calificacion_energia_primaria_no_renovable.Refrigeracion = self.astext(self.xmltree,
                                                                './Calificacion/EnergiaPrimariaNoRenovable/Refrigeracion')
        calificacion_energia_primaria_no_renovable.ACS = self.astext(self.xmltree,
                                                                './Calificacion/EnergiaPrimariaNoRenovable/ACS')
        calificacion_energia_primaria_no_renovable.Iluminacion = self.astext(self.xmltree,
                                                                './Calificacion/EnergiaPrimariaNoRenovable/Iluminacion')

        return calificacion_energia_primaria_no_renovable

    def get_calificacion_emisiones_co2(self):
        calificacion_emisiones_co2 = Bunch()

        escala = self.xmltree.find('./Calificacion/EmisionesCO2/EscalaGlobal')
        if escala is not None:
            escala_global = Bunch()
            for nivel in NIVELESESCALA:
                setattr(escala_global, nivel, self.asfloat(escala, './%s' % nivel, prec=2))
            calificacion_emisiones_co2.EscalaGlobal = escala_global

        calificacion_emisiones_co2.Global = self.astext(self.xmltree, './Calificacion/EmisionesCO2/Global')
        calificacion_emisiones_co2.Calefaccion = self.astext(self.xmltree, './Calificacion/EmisionesCO2/Calefaccion')
        calificacion_emisiones_co2.Refrigeracion = self.astext(self.xmltree, './Calificacion/EmisionesCO2/Refrigeracion')
        calificacion_emisiones_co2.ACS = self.astext(self.xmltree, './Calificacion/EmisionesCO2/ACS')
        calificacion_emisiones_co2.Iluminacion = self.astext(self.xmltree, './Calificacion/EmisionesCO2/Iluminacion')

        return calificacion_emisiones_co2


    def get_datos_personalizados(self):
        txt = self.astext(self.xmltree, './DatosPersonalizados')
        return txt


    def validate(self):
        """Valida el informe XML según el esquema XSD"""
        # http://lxml.de/validation.html
        self.xmlschema = lxml.etree.XMLSchema(lxml.etree.parse(open(XSDPATH, encoding='UTF-8')))
        self.xmlschema.validate(self.xmltree)

        errors = [(error.line, error.message) for error in self.xmlschema.error_log]
        self.errors['validation_errors'] += errors


with open(settings.MINI_XML_PATH) as f:
    BASE_XML_MINI = f.read()
