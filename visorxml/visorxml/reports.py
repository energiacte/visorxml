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
from .imgb64 import base64check
import datetime

XSDPATH2 = settings.XSDPATH2
XSDPATH1 = settings.XSDPATH1

VECTORES = ('GasNatural GasoleoC GLP Carbon BiomasaPellet BiomasaOtros '
            'ElectricidadPeninsular ElectricidadBaleares '
            'ElectricidadCanarias ElectricidadCeutayMelilla Biocarburante').split()
SERVICIOS = 'Global Calefaccion Refrigeracion ACS Iluminacion'.split()
NIVELESESCALA = 'A B C D E F'.split()
ALERTINT = 9999999999
ALERT = ALERTINT / 100


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

class XMLReport(object):
    def __init__(self, xml_strings):
        '''
        xml_strings es una lista de tuplas. Las tuplas son de la forma (nombre_fichero, contenido)
        '''
        self.xml_parser = lxml.etree.XMLParser(resolve_entities=False,  # no sustituye unicode a entidades
                                               remove_blank_text=True,
                                               ns_clean=True,  # limpia namespaces
                                               remove_comments=True,
                                               recover=True,
                                               encoding='UTF-8')

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
            self.calculate_improvement_measures()
            self._parsetree()
            self.validate()
            self.analize()

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
        if procedimiento is not None and 'VisorXML' not in procedimiento.text:
            procedimiento.text += ' + [VisorXML%s]' % settings.VERSION

    def update_element(self, element, value):
        path = './%s' % '/'.join(element.split('.'))
        try:
            if (
                (path.split("/")[1] == "MedidasDeMejora" and path.split("/")[-1] == "Descripcion") or
                (path.split("/")[1] == "PruebasComprobacionesInspecciones" and path.split("/")[-1] == "Datos") or
                (path.split("/")[1] == "DatosPersonalizados" and path.split("/")[-1] == "SolucionesSingulares")
                ):

                self.xmltree.find(path).text = lxml.etree.CDATA(value)

            else:
                self.xmltree.find(path).text = value
            self.update_procedimiento()
            base_xml_filename, base_xml_string = self._xml_strings[0]
            self.save_to_file(base_xml_filename)

        except AttributeError:
            if path == './DatosPersonalizados/SolucionesSingulares':
                self.add_singular_solutions(value)
            elif path == "./PruebasComprobacionesInspecciones/Visita[1]/FechaVisita":
                self.new_visit(date = value)
            elif path == "./PruebasComprobacionesInspecciones/Visita[1]/Datos":
                self.new_visit(text=value)

    def update_image(self, section, value):
        path = './DatosGeneralesyGeometria/%s' % section

        element = self.xmltree.find(path)
        if element is None:
            parent = self.xmltree.find('./DatosGeneralesyGeometria')
            element = lxml.etree.SubElement(parent, section)

        element.text = lxml.etree.CDATA('data:image/png;base64,%s' % value.decode("utf-8"))

        self.update_procedimiento()

        base_xml_filename, base_xml_string = self._xml_strings[0]
        self.save_to_file(base_xml_filename)

    def get_XML_value(self, xml_tree, path, default_value=0):
        try:
            return xml_tree.find(path).text
        except AttributeError:
            return default_value

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
            return '-'
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

    def calculate_improvement_measures(self):
        # Loop over the xml strings list, except the first element, which is the base file
        for improvement_xml_filename, improvement_xml_string in self._xml_strings[1:]:
            try:
                improvement_xml_tree = lxml.etree.XML(improvement_xml_string, parser=self.xml_parser)
            except lxml.etree.XMLSyntaxError:
                error = (None, 'El archivo "<strong>%s</strong>" no está correctamente formateado' % improvement_xml_filename)
                self.errors['validation_errors'].append(error)
                continue

            improvement_xml_fragment = lxml.etree.Element('Medida')

            lxml.etree.SubElement(improvement_xml_fragment, 'Nombre').text = 'NOMBRE'
            lxml.etree.SubElement(improvement_xml_fragment, 'Descripcion').text = 'DESCRIPCION'
            lxml.etree.SubElement(improvement_xml_fragment, 'CosteEstimado').text = 'COSTE ESTIMADO'
            lxml.etree.SubElement(improvement_xml_fragment, 'OtrosDatos').text = 'OTROS DATOS'

            self.check_building_properties(improvement_xml_filename,
                                           improvement_xml_tree)

            self.improvement_fragment_add_demanda(improvement_xml_tree, improvement_xml_fragment)
            self.improvement_fragment_add_calificacion_demanda(improvement_xml_tree, improvement_xml_fragment)
            self.improvement_fragment_add_energia_final(improvement_xml_tree, improvement_xml_fragment)
            self.improvement_fragment_add_energia_primaria_no_renovable(improvement_xml_tree, improvement_xml_fragment)
            self.improvement_fragment_add_calificacion_energia_primaria_no_renovable(improvement_xml_tree, improvement_xml_fragment)
            self.improvement_fragment_add_emisiones_co2(improvement_xml_tree, improvement_xml_fragment)
            self.improvement_fragment_add_calificacion_emisiones_co2(improvement_xml_tree, improvement_xml_fragment)

            self.append_improvement_fragment(improvement_xml_fragment)

    def check_building_properties(self, improvement_xml_filename, improvement_xml_tree):
        attrs_to_check = {
            './IdentificacionEdificio/Direccion': 'Direccion',
            './IdentificacionEdificio/Municipio': 'Municipio',
            './IdentificacionEdificio/CodigoPostal': 'CodigoPostal',
            './IdentificacionEdificio/Provincia': 'Provincia',
            './IdentificacionEdificio/ComunidadAutonoma': 'ComunidadAutonoma',
            './IdentificacionEdificio/ZonaClimatica': 'ZonaClimatica',
            './IdentificacionEdificio/ReferenciaCatastral': 'ReferenciaCatastral'
        }

        errors = []
        for attr, attr_name in attrs_to_check.items():
            main_tree_value = self.xmltree.find(attr).text
            value = improvement_xml_tree.find(attr).text
            if main_tree_value != value:
                errors.append('"%s" no coincide con el archivo base' % attr_name)

        if len(errors) > 0:
            if self.errors['extra_files_errors'] is None:
                self.errors['extra_files_errors'] = {}
            self.errors['extra_files_errors'][improvement_xml_filename] = errors

    def improvement_fragment_add_demanda(self, improvement_xml_tree, improvement_xml_fragment):
        base_demanda = Decimal(self.get_XML_value(self.xmltree,
                                                  './Demanda/EdificioObjeto/Global'))
        improvement_demanda = Decimal(self.get_XML_value(improvement_xml_tree,
                                                         './Demanda/EdificioObjeto/Global'))
        diff = improvement_demanda - base_demanda

        improvement_calefaccion = Decimal(self.get_XML_value(improvement_xml_tree,
                                                             './Demanda/EdificioObjeto/Calefaccion'))
        improvement_refrigeracion = Decimal(self.get_XML_value(improvement_xml_tree,
                                                               './Demanda/EdificioObjeto/Refrigeracion'))

        element = lxml.etree.SubElement(improvement_xml_fragment, 'Demanda')
        lxml.etree.SubElement(element, 'Global').text = '%s' % improvement_demanda
        lxml.etree.SubElement(element, 'GlobalDiferenciaSituacionInicial').text = '%s' % diff
        lxml.etree.SubElement(element, 'Calefaccion').text = '%s' % improvement_calefaccion
        lxml.etree.SubElement(element, 'Refrigeracion').text = '%s' % improvement_refrigeracion

    def improvement_fragment_add_calificacion_demanda(self, improvement_xml_tree, improvement_xml_fragment):
        calefaccion = self.get_XML_value(improvement_xml_tree, './Calificacion/Demanda/Calefaccion')
        refrigeracion = self.get_XML_value(improvement_xml_tree, './Calificacion/Demanda/Refrigeracion')

        element = lxml.etree.SubElement(improvement_xml_fragment, 'CalificacionDemanda')
        if calefaccion:
            lxml.etree.SubElement(element, 'Calefaccion').text = '%s' % calefaccion
        if refrigeracion:
            lxml.etree.SubElement(element, 'Refrigeracion').text = '%s' % refrigeracion

    def improvement_fragment_add_energia_final(self, improvement_xml_tree, improvement_xml_fragment):
        servicios = defaultdict(int)
        for vec in VECTORES:
            for servicio in SERVICIOS:
                servicios[servicio] += Decimal(self.get_XML_value(improvement_xml_tree,
                                                                  './Consumo/EnergiaFinalVectores/%s/%s' % (vec, servicio)))

        # Si no hay Global definido (vivienda) sumamos resto de servicios
        if not servicios.get('Global', None):
            servicios['Global'] = sum(servicios.get(servicio, 0) for servicio in servicios if servicio.strip() is not 'Global')

        element = lxml.etree.SubElement(improvement_xml_fragment, 'EnergiaFinal')
        for servicio, valor in servicios.items():
            lxml.etree.SubElement(element, servicio).text = '%s' % valor

    def improvement_fragment_add_energia_primaria_no_renovable(self,
                                                               improvement_xml_tree,
                                                               improvement_xml_fragment):
        element = lxml.etree.SubElement(improvement_xml_fragment, 'EnergiaPrimariaNoRenovable')

        energia_global = Decimal(self.get_XML_value(improvement_xml_tree, './Consumo/EnergiaPrimariaNoRenovable/Global'))
        energia_global_base = Decimal(self.get_XML_value(self.xmltree, './Consumo/EnergiaPrimariaNoRenovable/Global'))
        energia_calefaccion = Decimal(self.get_XML_value(improvement_xml_tree, './Consumo/EnergiaPrimariaNoRenovable/Calefaccion'))
        energia_refrigeracion = Decimal(self.get_XML_value(improvement_xml_tree, './Consumo/EnergiaPrimariaNoRenovable/Refrigeracion'))
        energia_acs = Decimal(self.get_XML_value(improvement_xml_tree, './Consumo/EnergiaPrimariaNoRenovable/ACS'))
        energia_iluminacion = Decimal(self.get_XML_value(improvement_xml_tree, './Consumo/EnergiaPrimariaNoRenovable/Iluminacion'))

        diff = energia_global - energia_global_base

        lxml.etree.SubElement(element, 'Global').text = '%s' % energia_global
        lxml.etree.SubElement(element, 'GlobalDiferenciaSituacionInicial').text = '%s' % diff
        lxml.etree.SubElement(element, 'Calefaccion').text = '%s' % energia_calefaccion
        lxml.etree.SubElement(element, 'Refrigeracion').text = '%s' % energia_refrigeracion
        lxml.etree.SubElement(element, 'ACS').text = '%s' % energia_acs
        lxml.etree.SubElement(element, 'Iluminacion').text = '%s' % energia_iluminacion

    def improvement_fragment_add_calificacion_energia_primaria_no_renovable(self,
                                                                            improvement_xml_tree,
                                                                            improvement_xml_fragment):
        element = lxml.etree.SubElement(improvement_xml_fragment, 'CalificacionEnergiaPrimariaNoRenovable')

        energia_global = self.get_XML_value(improvement_xml_tree, './Calificacion/EnergiaPrimariaNoRenovable/Global', None)
        energia_calefaccion = self.get_XML_value(improvement_xml_tree, './Calificacion/EnergiaPrimariaNoRenovable/Calefaccion', None)
        energia_refrigeracion = self.get_XML_value(improvement_xml_tree, './Calificacion/EnergiaPrimariaNoRenovable/Refrigeracion', None)
        energia_acs = self.get_XML_value(improvement_xml_tree, './Calificacion/EnergiaPrimariaNoRenovable/ACS', None)
        energia_iluminacion = self.get_XML_value(improvement_xml_tree, './Calificacion/EnergiaPrimariaNoRenovable/Iluminacion', None)

        if energia_global:
            lxml.etree.SubElement(element, 'Global').text = '%s' % energia_global
        if energia_calefaccion:
            lxml.etree.SubElement(element, 'Calefaccion').text = '%s' % energia_calefaccion
        if energia_refrigeracion:
            lxml.etree.SubElement(element, 'Refrigeracion').text = '%s' % energia_refrigeracion
        if energia_acs:
            lxml.etree.SubElement(element, 'ACS').text = '%s' % energia_acs
        if energia_iluminacion:
            lxml.etree.SubElement(element, 'Iluminacion').text = energia_iluminacion

    def improvement_fragment_add_emisiones_co2(self, improvement_xml_tree, improvement_xml_fragment):
        element = lxml.etree.SubElement(improvement_xml_fragment, 'EmisionesCO2')

        emisiones_global = Decimal(self.get_XML_value(improvement_xml_tree, './EmisionesCO2/Global'))
        emisiones_global_base = Decimal(self.get_XML_value(self.xmltree, './EmisionesCO2/Global'))
        emisiones_calefaccion = Decimal(self.get_XML_value(improvement_xml_tree, './EmisionesCO2/Calefaccion'))
        emisiones_refrigeracion = Decimal(self.get_XML_value(improvement_xml_tree, './EmisionesCO2/Refrigeracion'))
        emisiones_acs = Decimal(self.get_XML_value(improvement_xml_tree, './EmisionesCO2/ACS'))
        emisiones_iluminacion = Decimal(self.get_XML_value(improvement_xml_tree, './EmisionesCO2/Iluminacion'))
        diff = emisiones_global - emisiones_global_base

        lxml.etree.SubElement(element, 'Global').text = '%s' % emisiones_global
        lxml.etree.SubElement(element, 'GlobalDiferenciaSituacionInicial').text = '%s' % diff
        lxml.etree.SubElement(element, 'Calefaccion').text = '%s' % emisiones_calefaccion
        lxml.etree.SubElement(element, 'Refrigeracion').text = '%s' % emisiones_refrigeracion
        lxml.etree.SubElement(element, 'ACS').text = '%s' % emisiones_acs
        lxml.etree.SubElement(element, 'Iluminacion').text = '%s' % emisiones_iluminacion

    def improvement_fragment_add_calificacion_emisiones_co2(self, improvement_xml_tree, improvement_xml_fragment):
        element = lxml.etree.SubElement(improvement_xml_fragment, 'CalificacionEmisionesCO2')

        emisiones_global = self.get_XML_value(improvement_xml_tree, './Calificacion/EmisionesCO2/Global', None)
        emisiones_calefaccion = self.get_XML_value(improvement_xml_tree, './Calificacion/EmisionesCO2/Calefaccion', None)
        emisiones_refrigeracion = self.get_XML_value(improvement_xml_tree, './Calificacion/EmisionesCO2/Refrigeracion', None)
        emisiones_acs = self.get_XML_value(improvement_xml_tree, './Calificacion/EmisionesCO2/ACS', None)
        emisiones_iluminacion = self.get_XML_value(improvement_xml_tree, './Calificacion/EmisionesCO2/Iluminacion', None)

        if emisiones_global:
            lxml.etree.SubElement(element, 'Global').text = '%s' % emisiones_global
        if emisiones_calefaccion:
            lxml.etree.SubElement(element, 'Calefaccion').text = '%s' % emisiones_calefaccion
        if emisiones_refrigeracion:
            lxml.etree.SubElement(element, 'Refrigeracion').text = '%s' % emisiones_refrigeracion
        if emisiones_acs:
            lxml.etree.SubElement(element, 'ACS').text = '%s' % emisiones_acs
        if emisiones_iluminacion:
            lxml.etree.SubElement(element, 'Iluminacion').text = '%s' % emisiones_iluminacion

    def append_improvement_fragment(self, improvement_xml_fragment):
        if improvement_xml_fragment is not None:
            improvement_measures = self.xmltree.find('./MedidasDeMejora')
            if improvement_measures is None:
                improvement_measures = lxml.etree.SubElement(self.xmltree, 'MedidasDeMejora')
            improvement_measures.append(improvement_xml_fragment)

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

    @property
    def esvivienda(self):
        """Es un edificio de uso Vivienda?"""
        try:
            return 'Vivienda' in self.data.IdentificacionEdificio.TipoDeEdificio
        except:
            return False

    def _parsetree(self):
        data = Bunch()

        data.DatosDelCertificador = self.get_datos_certificador()
        data.IdentificacionEdificio = self.get_identificacion_edificio()
        data.DatosGeneralesyGeometria = self.get_datos_generales_y_geometria()
        data.DatosEnvolventeTermica = self.get_datos_envolvente_termica()
        data.InstalacionesTermicas = self.get_instalaciones_termicas()
        data.CondicionesFuncionamientoyOcupacion, data.superficies = self.get_condiciones_funcionamiento_y_ocupacion()
        data.InstalacionesIluminacion = self.get_instalaciones_iluminacion()
        data.EnergiasRenovables = self.get_energias_renovables()
        data.Demanda = self.get_demanda()
        data.Consumo = self.get_consumo()
        data.EmisionesCO2 = self.get_emisiones_co2()
        data.Calificacion = self.get_calificacion()
        data.MedidasDeMejora = self.get_medidas_de_mejora()
        data.PruebasComprobacionesInspecciones = self.get_pruebas_comprobaciones_inspecciones()
        data.DatosPersonalizados = self.get_datos_personalizados()

        return data

    def delete_element(self, type, index):
        change = False
        if type == "measure":
            measures = self.xmltree.find('./MedidasDeMejora')
            measures.remove(measures[int(index)])
            if len(measures) == 0:
                measures.getparent().remove(measures)

            change = True

        elif type == "visit":
            visits = self.xmltree.find('./PruebasComprobacionesInspecciones')
            visits.remove(visits[int(index)])
            if len(visits) == 0:
                visits.getparent().remove(visits)

            change = True

        elif type == "solutions":
            singular_solutions = self.xmltree.find('./DatosPersonalizados/SolucionesSingulares')
            if singular_solutions is not None:
                datos = self.xmltree.find('./DatosPersonalizados')
                datos.getparent().remove(datos)
                change = True

        if change:
            self.save_to_file(self._xml_strings[0][0])


    def add_singular_solutions(self, text="DESCRIPCIÓN"):
        if self.xmltree.find('./DatosPersonalizados/SolucionesSingulares') is None:
            new_node = lxml.etree.Element("SolucionesSingulares")
            new_node.text = lxml.etree.CDATA(text)
            datos_p = self.xmltree.find('./DatosPersonalizados')

            #if ./DatosPersonalizados doesn't exist, create it.
            if not datos_p:
                datos_p = lxml.etree.Element("DatosPersonalizados")
                self.xmltree.find(".").append(datos_p)

            datos_p.append(new_node)
            self.update_procedimiento()
            self.save_to_file(self._xml_strings[0][0])

    def has_annex_v(self):
        return self.xmltree.find('./DatosPersonalizados/SolucionesSingulares') is not None

    def get_annex_v(self):
        return self.xmltree.find('./DatosPersonalizados/SolucionesSingulares').text


    def new_visit(self, date = datetime.date.today().strftime("%d/%m/%Y"), text = ""):
        visits = self.xmltree.find('./PruebasComprobacionesInspecciones')
        if visits == None:
           visits = lxml.etree.Element("PruebasComprobacionesInspecciones")
           self.xmltree.find(".").append(visits)

        new_visit = lxml.etree.Element("Visita")
        lxml.etree.SubElement(new_visit, 'FechaVisita').text = date
        lxml.etree.SubElement(new_visit, 'Datos').text = lxml.etree.CDATA(text)
        visits.append(new_visit)
        self.save_to_file(self._xml_strings[0][0])

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

        datos_generales_y_geometria.NumeroDePlantasSobreRasante = self.astext(
            self.xmltree,
            './DatosGeneralesyGeometria/NumeroDePlantasSobreRasante')
        img = self.xmltree.find('./DatosGeneralesyGeometria/Imagen')
        datos_generales_y_geometria.Imagen = base64check(img.text) if (img is not None and img.text) else None
        img = self.xmltree.find('./DatosGeneralesyGeometria/Plano')
        datos_generales_y_geometria.Plano = base64check(img.text) if (img is not None and img.text) else None
        for attr in ['NumeroDePlantasBajoRasante',
                     'PorcentajeSuperficieHabitableCalefactada',
                     'PorcentajeSuperficieHabitableRefrigerada']:
            setattr(datos_generales_y_geometria, attr, self.asint(self.xmltree, './DatosGeneralesyGeometria/%s' % attr))
        for attr in ['SuperficieHabitable',
                     'VolumenEspacioHabitable',
                     'Compacidad',
                     'PorcentajeSuperficieAcristalada',
                     'DensidadFuentesInternas',
                     'VentilacionUsoResidencial',
                     'VentilacionTotal',
                     'DemandaDiariaACS']:
            setattr(datos_generales_y_geometria, attr,
                    self.asfloat(self.xmltree, './DatosGeneralesyGeometria/%s' % attr, prec=2))
        datos_generales_y_geometria.PorcentajeSuperficieAcristalada = {
            key: self.asint(self.xmltree, './DatosGeneralesyGeometria/PorcentajeSuperficieAcristalada/%s' % key)
            for key in 'N NE E SE S SO O NO'.split()
            }

        return datos_generales_y_geometria

    def get_datos_envolvente_termica(self):
        datos_envolvente_termica = Bunch()

        datos_envolvente_termica.CerramientosOpacos = self.get_cerramientos_opacos()
        datos_envolvente_termica.HuecosyLucernarios = self.get_huecos_y_lucernarios()
        datos_envolvente_termica.PuentesTermicos = self.get_puentes_termicos()

        return datos_envolvente_termica

    def get_cerramientos_opacos(self):
        cerramientos_opacos = []

        elementos_opacos = self.xmltree.find('./DatosEnvolventeTermica/CerramientosOpacos')
        elementos_opacos = [] if elementos_opacos is None else elementos_opacos
        for elemento in elementos_opacos:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'Orientacion', 'ModoDeObtencion']:
                setattr(obj, attr, self.astext(elemento, './%s' % attr))
            for attr in ['Superficie', 'Transmitancia']:
                setattr(obj, attr, self.asfloat(elemento, './%s' % attr, prec=2))
            obj.Capas = []
            capas = elemento.find('./Capas')
            if capas is not None:
                for ecapa in elemento.find('./Capas'):
                    capa = Bunch()
                    capa.Material = self.astext(ecapa, './Material')
                    setattr(capa, 'Espesor',
                            self.asfloat(ecapa, './Espesor', prec=4))
                    setattr(capa, 'ConductividadTermica',
                            self.asfloat(ecapa, './ConductividadTermica', prec=3))
                    for attr in ['ResistenciaTermica', 'Densidad',
                                'FactorResistenciaVapor', 'CalorEspecifico']:
                        setattr(capa, attr, self.asfloat(ecapa, './%s' % attr, prec=2))
                    obj.Capas.append(capa)
            cerramientos_opacos.append(obj)

        return cerramientos_opacos

    def get_huecos_y_lucernarios(self):
        huecos_y_lucernarios = []

        elementos_huecos = self.xmltree.find('./DatosEnvolventeTermica/HuecosyLucernarios')
        elementos_huecos = [] if elementos_huecos is None else elementos_huecos
        for elemento in elementos_huecos:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'Orientacion',
                         'ModoDeObtencionTransmitancia',
                         'ModoDeObtencionFactorSolar']:
                setattr(obj, attr, self.astext(elemento, './%s' % attr))
            for attr in ['Superficie', 'Transmitancia', 'FactorSolar']:
                setattr(obj, attr, self.asfloat(elemento, './%s' % attr, prec=2))
            huecos_y_lucernarios.append(obj)

        return huecos_y_lucernarios

    def get_puentes_termicos(self):
        puentes_termicos = []

        elementos_pts = self.xmltree.find('./DatosEnvolventeTermica/PuentesTermicos')
        elementos_pts = [] if elementos_pts is None else elementos_pts
        for elemento in elementos_pts:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'ModoDeObtencion']:
                setattr(obj, attr, self.astext(elemento, './%s' % attr))
            for attr in ['Longitud', 'Transmitancia']:
                setattr(obj, attr, self.asfloat(elemento, './%s' % attr, prec=2))
            puentes_termicos.append(obj)

        return puentes_termicos

    def get_instalaciones_termicas(self):
        bb = Bunch()

        bb.GeneradoresDeCalefaccion, bb.totalpotenciageneradoresdecalefaccion = self.get_generadores_de_calefaccion()
        bb.GeneradoresDeRefrigeracion, bb.totalpotenciageneradoresderefrigeracion = self.get_generadores_de_refrigeracion()
        bb.InstalacionesACS = self.get_instalaciones_acs()
        bb.SistemasSecundariosCalefaccionRefrigeracion = self.get_sistemas_secundarios_calefaccion_refrigeracion()
        bb.TorresyRefrigeracion, bb.totalconsumotorresyrefrigeracion = self.get_torres_y_refrigeracion()
        bb.VentilacionyBombeo, bb.totalconsumoventilacionybombeo = self.get_ventilacion_y_bombeo()

        return bb

    def get_generadores_de_calefaccion(self):
        generadores_de_calefaccion = []

        elementos_generadores = self.xmltree.find('./InstalacionesTermicas/GeneradoresDeCalefaccion')
        elementos_generadores = [] if elementos_generadores is None else elementos_generadores
        for elemento in elementos_generadores:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'VectorEnergetico',
                         'ModoDeObtencion']:
                setattr(obj, attr, self.astext(elemento, './%s' % attr))
            for attr in ['PotenciaNominal', 'RendimientoNominal', 'RendimientoEstacional']:
                setattr(obj, attr, self.asfloat(elemento, './%s' % attr, prec=2))
            generadores_de_calefaccion.append(obj)

        total_potencia_generadores_de_calefaccion = sum(
            e.PotenciaNominal for e in generadores_de_calefaccion if e.PotenciaNominal < ALERT)

        return generadores_de_calefaccion, total_potencia_generadores_de_calefaccion

    def get_generadores_de_refrigeracion(self):
        generadores_de_refrigeracion = []

        elementos_generadores = self.xmltree.find('./InstalacionesTermicas/GeneradoresDeRefrigeracion')
        elementos_generadores = [] if elementos_generadores is None else elementos_generadores
        for elemento in elementos_generadores:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'VectorEnergetico',
                         'ModoDeObtencion']:
                setattr(obj, attr, self.astext(elemento, './%s' % attr))
            for attr in ['PotenciaNominal', 'RendimientoNominal', 'RendimientoEstacional']:
                setattr(obj, attr, self.asfloat(elemento, './%s' % attr, prec=2))
            generadores_de_refrigeracion.append(obj)

        total_potencia_generadores_de_refrigeracion = sum(
            e.PotenciaNominal for e in generadores_de_refrigeracion if e.PotenciaNominal < ALERT)

        return generadores_de_refrigeracion, total_potencia_generadores_de_refrigeracion

    def get_instalaciones_acs(self):
        instalaciones_acs = []

        elementos_generadores = self.xmltree.find('./InstalacionesTermicas/InstalacionesACS')
        elementos_generadores = [] if elementos_generadores is None else elementos_generadores
        for elemento in elementos_generadores:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'VectorEnergetico',
                         'ModoDeObtencion']:
                setattr(obj, attr, self.astext(elemento, './%s' % attr))
            for attr in ['PotenciaNominal', 'RendimientoNominal', 'RendimientoEstacional']:
                setattr(obj, attr, self.asfloat(elemento, './%s' % attr, prec=2))
            instalaciones_acs.append(obj)

        return instalaciones_acs

    def get_sistemas_secundarios_calefaccion_refrigeracion(self):
        sistemas_secundarios_calefaccion_refrigeracion = []

        elementos_secundarios = self.xmltree.find('./InstalacionesTermicas/SistemasSecundariosCalefaccionRefrigeracion')
        elementos_secundarios = [] if elementos_secundarios is None else elementos_secundarios
        for elemento in elementos_secundarios:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'ZonaAsociada',
                         'EnfriamientoEvaporativo', 'RecuperacionEnergia',
                         'EnfriamentoGratuito', 'TipoControl']:
                setattr(obj, attr, self.astext(elemento, './%s' % attr))
            for attr in ['PotenciaCalor', 'PotenciaFrio', 'RendimentoCalor', 'RendimientoFrio',
                         'RendimientoEstacionalCalor', 'RendimientoEstacionalFrio']:
                setattr(obj, attr, self.asfloat(elemento, './%s' % attr, prec=2))
            sistemas_secundarios_calefaccion_refrigeracion.append(obj)

        return sistemas_secundarios_calefaccion_refrigeracion

    def get_torres_y_refrigeracion(self):
        torres_y_refrigeracion = []

        elementos_torres = self.xmltree.find('./InstalacionesTermicas/TorresyRefrigeracion')
        elementos_torres = [] if elementos_torres is None else elementos_torres
        for elemento in elementos_torres:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'ServicioAsociado']:
                setattr(obj, attr, self.astext(elemento, './%s' % attr))
            for attr in ['ConsumoDeEnergia']:
                setattr(obj, attr, self.asfloat(elemento, './%s' % attr, prec=2))
            torres_y_refrigeracion.append(obj)

        total_consumo_torres_y_refrigeracion = sum(e.ConsumoDeEnergia for e in torres_y_refrigeracion)

        return torres_y_refrigeracion, total_consumo_torres_y_refrigeracion

    def get_ventilacion_y_bombeo(self):
        ventilacion_y_bombeo = []

        elementos_ventilacion = self.xmltree.find('./InstalacionesTermicas/VentilacionyBombeo')
        elementos_ventilacion = [] if elementos_ventilacion is None else elementos_ventilacion
        for elemento in elementos_ventilacion:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'ServicioAsociado']:
                setattr(obj, attr, self.astext(elemento, './%s' % attr))
            for attr in ['ConsumoDeEnergia']:
                setattr(obj, attr, self.asfloat(elemento, './%s' % attr, prec=2))
            ventilacion_y_bombeo.append(obj)

        total_consumo_ventilacion_y_bombeo = sum(e.ConsumoDeEnergia for e in ventilacion_y_bombeo)

        return ventilacion_y_bombeo, total_consumo_ventilacion_y_bombeo

    def get_condiciones_funcionamiento_y_ocupacion(self):
        condiciones_funcionamiento_y_ocupacion = []

        elementoscond = self.xmltree.find('./CondicionesFuncionamientoyOcupacion')
        elementoscond = [] if elementoscond is None else elementoscond
        for elemento in elementoscond:
            obj = Bunch()
            for attr in ['Nombre', 'NivelDeAcondicionamiento', 'PerfilDeUso']:
                setattr(obj, attr, self.astext(elemento, './%s' % attr))
            for attr in ['Superficie']:
                setattr(obj, attr, self.asfloat(elemento, './%s' % attr, prec=2))
            condiciones_funcionamiento_y_ocupacion.append(obj)

        superficies = dict((e.Nombre, e.Superficie) for e in condiciones_funcionamiento_y_ocupacion)

        return condiciones_funcionamiento_y_ocupacion, superficies

    def get_instalaciones_iluminacion(self):
        instalaciones_iluminacion = Bunch()

        instalaciones_iluminacion.PotenciaTotalInstalada = self.asfloat(self.xmltree,
                                        './InstalacionesIluminacion/PotenciaTotalInstalada', prec=2)
        instalaciones_iluminacion.Espacios = []
        elementosilumina = self.xmltree.find('./InstalacionesIluminacion')
        elementosilumina = [] if elementosilumina is None else elementosilumina
        for elemento in elementosilumina:
            if elemento.tag == 'PotenciaTotalInstalada':
                continue
            obj = Bunch()
            for attr in ['Nombre', 'ModoDeObtencion']:
                setattr(obj, attr, self.astext(elemento, './%s' % attr))
            for attr in ['PotenciaInstalada', 'VEEI', 'IluminanciaMedia']:
                setattr(obj, attr, self.asfloat(elemento, './%s' % attr, prec=2))
            instalaciones_iluminacion.Espacios.append(obj)
        return instalaciones_iluminacion

    def get_energias_renovables(self):
        energias_renovables = Bunch()

        energias_renovables.Termica, energias_renovables.totaltermica = self.get_energia_renovable_termica()
        energias_renovables.Electrica, energias_renovables.totalelectrica = self.get_energia_renovable_electrica()

        return energias_renovables

    def get_energia_renovable_termica(self):
        energia_renovable_termica = []

        elementosertermica = self.xmltree.find('./EnergiasRenovables/Termica')
        elementosertermica = [] if elementosertermica is None else elementosertermica
        for elemento in elementosertermica:
            obj = Bunch()
            for attr in ['Nombre']:
                setattr(obj, attr, self.astext(elemento, './%s' % attr))
            for attr in ['ConsumoFinalCalefaccion', 'ConsumoFinalRefrigeracion',
                         'ConsumoFinalACS', 'DemandaACS']:
                setattr(obj, attr, self.asfloat(elemento, './%s' % attr, prec=2))
            energia_renovable_termica.append(obj)

        energia_renovable_total_termica = self.get_energia_renovable_total_termica(energia_renovable_termica)

        return energia_renovable_termica, energia_renovable_total_termica

    def get_energia_renovable_total_termica(self, termica):

        total_termica = Bunch()

        _noneaszero = lambda x: x if x is not None else 0

        total_termica.ConsumoFinalCalefaccion = sum(_noneaszero(getattr(e, 'ConsumoFinalCalefaccion', 0)) for e in termica)
        total_termica.ConsumoFinalRefrigeracion = sum(_noneaszero(getattr(e, 'ConsumoFinalRefrigeracion', 0)) for e in termica)
        total_termica.ConsumoFinalACS = sum(_noneaszero(getattr(e, 'ConsumoFinalACS', 0)) for e in termica)
        total_termica.DemandaACS = sum(_noneaszero(getattr(e, 'DemandaACS', 0)) for e in termica)

        return total_termica

    def get_energia_renovable_electrica(self):
        energia_renovable_electrica = []

        elementos_er_electrica = self.xmltree.find('./EnergiasRenovables/Electrica')
        elementos_er_electrica = [] if elementos_er_electrica is None else elementos_er_electrica
        for elemento in elementos_er_electrica:
            obj = Bunch()
            for attr in ['Nombre']:
                setattr(obj, attr, self.astext(elemento, './%s' % attr))
            for attr in ['EnergiaGeneradaAutoconsumida']:
                setattr(obj, attr, self.asfloat(elemento, './%s' % attr, prec=2))
            energia_renovable_electrica.append(obj)

        energia_renovable_total_electrica = sum(e.EnergiaGeneradaAutoconsumida for e in energia_renovable_electrica)

        return energia_renovable_electrica, energia_renovable_total_electrica

    def get_demanda(self):
        demanda = Bunch()

        demanda.EdificioObjeto = Bunch()
        for attr in ['Global', 'Calefaccion', 'Refrigeracion', 'ACS',
                     'Conjunta', 'Calefaccion08', 'Refrigeracion08',
                     'Conjunta08', 'Ahorro08']:
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
        consumo.FactoresdePaso = self.get_factores_de_paso()
        (consumo.EnergiaFinalVectores,
         consumo.EnergiaFinalPorVector,
         consumo.EnergiaFinalPorServicio) = self.get_energia_final_vectores()
        consumo.EnergiaFinal = self.get_energia_final_por_servicios(consumo.EnergiaFinalVectores)
        consumo.EnergiaPrimariaNoRenovable = self.get_energia_primaria_no_renovable()

        consumo.Exigencias = Bunch()
        consumo.Exigencias.LimiteViviendaGlobalEPNR = self.asfloat(self.xmltree,
                                                                   './Consumo/Exigencias/LimiteViviendaGlobalEPNR',
                                                                   prec=2)

        return consumo

    def get_factores_de_paso(self):
        factores_de_paso = Bunch()

        final_a_primaria_no_renovable = Bunch()
        for attr in VECTORES:
            value = './Consumo/FactoresdePaso/FinalAPrimariaNoRenovable/%s' % attr
            setattr(final_a_primaria_no_renovable, attr, self.asfloat(self.xmltree, value, prec=3))
        factores_de_paso.FinalAPrimariaNoRenovable = final_a_primaria_no_renovable

        final_a_emisiones = Bunch()
        for attr in VECTORES:
            setattr(final_a_emisiones, attr, self.asfloat(self.xmltree,
                                                          './Consumo/FactoresdePaso/FinalAEmisiones/%s' % attr,
                                                          prec=3))
        factores_de_paso.FinalAEmisiones = final_a_emisiones

        return factores_de_paso

    def get_energia_final_vectores(self):
        energia_final_vectores = Bunch()
        energia_final_por_vector = {}
        energia_final_por_servicio = defaultdict(float)

        for vec in VECTORES:
            vector = Bunch()
            if self.xmltree.find('./Consumo/EnergiaFinalVectores/%s' % vec) is not None:
                total_por_vector = 0
                for servicio in SERVICIOS:
                    energia = self.asfloat(self.xmltree,
                                           './Consumo/EnergiaFinalVectores/%s/%s' % (vec, servicio),
                                           prec=2)
                    setattr(vector, servicio, energia)

                    if servicio != 'Global' and energia is not None:
                        total_por_vector += energia
                        energia_final_por_servicio[servicio] += energia

                setattr(energia_final_vectores, vec, vector)

                # Si el vector tiene un campo Global, usamos ese campo. Si no, sumamos todos los demás
                if vector.get('Global', None) is not None:
                    energia_final_por_vector[vec] = vector['Global']
                else:
                    energia_final_por_vector[vec] = total_por_vector

        return energia_final_vectores, energia_final_por_vector, dict(energia_final_por_servicio)

    def get_energia_final_por_servicios(self, energia_final_vectores):
        energia_final_por_servicios = Bunch()

        for vector in VECTORES:
            vecdata = getattr(energia_final_vectores, vector, None)
            if vecdata is None:
                continue
            for servicio in SERVICIOS:
                veccval = getattr(vecdata, servicio, 0.0)
                if veccval is None:
                    continue
                cval = getattr(energia_final_por_servicios, servicio, 0.0)
                cval = 0.0 if cval is None else cval
                setattr(energia_final_por_servicios, servicio, cval + veccval)
        if not getattr(energia_final_por_servicios, 'Global', None):
            globalservicios = sum(getattr(energia_final_por_servicios, servicio, 0.0)
                                  for servicio in SERVICIOS if servicio != 'Global')
            setattr(energia_final_por_servicios, 'Global', globalservicios)

        return energia_final_por_servicios

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

        escala = self.xmltree.find('./Calificacion/Demanda/EscalaCalefaccion')
        if escala is not None:
            dd = Bunch()
            for nivel in NIVELESESCALA:
                setattr(dd, nivel, self.asfloat(escala, './%s' % nivel, prec=2))
            calificacion_demanda.EscalaCalefaccion = dd

        escala = self.xmltree.find('./Calificacion/Demanda/EscalaRefrigeracion')
        if escala is not None:
            dd = Bunch()
            for nivel in NIVELESESCALA:
                setattr(dd, nivel, self.asfloat(escala, './%s' % nivel, prec=2))
            calificacion_demanda.EscalaRefrigeracion = dd

        calificacion_demanda.Calefaccion = self.astext(self.xmltree, './Calificacion/Demanda/Calefaccion')
        calificacion_demanda.Refrigeracion = self.astext(self.xmltree, './Calificacion/Demanda/Calefaccion')

        return calificacion_demanda

    def get_calificacion_energia_primaria_no_renovable(self):
        calificacion_energia_primaria_no_renovable = Bunch()

        escala = self.xmltree.find('./Calificacion/EnergiaPrimariaNoRenovable/EscalaGlobal')
        if escala is not None:
            escala_global = Bunch()
            for nivel in NIVELESESCALA:
                setattr(escala_global, nivel, self.asfloat(escala, './%s' % nivel, prec=2))
            calificacion_energia_primaria_no_renovable.EscalaGlobal = escala_global

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

    def get_medidas_de_mejora(self):
        medidas_de_mejora = []

        medidas = self.xmltree.find('./MedidasDeMejora')
        medidas = [] if medidas is None else medidas
        for medida in medidas:
            medida_de_mejora = Bunch()

            for attr in 'Nombre Descripcion CosteEstimado OtrosDatos'.split():
                txt = self.astext(medida, './%s' % attr)
                setattr(medida_de_mejora, attr, txt)

            medida_de_mejora.Demanda = Bunch()
            for attr in 'Global GlobalDiferenciaSituacionInicial Calefaccion Refrigeracion'.split():
                setattr(medida_de_mejora.Demanda, attr, self.asfloat(medida, './Demanda/%s' % attr, prec=2))

            medida_de_mejora.CalificacionDemanda = Bunch()
            for attr in 'Calefaccion Refrigeracion'.split():
                setattr(medida_de_mejora.CalificacionDemanda, attr,
                        self.astext(medida, './CalificacionDemanda/%s' % attr))

            medida_de_mejora.EnergiaFinal = Bunch()
            for attr in SERVICIOS:
                setattr(medida_de_mejora.EnergiaFinal, attr, self.asfloat(medida, './EnergiaFinal/%s' % attr, prec=2))

            medida_de_mejora.EnergiaPrimariaNoRenovable = Bunch()
            for attr in SERVICIOS:
                setattr(medida_de_mejora.EnergiaPrimariaNoRenovable, attr,
                        self.asfloat(medida, './EnergiaPrimariaNoRenovable/%s' % attr, prec=2))
            medida_de_mejora.EnergiaPrimariaNoRenovable.GlobalDiferenciaSituacionInicial = self.asfloat(medida,
                                                    './EnergiaPrimariaNoRenovable/GlobalDiferenciaSituacionInicial',
                                                    prec=2)

            medida_de_mejora.CalificacionEnergiaPrimariaNoRenovable = Bunch()
            for attr in SERVICIOS:
                setattr(medida_de_mejora.CalificacionEnergiaPrimariaNoRenovable, attr,
                        self.astext(medida, './CalificacionEnergiaPrimariaNoRenovable/%s' % attr))

            medida_de_mejora.EmisionesCO2 = Bunch()
            for attr in SERVICIOS:
                setattr(medida_de_mejora.EmisionesCO2, attr, self.asfloat(medida,
                                                                          './EmisionesCO2/%s' % attr, prec=2))
            medida_de_mejora.EmisionesCO2.GlobalDiferenciaSituacionInicial = self.asfloat(medida,
                                                                                          './EmisionesCO2/GlobalDiferenciaSituacionInicial',
                                                                                          prec=2)

            medida_de_mejora.CalificacionEmisionesCO2 = Bunch()
            for attr in SERVICIOS:
                setattr(medida_de_mejora.CalificacionEmisionesCO2, attr,
                        self.astext(medida, './CalificacionEmisionesCO2/%s' % attr))

            medidas_de_mejora.append(medida_de_mejora)

        return medidas_de_mejora

    def get_pruebas_comprobaciones_inspecciones(self):
        pruebas_comprobaciones_inspecciones = []

        pruebas = self.xmltree.find('./PruebasComprobacionesInspecciones')
        pruebas = [] if pruebas is None else pruebas
        for prueba in pruebas:
            bb = Bunch()
            bb.FechaVisita = self.astext(prueba, './FechaVisita')
            txt = self.astext(prueba, './Datos')
            bb.Datos = txt
            pruebas_comprobaciones_inspecciones.append(bb)

        return pruebas_comprobaciones_inspecciones

    def get_datos_personalizados(self):
        txt = self.astext(self.xmltree, './DatosPersonalizados')
        return txt

    def validate(self):
        """Valida el informe XML según el esquema XSD"""
        # http://lxml.de/validation.html
        if self.version.startswith('1'):
            self.xmlschema = lxml.etree.XMLSchema(lxml.etree.parse(open(XSDPATH1, encoding='UTF-8')))
        else:
            self.xmlschema = lxml.etree.XMLSchema(lxml.etree.parse(open(XSDPATH2, encoding='UTF-8')))
        self.xmlschema.validate(self.xmltree)

        errors = [(error.line, error.message) for error in self.xmlschema.error_log]
        self.errors['validation_errors'] += errors

    def analize(self):
        """Analiza contenidos de un Informe XML en busca de posibles errores"""
        if self.data is None:
            return

        zci = self.data.IdentificacionEdificio.ZonaClimatica[:-1]
        zcv = self.data.IdentificacionEdificio.ZonaClimatica[-1]
        esvivienda = self.esvivienda

        info = self.errors['info']
        if self.data.IdentificacionEdificio.AnoConstruccion == '-':
            info.append(('AVISO', 'No se ha definido el año de construcción', "IdentificacionEdificio.AnoConstruccion"))
        if self.data.IdentificacionEdificio.ReferenciaCatastral == '-':
            info.append(('AVISO', 'No se ha definido la referencia catastral',"IdentificacionEdificio.ReferenciaCatastral"))
        if self.data.DatosGeneralesyGeometria.DemandaDiariaACS <= 0.0:
            info.append(('AVISO', 'Demanda diaria de ACS nula',"DatosGeneralesyGeometria.DemandaDiariaACS"))

        suphabitable = sum([obj.Superficie for obj in self.data.CondicionesFuncionamientoyOcupacion if obj.NivelDeAcondicionamiento != 'NoHabitable'])
        if suphabitable > 1.1 * self.data.DatosGeneralesyGeometria.SuperficieHabitable:
            info.append(('ERROR', 'Superficie habitable menor que suma de la superficie de los espacios', "DatosGeneralesyGeometria.SuperficieHabitable"))
        if zcv not in '1234':
            info.append(('ERROR', 'Zona climática de verano incorrecta', "IdentificacionEdificio.ZonaClimatica"))
        if zci not in ['A', 'B', 'C', 'D', 'E', 'alfa', 'alpha']:
            info.append(('ERROR', 'Zona climática de invierno incorrecta', "IdentificacionEdificio.ZonaClimatica"))

        plano_ = self.data.DatosGeneralesyGeometria.Plano
        if not plano_:
            info.append(('AVISO', 'Sin datos de plano', "DatosGeneralesyGeometria.Plano"))
        elif not base64check(plano_):
            info.append(('AVISO', 'Datos de plano incorrectos', "DatosGeneralesyGeometria.Plano"))

        imagen_ = self.data.DatosGeneralesyGeometria.Imagen
        if not imagen_:
            info.append(('AVISO', 'Sin datos de imagen', "DatosGeneralesyGeometria.Imagen"))
        elif not base64check(imagen_):
            info.append(('AVISO', 'Datos de imagen incorrectos', "DatosGeneralesyGeometria.Imagen"))

        if ((0 > self.data.DatosGeneralesyGeometria.PorcentajeSuperficieHabitableCalefactada > 100) or
                (0 > self.data.DatosGeneralesyGeometria.PorcentajeSuperficieHabitableRefrigerada > 100)):
            info.append(('ERROR', 'Porcentajes de superficies acondicionadas fuera de rango',"DatosGeneralesyGeometria.PorcentajeSuperficieHabitableCalefactada", ""))

        if esvivienda:
            # Sin chequear
            if (zcv == '1' and
                    (self.data.Demanda.EdificioDeReferencia.Refrigeracion or
                     self.data.Calificacion.EmisionesCO2.Refrigeracion or
                     self.data.Calificacion.Demanda.Refrigeracion or
                     self.data.Calificacion.EnergiaPrimariaNoRenovable.Refrigeracion)):
                info.append(('ERROR',
                             'Zona sin demanda de refrigeración de referencia y para el que se ha definido calificación para ese servicio', ""))
            # Sin chequear
            if (zci in ('alpha', 'alfa', 'a') and
                    (self.data.Demanda.EdificioDeReferencia.Calefaccion or
                     self.data.Calificacion.EmisionesCO2.Calefaccion or
                     self.data.Calificacion.Demanda.Calefaccion or
                     self.data.Calificacion.EnergiaPrimariaNoRenovable.Calefaccion)):
                info.append(('ERROR',
                             'Zona sin demanda de calefacción de referencia y para la que se ha definido calificación para ese servicio', ""))

        if not esvivienda:
            if not self.data.InstalacionesTermicas.SistemasSecundariosCalefaccionRefrigeracion:
                info.append(('AVISO', 'No se han definido sistemas secundarios de calefacción y/o refrigeración', ""))
            if not self.data.InstalacionesTermicas.VentilacionyBombeo:
                info.append(('AVISO', 'No se han definido sistemas de ventilación y bombeo', ""))

        def _visit(res, ckey, obj):
            """Incluye en res la lista de valores numéricos con sus etiquetas"""

            if isinstance(obj, numbers.Number):
                res.append((obj, ckey))
            elif isinstance(obj, (list, tuple)):
                for item in obj:
                    _visit(res, ckey, item)
            elif isinstance(obj, (Bunch,)):
                for key in obj.keys():
                    if key.startswith('_'):
                        continue
                    _visit(res, key, obj[key])

        values = []
        _visit(values, 'root', self.data)
        suspects = [key for (value, key) in values if value >= ALERT]
        if suspects:
            info.append(('AVISO', 'Valores numéricos erróneos en : %s' % ', '.join(set(suspects)), ""))

        for i in range(len(info)):
            info[i] = (info[i][0], info[i][1], info[i][2].replace(".","\\\\.") )

